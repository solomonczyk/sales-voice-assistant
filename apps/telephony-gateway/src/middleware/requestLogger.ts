import { Request, Response, NextFunction } from 'express';
import { Logger } from '../utils/logger';

const logger = new Logger('RequestLogger');

export function requestLogger(req: Request, res: Response, next: NextFunction): void {
  const startTime = Date.now();
  
  // Логирование входящего запроса
  logger.info('Входящий HTTP запрос', {
    method: req.method,
    url: req.url,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    headers: {
      'content-type': req.get('Content-Type'),
      'authorization': req.get('Authorization') ? '***MASKED***' : undefined,
    },
  });

  // Перехват завершения ответа
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    
    logger.info('Исходящий HTTP ответ', {
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip,
    });
  });

  next();
}
