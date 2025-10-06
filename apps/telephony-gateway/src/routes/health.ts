import { Router, Request, Response } from 'express';
import { CallManager } from '../services/CallManager';
import { DatabaseService } from '../services/DatabaseService';
import { RedisService } from '../services/RedisService';

const router = Router();

// Получение экземпляров сервисов (должны быть переданы из app)
let callManager: CallManager;
let databaseService: DatabaseService;
let redisService: RedisService;

export function setServices(
  callManagerInstance: CallManager,
  databaseServiceInstance: DatabaseService,
  redisServiceInstance: RedisService
) {
  callManager = callManagerInstance;
  databaseService = databaseServiceInstance;
  redisService = redisServiceInstance;
}

// Базовый health check
router.get('/', (req: Request, res: Response) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'telephony-gateway',
    version: process.env.APP_VERSION || '1.0.0',
  });
});

// Детальный health check
router.get('/detailed', async (req: Request, res: Response) => {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'telephony-gateway',
    version: process.env.APP_VERSION || '1.0.0',
    checks: {
      database: { status: 'unknown', message: '' },
      redis: { status: 'unknown', message: '' },
      callManager: { status: 'unknown', message: '' },
    },
  };

  let overallStatus = 'ok';

  // Проверка базы данных
  try {
    await databaseService.healthCheck();
    health.checks.database = { status: 'ok', message: 'Database connection is healthy' };
  } catch (error) {
    health.checks.database = { 
      status: 'error', 
      message: `Database error: ${error instanceof Error ? error.message : 'Unknown error'}` 
    };
    overallStatus = 'error';
  }

  // Проверка Redis
  try {
    await redisService.healthCheck();
    health.checks.redis = { status: 'ok', message: 'Redis connection is healthy' };
  } catch (error) {
    health.checks.redis = { 
      status: 'error', 
      message: `Redis error: ${error instanceof Error ? error.message : 'Unknown error'}` 
    };
    overallStatus = 'error';
  }

  // Проверка CallManager
  try {
    const activeCalls = callManager.getActiveCalls();
    const activeSessions = callManager.getActiveSessions();
    health.checks.callManager = { 
      status: 'ok', 
      message: `Active calls: ${activeCalls.length}, Active sessions: ${activeSessions.length}` 
    };
  } catch (error) {
    health.checks.callManager = { 
      status: 'error', 
      message: `CallManager error: ${error instanceof Error ? error.message : 'Unknown error'}` 
    };
    overallStatus = 'error';
  }

  health.status = overallStatus;

  const statusCode = overallStatus === 'ok' ? 200 : 503;
  res.status(statusCode).json(health);
});

// Readiness check (готовность к работе)
router.get('/ready', async (req: Request, res: Response) => {
  try {
    // Проверяем критические зависимости
    await databaseService.healthCheck();
    await redisService.healthCheck();
    
    res.json({
      status: 'ready',
      timestamp: new Date().toISOString(),
      message: 'Service is ready to handle requests',
    });
  } catch (error) {
    res.status(503).json({
      status: 'not ready',
      timestamp: new Date().toISOString(),
      message: `Service is not ready: ${error instanceof Error ? error.message : 'Unknown error'}`,
    });
  }
});

// Liveness check (живость сервиса)
router.get('/live', (req: Request, res: Response) => {
  res.json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    message: 'Service is alive',
  });
});

export { router as healthRoutes };
