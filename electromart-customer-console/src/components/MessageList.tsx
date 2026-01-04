'use client';

import { useEffect, useRef, useState } from 'react';
import {
    Box,
    Paper,
    Typography,
    Avatar,
    Chip,
    Card,
    CardContent,
    Grid,
    CircularProgress,
} from '@mui/material';
import {
    ShoppingBag as ShoppingBagIcon,
    Campaign as CampaignIcon,
    Build as BuildIcon,
    LocalShipping as LocalShippingIcon,
    Info as InfoIcon,
    SmartToy as SmartToyIcon,
    CheckCircle as CheckCircleIcon,
    Schedule as ScheduleIcon,
    Cancel as CancelIcon,
} from '@mui/icons-material';
import { Message, AgentType, PendingMessage } from '@/types';
import useMessageCorrelation, {
    getCorrelationColor,
    getMessageCorrelationInfo,
} from '../hooks/useMessageCorrelation';

interface MessageListProps {
    messages: Message[];
    isTyping: boolean;
    currentAgent: AgentType | null;
    pendingMessages?: Map<string, PendingMessage>;
    onCancelMessage?: (messageId: string) => void;
}

export default function MessageList({
                                        messages,
                                        isTyping,
                                        currentAgent,
                                        pendingMessages = new Map(),
                                        onCancelMessage,
                                    }: MessageListProps) {
    const [mounted, setMounted] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Only render dynamic content after client mount
    useEffect(() => {
        setMounted(true);
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        if (mounted) scrollToBottom();
    }, [messages, isTyping, mounted]);

    const correlationMap = useMessageCorrelation(messages, pendingMessages);

    const getCorrelationNumber = (message: Message, index: number): number | null => {
        if (!mounted) return null; // avoid dynamic values on SSR
        const messageId = message.message_id || index;
        const correlationData = getMessageCorrelationInfo(messageId, correlationMap);
        return correlationData?.correlationNumber || null;
    };

    const isMessagePending = (message: Message, index: number): boolean => {
        if (!mounted) return false; // SSR-safe
        if (message.role === 'user') {
            const messageId = message.message_id || index;
            return (
                pendingMessages.has(message.message_id || '') ||
                getMessageCorrelationInfo(messageId, correlationMap)?.isPending ||
                false
            );
        }
        return false;
    };

    const getAgentIcon = (agent?: AgentType) => {
        switch (agent) {
            case 'sales':
                return <ShoppingBagIcon />;
            case 'marketing':
                return <CampaignIcon />;
            case 'support':
                return <BuildIcon />;
            case 'logistics':
                return <LocalShippingIcon />;
            case 'system':
                return <InfoIcon />;
            default:
                return <SmartToyIcon />;
        }
    };

    const getAgentColor = (agent?: AgentType): string => {
        switch (agent) {
            case 'sales':
                return '#1976d2';
            case 'marketing':
                return '#9c27b0';
            case 'support':
                return '#2e7d32';
            case 'logistics':
                return '#ed6c02';
            case 'system':
                return '#757575';
            default:
                return '#1976d2';
        }
    };

    const getAgentName = (agent?: AgentType): string => {
        if (!agent) return 'Assistant';
        return agent.charAt(0).toUpperCase() + agent.slice(1) + ' Agent';
    };

    // SSR fallback if not mounted
    if (!mounted) {
        return (
            <Box
                sx={{
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    p: 3,
                }}
            >
                <Typography variant="body1" color="text.secondary">
                    Loading chat messages...
                </Typography>
            </Box>
        );
    }

    if (messages.length === 0) {
        return (
            <Box
                sx={{
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    p: 3,
                }}
            >
                <Box sx={{ textAlign: 'center', maxWidth: 600 }}>
                    <Typography variant="h3" sx={{ mb: 2 }}>
                        👋
                    </Typography>
                    <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                        Welcome to ElectroMart!
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                        How can I help you today?
                    </Typography>
                </Box>
            </Box>
        );
    }

    return (
        <Box
            sx={{
                height: '100%',
                overflowY: 'auto',
                p: 3,
            }}
        >
            <Box sx={{ maxWidth: 900, mx: 'auto' }}>
                {messages.map((message, index) => {
                    const correlationNumber = getCorrelationNumber(message, index);
                    const isPending = isMessagePending(message, index);
                    const correlationColor = correlationNumber ? getCorrelationColor(correlationNumber) : null;

                    return (
                        <Box
                            key={message.message_id || index}
                            sx={{
                                display: 'flex',
                                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                                mb: 2,
                                position: 'relative',
                            }}
                        >
                            {message.role === 'assistant' && (
                                <Avatar sx={{ bgcolor: getAgentColor(message.agent), mr: 2, mt: 0.5 }}>
                                    {getAgentIcon(message.agent)}
                                </Avatar>
                            )}

                            <Box sx={{ maxWidth: '70%' }}>
                                {message.role === 'assistant' && (
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                        <Chip
                                            label={getAgentName(message.agent)}
                                            size="small"
                                            sx={{ bgcolor: getAgentColor(message.agent), color: 'white', fontWeight: 600 }}
                                        />
                                        {correlationNumber && (
                                            <Chip
                                                label={`Reply to #${correlationNumber}`}
                                                size="small"
                                                icon={<CheckCircleIcon sx={{ fontSize: '16px !important' }} />}
                                                sx={{ bgcolor: correlationColor!, color: 'white', fontWeight: 600, fontSize: '0.7rem' }}
                                            />
                                        )}
                                    </Box>
                                )}

                                <Paper
                                    elevation={isPending ? 2 : 1}
                                    sx={{
                                        p: 2,
                                        bgcolor: message.role === 'user' ? '#1976d2' : 'white',
                                        color: message.role === 'user' ? 'white' : 'text.primary',
                                        border: correlationNumber ? `2px solid ${correlationColor}` : 'none',
                                        opacity: isPending ? 0.8 : 1,
                                        position: 'relative',
                                    }}
                                >
                                    {correlationNumber && (
                                        <Chip
                                            label={`#${correlationNumber}`}
                                            size="small"
                                            sx={{
                                                position: 'absolute',
                                                top: -10,
                                                left: -10,
                                                bgcolor: correlationColor!,
                                                color: 'white',
                                                fontWeight: 700,
                                                fontSize: '0.75rem',
                                                minWidth: 32,
                                                height: 24,
                                                boxShadow: 2,
                                            }}
                                        />
                                    )}

                                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                                        {message.content}
                                    </Typography>

                                    {isPending && message.role === 'user' && (
                                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1, mt: 1 }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <CircularProgress size={12} sx={{ color: 'rgba(255,255,255,0.7)' }} />
                                                <Typography variant="caption" sx={{ fontStyle: 'italic', opacity: 0.9 }}>
                                                    Processing...
                                                </Typography>
                                            </Box>
                                            {onCancelMessage && message.message_id && (
                                                <Chip
                                                    label="Cancel"
                                                    size="small"
                                                    icon={<CancelIcon sx={{ fontSize: '14px !important' }} />}
                                                    onClick={() => onCancelMessage(message.message_id!)}
                                                    sx={{
                                                        height: 20,
                                                        bgcolor: 'rgba(255, 255, 255, 0.2)',
                                                        color: 'white',
                                                        fontSize: '0.65rem',
                                                        cursor: 'pointer',
                                                        '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.3)' },
                                                    }}
                                                />
                                            )}
                                        </Box>
                                    )}
                                </Paper>
                            </Box>

                            {message.role === 'user' && (
                                <Box sx={{ position: 'relative', ml: 2, mt: 0.5 }}>
                                    <Avatar sx={{ bgcolor: '#1976d2' }}>U</Avatar>
                                    {isPending && (
                                        <ScheduleIcon
                                            sx={{
                                                position: 'absolute',
                                                bottom: -2,
                                                right: -2,
                                                fontSize: 16,
                                                color: '#ed6c02',
                                                bgcolor: 'white',
                                                borderRadius: '50%',
                                                padding: '2px',
                                            }}
                                        />
                                    )}
                                </Box>
                            )}
                        </Box>
                    );
                })}

                {isTyping && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Avatar sx={{ bgcolor: getAgentColor(currentAgent || undefined), mr: 2 }}>
                            {getAgentIcon(currentAgent || undefined)}
                        </Avatar>
                        <Paper elevation={1} sx={{ p: 2 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {[0, 1, 2].map((i) => (
                                    <Box
                                        key={i}
                                        sx={{
                                            width: 8,
                                            height: 8,
                                            borderRadius: '50%',
                                            bgcolor: '#757575',
                                            animation: 'bounce 1.4s infinite ease-in-out',
                                            animationDelay: `${i * 0.2}s`,
                                            '@keyframes bounce': {
                                                '0%, 80%, 100%': { transform: 'scale(0)' },
                                                '40%': { transform: 'scale(1)' },
                                            },
                                        }}
                                    />
                                ))}
                                <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                    Agent is typing...
                                </Typography>
                            </Box>
                        </Paper>
                    </Box>
                )}

                <div ref={messagesEndRef} />
            </Box>
        </Box>
    );
}
