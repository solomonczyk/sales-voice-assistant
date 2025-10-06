import { Pool, PoolClient } from 'pg';
import { Logger } from '../utils/logger';
import { Call } from './CallManager';

export class DatabaseService {
  private pool: Pool;
  private logger: Logger;

  constructor() {
    this.logger = new Logger('DatabaseService');
    
    this.pool = new Pool({
      connectionString: process.env.POSTGRES_URL || 'postgresql://postgres:postgres@localhost:5432/sales_voice',
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    this.pool.on('error', (err) => {
      this.logger.error('Ошибка подключения к базе данных', { error: err });
    });

    this.pool.on('connect', () => {
      this.logger.info('Подключение к базе данных установлено');
    });
  }

  async createCall(call: Call): Promise<void> {
    const client = await this.pool.connect();
    
    try {
      await client.query('BEGIN');
      
      const query = `
        INSERT INTO calls (
          id, client_id, phone_number, direction, status, duration,
          recording_url, transcript, summary, sentiment, confidence_score,
          created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
      `;
      
      const values = [
        call.id,
        call.clientId || null,
        call.phoneNumber,
        call.direction,
        call.status,
        call.duration,
        call.recordingUrl || null,
        call.transcript || null,
        call.summary || null,
        call.sentiment || null,
        call.confidenceScore || null,
        call.createdAt,
        call.updatedAt,
      ];
      
      await client.query(query, values);
      await client.query('COMMIT');
      
      this.logger.info('Звонок сохранен в базе данных', { callId: call.id });
    } catch (error) {
      await client.query('ROLLBACK');
      this.logger.error('Ошибка при сохранении звонка в БД', { error, callId: call.id });
      throw error;
    } finally {
      client.release();
    }
  }

  async getCall(callId: string): Promise<Call | null> {
    const client = await this.pool.connect();
    
    try {
      const query = `
        SELECT 
          id, client_id, phone_number, direction, status, duration,
          recording_url, transcript, summary, sentiment, confidence_score,
          created_at, updated_at
        FROM calls 
        WHERE id = $1
      `;
      
      const result = await client.query(query, [callId]);
      
      if (result.rows.length === 0) {
        return null;
      }
      
      const row = result.rows[0];
      return {
        id: row.id,
        clientId: row.client_id,
        phoneNumber: row.phone_number,
        direction: row.direction,
        status: row.status,
        duration: row.duration,
        recordingUrl: row.recording_url,
        transcript: row.transcript,
        summary: row.summary,
        sentiment: row.sentiment,
        confidenceScore: row.confidence_score,
        createdAt: row.created_at,
        updatedAt: row.updated_at,
      };
    } catch (error) {
      this.logger.error('Ошибка при получении звонка из БД', { error, callId });
      throw error;
    } finally {
      client.release();
    }
  }

  async updateCall(callId: string, updates: Partial<Call>): Promise<void> {
    const client = await this.pool.connect();
    
    try {
      await client.query('BEGIN');
      
      const setParts: string[] = [];
      const values: any[] = [];
      let paramIndex = 1;
      
      // Динамическое построение запроса
      if (updates.status !== undefined) {
        setParts.push(`status = $${paramIndex++}`);
        values.push(updates.status);
      }
      
      if (updates.duration !== undefined) {
        setParts.push(`duration = $${paramIndex++}`);
        values.push(updates.duration);
      }
      
      if (updates.recordingUrl !== undefined) {
        setParts.push(`recording_url = $${paramIndex++}`);
        values.push(updates.recordingUrl);
      }
      
      if (updates.transcript !== undefined) {
        setParts.push(`transcript = $${paramIndex++}`);
        values.push(updates.transcript);
      }
      
      if (updates.summary !== undefined) {
        setParts.push(`summary = $${paramIndex++}`);
        values.push(updates.summary);
      }
      
      if (updates.sentiment !== undefined) {
        setParts.push(`sentiment = $${paramIndex++}`);
        values.push(updates.sentiment);
      }
      
      if (updates.confidenceScore !== undefined) {
        setParts.push(`confidence_score = $${paramIndex++}`);
        values.push(updates.confidenceScore);
      }
      
      // Всегда обновляем updated_at
      setParts.push(`updated_at = $${paramIndex++}`);
      values.push(new Date());
      
      // Добавляем callId в конец
      values.push(callId);
      
      const query = `
        UPDATE calls 
        SET ${setParts.join(', ')}
        WHERE id = $${paramIndex}
      `;
      
      const result = await client.query(query, values);
      
      if (result.rowCount === 0) {
        throw new Error(`Звонок с ID ${callId} не найден`);
      }
      
      await client.query('COMMIT');
      
      this.logger.info('Звонок обновлен в базе данных', { callId });
    } catch (error) {
      await client.query('ROLLBACK');
      this.logger.error('Ошибка при обновлении звонка в БД', { error, callId });
      throw error;
    } finally {
      client.release();
    }
  }

  async getCalls(filters: {
    clientId?: string;
    direction?: string;
    status?: string;
    fromDate?: Date;
    toDate?: Date;
    limit?: number;
    offset?: number;
  } = {}): Promise<Call[]> {
    const client = await this.pool.connect();
    
    try {
      const whereConditions: string[] = [];
      const values: any[] = [];
      let paramIndex = 1;
      
      if (filters.clientId) {
        whereConditions.push(`client_id = $${paramIndex++}`);
        values.push(filters.clientId);
      }
      
      if (filters.direction) {
        whereConditions.push(`direction = $${paramIndex++}`);
        values.push(filters.direction);
      }
      
      if (filters.status) {
        whereConditions.push(`status = $${paramIndex++}`);
        values.push(filters.status);
      }
      
      if (filters.fromDate) {
        whereConditions.push(`created_at >= $${paramIndex++}`);
        values.push(filters.fromDate);
      }
      
      if (filters.toDate) {
        whereConditions.push(`created_at <= $${paramIndex++}`);
        values.push(filters.toDate);
      }
      
      const whereClause = whereConditions.length > 0 
        ? `WHERE ${whereConditions.join(' AND ')}`
        : '';
      
      const limitClause = filters.limit 
        ? `LIMIT $${paramIndex++}`
        : '';
      if (filters.limit) values.push(filters.limit);
      
      const offsetClause = filters.offset 
        ? `OFFSET $${paramIndex++}`
        : '';
      if (filters.offset) values.push(filters.offset);
      
      const query = `
        SELECT 
          id, client_id, phone_number, direction, status, duration,
          recording_url, transcript, summary, sentiment, confidence_score,
          created_at, updated_at
        FROM calls 
        ${whereClause}
        ORDER BY created_at DESC
        ${limitClause}
        ${offsetClause}
      `;
      
      const result = await client.query(query, values);
      
      return result.rows.map(row => ({
        id: row.id,
        clientId: row.client_id,
        phoneNumber: row.phone_number,
        direction: row.direction,
        status: row.status,
        duration: row.duration,
        recordingUrl: row.recording_url,
        transcript: row.transcript,
        summary: row.summary,
        sentiment: row.sentiment,
        confidenceScore: row.confidence_score,
        createdAt: row.created_at,
        updatedAt: row.updated_at,
      }));
    } catch (error) {
      this.logger.error('Ошибка при получении звонков из БД', { error, filters });
      throw error;
    } finally {
      client.release();
    }
  }

  async healthCheck(): Promise<void> {
    const client = await this.pool.connect();
    
    try {
      await client.query('SELECT 1');
      this.logger.debug('Health check базы данных прошел успешно');
    } catch (error) {
      this.logger.error('Health check базы данных не прошел', { error });
      throw error;
    } finally {
      client.release();
    }
  }

  async close(): Promise<void> {
    try {
      await this.pool.end();
      this.logger.info('Подключение к базе данных закрыто');
    } catch (error) {
      this.logger.error('Ошибка при закрытии подключения к БД', { error });
      throw error;
    }
  }
}