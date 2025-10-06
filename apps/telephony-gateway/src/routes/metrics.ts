import { Router, Request, Response } from 'express';
import { MetricsCollector } from '../utils/metrics';

const router = Router();

// Получение экземпляра MetricsCollector (должен быть передан из app)
let metrics: MetricsCollector;

export function setMetrics(metricsInstance: MetricsCollector) {
  metrics = metricsInstance;
}

// Получение метрик Prometheus
router.get('/', async (req: Request, res: Response) => {
  try {
    const metricsData = await metrics.getMetrics();
    
    res.set('Content-Type', 'text/plain; version=0.0.4; charset=utf-8');
    res.send(metricsData);
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Ошибка при получении метрик',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

export { router as metricsRoutes };
