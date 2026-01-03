/**
 * Input Box Component with Material-UI
 * Supports both text and voice input
 */
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

  const {
    isListening,
    isSupported,
    transcript,
    error: voiceError,
    startListening,
    stopListening,
    resetTranscript,
  } = useVoiceInput();

  /**
   * Sync voice transcript with message input
   */
  useEffect(() => {
    if (transcript) {
      setMessage(transcript);
    }
  }, [transcript]);

  /**
   * Show error notification when voice recognition fails
   */
  useEffect(() => {
    if (voiceError) {
      setShowVoiceError(true);
    }
  }, [voiceError]);

  /**
   * Handle send button click
   * Sends message and resets input
   */
  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
      resetTranscript();
    }
  };

  /**
   * Handle Enter key press to send message
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  /**
   * Toggle voice input on/off
   */
  const handleVoiceToggle = () => {
    if (isListening) {
      stopListening();
    } else {
      resetTranscript();
      setMessage(''); // Clear text input when starting voice
      startListening();
    }
  };

  /**
   * Close error notification
   */
  const handleCloseError = () => {
    setShowVoiceError(false);
  };

  return (
    <>
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
        {/* Text Input Field */}
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

        {/* Voice Input Button */}
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
                  // Pulsing animation when listening
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

        {/* Send Button */}
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
                // Pulse animation when sending
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

      {/* Voice Error Notification */}
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
