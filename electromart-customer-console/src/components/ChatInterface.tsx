'use client';

import React, { useState, useEffect } from 'react';
import { Box, AppBar, Toolbar, Typography, Chip, Button, Alert, Snackbar } from '@mui/material';
import { Circle as CircleIcon, DeleteOutline as DeleteIcon, CancelOutlined as CancelIcon } from '@mui/icons-material';
import { useSocket } from '@/hooks/useSocket';
import MessageList from './MessageList';
import InputBox from './InputBox';
import { STATUS_COLORS, PLACEHOLDERS, getAgentDisplayName } from '@/config/constants';

export default function ChatInterface() {
    const [mounted, setMounted] = useState(false); // Track client mount
    const [showError, setShowError] = useState<string | null>(null);

    const {
        isConnected,
        isReconnecting,
        reconnectAttempt,
        sessionId,
        messages,
        isTyping,
        isSending,
        currentAgent,
        sendMessage,
        clearMessages,
        cancelMessage,
        cancelAllMessages,
        error,
        pendingMessagesCount,
        pendingMessages,
        offlineQueueCount,
    } = useSocket();

    useEffect(() => {
        setMounted(true);
    }, []);

    // Show error in Snackbar
    useEffect(() => {
        if (error) setShowError(error);
    }, [error]);

    const handleCloseError = () => setShowError(null);

    // Don't render dynamic parts until client mount
    if (!mounted) return <Box sx={{ height: '100vh', bgcolor: '#f5f5f5' }} />;

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
            {/* Header */}
            <AppBar position="static" elevation={1}>
                <Toolbar>
                    <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" component="div">
                            ElectroMart Support
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                            <CircleIcon
                                sx={{
                                    fontSize: 12,
                                    mr: 1,
                                    color: isConnected
                                        ? STATUS_COLORS.CONNECTED
                                        : isReconnecting
                                            ? STATUS_COLORS.RECONNECTING
                                            : STATUS_COLORS.DISCONNECTED,
                                    animation: isReconnecting ? 'pulse 1.5s ease-in-out infinite' : 'none',
                                    '@keyframes pulse': {
                                        '0%, 100%': { opacity: 1 },
                                        '50%': { opacity: 0.4 },
                                    },
                                }}
                            />
                            <Typography
                                variant="body2"
                                sx={{ color: 'rgba(255, 255, 255, 0.9)' }}
                                aria-live="polite"
                            >
                                {isConnected
                                    ? 'Connected'
                                    : isReconnecting
                                        ? `Reconnecting... (${reconnectAttempt})`
                                        : 'Disconnected'}
                                {currentAgent && ` • ${getAgentDisplayName(currentAgent)}`}
                                {pendingMessagesCount > 0 &&
                                    ` • Processing ${pendingMessagesCount} message${pendingMessagesCount > 1 ? 's' : ''}`}
                                {offlineQueueCount > 0 && ` • ${offlineQueueCount} queued`}
                            </Typography>
                        </Box>
                    </Box>

                    {/* Action Buttons */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {sessionId && (
                            <Chip
                                label={`Session: ${sessionId.slice(0, 8)}...`}
                                size="small"
                                sx={{
                                    bgcolor: 'rgba(255, 255, 255, 0.2)',
                                    color: 'white',
                                    fontFamily: 'monospace',
                                }}
                            />
                        )}

                        <Button
                            variant="outlined"
                            size="small"
                            startIcon={<CancelIcon />}
                            onClick={cancelAllMessages}
                            disabled={!isConnected || pendingMessagesCount === 0}
                            sx={{
                                color: STATUS_COLORS.WARNING,
                                borderColor: 'rgba(255, 152, 0, 0.7)',
                                '&:hover': {
                                    borderColor: STATUS_COLORS.WARNING,
                                    bgcolor: 'rgba(255, 152, 0, 0.1)',
                                },
                            }}
                        >
                            Cancel All ({pendingMessagesCount})
                        </Button>

                        <Button
                            variant="outlined"
                            size="small"
                            startIcon={<DeleteIcon />}
                            onClick={clearMessages}
                            sx={{
                                color: 'white',
                                borderColor: 'rgba(255, 255, 255, 0.5)',
                                '&:hover': {
                                    borderColor: 'white',
                                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                                },
                            }}
                        >
                            Clear Chat
                        </Button>
                    </Box>
                </Toolbar>
            </AppBar>

            {/* Error Snackbar */}
            <Snackbar
                open={!!showError}
                autoHideDuration={5000}
                onClose={handleCloseError}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
                    {showError}
                </Alert>
            </Snackbar>

            {/* Messages Area */}
            <Box sx={{ flexGrow: 1, overflow: 'hidden', bgcolor: '#f5f5f5' }}>
                <MessageList
                    messages={messages}
                    isTyping={isTyping}
                    currentAgent={currentAgent}
                    pendingMessages={pendingMessages}
                    onCancelMessage={cancelMessage}
                />
            </Box>

            {/* Input Area */}
            <Box sx={{ borderTop: 1, borderColor: 'divider', bgcolor: 'white', p: 2 }}>
                <InputBox
                    onSend={sendMessage}
                    disabled={!mounted} // Disable until client mount
                    isSending={isSending}
                    placeholder={
                        !isConnected
                            ? isReconnecting
                                ? PLACEHOLDERS.RECONNECTING
                                : PLACEHOLDERS.OFFLINE
                            : PLACEHOLDERS.DEFAULT
                    }
                />
            </Box>
        </Box>
    );
}
