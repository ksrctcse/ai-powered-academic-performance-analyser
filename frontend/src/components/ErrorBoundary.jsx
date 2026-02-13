import React from 'react';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import './ErrorBoundary.css';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[Error Boundary Caught Error]', {
      timestamp: new Date().toISOString(),
      error: error.toString(),
      componentStack: errorInfo.componentStack
    });

    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1
    }));
  }

  handleReset = () => {
    this.setState({ 
      hasError: false, 
      error: null,
      errorInfo: null
    });
  };

  handleReload = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-container">
          <Card className="error-card">
            <div className="error-content">
              <h1>⚠️ Something went wrong</h1>
              <p className="error-message">
                An unexpected error occurred. Please try again or contact support if the problem persists.
              </p>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="error-details">
                  <summary>Error Details (Dev Only)</summary>
                  <pre className="error-stack">
                    {this.state.error.toString()}
                    {this.state.errorInfo && this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}
              
              <div className="error-actions">
                <Button 
                  label="Try Again"
                  onClick={this.handleReset}
                  className="p-button-primary"
                />
                <Button 
                  label="Go to Home"
                  onClick={this.handleReload}
                  className="p-button-secondary"
                />
              </div>

              {this.state.errorCount > 3 && (
                <p className="error-warning">
                  Multiple errors detected. Please reload the page.
                </p>
              )}
            </div>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
