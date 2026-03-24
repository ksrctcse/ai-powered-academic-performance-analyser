
import React from 'react';
import ReactDOM from 'react-dom/client';
import 'primereact/resources/themes/lara-light-cyan/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import './styles/global.css';
import App from './pages/App';
import ErrorBoundary from './components/ErrorBoundary';

// Setup global error handler
window.addEventListener('error', (event) => {
  console.error('[Global Error Handler]', {
    timestamp: new Date().toISOString(),
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error
  });
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('[Unhandled Promise Rejection]', {
    timestamp: new Date().toISOString(),
    reason: event.reason
  });
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
