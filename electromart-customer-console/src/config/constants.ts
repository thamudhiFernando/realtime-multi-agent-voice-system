/**
 * Frontend Constants - Single Source of Truth
 * Eliminates magic numbers and provides configuration
 */

// ============================================================================
// TIMING CONSTANTS
// ============================================================================

export const TIMING = {
  // Send throttling
  DUPLICATE_SEND_THROTTLE_MS: 2000,
  SENDING_STATE_DURATION_MS: 1000,

  // Error display
  ERROR_AUTO_CLEAR_MS: 2000,
  SNACKBAR_AUTO_HIDE_MS: 6000,

  // Socket.IO reconnection
  RECONNECTION_DELAY_MS: 1000,
  RECONNECTION_DELAY_MAX_MS: 10000,
  RECONNECTION_TIMEOUT_MS: 20000,

  // UI updates
  TYPING_INDICATOR_DEBOUNCE_MS: 300,
  SCROLL_TO_BOTTOM_DEBOUNCE_MS: 100,
  SCROLL_BEHAVIOR_THRESHOLD_PX: 100,

  // Animation durations
  PULSE_ANIMATION_DURATION_MS: 1500,
  FADE_ANIMATION_DURATION_MS: 300,
} as const;

// ============================================================================
// MESSAGE CORRELATION
// ============================================================================

export const MESSAGE_CORRELATION = {
  COLORS: [
    '#1976d2', // Blue
    '#9c27b0', // Purple
    '#2e7d32', // Green
    '#ed6c02', // Orange
    '#d32f2f', // Red
    '#00796b', // Teal
  ],
  MAX_HISTORY_MESSAGES: 5,
  BADGE_SIZE: 24,
} as const;

// ============================================================================
// UI CONFIGURATION
// ============================================================================

export const UI_CONFIG = {
  // Message list
  MAX_VISIBLE_MESSAGES: 100, // Virtual scrolling threshold
  MESSAGE_BATCH_SIZE: 20,

  // Input box
  MAX_INPUT_ROWS: 4,
  MAX_MESSAGE_LENGTH: 1000,

  // Voice input
  VOICE_RECOGNITION_TIMEOUT_MS: 5000,
  VOICE_INACTIVITY_TIMEOUT_MS: 3000,

  // Responsive breakpoints (Material-UI)
  BREAKPOINTS: {
    xs: 0,
    sm: 600,
    md: 960,
    lg: 1280,
    xl: 1920,
  },
} as const;

// ============================================================================
// SOCKET CONFIGURATION
// ============================================================================

export const SOCKET_CONFIG = {
  URL: process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:8000',

  // Connection options
  RECONNECTION: true,
  RECONNECTION_ATTEMPTS: Infinity,
  RECONNECTION_DELAY: 1000,
  RECONNECTION_DELAY_MAX: 10000,
  RANDOMIZATION_FACTOR: 0.5,
  TIMEOUT: 20000,

  // Transport
  TRANSPORTS: ['websocket', 'polling'] as const,
  UPGRADE: true,

  // Ping/Pong
  PING_INTERVAL: 25000,
  PING_TIMEOUT: 60000,
} as const;

// ============================================================================
// ANIMATION KEYFRAMES
// ============================================================================

export const ANIMATIONS = {
  PULSE: {
    '0%': { opacity: 1 },
    '50%': { opacity: 0.4 },
    '100%': { opacity: 1 },
  },

  PULSE_SHADOW: {
    '0%': { boxShadow: '0 0 0 0 rgba(76, 175, 80, 0.7)' },
    '70%': { boxShadow: '0 0 0 10px rgba(76, 175, 80, 0)' },
    '100%': { boxShadow: '0 0 0 0 rgba(76, 175, 80, 0)' },
  },

  SEND_PULSE: {
    '0%, 100%': { opacity: 1 },
    '50%': { opacity: 0.6 },
  },

  FADE_IN: {
    from: { opacity: 0 },
    to: { opacity: 1 },
  },
} as const;

// ============================================================================
// STATUS COLORS
// ============================================================================

export const STATUS_COLORS = {
  CONNECTED: '#4caf50',
  RECONNECTING: '#ff9800',
  DISCONNECTED: '#f44336',

  SENDING: '#ff9800',
  SUCCESS: '#4caf50',
  ERROR: '#f44336',
  WARNING: '#ff9800',
  INFO: '#2196f3',
} as const;

// ============================================================================
// ERROR MESSAGES
// ============================================================================

export const ERROR_MESSAGES = {
  CONNECTION_LOST: 'Connection lost. Attempting to reconnect...',
  RECONNECTING: 'Reconnecting...',
  CANNOT_RECONNECT: 'Cannot reconnect to server. Please refresh the page.',

  SEND_TOO_FAST: 'Please wait before sending the same message again',
  MESSAGE_EMPTY: 'Please enter a message',
  MESSAGE_TOO_LONG: 'Message is too long. Please keep it under 1000 characters',

  VOICE_NOT_SUPPORTED: 'Voice input is not supported in your browser',
  VOICE_PERMISSION_DENIED: 'Microphone permission denied',
  VOICE_NO_SPEECH: 'No speech detected. Please try again.',
  VOICE_ERROR: 'Voice recognition error. Please try again.',

  OFFLINE: 'You are offline. Messages will be sent when connection is restored.',
  ALREADY_PROCESSING: 'This message is already being processed.',
} as const;

// ============================================================================
// SUCCESS MESSAGES
// ============================================================================

export const SUCCESS_MESSAGES = {
  CONNECTED: 'Connected',
  RECONNECTED: 'Reconnected successfully!',
  MESSAGE_SENT: 'Message sent',
  MESSAGE_CANCELLED: 'Message cancelled',
} as const;

// ============================================================================
// PLACEHOLDER TEXT
// ============================================================================

export const PLACEHOLDERS = {
  DEFAULT: 'Type your message or use voice input... (Press Enter to send)',
  CONNECTING: 'Connecting...',
  RECONNECTING: 'Reconnecting... Messages will be queued',
  OFFLINE: 'Offline - Messages will be sent when reconnected',
  LISTENING: 'Listening... Speak now',
  DISABLED: 'Please wait...',
} as const;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get agent display name
 */
export function getAgentDisplayName(agent: string | null | undefined): string {
  if (!agent) return 'Assistant';
  return agent.charAt(0).toUpperCase() + agent.slice(1) + ' Agent';
}
