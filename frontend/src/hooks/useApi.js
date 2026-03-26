import { useState, useCallback } from 'react';
import { createLogger } from '../utils/logger';

const logger = createLogger('useApi');

/**
 * Custom hook for making API calls with built-in error handling and loading states
 */
export const useApi = (componentName = 'Component') => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const call = useCallback(
    async (apiFunction, onSuccess = null, onError = null) => {
      setLoading(true);
      setError(null);

      try {
        logger.info(`[${componentName}] API call started`);
        const response = await apiFunction();
        
        logger.info(`[${componentName}] API call successful`, { data: response.data });
        
        if (onSuccess) {
          onSuccess(response.data);
        }
        
        return response.data;
      } catch (err) {
        const errorMessage = err.response?.data?.detail || err.message || 'An error occurred';
        
        logger.error(`[${componentName}] API call failed`, err, {
          status: err.response?.status,
          message: errorMessage
        });
        
        setError(errorMessage);
        
        if (onError) {
          onError(err);
        }
        
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [componentName]
  );

  const clearError = useCallback(() => setError(null), []);

  return {
    loading,
    error,
    call,
    clearError
  };
};

export default useApi;
