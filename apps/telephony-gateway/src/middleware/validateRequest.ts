import { Request, Response, NextFunction } from 'express';
import Joi from 'joi';
import { CustomError } from './errorHandler';

export function validateRequest(schema: Joi.ObjectSchema) {
  return (req: Request, res: Response, next: NextFunction) => {
    const { error } = schema.validate(req.body);
    
    if (error) {
      const message = error.details.map(detail => detail.message).join(', ');
      throw new CustomError(`Ошибка валидации: ${message}`, 400);
    }
    
    next();
  };
}

export function validateQuery(schema: Joi.ObjectSchema) {
  return (req: Request, res: Response, next: NextFunction) => {
    const { error } = schema.validate(req.query);
    
    if (error) {
      const message = error.details.map(detail => detail.message).join(', ');
      throw new CustomError(`Ошибка валидации запроса: ${message}`, 400);
    }
    
    next();
  };
}

export function validateParams(schema: Joi.ObjectSchema) {
  return (req: Request, res: Response, next: NextFunction) => {
    const { error } = schema.validate(req.params);
    
    if (error) {
      const message = error.details.map(detail => detail.message).join(', ');
      throw new CustomError(`Ошибка валидации параметров: ${message}`, 400);
    }
    
    next();
  };
}

// Базовые схемы валидации
export const schemas = {
  // Создание звонка
  createCall: Joi.object({
    clientId: Joi.string().uuid().optional(),
    phoneNumber: Joi.string().pattern(/^\+?[1-9]\d{1,14}$/).required(),
    direction: Joi.string().valid('incoming', 'outgoing').required(),
  }),

  // Обновление звонка
  updateCall: Joi.object({
    status: Joi.string().valid('initiated', 'ringing', 'answered', 'completed', 'failed', 'busy', 'no_answer').optional(),
    duration: Joi.number().integer().min(0).optional(),
    recordingUrl: Joi.string().uri().optional(),
    transcript: Joi.string().optional(),
    summary: Joi.string().optional(),
    sentiment: Joi.string().valid('positive', 'neutral', 'negative').optional(),
    confidenceScore: Joi.number().min(0).max(1).optional(),
  }),

  // Завершение звонка
  endCall: Joi.object({
    duration: Joi.number().integer().min(0).required(),
    recordingUrl: Joi.string().uri().optional(),
    transcript: Joi.string().optional(),
    summary: Joi.string().optional(),
    sentiment: Joi.string().valid('positive', 'neutral', 'negative').optional(),
    confidenceScore: Joi.number().min(0).max(1).optional(),
  }),

  // Создание сессии
  createSession: Joi.object({
    callId: Joi.string().uuid().required(),
    userId: Joi.string().uuid().optional(),
  }),

  // ID параметр
  idParam: Joi.object({
    id: Joi.string().uuid().required(),
  }),

  // Пагинация
  pagination: Joi.object({
    page: Joi.number().integer().min(1).default(1),
    limit: Joi.number().integer().min(1).max(100).default(10),
  }),

  // Фильтры звонков
  callFilters: Joi.object({
    clientId: Joi.string().uuid().optional(),
    direction: Joi.string().valid('incoming', 'outgoing').optional(),
    status: Joi.string().valid('initiated', 'ringing', 'answered', 'completed', 'failed', 'busy', 'no_answer').optional(),
    fromDate: Joi.date().iso().optional(),
    toDate: Joi.date().iso().optional(),
  }),
};

// Middleware для общей валидации
export function validateHeaders(req: Request, res: Response, next: NextFunction) {
  // Базовая валидация заголовков
  if (!req.get('Content-Type') && req.method !== 'GET' && req.method !== 'DELETE') {
    throw new CustomError('Отсутствует заголовок Content-Type', 400);
  }

  next();
}
