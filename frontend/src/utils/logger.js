/**
 * Frontend logging utility
 * Provides consistent logging across the application
 */

const LOG_LEVELS = {
  DEBUG: 'DEBUG',
  INFO: 'INFO',
  WARN: 'WARN',
  ERROR: 'ERROR'
};

const LOG_COLORS = {
  DEBUG: '#00a4ef',
  INFO: '#28a745',
  WARN: '#ffc107',
  ERROR: '#dc3545'
};

class Logger {
  constructor(namespace = 'App') {
    this.namespace = namespace;
  }

  _formatMessage(level, message, data) {
    const timestamp = new Date().toISOString();
    const style = `color: ${LOG_COLORS[level]}; font-weight: bold;`;
    
    return {
      formatted: `%c[${timestamp}] [${level}] [${this.namespace}] ${message}`,
      style,
      data
    };
  }

  debug(message, data = null) {
    const { formatted, style, data: logData } = this._formatMessage(LOG_LEVELS.DEBUG, message, data);
    console.log(formatted, style, logData);
  }

  info(message, data = null) {
    const { formatted, style, data: logData } = this._formatMessage(LOG_LEVELS.INFO, message, data);
    console.log(formatted, style, logData);
  }

  warn(message, data = null) {
    const { formatted, style, data: logData } = this._formatMessage(LOG_LEVELS.WARN, message, data);
    console.warn(formatted, style, logData);
  }

  error(message, error = null, data = null) {
    const { formatted, style } = this._formatMessage(LOG_LEVELS.ERROR, message, data);
    console.error(formatted, style, { error, ...data });
  }
}

export const createLogger = (namespace) => new Logger(namespace);
export default Logger;
