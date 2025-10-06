import { v4 as uuidv4 } from 'uuid';
import { EventEmitter } from 'events';
import { DatabaseService } from './DatabaseService';
import { RedisService } from './RedisService';
import { MetricsCollector } from '../utils/metrics';
import { Logger } from '../utils/logger';

export interface Call {
  id: string;
  clientId?: string;
  phoneNumber: string;
  direction: 'incoming' | 'outgoing';
  status: 'initiated' | 'ringing' | 'answered' | 'completed' | 'failed' | 'busy' | 'no_answer';
  duration: number;
  recordingUrl?: string;
  transcript?: string;
  summary?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  confidenceScore?: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface CallSession {
  callId: string;
  sessionId: string;
  userId?: string;
  startTime: Date;
  lastActivity: Date;
  isActive: boolean;
}

export class CallManager extends EventEmitter {
  private logger: Logger;
  private activeCalls: Map<string, Call> = new Map();
  private activeSessions: Map<string, CallSession> = new Map();
  private metrics: MetricsCollector;

  constructor(
    private databaseService: DatabaseService,
    private redisService: RedisService,
    metrics: MetricsCollector
  ) {
    super();
    this.logger = new Logger('CallManager');
    this.metrics = metrics;
  }

  /**
   * Создать новый звонок
   */
  async createCall(callData: Partial<Call>): Promise<Call> {
    const call: Call = {
      id: uuidv4(),
      phoneNumber: callData.phoneNumber!,
      direction: callData.direction!,
      status: 'initiated',
      duration: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
      ...callData,
    };

    try {
      // Сохранение в базе данных
      await this.databaseService.createCall(call);
      
      // Сохранение в Redis для быстрого доступа
      await this.redisService.set(`call:${call.id}`, JSON.stringify(call), 3600);
      
      // Добавление в активные звонки
      this.activeCalls.set(call.id, call);
      
      // Запись метрики
      this.metrics.recordCall(call.direction, call.status);
      this.metrics.setActiveCalls(this.activeCalls.size);
      
      this.logger.info('Звонок создан', { callId: call.id, phoneNumber: call.phoneNumber });
      this.emit('call:created', call);
      
      return call;
    } catch (error) {
      this.logger.error('Ошибка при создании звонка', { error, callData });
      throw error;
    }
  }

  /**
   * Получить звонок по ID
   */
  async getCall(callId: string): Promise<Call | null> {
    try {
      // Сначала проверяем активные звонки
      let call = this.activeCalls.get(callId);
      
      if (!call) {
        // Проверяем Redis
        const callData = await this.redisService.get(`call:${callId}`);
        if (callData) {
          call = JSON.parse(callData);
          this.activeCalls.set(callId, call);
        } else {
          // Загружаем из базы данных
          call = await this.databaseService.getCall(callId);
          if (call) {
            await this.redisService.set(`call:${callId}`, JSON.stringify(call), 3600);
            this.activeCalls.set(callId, call);
          }
        }
      }
      
      return call;
    } catch (error) {
      this.logger.error('Ошибка при получении звонка', { error, callId });
      throw error;
    }
  }

  /**
   * Обновить статус звонка
   */
  async updateCallStatus(callId: string, status: Call['status']): Promise<Call | null> {
    try {
      const call = await this.getCall(callId);
      if (!call) {
        throw new Error(`Звонок ${callId} не найден`);
      }

      const oldStatus = call.status;
      call.status = status;
      call.updatedAt = new Date();

      // Обновление в базе данных
      await this.databaseService.updateCall(callId, { status });
      
      // Обновление в Redis
      await this.redisService.set(`call:${callId}`, JSON.stringify(call), 3600);
      
      // Обновление активных звонков
      this.activeCalls.set(callId, call);
      
      // Запись метрики
      this.metrics.recordCall(call.direction, status);
      
      this.logger.info('Статус звонка обновлен', { 
        callId, 
        oldStatus, 
        newStatus: status 
      });
      
      this.emit('call:statusUpdated', { call, oldStatus, newStatus: status });
      
      return call;
    } catch (error) {
      this.logger.error('Ошибка при обновлении статуса звонка', { error, callId, status });
      throw error;
    }
  }

  /**
   * Завершить звонок
   */
  async endCall(callId: string, endData: Partial<Call>): Promise<Call | null> {
    try {
      const call = await this.getCall(callId);
      if (!call) {
        throw new Error(`Звонок ${callId} не найден`);
      }

      // Обновление данных звонка
      Object.assign(call, endData);
      call.status = 'completed';
      call.updatedAt = new Date();

      // Обновление в базе данных
      await this.databaseService.updateCall(callId, endData);
      
      // Удаление из Redis
      await this.redisService.del(`call:${callId}`);
      
      // Удаление из активных звонков
      this.activeCalls.delete(callId);
      
      // Запись метрики
      this.metrics.recordCall(call.direction, 'completed', call.duration);
      this.metrics.setActiveCalls(this.activeCalls.size);
      
      this.logger.info('Звонок завершен', { 
        callId, 
        duration: call.duration,
        status: call.status 
      });
      
      this.emit('call:ended', call);
      
      return call;
    } catch (error) {
      this.logger.error('Ошибка при завершении звонка', { error, callId, endData });
      throw error;
    }
  }

  /**
   * Создать сессию звонка
   */
  async createCallSession(callId: string, userId?: string): Promise<CallSession> {
    const session: CallSession = {
      callId,
      sessionId: uuidv4(),
      userId,
      startTime: new Date(),
      lastActivity: new Date(),
      isActive: true,
    };

    try {
      // Сохранение в Redis
      await this.redisService.set(
        `session:${session.sessionId}`, 
        JSON.stringify(session), 
        3600
      );
      
      // Добавление в активные сессии
      this.activeSessions.set(session.sessionId, session);
      
      this.logger.info('Сессия звонка создана', { 
        sessionId: session.sessionId, 
        callId 
      });
      
      this.emit('session:created', session);
      
      return session;
    } catch (error) {
      this.logger.error('Ошибка при создании сессии звонка', { error, callId, userId });
      throw error;
    }
  }

  /**
   * Получить сессию по ID
   */
  async getCallSession(sessionId: string): Promise<CallSession | null> {
    try {
      // Сначала проверяем активные сессии
      let session = this.activeSessions.get(sessionId);
      
      if (!session) {
        // Проверяем Redis
        const sessionData = await this.redisService.get(`session:${sessionId}`);
        if (sessionData) {
          session = JSON.parse(sessionData);
          this.activeSessions.set(sessionId, session);
        }
      }
      
      return session;
    } catch (error) {
      this.logger.error('Ошибка при получении сессии звонка', { error, sessionId });
      throw error;
    }
  }

  /**
   * Обновить активность сессии
   */
  async updateSessionActivity(sessionId: string): Promise<void> {
    try {
      const session = await this.getCallSession(sessionId);
      if (!session) {
        return;
      }

      session.lastActivity = new Date();
      
      // Обновление в Redis
      await this.redisService.set(
        `session:${sessionId}`, 
        JSON.stringify(session), 
        3600
      );
      
      // Обновление активных сессий
      this.activeSessions.set(sessionId, session);
    } catch (error) {
      this.logger.error('Ошибка при обновлении активности сессии', { error, sessionId });
    }
  }

  /**
   * Завершить сессию звонка
   */
  async endCallSession(sessionId: string): Promise<void> {
    try {
      const session = await this.getCallSession(sessionId);
      if (!session) {
        return;
      }

      session.isActive = false;
      
      // Удаление из Redis
      await this.redisService.del(`session:${sessionId}`);
      
      // Удаление из активных сессий
      this.activeSessions.delete(sessionId);
      
      this.logger.info('Сессия звонка завершена', { sessionId });
      this.emit('session:ended', session);
    } catch (error) {
      this.logger.error('Ошибка при завершении сессии звонка', { error, sessionId });
    }
  }

  /**
   * Получить активные звонки
   */
  getActiveCalls(): Call[] {
    return Array.from(this.activeCalls.values());
  }

  /**
   * Получить активные сессии
   */
  getActiveSessions(): CallSession[] {
    return Array.from(this.activeSessions.values());
  }

  /**
   * Очистка неактивных сессий
   */
  async cleanupInactiveSessions(): Promise<void> {
    try {
      const now = new Date();
      const inactiveThreshold = 30 * 60 * 1000; // 30 минут
      
      for (const [sessionId, session] of this.activeSessions.entries()) {
        if (now.getTime() - session.lastActivity.getTime() > inactiveThreshold) {
          await this.endCallSession(sessionId);
        }
      }
      
      this.logger.info('Очистка неактивных сессий завершена');
    } catch (error) {
      this.logger.error('Ошибка при очистке неактивных сессий', { error });
    }
  }

  /**
   * Завершение работы менеджера звонков
   */
  async shutdown(): Promise<void> {
    try {
      this.logger.info('Завершение работы CallManager...');
      
      // Завершение всех активных сессий
      for (const sessionId of this.activeSessions.keys()) {
        await this.endCallSession(sessionId);
      }
      
      // Очистка активных звонков
      this.activeCalls.clear();
      this.activeSessions.clear();
      
      this.logger.info('CallManager завершен');
    } catch (error) {
      this.logger.error('Ошибка при завершении работы CallManager', { error });
      throw error;
    }
  }
}
