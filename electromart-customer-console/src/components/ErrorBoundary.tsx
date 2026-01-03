/**
 * Error Boundary Component
 * Catches React render errors and displays fallback UI
 * Prevents entire app crash from single component errors
 */
'use client';

import { Component, ReactNode, ErrorInfo } from 'react';
import { Box, Paper, Typography, Button, Alert } from '@mui/material';
import { ErrorOutline as ErrorIcon, Refresh as RefreshIcon } from '@mui/icons-material';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (props: FallbackProps) => ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

interface FallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  resetError: () => void;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    // Update state with error details
    this.setState((prevState) => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Send error to monitoring service (future)
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService = (error: Error, errorInfo: ErrorInfo): void => {
    // TODO: Send to error monitoring service (Sentry, LogRocket, etc.)
    console.error('Error logged:', {
      message: error.toString(),
      stack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
    });
  };

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback UI provided by parent
      if (this.props.fallback) {
        return this.props.fallback({
          error: this.state.error,
          errorInfo: this.state.errorInfo,
          resetError: this.handleReset,
        });
      }

      // Default fallback UI
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            bgcolor: '#f5f5f5',
            p: 3,
          }}
        >
          <Paper
            elevation={3}
            sx={{
              maxWidth: 600,
              width: '100%',
              p: 4,
              textAlign: 'center',
            }}
          >
            {/* Error Icon */}
            <ErrorIcon
              sx={{
                fontSize: 80,
                color: 'error.main',
                mb: 2,
              }}
            />

            {/* Error Title */}
            <Typography variant="h4" gutterBottom>
              Oops! Something went wrong
            </Typography>

            {/* Error Description */}
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              We encountered an unexpected error. Don&apos;t worry, your data is safe.
            </Typography>

            {/* Error Details (Development Only) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
                <Typography
                  variant="body2"
                  component="div"
                  sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
                >
                  <strong>Error:</strong> {this.state.error.toString()}
                </Typography>
                {this.state.errorInfo && (
                  <Typography
                    variant="body2"
                    component="pre"
                    sx={{
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      mt: 1,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      maxHeight: 200,
                      overflow: 'auto',
                    }}
                  >
                    {this.state.errorInfo.componentStack}
                  </Typography>
                )}
              </Alert>
            )}

            {/* Recovery Suggestions */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Try these steps to recover:
              </Typography>
              <Box component="ul" sx={{ textAlign: 'left', pl: 4 }}>
                <li>
                  <Typography variant="body2">Click &quot;Try Again&quot; to retry the operation</Typography>
                </li>
                <li>
                  <Typography variant="body2">Refresh the page if the problem persists</Typography>
                </li>
                <li>
                  <Typography variant="body2">Clear your browser cache and cookies</Typography>
                </li>
              </Box>
            </Box>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                onClick={this.handleReset}
                startIcon={<RefreshIcon />}
              >
                Try Again
              </Button>

              <Button variant="outlined" onClick={this.handleReload}>
                Reload Page
              </Button>
            </Box>

            {/* Error Count Warning */}
            {this.state.errorCount > 3 && (
              <Alert severity="warning" sx={{ mt: 3 }}>
                Multiple errors detected ({this.state.errorCount}). Please reload the page or contact support.
              </Alert>
            )}
          </Paper>

          {/* Additional Help */}
          <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
            Need help? Contact support at <a href="mailto:support@electromart.com">support@electromart.com</a>
          </Typography>
        </Box>
      );
    }

    // No error, render children normally
    return this.props.children;
  }
}

/**
 * Simple fallback component for chat errors
 * Can be used as custom fallback prop
 */
// export function ChatErrorFallback({ error, resetError }: { error: Error | null; resetError: () => void }): ReactNode {
//   return (
//     <Box
//       sx={{
//         display: 'flex',
//         flexDirection: 'column',
//         alignItems: 'center',
//         justifyContent: 'center',
//         height: '100vh',
//         p: 3,
//         bgcolor: '#f5f5f5',
//       }}
//     >
//       <Paper elevation={3} sx={{ p: 4, maxWidth: 500, textAlign: 'center' }}>
//         <ErrorIcon sx={{ fontSize: 60, color: 'error.main', mb: 2 }} />
//         <Typography variant="h5" gutterBottom>
//           Chat Error
//         </Typography>
//         <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
//           The chat encountered an error. Please try again.
//         </Typography>
//         {process.env.NODE_ENV === 'development' && error && (
//           <Alert severity="error" sx={{ mb: 2, textAlign: 'left' }}>
//             <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
//               {error.toString()}
//             </Typography>
//           </Alert>
//         )}
//         <Button variant="contained" onClick={resetError} startIcon={<RefreshIcon />}>
//           Restart Chat
//         </Button>
//       </Paper>
//     </Box>
//   );
// }

export default ErrorBoundary;
