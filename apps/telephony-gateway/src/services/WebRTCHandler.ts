import { Server as SocketIOServer, Socket } from 'socket.io';
import { EventEmitter } from 'events';
import { Logger } from '../utils/logger';
import { MetricsCollector } from '../utils/metrics';
import { CallManager, Call } from './CallManager';

export interface WebRTCConnection {
  id: string;
  callId: string;
  socketId: string;
  userId?: string;
  status: 'connecting' | 'connected' | 'disconnected' | 'failed';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  localSDP?: string;
  remoteSDP?: string;
  iceCandidates: string[];
}

export class WebRTCHandler extends EventEmitter {
  private logger: Logger;
  private activeConnections: Map<string, WebRTCConnection> = new Map();
  private socketToConnection: Map<string, string> = new Map();
  private metrics: MetricsCollector;

  constructor(
    private callManager: CallManager,
    private io: SocketIOServer,
    metrics: MetricsCollector
  ) {
    super();
    this.logger = new Logger('WebRTCHandler');
    this.metrics = metrics;
    
    this.setupSocketHandlers();
  }

  private setupSocketHandlers(): void {
    this.io.on('connection', (socket: Socket) => {
      this.logger.info('Новое WebSocket соединение', { socketId: socket.id });

      // Обработка подключения к звонку
      socket.on('join-call', async (data: { callId: string; userId?: string }) => {
        try {
          await this.handleJoinCall(socket, data.callId, data.userId);
        } catch (error) {
          this.logger.error('Ошибка при подключении к звонку', { error, socketId: socket.id, callId: data.callId });
          socket.emit('error', { message: 'Ошибка при подключении к звонку' });
        }
      });

      // Обработка отключения от звонка
      socket.on('leave-call', async () => {
        try {
          await this.handleLeaveCall(socket);
        } catch (error) {
          this.logger.error('Ошибка при отключении от звонка', { error, socketId: socket.id });
        }
      });

      // Обработка WebRTC предложения
      socket.on('offer', async (data: { callId: string; sdp: string }) => {
        try {
          await this.handleOffer(socket, data.callId, data.sdp);
        } catch (error) {
          this.logger.error('Ошибка при обработке WebRTC предложения', { error, socketId: socket.id, callId: data.callId });
          socket.emit('error', { message: 'Ошибка при обработке предложения' });
        }
      });

      // Обработка WebRTC ответа
      socket.on('answer', async (data: { callId: string; sdp: string }) => {
        try {
          await this.handleAnswer(socket, data.callId, data.sdp);
        } catch (error) {
          this.logger.error('Ошибка при обработке WebRTC ответа', { error, socketId: socket.id, callId: data.callId });
          socket.emit('error', { message: 'Ошибка при обработке ответа' });
        }
      });

      // Обработка ICE кандидатов
      socket.on('ice-candidate', async (data: { callId: string; candidate: string }) => {
        try {
          await this.handleIceCandidate(socket, data.callId, data.candidate);
        } catch (error) {
          this.logger.error('Ошибка при обработке ICE кандидата', { error, socketId: socket.id, callId: data.callId });
        }
      });

      // Обработка отключения
      socket.on('disconnect', async () => {
        try {
          await this.handleDisconnect(socket);
        } catch (error) {
          this.logger.error('Ошибка при обработке отключения', { error, socketId: socket.id });
        }
      });

      // Обработка ошибок
      socket.on('error', (error) => {
        this.logger.error('Ошибка WebSocket', { error, socketId: socket.id });
        this.metrics.recordError('websocket_error');
      });
    });
  }

  private async handleJoinCall(socket: Socket, callId: string, userId?: string): Promise<void> {
    const startTime = Date.now();
    
    try {
      this.logger.info('Подключение к звонку', { socketId: socket.id, callId, userId });

      // Проверка существования звонка
      const call = await this.callManager.getCall(callId);
      if (!call) {
        throw new Error(`Звонок ${callId} не найден`);
      }

      // Создание WebRTC соединения
      const connection: WebRTCConnection = {
        id: `${callId}-${socket.id}`,
        callId,
        socketId: socket.id,
        userId,
        status: 'connecting',
        startTime: new Date(),
        iceCandidates: [],
      };

      this.activeConnections.set(connection.id, connection);
      this.socketToConnection.set(socket.id, connection.id);

      // Присоединение к комнате звонка
      socket.join(`call-${callId}`);

      // Обновление статуса соединения
      connection.status = 'connected';
      this.activeConnections.set(connection.id, connection);

      // Запись метрики
      const duration = Date.now() - startTime;
      this.metrics.recordWebrtcConnection('connected', duration / 1000);
      this.metrics.setActiveWebrtcConnections(this.activeConnections.size);

      this.logger.info('Подключение к звонку успешно', { socketId: socket.id, callId });

      // Уведомление о успешном подключении
      socket.emit('joined-call', { callId, connectionId: connection.id });

      this.emit('connection:joined', { connection, call });

    } catch (error) {
      const duration = Date.now() - startTime;
      this.metrics.recordWebrtcConnection('failed', duration / 1000);
      this.metrics.recordError('webrtc_join_call_error');
      
      throw error;
    }
  }

  private async handleLeaveCall(socket: Socket): Promise<void> {
    try {
      const connectionId = this.socketToConnection.get(socket.id);
      if (!connectionId) {
        return;
      }

      const connection = this.activeConnections.get(connectionId);
      if (!connection) {
        return;
      }

      this.logger.info('Отключение от звонка', { socketId: socket.id, callId: connection.callId });

      // Обновление статуса соединения
      connection.status = 'disconnected';
      connection.endTime = new Date();
      connection.duration = connection.endTime.getTime() - connection.startTime.getTime();

      // Покидание комнаты звонка
      socket.leave(`call-${connection.callId}`);

      // Удаление соединения
      this.activeConnections.delete(connectionId);
      this.socketToConnection.delete(socket.id);

      // Запись метрики
      this.metrics.recordWebrtcConnection('disconnected', connection.duration / 1000);
      this.metrics.setActiveWebrtcConnections(this.activeConnections.size);

      this.logger.info('Отключение от звонка завершено', { socketId: socket.id, callId: connection.callId });

      this.emit('connection:left', { connection });

    } catch (error) {
      this.metrics.recordError('webrtc_leave_call_error');
      throw error;
    }
  }

  private async handleOffer(socket: Socket, callId: string, sdp: string): Promise<void> {
    try {
      const connectionId = this.socketToConnection.get(socket.id);
      if (!connectionId) {
        throw new Error('Соединение не найдено');
      }

      const connection = this.activeConnections.get(connectionId);
      if (!connection) {
        throw new Error('Соединение не найдено');
      }

      this.logger.debug('Обработка WebRTC предложения', { socketId: socket.id, callId });

      // Сохранение локального SDP
      connection.localSDP = sdp;
      this.activeConnections.set(connectionId, connection);

      // Пересылка предложения другим участникам звонка
      socket.to(`call-${callId}`).emit('offer', { callId, sdp, from: socket.id });

      this.emit('webrtc:offer', { connection, sdp });

    } catch (error) {
      this.metrics.recordError('webrtc_offer_error');
      throw error;
    }
  }

  private async handleAnswer(socket: Socket, callId: string, sdp: string): Promise<void> {
    try {
      const connectionId = this.socketToConnection.get(socket.id);
      if (!connectionId) {
        throw new Error('Соединение не найдено');
      }

      const connection = this.activeConnections.get(connectionId);
      if (!connection) {
        throw new Error('Соединение не найдено');
      }

      this.logger.debug('Обработка WebRTC ответа', { socketId: socket.id, callId });

      // Сохранение удаленного SDP
      connection.remoteSDP = sdp;
      this.activeConnections.set(connectionId, connection);

      // Пересылка ответа другим участникам звонка
      socket.to(`call-${callId}`).emit('answer', { callId, sdp, from: socket.id });

      this.emit('webrtc:answer', { connection, sdp });

    } catch (error) {
      this.metrics.recordError('webrtc_answer_error');
      throw error;
    }
  }

  private async handleIceCandidate(socket: Socket, callId: string, candidate: string): Promise<void> {
    try {
      const connectionId = this.socketToConnection.get(socket.id);
      if (!connectionId) {
        return;
      }

      const connection = this.activeConnections.get(connectionId);
      if (!connection) {
        return;
      }

      this.logger.debug('Обработка ICE кандидата', { socketId: socket.id, callId });

      // Сохранение ICE кандидата
      connection.iceCandidates.push(candidate);
      this.activeConnections.set(connectionId, connection);

      // Пересылка ICE кандидата другим участникам звонка
      socket.to(`call-${callId}`).emit('ice-candidate', { callId, candidate, from: socket.id });

      this.emit('webrtc:ice-candidate', { connection, candidate });

    } catch (error) {
      this.metrics.recordError('webrtc_ice_candidate_error');
      this.logger.error('Ошибка при обработке ICE кандидата', { error, socketId: socket.id, callId });
    }
  }

  private async handleDisconnect(socket: Socket): Promise<void> {
    try {
      await this.handleLeaveCall(socket);
      
      this.logger.info('WebSocket соединение закрыто', { socketId: socket.id });
      
    } catch (error) {
      this.logger.error('Ошибка при обработке отключения WebSocket', { error, socketId: socket.id });
    }
  }

  /**
   * Получить активные WebRTC соединения
   */
  getActiveConnections(): WebRTCConnection[] {
    return Array.from(this.activeConnections.values());
  }

  /**
   * Получить соединение по ID
   */
  getConnection(connectionId: string): WebRTCConnection | undefined {
    return this.activeConnections.get(connectionId);
  }

  /**
   * Получить соединения для звонка
   */
  getConnectionsForCall(callId: string): WebRTCConnection[] {
    return Array.from(this.activeConnections.values()).filter(
      connection => connection.callId === callId
    );
  }

  /**
   * Отправить сообщение участникам звонка
   */
  sendToCall(callId: string, event: string, data: any): void {
    this.io.to(`call-${callId}`).emit(event, data);
  }

  /**
   * Отправить сообщение конкретному участнику
   */
  sendToSocket(socketId: string, event: string, data: any): void {
    this.io.to(socketId).emit(event, data);
  }

  /**
   * Очистка неактивных соединений
   */
  async cleanupInactiveConnections(): Promise<void> {
    try {
      const now = new Date();
      const inactiveThreshold = 30 * 60 * 1000; // 30 минут
      
      for (const [connectionId, connection] of this.activeConnections.entries()) {
        if (now.getTime() - connection.startTime.getTime() > inactiveThreshold) {
          await this.handleLeaveCall(this.io.sockets.sockets.get(connection.socketId)!);
        }
      }
      
      this.logger.info('Очистка неактивных WebRTC соединений завершена');
    } catch (error) {
      this.logger.error('Ошибка при очистке неактивных WebRTC соединений', { error });
    }
  }

  /**
   * Завершение работы WebRTC обработчика
   */
  async shutdown(): Promise<void> {
    try {
      this.logger.info('Завершение работы WebRTCHandler...');
      
      // Завершение всех активных соединений
      for (const connection of this.activeConnections.values()) {
        const socket = this.io.sockets.sockets.get(connection.socketId);
        if (socket) {
          await this.handleLeaveCall(socket);
        }
      }
      
      // Очистка активных соединений
      this.activeConnections.clear();
      this.socketToConnection.clear();
      
      this.logger.info('WebRTCHandler завершен');
    } catch (error) {
      this.logger.error('Ошибка при завершении работы WebRTCHandler', { error });
      throw error;
    }
  }
}
