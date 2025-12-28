// Core Types
export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  twoFactorEnabled: boolean;
  createdAt: string;
  lastLogin?: string;
}

export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  VIEWER = 'viewer',
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface LoginRequest {
  username: string;
  password: string;
  twoFactorCode?: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

// Database Types
export interface DatabaseConnection {
  id: string;
  name: string;
  type: DatabaseType;
  host: string;
  port: number;
  database: string;
  username: string;
  ssl?: boolean;
  status: ConnectionStatus;
  createdAt: string;
  lastUsed?: string;
}

export enum DatabaseType {
  POSTGRESQL = 'postgresql',
  MYSQL = 'mysql',
  MONGODB = 'mongodb',
  REDIS = 'redis',
  SQLITE = 'sqlite',
}

export enum ConnectionStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
}

// Query Types
export interface QueryRequest {
  connectionId: string;
  query: string;
  parameters?: Record<string, any>;
}

export interface QueryResult {
  id: string;
  query: string;
  columns: string[];
  rows: any[];
  rowCount: number;
  executionTime: number;
  timestamp: string;
}

export interface VisualQuery {
  id: string;
  name: string;
  tables: QueryTable[];
  joins: QueryJoin[];
  conditions: QueryCondition[];
  fields: QueryField[];
}

export interface QueryTable {
  id: string;
  name: string;
  alias?: string;
  position: { x: number; y: number };
}

export interface QueryJoin {
  id: string;
  leftTable: string;
  rightTable: string;
  leftField: string;
  rightField: string;
  type: JoinType;
}

export enum JoinType {
  INNER = 'INNER',
  LEFT = 'LEFT',
  RIGHT = 'RIGHT',
  FULL = 'FULL',
}

export interface QueryCondition {
  id: string;
  field: string;
  operator: ConditionOperator;
  value: any;
  connector?: 'AND' | 'OR';
}

export enum ConditionOperator {
  EQUALS = '=',
  NOT_EQUALS = '!=',
  GREATER_THAN = '>',
  LESS_THAN = '<',
  LIKE = 'LIKE',
  IN = 'IN',
}

export interface QueryField {
  id: string;
  table: string;
  field: string;
  alias?: string;
  aggregate?: AggregateFunction;
}

export enum AggregateFunction {
  COUNT = 'COUNT',
  SUM = 'SUM',
  AVG = 'AVG',
  MIN = 'MIN',
  MAX = 'MAX',
}

// Visualization Types
export interface ChartConfig {
  type: ChartType;
  xAxis: string;
  yAxis: string | string[];
  title?: string;
  legend?: boolean;
}

export enum ChartType {
  BAR = 'bar',
  LINE = 'line',
  PIE = 'pie',
  AREA = 'area',
  SCATTER = 'scatter',
}

// Performance Types
export interface PerformanceMetric {
  id: string;
  connectionId: string;
  metric: string;
  value: number;
  timestamp: string;
}

export interface Dashboard {
  id: string;
  name: string;
  widgets: DashboardWidget[];
  layout: DashboardLayout;
}

export interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  config: any;
  position: { x: number; y: number; w: number; h: number };
}

export enum WidgetType {
  CHART = 'chart',
  TABLE = 'table',
  METRIC = 'metric',
  LOG = 'log',
}

export interface DashboardLayout {
  cols: number;
  rows: number;
}

// Audit Types
export interface AuditLog {
  id: string;
  userId: string;
  username: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  timestamp: string;
  ipAddress?: string;
}

// Permission Types
export interface Permission {
  id: string;
  resource: string;
  actions: string[];
  role: UserRole;
}

// WebSocket Types
export interface WebSocketMessage {
  type: MessageType;
  payload: any;
}

export enum MessageType {
  QUERY_RESULT = 'query_result',
  METRIC_UPDATE = 'metric_update',
  CONNECTION_STATUS = 'connection_status',
  NOTIFICATION = 'notification',
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}
