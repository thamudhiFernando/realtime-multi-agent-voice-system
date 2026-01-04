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
    mounted: boolean; // Track client mount
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
            mounted: false,
        };
    }

    componentDidMount() {
        this.setState({ mounted: true });
    }

    static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
        return { hasError: true };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        // Log error in dev
        if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
            console.error('ErrorBoundary caught an error:', error, errorInfo);
        }

        this.setState((prev) => ({
            error,
            errorInfo,
            errorCount: prev.errorCount + 1,
        }));

        this.logErrorToService(error, errorInfo);
    }

    logErrorToService = (error: Error, errorInfo: ErrorInfo) => {
        // Example: Sentry, LogRocket, etc.
        if (typeof window !== 'undefined') {
            console.error('Error logged:', {
                message: error.toString(),
                stack: errorInfo.componentStack,
                timestamp: new Date().toISOString(),
            });
        }
    };

    handleReset = () => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null,
        });
    };

    handleReload = () => {
        if (typeof window !== 'undefined') {
            window.location.reload();
        }
    };

    render(): ReactNode {
        const { hasError, error, errorInfo, errorCount, mounted } = this.state;

        // SSR fallback: just render children if server
        if (!mounted) return this.props.children;

        if (hasError) {
            // Custom fallback if provided
            if (this.props.fallback) {
                return this.props.fallback({ error, errorInfo, resetError: this.handleReset });
            }

            // Default hydration-safe fallback
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
                        sx={{ maxWidth: 600, width: '100%', p: 4, textAlign: 'center' }}
                    >
                        <ErrorIcon sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
                        <Typography variant="h4" gutterBottom>
                            Oops! Something went wrong
                        </Typography>
                        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                            An unexpected error occurred. Your data is safe.
                        </Typography>

                        {error && (
                            <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
                                <Typography
                                    variant="body2"
                                    component="div"
                                    sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
                                >
                                    <strong>Error:</strong> {error.toString()}
                                </Typography>
                                {errorInfo && (
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
                                        {errorInfo.componentStack}
                                    </Typography>
                                )}
                            </Alert>
                        )}

                        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 2 }}>
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

                        {errorCount > 3 && (
                            <Alert severity="warning" sx={{ mt: 3 }}>
                                Multiple errors detected ({errorCount}). Please reload the page or contact support.
                            </Alert>
                        )}
                    </Paper>

                    <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
                        Need help? Contact support at{' '}
                        <a href="mailto:support@electromart.com">support@electromart.com</a>
                    </Typography>
                </Box>
            );
        }

        // No error, render normally
        return this.props.children;
    }
}

export default ErrorBoundary;
