import { CallManager } from '../services/CallManager';
import { DatabaseService } from '../services/DatabaseService';
import { RedisService } from '../services/RedisService';
import { MetricsCollector } from '../utils/metrics';

// Mock dependencies
jest.mock('../services/DatabaseService');
jest.mock('../services/RedisService');
jest.mock('../utils/metrics');

describe('CallManager', () => {
  let callManager: CallManager;
  let mockDatabaseService: jest.Mocked<DatabaseService>;
  let mockRedisService: jest.Mocked<RedisService>;
  let mockMetrics: jest.Mocked<MetricsCollector>;

  beforeEach(() => {
    mockDatabaseService = new DatabaseService() as jest.Mocked<DatabaseService>;
    mockRedisService = new RedisService() as jest.Mocked<RedisService>;
    mockMetrics = new MetricsCollector('test') as jest.Mocked<MetricsCollector>;

    callManager = new CallManager(mockDatabaseService, mockRedisService, mockMetrics);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('createCall', () => {
    it('should create a new call successfully', async () => {
      const callData = {
        phoneNumber: '+7 (999) 123-45-67',
        direction: 'incoming' as const,
      };

      mockDatabaseService.createCall.mockResolvedValue();
      mockRedisService.set.mockResolvedValue();

      const call = await callManager.createCall(callData);

      expect(call).toBeDefined();
      expect(call.phoneNumber).toBe(callData.phoneNumber);
      expect(call.direction).toBe(callData.direction);
      expect(call.status).toBe('initiated');
      expect(mockDatabaseService.createCall).toHaveBeenCalledWith(call);
      expect(mockRedisService.set).toHaveBeenCalled();
      expect(mockMetrics.recordCall).toHaveBeenCalled();
    });

    it('should handle database errors', async () => {
      const callData = {
        phoneNumber: '+7 (999) 123-45-67',
        direction: 'incoming' as const,
      };

      mockDatabaseService.createCall.mockRejectedValue(new Error('Database error'));

      await expect(callManager.createCall(callData)).rejects.toThrow('Database error');
    });
  });

  describe('getCall', () => {
    it('should return call from active calls', async () => {
      const callData = {
        phoneNumber: '+7 (999) 123-45-67',
        direction: 'incoming' as const,
      };

      mockDatabaseService.createCall.mockResolvedValue();
      mockRedisService.set.mockResolvedValue();

      const createdCall = await callManager.createCall(callData);
      const retrievedCall = await callManager.getCall(createdCall.id);

      expect(retrievedCall).toEqual(createdCall);
    });

    it('should return null for non-existent call', async () => {
      const nonExistentId = 'non-existent-id';
      
      mockRedisService.get.mockResolvedValue(null);
      mockDatabaseService.getCall.mockResolvedValue(null);

      const call = await callManager.getCall(nonExistentId);

      expect(call).toBeNull();
    });
  });

  describe('updateCallStatus', () => {
    it('should update call status successfully', async () => {
      const callData = {
        phoneNumber: '+7 (999) 123-45-67',
        direction: 'incoming' as const,
      };

      mockDatabaseService.createCall.mockResolvedValue();
      mockRedisService.set.mockResolvedValue();
      mockDatabaseService.updateCall.mockResolvedValue();

      const call = await callManager.createCall(callData);
      const updatedCall = await callManager.updateCallStatus(call.id, 'answered');

      expect(updatedCall).toBeDefined();
      expect(updatedCall?.status).toBe('answered');
      expect(mockDatabaseService.updateCall).toHaveBeenCalled();
    });
  });
});
