import { UserAgent, Registerer, Inviter, Invitation, SessionState } from 'sip.js';
import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';
import { MetricsCollector } from '../utils/metrics';
import { CallManager } from './CallManager';

export interface SIPConfig {
  server: string;
  username: string;
  password: string;
  domain: string;
  displayName?: string;
}

export interface SIPCall {
  id: string;
  session: Inviter | Invitation;
  direction: 'incoming' | 'outgoing';
  from: string;
  to: string;
  status: 'initiated' | 'ringing' | 'answered' | 'completed' | 'failed';
  startTime: Date;
  endTime?: Date;
  duration?: number;
}

export class SIPService extends EventEmitter {
  private logger: Logger;
  private userAgent: UserAgent;
  private registerer: Registerer;
  private activeCalls: Map<string, SIPCall> = new Map();
  private metrics: MetricsCollector;
  private isRegistered: boolean = false;

  constructor(
    private config: SIPConfig,
    private callManager: CallManager,
    metrics: MetricsCollector
  ) {
    super();
    this.logger = new Logger('SIPService');
    this.metrics = metrics;
    
    this.initializeUserAgent();
  }

  private initializeUserAgent(): void {
    const server = `sip:${this.config.server}`;
    
    this.userAgent = new UserAgent({
      uri: UserAgent.makeURI(`sip:${this.config.username}@${this.config.domain}`),
      transportOptions: {
        server,
      },
      authorizationUsername: this.config.username,
      authorizationPassword: this.config.password,
      displayName: this.config.displayName || this.config.username,
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    // Обработка входящих звонков
    this.userAgent.delegate = {
      onInvite: (invitation: Invitation) => {
        this.handleIncomingCall(invitation);
      },
    };

    // Обработка состояния регистрации
    this.userAgent.on('registered', () => {
      this.isRegistered = true;
      this.logger.info('SIP регистрация успешна');
      this.emit('registered');
    });

    this.userAgent.on('unregistered', () => {
      this.isRegistered = false;
      this.logger.warn('SIP регистрация потеряна');
      this.emit('unregistered');
    });

    // Обработка ошибок
    this.userAgent.on('invite', (invitation: Invitation) => {
      this.logger.info('Получено SIP приглашение', { 
        from: invitation.remoteIdentity?.uri?.toString(),
        to: invitation.localIdentity?.uri?.toString()
      });
    });
  }

  async start(): Promise<void> {
    try {
      this.logger.info('Запуск SIP сервиса...');
      
      // Запуск UserAgent
      await this.userAgent.start();
      
      // Регистрация
      this.registerer = new Registerer(this.userAgent);
      await this.registerer.register();
      
      this.logger.info('SIP сервис запущен успешно');
      this.emit('started');
      
    } catch (error) {
      this.logger.error('Ошибка при запуске SIP сервиса', { error });
      throw error;
    }
  }

  async stop(): Promise<void> {
    try {
      this.logger.info('Остановка SIP сервиса...');
      
      // Завершение всех активных звонков
      for (const [callId, call] of this.activeCalls.entries()) {
        await this.endCall(callId, 'service_stop');
      }
      
      // Отмена регистрации
      if (this.registerer) {
        await this.registerer.unregister();
      }
      
      // Остановка UserAgent
      await this.userAgent.stop();
      
      this.logger.info('SIP сервис остановлен');
      this.emit('stopped');
      
    } catch (error) {
      this.logger.error('Ошибка при остановке SIP сервиса', { error });
      throw error;
    }
  }

  private async handleIncomingCall(invitation: Invitation): Promise<void> {
    const startTime = Date.now();
    
    try {
      const from = invitation.remoteIdentity?.uri?.toString() || 'unknown';
      const to = invitation.localIdentity?.uri?.toString() || 'unknown';
      const callId = invitation.id;
      
      this.logger.info('Обработка входящего SIP звонка', { callId, from, to });
      
      // Создание SIP звонка
      const sipCall: SIPCall = {
        id: callId,
        session: invitation,
        direction: 'incoming',
        from,
        to,
        status: 'initiated',
        startTime: new Date(),
      };
      
      this.activeCalls.set(callId, sipCall);
      
      // Создание звонка в CallManager
      const call = await this.callManager.createCall({
        phoneNumber: from,
        direction: 'incoming',
        status: 'initiated',
      });
      
      // Настройка обработчиков событий для сессии
      this.setupSessionHandlers(invitation, call.id);
      
      // Запись метрики
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('INVITE', 'success', duration / 1000);
      
      this.logger.info('Входящий SIP звонок обработан', { callId, callIdInManager: call.id });
      
      this.emit('call:incoming', { call, sipCall });
      
    } catch (error) {
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('INVITE', 'error', duration / 1000);
      this.metrics.recordError('sip_incoming_call_error');
      
      this.logger.error('Ошибка при обработке входящего SIP звонка', { error });
      
      // Отклонение звонка при ошибке
      try {
        await invitation.reject();
      } catch (rejectError) {
        this.logger.error('Ошибка при отклонении звонка', { error: rejectError });
      }
    }
  }

  async makeCall(to: string): Promise<string> {
    const startTime = Date.now();
    
    try {
      if (!this.isRegistered) {
        throw new Error('SIP сервис не зарегистрирован');
      }
      
      this.logger.info('Инициация исходящего SIP звонка', { to });
      
      // Создание приглашения
      const target = UserAgent.makeURI(`sip:${to}@${this.config.domain}`);
      if (!target) {
        throw new Error(`Неверный URI: ${to}`);
      }
      
      const inviter = new Inviter(this.userAgent, target);
      const callId = inviter.id;
      
      // Создание SIP звонка
      const sipCall: SIPCall = {
        id: callId,
        session: inviter,
        direction: 'outgoing',
        from: this.userAgent.uri?.toString() || 'unknown',
        to: target.toString(),
        status: 'initiated',
        startTime: new Date(),
      };
      
      this.activeCalls.set(callId, sipCall);
      
      // Создание звонка в CallManager
      const call = await this.callManager.createCall({
        phoneNumber: to,
        direction: 'outgoing',
        status: 'initiated',
      });
      
      // Настройка обработчиков событий
      this.setupSessionHandlers(inviter, call.id);
      
      // Отправка приглашения
      await inviter.invite();
      
      // Запись метрики
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('INVITE', 'success', duration / 1000);
      
      this.logger.info('Исходящий SIP звонок инициирован', { callId, callIdInManager: call.id });
      
      this.emit('call:outgoing', { call, sipCall });
      
      return callId;
      
    } catch (error) {
      const duration = Date.now() - startTime;
      this.metrics.recordSipRequest('INVITE', 'error', duration / 1000);
      this.metrics.recordError('sip_outgoing_call_error');
      
      this.logger.error('Ошибка при инициации исходящего SIP звонка', { error, to });
      throw error;
    }
  }

  private setupSessionHandlers(session: Inviter | Invitation, callId: string): void {
    // Обработка изменения состояния сессии
    session.stateChange.addListener((newState: SessionState) => {
      this.logger.debug('Изменение состояния SIP сессии', { 
        callId, 
        sessionId: session.id, 
        newState 
      });
      
      const sipCall = this.activeCalls.get(session.id);
      if (!sipCall) return;
      
      switch (newState) {
        case SessionState.Initial:
          sipCall.status = 'initiated';
          break;
        case SessionState.Establishing:
          sipCall.status = 'ringing';
          this.callManager.updateCallStatus(callId, 'ringing');
          this.emit('call:ringing', { sipCall });
          break;
        case SessionState.Established:
          sipCall.status = 'answered';
          this.callManager.updateCallStatus(callId, 'answered');
          this.emit('call:answered', { sipCall });
          break;
        case SessionState.Terminated:
          sipCall.status = 'completed';
          sipCall.endTime = new Date();
          sipCall.duration = sipCall.endTime.getTime() - sipCall.startTime.getTime();
          
          this.callManager.endCall(callId, {
            duration: Math.floor(sipCall.duration / 1000),
            status: 'completed',
          });
          
          this.activeCalls.delete(session.id);
          this.emit('call:ended', { sipCall });
          break;
      }
    });
  }

  async answerCall(callId: string): Promise<void> {
    try {
      const sipCall = this.activeCalls.get(callId);
      if (!sipCall) {
        throw new Error(`SIP звонок ${callId} не найден`);
      }
      
      if (sipCall.session instanceof Invitation) {
        await sipCall.session.accept();
        this.logger.info('SIP звонок принят', { callId });
      } else {
        throw new Error('Можно принимать только входящие звонки');
      }
      
    } catch (error) {
      this.logger.error('Ошибка при принятии SIP звонка', { error, callId });
      throw error;
    }
  }

  async rejectCall(callId: string, reason?: string): Promise<void> {
    try {
      const sipCall = this.activeCalls.get(callId);
      if (!sipCall) {
        throw new Error(`SIP звонок ${callId} не найден`);
      }
      
      if (sipCall.session instanceof Invitation) {
        await sipCall.session.reject();
        this.logger.info('SIP звонок отклонен', { callId, reason });
      } else {
        throw new Error('Можно отклонять только входящие звонки');
      }
      
      // Удаление из активных звонков
      this.activeCalls.delete(callId);
      
    } catch (error) {
      this.logger.error('Ошибка при отклонении SIP звонка', { error, callId });
      throw error;
    }
  }

  async endCall(callId: string, reason?: string): Promise<void> {
    try {
      const sipCall = this.activeCalls.get(callId);
      if (!sipCall) {
        throw new Error(`SIP звонок ${callId} не найден`);
      }
      
      await sipCall.session.bye();
      this.logger.info('SIP звонок завершен', { callId, reason });
      
    } catch (error) {
      this.logger.error('Ошибка при завершении SIP звонка', { error, callId });
      throw error;
    }
  }

  getActiveCalls(): SIPCall[] {
    return Array.from(this.activeCalls.values());
  }

  getCall(callId: string): SIPCall | undefined {
    return this.activeCalls.get(callId);
  }

  isServiceRegistered(): boolean {
    return this.isRegistered;
  }
}
