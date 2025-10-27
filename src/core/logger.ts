/**
 * Structured Logging with Winston
 * Provides comprehensive logging with rotation, audit trails, and contextual metadata
 */

import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';

/**
 * Log levels enum for type safety
 */
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

/**
 * Custom log metadata interface
 */
export interface LogMetadata {
  [key: string]: any;
  duration?: number;
  context?: string;
  component?: string;
  userId?: string;
  requestId?: string;
}

/**
 * Winston logger configuration
 */
const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
  winston.format.printf(({ level, message, timestamp, ...metadata }) => {
    let msg = `${timestamp} [${level}]: ${message}`;
    if (Object.keys(metadata).length > 0) {
      msg += ` ${JSON.stringify(metadata)}`;
    }
    return msg;
  })
);

/**
 * Main application logger
 */
export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  defaultMeta: { service: 'ai-shell' },
  transports: [
    // Console output with colors
    new winston.transports.Console({
      format: consoleFormat,
      level: process.env.NODE_ENV === 'production' ? 'info' : 'debug'
    }),
    // Daily rotating file for all logs
    new DailyRotateFile({
      filename: 'logs/ai-shell-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '14d',
      format: logFormat,
      level: 'info'
    }),
    // Daily rotating file for errors only
    new DailyRotateFile({
      filename: 'logs/ai-shell-error-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '30d',
      format: logFormat,
      level: 'error'
    }),
    // Debug logs (only in development)
    ...(process.env.NODE_ENV !== 'production' ? [
      new DailyRotateFile({
        filename: 'logs/ai-shell-debug-%DATE%.log',
        datePattern: 'YYYY-MM-DD',
        maxSize: '20m',
        maxFiles: '7d',
        format: logFormat,
        level: 'debug'
      })
    ] : [])
  ],
  // Handle uncaught exceptions
  exceptionHandlers: [
    new DailyRotateFile({
      filename: 'logs/exceptions-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '30d'
    })
  ],
  // Handle unhandled promise rejections
  rejectionHandlers: [
    new DailyRotateFile({
      filename: 'logs/rejections-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '30d'
    })
  ]
});

/**
 * Audit logger for security-critical events
 * Retains logs for 90 days for compliance
 */
export const auditLogger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { type: 'audit' },
  transports: [
    new DailyRotateFile({
      filename: 'logs/audit-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '90d', // Longer retention for audit logs
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      )
    })
  ]
});

/**
 * Performance logger for metrics and benchmarks
 */
export const perfLogger = winston.createLogger({
  level: 'debug',
  format: logFormat,
  defaultMeta: { type: 'performance' },
  transports: [
    new DailyRotateFile({
      filename: 'logs/performance-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '7d'
    })
  ]
});

/**
 * Security logger for security events
 */
export const securityLogger = winston.createLogger({
  level: 'warn',
  format: logFormat,
  defaultMeta: { type: 'security' },
  transports: [
    new DailyRotateFile({
      filename: 'logs/security-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '90d'
    })
  ]
});

/**
 * Logger utility class for namespaced logging
 * Provides backward compatibility with old Logger class
 */
export class Logger {
  private namespace: string;
  private contextMetadata: LogMetadata;

  constructor(namespace: string, metadata: LogMetadata = {}) {
    this.namespace = namespace;
    this.contextMetadata = { component: namespace, ...metadata };
  }

  /**
   * Log debug message
   */
  debug(message: string, metadata?: LogMetadata): void {
    logger.debug(message, { ...this.contextMetadata, ...metadata });
  }

  /**
   * Log info message
   */
  info(message: string, metadata?: LogMetadata): void {
    logger.info(message, { ...this.contextMetadata, ...metadata });
  }

  /**
   * Log warning message
   */
  warn(message: string, metadata?: LogMetadata): void {
    logger.warn(message, { ...this.contextMetadata, ...metadata });
  }

  /**
   * Log error message
   */
  error(message: string, error?: Error | unknown, metadata?: LogMetadata): void {
    const errorMeta: LogMetadata = { ...this.contextMetadata, ...metadata };

    if (error instanceof Error) {
      errorMeta.error = {
        message: error.message,
        stack: error.stack,
        name: error.name
      };
    } else if (error) {
      errorMeta.error = error;
    }

    logger.error(message, errorMeta);
  }

  /**
   * Log audit event
   */
  audit(event: string, metadata: LogMetadata): void {
    auditLogger.info(event, { ...this.contextMetadata, ...metadata });
  }

  /**
   * Log performance metric
   */
  perf(metric: string, duration: number, metadata?: LogMetadata): void {
    perfLogger.debug(metric, {
      ...this.contextMetadata,
      ...metadata,
      duration,
      durationMs: duration
    });
  }

  /**
   * Log security event
   */
  security(event: string, severity: 'warn' | 'error', metadata?: LogMetadata): void {
    securityLogger[severity](event, { ...this.contextMetadata, ...metadata });
  }

  /**
   * Create child logger with additional context
   */
  child(childNamespace: string, additionalMetadata?: LogMetadata): Logger {
    return new Logger(
      `${this.namespace}:${childNamespace}`,
      { ...this.contextMetadata, ...additionalMetadata }
    );
  }

  /**
   * Set log level dynamically
   */
  setLevel(level: LogLevel): void {
    logger.level = level;
  }
}

/**
 * Create a namespaced logger instance
 */
export function createLogger(namespace: string, metadata?: LogMetadata): Logger {
  return new Logger(namespace, metadata);
}

/**
 * Default export for convenience
 */
export default logger;
