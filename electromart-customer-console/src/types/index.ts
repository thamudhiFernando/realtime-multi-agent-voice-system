/**
 * TypeScript Type Definitions for ElectroMart
 */

export type MessageRole = 'user' | 'assistant';

export type AgentType = 'orchestrator' | 'sales' | 'marketing' | 'support' | 'logistics' | 'human' | 'system';

export type MessageType = 'text' | 'voice' | 'system' | 'error';

export type MetadataType =
    | 'agent_switch'
    | 'disconnection'
    | 'reconnection'
    | 'reconnection_failed'
    | 'offline_queued'
    | 'duplicate'
    | 'cancellation';

export interface MessageMetadata {
    type?: MetadataType;
    from_agent?: AgentType;
    to_agent?: AgentType;
    reason?: string;
    attempts?: number;
    [key: string]: any;
}

export interface Message {
    role: MessageRole;
    content: string;
    timestamp: string;
    agent?: AgentType;
    metadata?: MessageMetadata;
    message_id?: string;
}

export interface PendingMessage {
    message: string;
    status: 'sending' | 'queued';
    sent_at: number;
    is_typing: boolean;
    queue_position?: number;
}

export interface OfflineQueuedMessage {
    message: string;
    type: MessageType;
    queued_at: number;
    message_id: string;
}

export interface SocketResponse {
    message: string;
    agent: AgentType;
    timestamp?: string;
    metadata?: MessageMetadata;
    message_id?: string;
}

export interface SocketError {
    message: string;
    message_id?: string;
    code?: string;
}

export interface AgentSwitchData {
    from_agent: AgentType;
    to_agent: AgentType;
    reason: string;
    message_id?: string;
}

export interface MessageQueuedData {
    message_id: string;
    queue_position: number;
}

export interface MessageCancelledData {
    message_id: string;
    success: boolean;
}

export interface AllMessagesCancelledData {
    cancelled_count: number;
    message?: string;
}

export interface ConnectedData {
    session_id: string;
}

export interface CorrelationData {
    correlationNumber: number;
    color: string;
    isPending: boolean;
    isUserMessage: boolean;
    replyToMessageId?: string | number;
    pendingData?: PendingMessage;
}

export interface VoiceInputHook {
    isListening: boolean;
    isSupported: boolean | null; // null = checking, true = supported, false = not supported
    transcript: string;
    error: string | null;
    startListening: () => void;
    stopListening: () => void;
    resetTranscript: () => void;
}

export interface SocketHook {
    socket: any;
    isConnected: boolean;
    isReconnecting: boolean;
    reconnectAttempt: number;
    sessionId: string | null;
    messages: Message[];
    isTyping: boolean;
    isSending: boolean;
    currentAgent: AgentType | null;
    sendMessage: (message: string) => void;
    clearMessages: () => void;
    cancelMessage: (messageId: string) => void;
    cancelAllMessages: () => void;
    error: string | null;
    pendingMessages: Map<string, PendingMessage>;
    pendingMessagesCount: number;
    offlineQueue: OfflineQueuedMessage[];
    offlineQueueCount: number;
}
