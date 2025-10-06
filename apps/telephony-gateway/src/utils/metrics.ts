import { register, Counter, Histogram, Gauge, collectDefaultMetrics } from 'prom-client';

export class MetricsCollector {
  // HTTP метрики
  public httpRequestsTotal: Counter<string>;
  public httpRequestDuration: Histogram<string>;
  
  // Метрики звонков
  public callsTotal: Counter<string>;
  public callDuration: Histogram<string>;
  public activeCalls: Gauge<string>;
  
  // Метрики SIP
  public sipRequestsTotal: Counter<string>;
  public sipRequestDuration: Histogram<string>;
  
  // Метрики WebRTC
  public webrtcConnectionsTotal: Counter<string>;
  public webrtcConnectionDuration: Histogram<string>;
  public activeWebrtcConnections: Gauge<string>;
  
  // Метрики ошибок
  public errorsTotal: Counter<string>;
  
  // Метрики производительности
  public memoryUsage: Gauge<string>;
  public cpuUsage: Gauge<string>;

  constructor(private serviceName: string) {
    // Сбор стандартных метрик Node.js
    collectDefaultMetrics({ register });

    // HTTP метрики
    this.httpRequestsTotal = new Counter({
      name: 'http_requests_total',
      help: 'Total number of HTTP requests',
      labelNames: ['method', 'endpoint', 'status_code', 'service'],
      registers: [register],
    });

    this.httpRequestDuration = new Histogram({
      name: 'http_request_duration_seconds',
      help: 'HTTP request duration in seconds',
      labelNames: ['method', 'endpoint', 'service'],
      registers: [register],
    });

    // Метрики звонков
    this.callsTotal = new Counter({
      name: 'calls_total',
      help: 'Total number of calls',
      labelNames: ['direction', 'status', 'service'],
      registers: [register],
    });

    this.callDuration = new Histogram({
      name: 'call_duration_seconds',
      help: 'Call duration in seconds',
      labelNames: ['direction', 'service'],
      registers: [register],
    });

    this.activeCalls = new Gauge({
      name: 'active_calls',
      help: 'Number of active calls',
      labelNames: ['service'],
      registers: [register],
    });

    // Метрики SIP
    this.sipRequestsTotal = new Counter({
      name: 'sip_requests_total',
      help: 'Total number of SIP requests',
      labelNames: ['method', 'status', 'service'],
      registers: [register],
    });

    this.sipRequestDuration = new Histogram({
      name: 'sip_request_duration_seconds',
      help: 'SIP request duration in seconds',
      labelNames: ['method', 'service'],
      registers: [register],
    });

    // Метрики WebRTC
    this.webrtcConnectionsTotal = new Counter({
      name: 'webrtc_connections_total',
      help: 'Total number of WebRTC connections',
      labelNames: ['status', 'service'],
      registers: [register],
    });

    this.webrtcConnectionDuration = new Histogram({
      name: 'webrtc_connection_duration_seconds',
      help: 'WebRTC connection duration in seconds',
      labelNames: ['service'],
      registers: [register],
    });

    this.activeWebrtcConnections = new Gauge({
      name: 'active_webrtc_connections',
      help: 'Number of active WebRTC connections',
      labelNames: ['service'],
      registers: [register],
    });

    // Метрики ошибок
    this.errorsTotal = new Counter({
      name: 'errors_total',
      help: 'Total number of errors',
      labelNames: ['error_type', 'service'],
      registers: [register],
    });

    // Метрики производительности
    this.memoryUsage = new Gauge({
      name: 'memory_usage_bytes',
      help: 'Memory usage in bytes',
      labelNames: ['service'],
      registers: [register],
    });

    this.cpuUsage = new Gauge({
      name: 'cpu_usage_percent',
      help: 'CPU usage percentage',
      labelNames: ['service'],
      registers: [register],
    });
  }

  recordHttpRequest(method: string, endpoint: string, statusCode: number, duration: number): void {
    this.httpRequestsTotal.inc({
      method,
      endpoint,
      status_code: statusCode.toString(),
      service: this.serviceName,
    });

    this.httpRequestDuration.observe(
      {
        method,
        endpoint,
        service: this.serviceName,
      },
      duration
    );
  }

  recordCall(direction: string, status: string, duration?: number): void {
    this.callsTotal.inc({
      direction,
      status,
      service: this.serviceName,
    });

    if (duration !== undefined) {
      this.callDuration.observe(
        {
          direction,
          service: this.serviceName,
        },
        duration
      );
    }
  }

  setActiveCalls(count: number): void {
    this.activeCalls.set({ service: this.serviceName }, count);
  }

  recordSipRequest(method: string, status: string, duration: number): void {
    this.sipRequestsTotal.inc({
      method,
      status,
      service: this.serviceName,
    });

    this.sipRequestDuration.observe(
      {
        method,
        service: this.serviceName,
      },
      duration
    );
  }

  recordWebrtcConnection(status: string, duration?: number): void {
    this.webrtcConnectionsTotal.inc({
      status,
      service: this.serviceName,
    });

    if (duration !== undefined) {
      this.webrtcConnectionDuration.observe(
        { service: this.serviceName },
        duration
      );
    }
  }

  setActiveWebrtcConnections(count: number): void {
    this.activeWebrtcConnections.set({ service: this.serviceName }, count);
  }

  recordError(errorType: string): void {
    this.errorsTotal.inc({
      error_type: errorType,
      service: this.serviceName,
    });
  }

  setMemoryUsage(bytes: number): void {
    this.memoryUsage.set({ service: this.serviceName }, bytes);
  }

  setCpuUsage(percent: number): void {
    this.cpuUsage.set({ service: this.serviceName }, percent);
  }

  getMetrics(): Promise<string> {
    return register.metrics();
  }
}

export function setupMetrics(serviceName: string): MetricsCollector {
  return new MetricsCollector(serviceName);
}
