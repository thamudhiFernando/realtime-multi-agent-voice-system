'use client';

import React, { useState, useEffect } from 'react';
import { Box, TextField, IconButton, Tooltip, Alert, Snackbar } from '@mui/material';
import { Send as SendIcon, Mic as MicIcon, MicOff as MicOffIcon } from '@mui/icons-material';
import useVoiceInput from '../hooks/useVoiceInput';
import { STATUS_COLORS, PLACEHOLDERS, TIMING, UI_CONFIG, ANIMATIONS } from '@/config/constants';

interface InputBoxProps {
    onSend: (message: string) => void;
    disabled?: boolean;
    placeholder?: string;
    isSending?: boolean;
}

export default function InputBox({ onSend, disabled = false, placeholder, isSending = false }: InputBoxProps) {
    const [message, setMessage] = useState<string>('');
    const [showVoiceError, setShowVoiceError] = useState<boolean>(false);
    const [mounted, setMounted] = useState(false); // ✅ track client mount

    const {
        isListening,
        isSupported,
        transcript,
        error: voiceError,
        startListening,
        stopListening,
        resetTranscript,
    } = useVoiceInput();

    // Mark as mounted
    useEffect(() => setMounted(true), []);

    // Sync voice transcript with input
    useEffect(() => {
        if (transcript) setMessage(transcript);
    }, [transcript]);

    useEffect(() => {
        if (voiceError) setShowVoiceError(true);
    }, [voiceError]);

    const handleSend = () => {
        if (message.trim() && !disabled) {
            onSend(message.trim());
            setMessage('');
            resetTranscript();
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleVoiceToggle = () => {
        if (!mounted) return; // prevent SSR click
        if (isListening) stopListening();
        else {
            resetTranscript();
            setMessage('');
            startListening();
        }
    };

    const handleCloseError = () => setShowVoiceError(false);

    // ❌ Don’t render dynamic buttons before mount
    if (!mounted) return (
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            <TextField fullWidth disabled placeholder="Loading..." />
            <IconButton disabled />
            <IconButton disabled />
        </Box>
    );

    return (
        <>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
                <TextField
                    fullWidth
                    multiline
                    maxRows={UI_CONFIG.MAX_INPUT_ROWS}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={
                        placeholder ||
                        (disabled
                            ? PLACEHOLDERS.CONNECTING
                            : isListening
                                ? PLACEHOLDERS.LISTENING
                                : PLACEHOLDERS.DEFAULT)
                    }
                    disabled={disabled}
                    variant="outlined"
                    sx={{
                        '& .MuiOutlinedInput-root': {
                            bgcolor: isListening ? '#e8f5e9' : 'background.paper',
                            transition: 'background-color 0.3s ease',
                            ...(isListening && {
                                borderColor: STATUS_COLORS.CONNECTED,
                                '& fieldset': {
                                    borderColor: `${STATUS_COLORS.CONNECTED} !important`,
                                    borderWidth: '2px !important',
                                },
                            }),
                        },
                    }}
                />

                {isSupported && (
                    <Tooltip title={isListening ? 'Stop recording' : 'Start voice input'}>
            <span>
              <IconButton
                  onClick={handleVoiceToggle}
                  disabled={disabled}
                  sx={{
                      bgcolor: isListening ? STATUS_COLORS.CONNECTED : 'secondary.main',
                      color: 'white',
                      width: 56,
                      height: 56,
                      '&:hover': {
                          bgcolor: isListening ? '#45a049' : 'secondary.dark',
                      },
                      '&.Mui-disabled': {
                          bgcolor: 'action.disabledBackground',
                          color: 'action.disabled',
                      },
                      ...(isListening && {
                          animation: `pulse ${TIMING.PULSE_ANIMATION_DURATION_MS}ms ease-in-out infinite`,
                          '@keyframes pulse': ANIMATIONS.PULSE_SHADOW,
                      }),
                  }}
              >
                {isListening ? <MicIcon /> : <MicOffIcon />}
              </IconButton>
            </span>
                    </Tooltip>
                )}

                <Tooltip title={isSending ? 'Sending...' : 'Send message'}>
          <span>
            <IconButton
                color="primary"
                onClick={handleSend}
                disabled={disabled || !message.trim() || isSending}
                sx={{
                    bgcolor: isSending ? STATUS_COLORS.SENDING : 'primary.main',
                    color: 'white',
                    width: 56,
                    height: 56,
                    '&:hover': {
                        bgcolor: isSending ? STATUS_COLORS.SENDING : 'primary.dark',
                    },
                    '&.Mui-disabled': {
                        bgcolor: 'action.disabledBackground',
                        color: 'action.disabled',
                    },
                    ...(isSending && {
                        animation: 'sendPulse 1s ease-in-out infinite',
                        '@keyframes sendPulse': ANIMATIONS.SEND_PULSE,
                    }),
                }}
            >
              <SendIcon />
            </IconButton>
          </span>
                </Tooltip>
            </Box>

            <Snackbar
                open={showVoiceError}
                autoHideDuration={TIMING.SNACKBAR_AUTO_HIDE_MS}
                onClose={handleCloseError}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
                    {voiceError}
                </Alert>
            </Snackbar>
        </>
    );
}
