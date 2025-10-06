import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';
import { MetricsCollector } from '../utils/metrics';
import { CallManager, Call } from './CallManager';
import { SIPService, SIPConfig } from './SIPService';

export interface SIPCall {
  id: string;
  from: string;
  to: string;
  direction: 'incoming' | 'outgoing';
  status: 'initiated' | 'ringing' | 'answered' | 'completed' | 'failed' | 'busy' | 'no_answer';
  startTime: Date;
  endTime?: Date;
  duration?: number;
}

export class SIPHandler extends EventEmitter {
  private logger: Logger;
  private sipService: SIPService;
  private metrics: MetricsCollector;

  constructor(
    private callManager: CallManager,
    metrics: MetricsCollector,
    sipConfig: SIPConfig
  ) {
    super();
    this.logger = new Logger('SIPHandler');
    this.metrics = metrics;
    this.sipService = new SIPService(sipConfig, callManager, metrics);
    
    this.setupSIPEventHandlers();
  }

  private setupSIPEventHandlers(): void {
    this.sipService.on('call:incoming', (data: { call: Call; sipCall: any }) => {
      this.emit('call:incoming', data);
    });

    this.sipService.on('call:outgoing', (data: { call: Call; sipCall: any }) => {
      this.emit('call:outgoing', data);
    });

    this.sipService.on('call:answered', (data: { sipCall: any }) => {
      this.emit('call:answered', data);
    });

    this.sipService.on('call:ended', (data: { sipCall: any }) => {
      this.emit('call:ended', data);
    });

    this.sipService.on('registered', () => {
      this.logger.info('SIP сервис зарегистрирован');
    });

    this.sipService.on('unregistered', () => {
      this.logger.warn('SIP сервис потерял регистрацию');
    });
  }

  async start(): Promise<void> {
    try {
      await this.sipService.start();
      this.logger.info('SIP Handler запущен');
    } catch (error) {
      this.logger.error('Ошибка при запуске SIP Handler', { error });
      throw error;
    }
  }

  async stop(): Promise<void> {
    try {
      await this.sipService.stop();
      this.logger.info('SIP Handler остановлен');
    } catch (error) {
      this.logger.error('Ошибка при остановке SIP Handler', { error });
      throw error;
    }
  }

  /**
   * Обработка входящего SIP звонка
   */
  async handleIncomingCall(sipData: {
    callId: string;
    from: string;
    to: string;
    headers: Record<string, string>;
  }): Promise<void> {
    const startTime = Date.now();
    
    try {
      this.logger.info('Обработка входящего SIP звонка', {
        callId: sipData.callId,
        from: sipData.from,
        to: sipData.to,
      });

      // Создание SIP звонка
      const sipCall: SIPCall = {
        id: sipData.callId,
        from: sipData.from,
        to: sipData.to,
        direction: 'incoming',
        status: 'initiated',
        startTime: new Date(),
      };

      this.activeSIPCalls.set(sipData.callId, sipCall);

      // Создание звонка в CallManager
      const call = await this.callManager.createCall({
        phoneNumber: sipData.from,
        direction: 'incoming',
        status: 'initiated',
      });

      // Связывание SIP звонка с CallManager звонком
      sipCall.id = call.id;

      // Запись метрики
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('INVITE', 'success', duration / 1000);

      this.logger.info('Входящий SIP звонок обработан', {
        callId: call.id,
        sipCallId: sipData.callId,
      });

      this.emit('call:incoming', { call, sipCall, sipData });

    } catch (error) {
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('INVITE', 'error', duration / 1000);
      this.metrics.recordError('sip_incoming_call_error');
      
      this.logger.error('Ошибка при обработке входящего SIP звонка', {
        error,
        callId: sipData.callId,
      });
      
      throw error;
    }
  }

  /**
   * Обработка исходящего SIP звонка
   */
  async handleOutgoingCall(sipData: {
    callId: string;
    from: string;
    to: string;
    headers: Record<string, string>;
  }): Promise<void> {
    const startTime = Date.now();
    
    try {
      this.logger.info('Обработка исходящего SIP звонка', {
        callId: sipData.callId,
        from: sipData.from,
        to: sipData.to,
      });

      // Создание SIP звонка
      const sipCall: SIPCall = {
        id: sipData.callId,
        from: sipData.from,
        to: sipData.to,
        direction: 'outgoing',
        status: 'initiated',
        startTime: new Date(),
      };

      this.activeSIPCalls.set(sipData.callId, sipCall);

      // Создание звонка в CallManager
      const call = await this.callManager.createCall({
        phoneNumber: sipData.to,
        direction: 'outgoing',
        status: 'initiated',
      });

      // Связывание SIP звонка с CallManager звонком
      sipCall.id = call.id;

      // Запись метрики
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('INVITE', 'success', duration / 1000);

      this.logger.info('Исходящий SIP звонок обработан', {
        callId: call.id,
        sipCallId: sipData.callId,
      });

      this.emit('call:outgoing', { call, sipCall, sipData });

    } catch (error) {
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('INVITE', 'error', duration / 1000);
      this.metrics.recordError('sip_outgoing_call_error');
      
      this.logger.error('Ошибка при обработке исходящего SIP звонка', {
        error,
        callId: sipData.callId,
      });
      
      throw error;
    }
  }

  /**
   * Обработка ответа на SIP звонок
   */
  async handleCallAnswered(sipCallId: string): Promise<void> {
    const startTime = Date.now();
    
    try {
      const sipCall = this.activeSIPCalls.get(sipCallId);
      if (!sipCall) {
        throw new Error(`SIP звонок ${sipCallId} не найден`);
      }

      this.logger.info('Обработка ответа на SIP звонок', { sipCallId });

      // Обновление статуса SIP звонка
      sipCall.status = 'answered';
      this.activeSIPCalls.set(sipCallId, sipCall);

      // Обновление статуса в CallManager
      await this.callManager.updateCallStatus(sipCall.id, 'answered');

      // Запись метрики
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('200 OK', 'success', duration / 1000);

      this.logger.info('Ответ на SIP звонок обработан', { sipCallId });

      this.emit('call:answered', { sipCall });

    } catch (error) {
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('200 OK', 'error', duration / 1000);
      this.metrics.recordError('sip_call_answered_error');
      
      this.logger.error('Ошибка при обработке ответа на SIP звонок', {
        error,
        sipCallId,
      });
      
      throw error;
    }
  }

  /**
   * Обработка завершения SIP звонка
   */
  async handleCallEnded(sipCallId: string, reason: string): Promise<void> {
    const startTime = Date.now();
    
    try {
      const sipCall = this.activeSIPCalls.get(sipCallId);
      if (!sipCall) {
        throw new Error(`SIP звонок ${sipCallId} не найден`);
      }

      this.logger.info('Обработка завершения SIP звонка', { sipCallId, reason });

      // Обновление SIP звонка
      sipCall.status = 'completed';
      sipCall.endTime = new Date();
      sipCall.duration = sipCall.endTime.getTime() - sipCall.startTime.getTime();

      // Завершение звонка в CallManager
      await this.callManager.endCall(sipCall.id, {
        duration: Math.floor(sipCall.duration / 1000), // в секундах
        status: 'completed',
      });

      // Удаление из активных SIP звонков
      this.activeSIPCalls.delete(sipCallId);

      // Запись метрики
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('BYE', 'success', duration / 1000);

      this.logger.info('SIP звонок завершен', {
        sipCallId,
        duration: sipCall.duration,
        reason,
      });

      this.emit('call:ended', { sipCall, reason });

    } catch (error) {
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('BYE', 'error', duration / 1000);
      this.metrics.recordError('sip_call_ended_error');
      
      this.logger.error('Ошибка при обработке завершения SIP звонка', {
        error,
        sipCallId,
        reason,
      });
      
      throw error;
    }
  }

  /**
   * Обработка ошибки SIP звонка
   */
  async handleCallError(sipCallId: string, errorCode: number, errorMessage: string): Promise<void> {
    const startTime = Date.now();
    
    try {
      const sipCall = this.activeSIPCalls.get(sipCallId);
      if (!sipCall) {
        throw new Error(`SIP звонок ${sipCallId} не найден`);
      }

      this.logger.error('Обработка ошибки SIP звонка', {
        sipCallId,
        errorCode,
        errorMessage,
      });

      // Обновление SIP звонка
      sipCall.status = 'failed';
      sipCall.endTime = new Date();
      sipCall.duration = sipCall.endTime.getTime() - sipCall.startTime.getTime();

      // Завершение звонка в CallManager с ошибкой
      await this.callManager.endCall(sipCall.id, {
        duration: Math.floor(sipCall.duration / 1000),
        status: 'failed',
      });

      // Удаление из активных SIP звонков
      this.activeSIPCalls.delete(sipCallId);

      // Запись метрики
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('ERROR', 'error', duration / 1000);
      this.metrics.recordError('sip_call_error');

      this.logger.info('SIP звонок завершен с ошибкой', {
        sipCallId,
        errorCode,
        errorMessage,
      });

      this.emit('call:error', { sipCall, errorCode, errorMessage });

    } catch (error) {
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('ERROR', 'error', duration / 1000);
      this.metrics.recordError('sip_call_error_handling_error');
      
      this.logger.error('Ошибка при обработке ошибки SIP звонка', {
        error,
        sipCallId,
        errorCode,
        errorMessage,
      });
      
      throw error;
    }
  }

  /**
   * Получить активные SIP звонки
   */
  getActiveSIPCalls(): SIPCall[] {
    return Array.from(this.activeSIPCalls.values());
  }

  /**
   * Получить SIP звонок по ID
   */
  getSIPCall(sipCallId: string): SIPCall | undefined {
    return this.activeSIPCalls.get(sipCallId);
  }

  /**
   * Очистка неактивных SIP звонков
   */
  async cleanupInactiveCalls(): Promise<void> {
    try {
      const now = new Date();
      const inactiveThreshold = 30 * 60 * 1000; // 30 минут
      
      for (const [sipCallId, sipCall] of this.activeSIPCalls.entries()) {
        if (now.getTime() - sipCall.startTime.getTime() > inactiveThreshold) {
          await this.handleCallEnded(sipCallId, 'timeout');
        }
      }
      
      this.logger.info('Очистка неактивных SIP звонков завершена');
    } catch (error) {
      this.logger.error('Ошибка при очистке неактивных SIP звонков', { error });
    }
  }

  /**
   * Завершение работы SIP обработчика
   */
  async shutdown(): Promise<void> {
    try {
      this.logger.info('Завершение работы SIPHandler...');
      
      // Завершение всех активных SIP звонков
      for (const sipCallId of this.activeSIPCalls.keys()) {
        await this.handleCallEnded(sipCallId, 'shutdown');
      }
      
      // Очистка активных звонков
      this.activeSIPCalls.clear();
      
      this.logger.info('SIPHandler завершен');
    } catch (error) {
      this.logger.error('Ошибка при завершении работы SIPHandler', { error });
      throw error;
    }
  }
}
