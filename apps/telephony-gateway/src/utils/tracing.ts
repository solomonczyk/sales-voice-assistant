// Упрощенная версия трассировки без OpenTelemetry
// В будущем можно добавить полноценную трассировку

export function setupTracing(serviceName: string): void {
  console.log(`Tracing setup for service: ${serviceName}`);
  console.log('Note: Full OpenTelemetry tracing will be implemented in future versions');
  
  // Заглушка для совместимости
  // В продакшене здесь будет полноценная настройка OpenTelemetry
}
