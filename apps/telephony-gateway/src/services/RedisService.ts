import { createClient, RedisClientType } from 'redis';
import { Logger } from '../utils/logger';

export class RedisService {
  private client: RedisClientType;
  private logger: Logger;

  constructor() {
    this.logger = new Logger('RedisService');
    
    this.client = createClient({
      url: process.env.REDIS_URL || 'redis://localhost:6379',
      socket: {
        reconnectStrategy: (retries) => {
          if (retries > 10) {
            this.logger.error('Превышено максимальное количество попыток переподключения к Redis');
            return false;
          }
          return Math.min(retries * 50, 1000);
        },
      },
    });

    this.client.on('error', (err) => {
      this.logger.error('Ошибка Redis', { error: err });
    });

    this.client.on('connect', () => {
      this.logger.info('Подключение к Redis установлено');
    });

    this.client.on('reconnecting', () => {
      this.logger.info('Переподключение к Redis...');
    });

    this.client.on('ready', () => {
      this.logger.info('Redis готов к работе');
    });
  }

  async connect(): Promise<void> {
    try {
      await this.client.connect();
      this.logger.info('Подключение к Redis успешно');
    } catch (error) {
      this.logger.error('Ошибка подключения к Redis', { error });
      throw error;
    }
  }

  async set(key: string, value: string, ttlSeconds?: number): Promise<void> {
    try {
      if (ttlSeconds) {
        await this.client.setEx(key, ttlSeconds, value);
      } else {
        await this.client.set(key, value);
      }
      
      this.logger.debug('Значение установлено в Redis', { key, ttlSeconds });
    } catch (error) {
      this.logger.error('Ошибка при установке значения в Redis', { error, key });
      throw error;
    }
  }

  async get(key: string): Promise<string | null> {
    try {
      const value = await this.client.get(key);
      this.logger.debug('Значение получено из Redis', { key, hasValue: !!value });
      return value;
    } catch (error) {
      this.logger.error('Ошибка при получении значения из Redis', { error, key });
      throw error;
    }
  }

  async del(key: string): Promise<void> {
    try {
      await this.client.del(key);
      this.logger.debug('Ключ удален из Redis', { key });
    } catch (error) {
      this.logger.error('Ошибка при удалении ключа из Redis', { error, key });
      throw error;
    }
  }

  async exists(key: string): Promise<boolean> {
    try {
      const result = await this.client.exists(key);
      return result === 1;
    } catch (error) {
      this.logger.error('Ошибка при проверке существования ключа в Redis', { error, key });
      throw error;
    }
  }

  async expire(key: string, ttlSeconds: number): Promise<void> {
    try {
      await this.client.expire(key, ttlSeconds);
      this.logger.debug('TTL установлен для ключа в Redis', { key, ttlSeconds });
    } catch (error) {
      this.logger.error('Ошибка при установке TTL для ключа в Redis', { error, key, ttlSeconds });
      throw error;
    }
  }

  async ttl(key: string): Promise<number> {
    try {
      const ttl = await this.client.ttl(key);
      this.logger.debug('TTL получен для ключа в Redis', { key, ttl });
      return ttl;
    } catch (error) {
      this.logger.error('Ошибка при получении TTL для ключа в Redis', { error, key });
      throw error;
    }
  }

  async keys(pattern: string): Promise<string[]> {
    try {
      const keys = await this.client.keys(pattern);
      this.logger.debug('Ключи получены из Redis', { pattern, count: keys.length });
      return keys;
    } catch (error) {
      this.logger.error('Ошибка при получении ключей из Redis', { error, pattern });
      throw error;
    }
  }

  async hSet(key: string, field: string, value: string): Promise<void> {
    try {
      await this.client.hSet(key, field, value);
      this.logger.debug('Поле хеша установлено в Redis', { key, field });
    } catch (error) {
      this.logger.error('Ошибка при установке поля хеша в Redis', { error, key, field });
      throw error;
    }
  }

  async hGet(key: string, field: string): Promise<string | null> {
    try {
      const value = await this.client.hGet(key, field);
      this.logger.debug('Поле хеша получено из Redis', { key, field, hasValue: !!value });
      return value;
    } catch (error) {
      this.logger.error('Ошибка при получении поля хеша из Redis', { error, key, field });
      throw error;
    }
  }

  async hGetAll(key: string): Promise<Record<string, string>> {
    try {
      const hash = await this.client.hGetAll(key);
      this.logger.debug('Хеш получен из Redis', { key, fieldCount: Object.keys(hash).length });
      return hash;
    } catch (error) {
      this.logger.error('Ошибка при получении хеша из Redis', { error, key });
      throw error;
    }
  }

  async hDel(key: string, field: string): Promise<void> {
    try {
      await this.client.hDel(key, field);
      this.logger.debug('Поле хеша удалено из Redis', { key, field });
    } catch (error) {
      this.logger.error('Ошибка при удалении поля хеша из Redis', { error, key, field });
      throw error;
    }
  }

  async lPush(key: string, value: string): Promise<void> {
    try {
      await this.client.lPush(key, value);
      this.logger.debug('Значение добавлено в начало списка в Redis', { key });
    } catch (error) {
      this.logger.error('Ошибка при добавлении значения в список в Redis', { error, key });
      throw error;
    }
  }

  async rPush(key: string, value: string): Promise<void> {
    try {
      await this.client.rPush(key, value);
      this.logger.debug('Значение добавлено в конец списка в Redis', { key });
    } catch (error) {
      this.logger.error('Ошибка при добавлении значения в список в Redis', { error, key });
      throw error;
    }
  }

  async lPop(key: string): Promise<string | null> {
    try {
      const value = await this.client.lPop(key);
      this.logger.debug('Значение извлечено из начала списка в Redis', { key, hasValue: !!value });
      return value;
    } catch (error) {
      this.logger.error('Ошибка при извлечении значения из списка в Redis', { error, key });
      throw error;
    }
  }

  async rPop(key: string): Promise<string | null> {
    try {
      const value = await this.client.rPop(key);
      this.logger.debug('Значение извлечено из конца списка в Redis', { key, hasValue: !!value });
      return value;
    } catch (error) {
      this.logger.error('Ошибка при извлечении значения из списка в Redis', { error, key });
      throw error;
    }
  }

  async lLen(key: string): Promise<number> {
    try {
      const length = await this.client.lLen(key);
      this.logger.debug('Длина списка получена из Redis', { key, length });
      return length;
    } catch (error) {
      this.logger.error('Ошибка при получении длины списка из Redis', { error, key });
      throw error;
    }
  }

  async lRange(key: string, start: number, stop: number): Promise<string[]> {
    try {
      const values = await this.client.lRange(key, start, stop);
      this.logger.debug('Диапазон списка получен из Redis', { key, start, stop, count: values.length });
      return values;
    } catch (error) {
      this.logger.error('Ошибка при получении диапазона списка из Redis', { error, key, start, stop });
      throw error;
    }
  }

  async publish(channel: string, message: string): Promise<void> {
    try {
      await this.client.publish(channel, message);
      this.logger.debug('Сообщение опубликовано в Redis', { channel });
    } catch (error) {
      this.logger.error('Ошибка при публикации сообщения в Redis', { error, channel });
      throw error;
    }
  }

  async subscribe(channel: string, callback: (message: string) => void): Promise<void> {
    try {
      const subscriber = this.client.duplicate();
      await subscriber.connect();
      
      await subscriber.subscribe(channel, (message) => {
        this.logger.debug('Сообщение получено из Redis', { channel });
        callback(message);
      });
      
      this.logger.info('Подписка на канал Redis создана', { channel });
    } catch (error) {
      this.logger.error('Ошибка при подписке на канал Redis', { error, channel });
      throw error;
    }
  }

  async healthCheck(): Promise<void> {
    try {
      await this.client.ping();
      this.logger.debug('Health check Redis прошел успешно');
    } catch (error) {
      this.logger.error('Health check Redis не прошел', { error });
      throw error;
    }
  }

  async close(): Promise<void> {
    try {
      await this.client.quit();
      this.logger.info('Подключение к Redis закрыто');
    } catch (error) {
      this.logger.error('Ошибка при закрытии подключения к Redis', { error });
      throw error;
    }
  }
}
