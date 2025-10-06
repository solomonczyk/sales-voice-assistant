import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';

export class Logger {
  private logger: winston.Logger;

  constructor(private context: string) {
    this.logger = winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: { service: 'telephony-gateway', context },
      transports: [
        // Консольный вывод
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          ),
        }),
        // Ротация файлов логов
        new DailyRotateFile({
          filename: 'logs/telephony-gateway-%DATE%.log',
          datePattern: 'YYYY-MM-DD',
          maxSize: '20m',
          maxFiles: '14d',
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
          ),
        }),
        // Логи ошибок
        new DailyRotateFile({
          filename: 'logs/telephony-gateway-error-%DATE%.log',
          datePattern: 'YYYY-MM-DD',
          level: 'error',
          maxSize: '20m',
          maxFiles: '30d',
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
          ),
        }),
      ],
    });
  }

  info(message: string, meta?: any): void {
    this.logger.info(message, meta);
  }

  error(message: string, meta?: any): void {
    this.logger.error(message, meta);
  }

  warn(message: string, meta?: any): void {
    this.logger.warn(message, meta);
  }

  debug(message: string, meta?: any): void {
    this.logger.debug(message, meta);
  }
}

export function setupLogging(): void {
  // Создание директории для логов
  const fs = require('fs');
  if (!fs.existsSync('logs')) {
    fs.mkdirSync('logs');
  }
}
