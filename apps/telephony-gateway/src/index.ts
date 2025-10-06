import express from 'express';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';

import { setupLogging } from './utils/logger';
import { setupTracing } from './utils/tracing';
import { setupMetrics } from './utils/metrics';
import { errorHandler } from './middleware/errorHandler';
import { requestLogger } from './middleware/requestLogger';
import { validateHeaders } from './middleware/validateRequest';

import { callRoutes } from './routes/calls';
import { healthRoutes } from './routes/health';
import { metricsRoutes } from './routes/metrics';

import { CallManager } from './services/CallManager';
import { SIPHandler } from './services/SIPHandler';
import { WebRTCHandler } from './services/WebRTCHandler';
import { DatabaseService } from './services/DatabaseService';
import { RedisService } from './services/RedisService';
import { SIPConfig } from './services/SIPService';

// Загрузка переменных окружения
dotenv.config();

const app = express();
const server = createServer(app);
const io = new SocketIOServer(server, {
  cors: {
    origin: process.env.CORS_ORIGINS?.split(',') || ['*'],
    methods: ['GET', 'POST'],
    credentials: true,
  },
});

// Настройка логирования, трассировки и метрик
setupLogging();
setupTracing('telephony-gateway');
const metrics = setupMetrics('telephony-gateway');

// Middleware
app.use(helmet());
app.use(compression());
app.use(cors({
  origin: process.env.CORS_ORIGINS?.split(',') || ['*'],
  credentials: true,
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 минут
  max: 100, // максимум 100 запросов с IP
  message: 'Слишком много запросов с этого IP',
});
app.use(limiter);

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Middleware для логирования и валидации
app.use(requestLogger);
app.use(validateHeaders);

// Конфигурация SIP
const sipConfig: SIPConfig = {
  server: process.env.SIP_SERVER || 'localhost',
  username: process.env.SIP_USERNAME || 'telephony-gateway',
  password: process.env.SIP_PASSWORD || 'password',
  domain: process.env.SIP_DOMAIN || 'localhost',
  displayName: process.env.SIP_DISPLAY_NAME || 'Sales Voice Assistant',
};

// Инициализация сервисов
const databaseService = new DatabaseService();
const redisService = new RedisService();
const callManager = new CallManager(databaseService, redisService, metrics);
const sipHandler = new SIPHandler(callManager, metrics, sipConfig);
const webrtcHandler = new WebRTCHandler(callManager, io, metrics);

// Инициализация подключений
async function initializeServices() {
  try {
    await redisService.connect();
    console.log('Redis подключен');
    
    await sipHandler.start();
    console.log('SIP Handler запущен');
  } catch (error) {
    console.error('Ошибка инициализации сервисов:', error);
  }
}

// Установка сервисов в маршруты
import { setCallManager } from './routes/calls';
import { setServices } from './routes/health';
import { setMetrics } from './routes/metrics';

setCallManager(callManager, metrics);
setServices(callManager, databaseService, redisService);
setMetrics(metrics);

// Маршруты
app.use('/api/v1/calls', callRoutes);
app.use('/health', healthRoutes);
app.use('/metrics', metricsRoutes);

// WebSocket соединения
io.on('connection', (socket) => {
  console.log('Новое WebSocket соединение:', socket.id);
  
  socket.on('join-call', (callId: string) => {
    socket.join(`call-${callId}`);
    console.log(`Клиент ${socket.id} присоединился к звонку ${callId}`);
  });
  
  socket.on('leave-call', (callId: string) => {
    socket.leave(`call-${callId}`);
    console.log(`Клиент ${socket.id} покинул звонок ${callId}`);
  });
  
  socket.on('disconnect', () => {
    console.log('WebSocket соединение закрыто:', socket.id);
  });
});

// Обработка ошибок
app.use(errorHandler);

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Получен сигнал SIGTERM, завершение работы...');
  
  try {
    await callManager.shutdown();
    await sipHandler.stop();
    await databaseService.close();
    await redisService.close();
    
    server.close(() => {
      console.log('HTTP сервер закрыт');
      process.exit(0);
    });
  } catch (error) {
    console.error('Ошибка при завершении работы:', error);
    process.exit(1);
  }
});

process.on('SIGINT', async () => {
  console.log('Получен сигнал SIGINT, завершение работы...');
  
  try {
    await callManager.shutdown();
    await sipHandler.stop();
    await databaseService.close();
    await redisService.close();
    
    server.close(() => {
      console.log('HTTP сервер закрыт');
      process.exit(0);
    });
  } catch (error) {
    console.error('Ошибка при завершении работы:', error);
    process.exit(1);
  }
});

// Запуск сервера
const PORT = process.env.PORT || 3000;

async function startServer() {
  try {
    await initializeServices();
    
    server.listen(PORT, () => {
      console.log(`Telephony Gateway запущен на порту ${PORT}`);
      console.log(`Окружение: ${process.env.NODE_ENV || 'development'}`);
      console.log(`Метрики доступны на /metrics`);
      console.log(`Health check доступен на /health`);
    });
  } catch (error) {
    console.error('Ошибка при запуске сервера:', error);
    process.exit(1);
  }
}

startServer();

export { app, server, io };
