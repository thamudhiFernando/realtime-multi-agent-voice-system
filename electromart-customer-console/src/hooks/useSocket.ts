/**
 * Custom React hook for Socket.IO integration
 * Supports concurrent message processing with correlation IDs
 * Enhanced with offline queue and reconnection handling
 */
'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { Socket } from 'socket.io-client';
import { getSocket, disconnectSocket } from '@/lib/socket';
import {
  Message,
  PendingMessage,
  OfflineQueuedMessage,
  SocketResponse,
  SocketError,
  AgentSwitchData,
  MessageQueuedData,
  MessageCancelledData,
  AllMessagesCancelledData,
  ConnectedData,
  AgentType,
  SocketHook,
} from '@/types';
import {
  TIMING,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
} from '@/config/constants';

export const useSocket = (): SocketHook => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isReconnecting, setIsReconnecting] = useState<boolean>(false);
  const [reconnectAttempt, setReconnectAttempt] = useState<number>(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [currentAgent, setCurrentAgent] = useState<AgentType | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Track in-flight messages for concurrent processing
  const [pendingMessages, setPendingMessages] = useState<Map<string, PendingMessage>>(new Map());

  // Offline message queue
  const [offlineQueue, setOfflineQueue] = useState<OfflineQueuedMessage[]>([]);

  // Sending state (prevents double-click)
  const [isSending, setIsSending] = useState<boolean>(false);
  const lastSentMessage = useRef<string | null>(null);
  const lastSentTime = useRef<number>(0);

  const messagesRef = useRef<Message[]>([]);
  const pendingMessagesRef = useRef<Map<string, PendingMessage>>(new Map());
  const offlineQueueRef = useRef<OfflineQueuedMessage[]>([]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    pendingMessagesRef.current = pendingMessages;
  }, [pendingMessages]);

  useEffect(() => {
    offlineQueueRef.current = offlineQueue;
  }, [offlineQueue]);

  useEffect(() => {
    // Initialize socket connection
    const socketInstance = getSocket();
    setSocket(socketInstance);

    // Connection events
    socketInstance.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
      setIsReconnecting(false);
      setReconnectAttempt(0);
      setError(null);

      // Process offline queue
      if (offlineQueueRef.current.length > 0) {
        console.log(`Processing ${offlineQueueRef.current.length} offline messages...`);

        const systemMessage: Message = {
          role: 'assistant',
          content: `Reconnected! Sending ${offlineQueueRef.current.length} message(s) from offline queue...`,
          timestamp: new Date().toISOString(),
          agent: 'system',
          metadata: { type: 'reconnection' },
        };

        setMessages((prev) => [...prev, systemMessage]);

        // Send all queued messages
        offlineQueueRef.current.forEach((queuedMsg) => {
          socketInstance.emit('message', {
            message: queuedMsg.message,
            type: queuedMsg.type,
          });
        });

        // Clear offline queue
        setOfflineQueue([]);
      }
    });

    socketInstance.on('disconnect', (reason: string) => {
      console.log('Socket disconnected:', reason);
      setIsConnected(false);
      setError(ERROR_MESSAGES.CONNECTION_LOST);

      // Show disconnection message
      const systemMessage: Message = {
        role: 'assistant',
        content: ERROR_MESSAGES.CONNECTION_LOST,
        timestamp: new Date().toISOString(),
        agent: 'system',
        metadata: { type: 'disconnection', reason },
      };

      setMessages((prev) => [...prev, systemMessage]);
    });

    // Reconnection events
    socketInstance.io.on('reconnect', (attempt: number) => {
      console.log('Reconnected after', attempt, 'attempts');
      setIsReconnecting(false);
      setReconnectAttempt(0);

      const systemMessage: Message = {
        role: 'assistant',
        content: `${SUCCESS_MESSAGES.RECONNECTED} ${attempt > 1 ? `(after ${attempt} attempts)` : ''}`,
        timestamp: new Date().toISOString(),
        agent: 'system',
        metadata: { type: 'reconnection', attempts: attempt },
      };

      setMessages((prev) => [...prev, systemMessage]);
    });

    socketInstance.io.on('reconnect_attempt', (attempt: number) => {
      console.log('Reconnection attempt:', attempt);
      setIsReconnecting(true);
      setReconnectAttempt(attempt);
      setError(`${ERROR_MESSAGES.RECONNECTING} (attempt ${attempt})`);
    });

    socketInstance.io.on('reconnect_error', (error: Error) => {
      console.error('Reconnection error:', error.message);
      setError(`Reconnection failed: ${error.message}`);
    });

    socketInstance.io.on('reconnect_failed', () => {
      console.error('Reconnection failed permanently');
      setIsReconnecting(false);
      setError(ERROR_MESSAGES.CANNOT_RECONNECT);

      const systemMessage: Message = {
        role: 'assistant',
        content: ERROR_MESSAGES.CANNOT_RECONNECT,
        timestamp: new Date().toISOString(),
        agent: 'system',
        metadata: { type: 'reconnection_failed' },
      };

      setMessages((prev) => [...prev, systemMessage]);
    });

    socketInstance.on('connected', (data: ConnectedData) => {
      console.log('Session established:', data.session_id);
      setSessionId(data.session_id);
    });

    // Message queued event - acknowledgment that message was queued
    socketInstance.on('message_queued', (data: MessageQueuedData) => {
      console.log('Message queued:', data.message_id);

      // Update pending message status
      setPendingMessages((prev) => {
        const updated = new Map(prev);
        const pendingMsg = updated.get(data.message_id);
        if (pendingMsg) {
          pendingMsg.status = 'queued';
          pendingMsg.queue_position = data.queue_position;
        }
        return updated;
      });
    });

    // Message events - with correlation ID support
    socketInstance.on('response', (data: SocketResponse) => {
      console.log('Response received from:', data.agent, 'for message:', data.message_id);

      const newMessage: Message = {
        role: 'assistant',
        content: data.message,
        timestamp: data.timestamp || new Date().toISOString(),
        agent: data.agent,
        metadata: data.metadata,
        message_id: data.message_id,
      };

      setMessages((prev) => [...prev, newMessage]);
      setCurrentAgent(data.agent);

      // Remove from pending messages
      if (data.message_id) {
        setPendingMessages((prev) => {
          const updated = new Map(prev);
          updated.delete(data.message_id!);
          return updated;
        });
      }

      // Only stop typing if no more pending messages
      setPendingMessages((prev) => {
        if (prev.size === 0) {
          setIsTyping(false);
        }
        return prev;
      });
    });

    // Typing events - with message_id for tracking
    socketInstance.on('typing', (data: { is_typing: boolean; message_id?: string }) => {
      if (data.message_id) {
        // Update pending message status
        setPendingMessages((prev) => {
          const updated = new Map(prev);
          const pendingMsg = updated.get(data.message_id!);
          if (pendingMsg) {
            pendingMsg.is_typing = data.is_typing;
          }
          return updated;
        });
      }

      // Show typing indicator if any messages are being processed
      setIsTyping(data.is_typing || pendingMessagesRef.current.size > 0);
    });

    // Agent switch events
    socketInstance.on('agent_switch', (data: AgentSwitchData) => {
      console.log(`Agent switched from ${data.from_agent} to ${data.to_agent}`);
      setCurrentAgent(data.to_agent);

      // Add system message about agent switch
      const systemMessage: Message = {
        role: 'assistant',
        content: `Transferring you to our ${data.to_agent} specialist...`,
        timestamp: new Date().toISOString(),
        agent: 'system',
        metadata: { type: 'agent_switch', ...data },
        message_id: data.message_id,
      };

      setMessages((prev) => [...prev, systemMessage]);
    });

    // Error events - with message_id for correlation
    socketInstance.on('error', (data: SocketError) => {
      console.error('Socket error:', data);
      setError(data.message);

      // Remove from pending messages if error relates to a specific message
      if (data.message_id) {
        setPendingMessages((prev) => {
          const updated = new Map(prev);
          updated.delete(data.message_id!);
          return updated;
        });
      }

      // Only stop typing if no more pending messages
      setPendingMessages((prev) => {
        if (prev.size === 0) {
          setIsTyping(false);
        }
        return prev;
      });
    });

    // Message cancelled event
    socketInstance.on('message_cancelled', (data: MessageCancelledData) => {
      console.log('Message cancelled:', data.message_id);

      // Remove from pending messages
      setPendingMessages((prev) => {
        const updated = new Map(prev);
        updated.delete(data.message_id);
        return updated;
      });

      // Remove from messages list (visual feedback)
      setMessages((prev) => prev.filter((msg) => msg.message_id !== data.message_id));

      // Only stop typing if no more pending messages
      if (pendingMessagesRef.current.size <= 1) {
        setIsTyping(false);
      }
    });

    // All messages cancelled event
    socketInstance.on('all_messages_cancelled', (data: AllMessagesCancelledData) => {
      console.log('All messages cancelled:', data.cancelled_count);

      // Clear all pending messages
      setPendingMessages(new Map());
      setIsTyping(false);

      // Show notification
      const systemMessage: Message = {
        role: 'assistant',
        content: data.message || `Cancelled ${data.cancelled_count} pending message(s)`,
        timestamp: new Date().toISOString(),
        agent: 'system',
        metadata: { type: 'cancellation', ...data },
      };

      setMessages((prev) => [...prev, systemMessage]);
    });

    // Message duplicate detection
    socketInstance.on('message_duplicate', (data: { original_message: string }) => {
      console.log('Duplicate message detected:', data.original_message);

      // Show subtle notification (don't spam with system messages)
      const systemMessage: Message = {
        role: 'assistant',
        content: ERROR_MESSAGES.ALREADY_PROCESSING,
        timestamp: new Date().toISOString(),
        agent: 'system',
        metadata: { type: 'duplicate', ...data },
      };

      setMessages((prev) => [...prev, systemMessage]);

      // Clear sending state
      setIsSending(false);
    });

    // Cleanup on unmount
    return () => {
      disconnectSocket();
    };
  }, []);

  const sendMessage = useCallback(
    (message: string) => {
      if (!message.trim()) {
        return;
      }

      // Frontend throttling - prevent rapid duplicate sends
      const now = Date.now();
      const timeSinceLastSend = now - lastSentTime.current;
      const normalizedMessage = message.trim().toLowerCase();

      // Check if same message sent within throttle time (double-click protection)
      if (lastSentMessage.current === normalizedMessage && timeSinceLastSend < TIMING.DUPLICATE_SEND_THROTTLE_MS) {
        console.log('Duplicate send attempt blocked (< 2s since last send)');
        setError(ERROR_MESSAGES.SEND_TOO_FAST);
        setTimeout(() => setError(null), TIMING.ERROR_AUTO_CLEAR_MS);
        return;
      }

      // Check if already sending
      if (isSending) {
        console.log('Already sending a message, please wait');
        return;
      }

      // Update last sent tracking
      lastSentMessage.current = normalizedMessage;
      lastSentTime.current = now;
      setIsSending(true);

      // Generate temporary message_id for tracking
        const tempMessageId = `temp_${Date.now()}_${Math.random()
            .toString(36)
            .substring(2, 11)}`;

      // Add user message to UI
      const userMessage: Message = {
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
        message_id: tempMessageId,
      };

      setMessages((prev) => [...prev, userMessage]);
      setError(null);

      // If not connected, queue message for later
      if (!socket || !isConnected) {
        console.log('Offline: Queueing message for later');

        setOfflineQueue((prev) => [
          ...prev,
          {
            message: message,
            type: 'text',
            queued_at: Date.now(),
            message_id: tempMessageId,
          },
        ]);

        // Show offline indicator on message
        const offlineMessage: Message = {
          role: 'assistant',
          content: ERROR_MESSAGES.OFFLINE,
          timestamp: new Date().toISOString(),
          agent: 'system',
          metadata: { type: 'offline_queued' },
        };

        setMessages((prev) => [...prev, offlineMessage]);
        setIsSending(false);
        return;
      }

      // Track as pending message
      setPendingMessages((prev) => {
        const updated = new Map(prev);
        updated.set(tempMessageId, {
          message: message,
          status: 'sending',
          sent_at: Date.now(),
          is_typing: false,
        });
        return updated;
      });

      // Send message to server (non-blocking)
      socket.emit('message', {
        message: message,
        type: 'text',
      });

      // Set typing indicator for this message
      setIsTyping(true);

      // Clear sending state after acknowledgment
      setTimeout(() => {
        setIsSending(false);
      }, TIMING.SENDING_STATE_DURATION_MS);

      console.log('Message sent:', message, 'with tracking ID:', tempMessageId);
    },
    [socket, isConnected, isSending]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setCurrentAgent(null);
    setError(null);
    setPendingMessages(new Map());
  }, []);

  const cancelMessage = useCallback(
    (messageId: string) => {
      if (!socket || !isConnected) {
        console.warn('Cannot cancel message: not connected');
        return;
      }

      socket.emit('cancel_message', { message_id: messageId });
      console.log('Cancel message requested:', messageId);
    },
    [socket, isConnected]
  );

  const cancelAllMessages = useCallback(() => {
    if (!socket || !isConnected) {
      console.warn('Cannot cancel messages: not connected');
      return;
    }

    socket.emit('cancel_all_messages');
    console.log('Cancel all messages requested');
  }, [socket, isConnected]);

  return {
    socket,
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
    pendingMessages,
    pendingMessagesCount: pendingMessages.size,
    offlineQueue,
    offlineQueueCount: offlineQueue.length,
  };
};
