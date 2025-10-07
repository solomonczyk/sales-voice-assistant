// Общие типы для telephony-gateway

export interface CallData {
  id?: string;
  clientId?: string;
  phoneNumber: string;
  direction: 'incoming' | 'outgoing';
  status?: 'initiated' | 'ringing' | 'answered' | 'completed' | 'failed' | 'busy' | 'no_answer';
  duration?: number;
  recordingUrl?: string;
  transcript?: string;
  summary?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  confidenceScore?: number;
  createdAt?: Date;
  updatedAt?: Date;
}

export interface CallSession {
  callId: string;
  sessionId: string;
  userId?: string;
  startTime: Date;
  lastActivity: Date;
  isActive: boolean;
}

export interface WebRTCConnection {
  id: string;
  callId: string;
  socketId: string;
  userId?: string;
  status: 'connecting' | 'connected' | 'disconnected' | 'failed';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  localSDP?: string;
  remoteSDP?: string;
  iceCandidates: string[];
}

export interface SIPCall {
  id: string;
  from: string;
  to: string;
  direction: 'incoming' | 'outgoing';
  status: 'initiated' | 'ringing' | 'answered' | 'completed' | 'failed' | 'busy' | 'no_answer';
  startTime: Date;
  endTime?: Date;
  duration?: number;
}

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T = any> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export interface HealthCheck {
  status: 'ok' | 'error';
  timestamp: string;
  service: string;
  version: string;
  checks?: {
    [key: string]: {
      status: 'ok' | 'error';
      message: string;
    };
  };
}

export interface MetricsData {
  http_requests_total: number;
  http_request_duration_seconds: number;
  calls_total: number;
  call_duration_seconds: number;
  active_calls: number;
  webrtc_connections_total: number;
  active_webrtc_connections: number;
  errors_total: number;
  memory_usage_bytes: number;
  cpu_usage_percent: number;
}

// WebSocket события - клиент → сервер
export interface ClientToServerEvents {
  'join-call': { callId: string; userId?: string };
  'leave-call': {};
  'offer': { callId: string; sdp: string };
  'answer': { callId: string; sdp: string };
  'ice-candidate': { callId: string; candidate: string };
}

// WebSocket события - сервер → клиент
export interface ServerToClientEvents {
  'joined-call': { callId: string; connectionId: string };
  'offer': { callId: string; sdp: string; from: string };
  'answer': { callId: string; sdp: string; from: string };
  'ice-candidate': { callId: string; candidate: string; from: string };
  'error': { message: string };
}

// API запросы
export interface CreateCallRequest {
  clientId?: string;
  phoneNumber: string;
  direction: 'incoming' | 'outgoing';
}

export interface UpdateCallRequest {
  status?: 'initiated' | 'ringing' | 'answered' | 'completed' | 'failed' | 'busy' | 'no_answer';
  duration?: number;
  recordingUrl?: string;
  transcript?: string;
  summary?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  confidenceScore?: number;
}

export interface EndCallRequest {
  duration: number;
  recordingUrl?: string;
  transcript?: string;
  summary?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  confidenceScore?: number;
}

export interface CreateSessionRequest {
  callId: string;
  userId?: string;
}

export interface CallFilters {
  clientId?: string;
  direction?: 'incoming' | 'outgoing';
  status?: 'initiated' | 'ringing' | 'answered' | 'completed' | 'failed' | 'busy' | 'no_answer';
  fromDate?: string;
  toDate?: string;
  page?: number;
  limit?: number;
}
