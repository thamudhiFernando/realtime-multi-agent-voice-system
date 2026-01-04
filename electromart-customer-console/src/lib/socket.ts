/**
 * Socket.IO Client for ElectroMart Multi-Agent System
 * Enhanced with robust reconnection and offline handling
 */
import { io, Socket } from 'socket.io-client';
import { SOCKET_CONFIG } from '@/config/constants';

let socket: Socket | null = null;
let sessionId: string | null = null; // Store session ID for reconnection

export const getSocket = (): Socket => {
    if (!socket) {
        socket = io(SOCKET_CONFIG.URL, {
            transports: SOCKET_CONFIG.TRANSPORTS as unknown as ('websocket' | 'polling')[],

            // Reconnection strategy
            reconnection: SOCKET_CONFIG.RECONNECTION,
            reconnectionAttempts: SOCKET_CONFIG.RECONNECTION_ATTEMPTS,
            reconnectionDelay: SOCKET_CONFIG.RECONNECTION_DELAY,
            reconnectionDelayMax: SOCKET_CONFIG.RECONNECTION_DELAY_MAX,
            randomizationFactor: SOCKET_CONFIG.RANDOMIZATION_FACTOR,

            // Connection timeout
            timeout: SOCKET_CONFIG.TIMEOUT,

            // Auto-connect
            autoConnect: true,

            // Path
            path: '/socket.io',

            // Auth - restore session if available
            auth: (cb) => {
                if (sessionId) {
                    cb({ session_id: sessionId });
                } else {
                    cb({});
                }
            },
        });

        // Store session ID when connected
        socket.on('connected', (data: { session_id: string }) => {
            sessionId = data.session_id;
            console.log('Session ID stored for reconnection:', sessionId);
        });

        // Log reconnection attempts
        socket.io.on('reconnect_attempt', (attempt: number) => {
            console.log(`Reconnection attempt ${attempt}...`);
        });

        socket.io.on('reconnect_error', (error: Error) => {
            console.error('Reconnection error:', error.message);
        });

        socket.io.on('reconnect_failed', () => {
            console.error('Reconnection failed after all attempts');
        });
    }

    return socket;
};

export const disconnectSocket = (): void => {
    if (socket) {
        socket.disconnect();
        socket = null;
        sessionId = null;
    }
};

export const getStoredSessionId = (): string | null => sessionId;
