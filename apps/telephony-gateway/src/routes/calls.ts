import { Router } from 'express';
import { CallManager } from '../services/CallManager';
import { asyncHandler } from '../middleware/errorHandler';
import { validateRequest, validateQuery, validateParams, schemas } from '../middleware/validateRequest';
import { MetricsCollector } from '../utils/metrics';

const router = Router();

// Получение экземпляра CallManager (должен быть передан из app)
let callManager: CallManager;
let metrics: MetricsCollector;

export function setCallManager(manager: CallManager, metricsCollector: MetricsCollector) {
  callManager = manager;
  metrics = metricsCollector;
}

// Создание звонка
router.post(
  '/',
  validateRequest(schemas.createCall),
  asyncHandler(async (req, res) => {
    const startTime = Date.now();
    
    try {
      const call = await callManager.createCall(req.body);
      
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('POST', '/calls', 201, duration / 1000);
      
      res.status(201).json({
        success: true,
        data: call,
      });
    } catch (error) {
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('POST', '/calls', 500, duration / 1000);
      metrics.recordError('create_call_error');
      throw error;
    }
  })
);

// Получение звонка по ID
router.get(
  '/:id',
  validateParams(schemas.idParam),
  asyncHandler(async (req, res) => {
    const startTime = Date.now();
    
    try {
      const call = await callManager.getCall(req.params.id);
      
      if (!call) {
        const duration = Date.now() - startTime;
        metrics.recordHttpRequest('GET', '/calls/:id', 404, duration / 1000);
        return res.status(404).json({
          success: false,
          error: 'Звонок не найден',
        });
      }
      
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('GET', '/calls/:id', 200, duration / 1000);
      
      res.json({
        success: true,
        data: call,
      });
    } catch (error) {
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('GET', '/calls/:id', 500, duration / 1000);
      metrics.recordError('get_call_error');
      throw error;
    }
  })
);

// Обновление статуса звонка
router.patch(
  '/:id/status',
  validateParams(schemas.idParam),
  validateRequest(schemas.updateCall),
  asyncHandler(async (req, res) => {
    const startTime = Date.now();
    
    try {
      const call = await callManager.updateCallStatus(req.params.id, req.body.status);
      
      if (!call) {
        const duration = Date.now() - startTime;
        metrics.recordHttpRequest('PATCH', '/calls/:id/status', 404, duration / 1000);
        return res.status(404).json({
          success: false,
          error: 'Звонок не найден',
        });
      }
      
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('PATCH', '/calls/:id/status', 200, duration / 1000);
      
      res.json({
        success: true,
        data: call,
      });
    } catch (error) {
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('PATCH', '/calls/:id/status', 500, duration / 1000);
      metrics.recordError('update_call_status_error');
      throw error;
    }
  })
);

// Завершение звонка
router.post(
  '/:id/end',
  validateParams(schemas.idParam),
  validateRequest(schemas.endCall),
  asyncHandler(async (req, res) => {
    const startTime = Date.now();
    
    try {
      const call = await callManager.endCall(req.params.id, req.body);
      
      if (!call) {
        const duration = Date.now() - startTime;
        metrics.recordHttpRequest('POST', '/calls/:id/end', 404, duration / 1000);
        return res.status(404).json({
          success: false,
          error: 'Звонок не найден',
        });
      }
      
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('POST', '/calls/:id/end', 200, duration / 1000);
      
      res.json({
        success: true,
        data: call,
      });
    } catch (error) {
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('POST', '/calls/:id/end', 500, duration / 1000);
      metrics.recordError('end_call_error');
      throw error;
    }
  })
);

// Создание сессии звонка
router.post(
  '/:id/sessions',
  validateParams(schemas.idParam),
  validateRequest(schemas.createSession),
  asyncHandler(async (req, res) => {
    const startTime = Date.now();
    
    try {
      const session = await callManager.createCallSession(req.params.id, req.body.userId);
      
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('POST', '/calls/:id/sessions', 201, duration / 1000);
      
      res.status(201).json({
        success: true,
        data: session,
      });
    } catch (error) {
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('POST', '/calls/:id/sessions', 500, duration / 1000);
      metrics.recordError('create_session_error');
      throw error;
    }
  })
);

// Получение активных звонков
router.get(
  '/',
  validateQuery(schemas.pagination),
  asyncHandler(async (req, res) => {
    const startTime = Date.now();
    
    try {
      const calls = callManager.getActiveCalls();
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 10;
      const startIndex = (page - 1) * limit;
      const endIndex = startIndex + limit;
      
      const paginatedCalls = calls.slice(startIndex, endIndex);
      
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('GET', '/calls', 200, duration / 1000);
      
      res.json({
        success: true,
        data: {
          calls: paginatedCalls,
          pagination: {
            page,
            limit,
            total: calls.length,
            pages: Math.ceil(calls.length / limit),
          },
        },
      });
    } catch (error) {
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('GET', '/calls', 500, duration / 1000);
      metrics.recordError('get_calls_error');
      throw error;
    }
  })
);

// Получение активных сессий
router.get(
  '/sessions/active',
  asyncHandler(async (req, res) => {
    const startTime = Date.now();
    
    try {
      const sessions = callManager.getActiveSessions();
      
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('GET', '/calls/sessions/active', 200, duration / 1000);
      
      res.json({
        success: true,
        data: sessions,
      });
    } catch (error) {
      const duration = Date.now() - startTime;
      metrics.recordHttpRequest('GET', '/calls/sessions/active', 500, duration / 1000);
      metrics.recordError('get_active_sessions_error');
      throw error;
    }
  })
);

export { router as callRoutes };
