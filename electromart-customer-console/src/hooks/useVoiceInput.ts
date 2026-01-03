/**
 * Custom React Hook for Voice Input using Web Speech API
 *
 * Provides voice recognition functionality with browser compatibility checks
 * and real-time transcription capabilities.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { VoiceInputHook } from '@/types';
import { ERROR_MESSAGES } from '@/config/constants';

// Extend Window interface to include webkit speech recognition
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

/**
 * Hook to manage voice input using the Web Speech API
 */
export default function useVoiceInput(): VoiceInputHook {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  // Check if Speech Recognition is supported
  const isSupported =
    typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  /**
   * Initialize Speech Recognition API
   */
  useEffect(() => {
    if (!isSupported) {
      setError(ERROR_MESSAGES.VOICE_NOT_SUPPORTED);
      return;
    }

    // Use webkit prefix for Chrome/Edge
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    // Configuration
    recognition.continuous = true; // Keep listening until stopped
    recognition.interimResults = true; // Get results while speaking
    recognition.lang = 'en-US'; // Language setting
    recognition.maxAlternatives = 1;

    /**
     * Handle speech recognition results
     */
    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      // Process all results
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPiece = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcriptPiece + ' ';
        } else {
          interimTranscript += transcriptPiece;
        }
      }

      // Update transcript with final or interim results
      if (finalTranscript) {
        setTranscript((prev) => prev + finalTranscript);
      } else if (interimTranscript) {
        setTranscript((prev) => {
          const lastSpace = prev.lastIndexOf(' ');
          return lastSpace >= 0
            ? prev.substring(0, lastSpace + 1) + interimTranscript
            : interimTranscript;
        });
      }
    };

    /**
     * Handle recognition errors
     */
    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);

      switch (event.error) {
        case 'no-speech':
          setError(ERROR_MESSAGES.VOICE_NO_SPEECH);
          break;
        case 'audio-capture':
          setError('No microphone found. Please check your device.');
          break;
        case 'not-allowed':
          setError(ERROR_MESSAGES.VOICE_PERMISSION_DENIED);
          break;
        case 'network':
          setError('Network error occurred. Please check your connection.');
          break;
        default:
          setError(ERROR_MESSAGES.VOICE_ERROR);
      }

      setIsListening(false);
    };

    /**
     * Handle recognition end
     */
    recognition.onend = () => {
      setIsListening(false);
    };

    /**
     * Handle recognition start
     */
    recognition.onstart = () => {
      setError(null);
      setIsListening(true);
    };

    recognitionRef.current = recognition;

    // Cleanup on unmount
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isSupported]);

  /**
   * Start listening for voice input
   */
  const startListening = useCallback(() => {
    if (!isSupported) {
      setError(ERROR_MESSAGES.VOICE_NOT_SUPPORTED);
      return;
    }

    if (!recognitionRef.current) {
      setError('Speech recognition not initialized');
      return;
    }

    try {
      setError(null);
      recognitionRef.current.start();
    } catch (err: any) {
      // Already started, ignore
      if (err.name === 'InvalidStateError') {
        console.log('Recognition already started');
      } else {
        setError(`Failed to start: ${err.message}`);
      }
    }
  }, [isSupported]);

  /**
   * Stop listening for voice input
   */
  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        console.error('Error stopping recognition:', err);
      }
    }
  }, [isListening]);

  /**
   * Reset the current transcript
   */
  const resetTranscript = useCallback(() => {
    setTranscript('');
    setError(null);
  }, []);

  return {
    isListening,
    isSupported,
    transcript,
    error,
    startListening,
    stopListening,
    resetTranscript,
  };
}
