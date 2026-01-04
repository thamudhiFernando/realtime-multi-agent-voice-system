/**
 * useMessageCorrelation Hook
 * Extracted from MessageList for better performance and reusability
 *
 * Performance: Uses useMemo to prevent O(n²) computation on every render
 */
import { useMemo } from 'react';
import { MESSAGE_CORRELATION } from '@/config/constants';
import { Message, PendingMessage, CorrelationData } from '@/types';

/**
 * Calculate message correlation mapping
 * Links user messages with their corresponding assistant responses
 */
export function useMessageCorrelation(
    messages: Message[],
    pendingMessages: Map<string, PendingMessage> = new Map()
): Map<string | number, CorrelationData> {
    return useMemo(() => {
        const correlationMap = new Map<string | number, CorrelationData>();
        let userMessageCounter = 0;

        // First pass: Assign correlation numbers to user messages
        messages.forEach((message, index) => {
            if (message.role === 'user') {
                userMessageCounter++;

                correlationMap.set(message.message_id || index, {
                    correlationNumber: userMessageCounter,
                    color: getCorrelationColor(userMessageCounter),
                    isPending: false,
                    isUserMessage: true,
                });
            }
        });

        // Second pass: Link assistant responses to their corresponding user messages
        // Use FIFO matching: first response goes to first unanswered question
        const unansweredQuestions: Array<{ id: string | number; correlationNumber: number }> = [];

        messages.forEach((message, index) => {
            if (message.role === 'user') {
                const messageId = message.message_id || index;
                const correlationData = correlationMap.get(messageId);
                if (correlationData) {
                    unansweredQuestions.push({
                        id: messageId,
                        correlationNumber: correlationData.correlationNumber
                    });
                }
            } else if (message.role === 'assistant' && message.agent !== 'system') {
                // Match this response to the first unanswered question (FIFO)
                if (unansweredQuestions.length > 0) {
                    const matchedQuestion = unansweredQuestions.shift()!; // Remove first question
                    const messageKey = message.message_id || index;

                    correlationMap.set(messageKey, {
                        correlationNumber: matchedQuestion.correlationNumber,
                        color: getCorrelationColor(matchedQuestion.correlationNumber),
                        isPending: false,
                        isUserMessage: false,
                        replyToMessageId: matchedQuestion.id,
                    });
                }
            }
        });

        // Third pass: Add pending messages
        let pendingCounter = userMessageCounter;
        pendingMessages.forEach((pendingData, messageId) => {
            if (!correlationMap.has(messageId)) {
                pendingCounter++;
                correlationMap.set(messageId, {
                    correlationNumber: pendingCounter,
                    color: getCorrelationColor(pendingCounter),
                    isPending: true,
                    isUserMessage: true,
                    pendingData,
                });
            }
        });

        return correlationMap;
    }, [messages, pendingMessages]); // Only recompute when messages or pending change
}

/**
 * Get correlation color by number
 * Cycles through predefined color palette
 */
export function getCorrelationColor(number: number): string {
    const colors = MESSAGE_CORRELATION.COLORS;
    return colors[(number - 1) % colors.length];
}

/**
 * Get correlation info for a specific message
 */
export function getMessageCorrelationInfo(
    messageId: string | number,
    correlationMap: Map<string | number, CorrelationData>
): CorrelationData | null {
    return correlationMap.get(messageId) || null;
}

/**
 * Check if message has correlation
 */
export function hasCorrelation(
    messageId: string | number,
    correlationMap: Map<string | number, CorrelationData>
): boolean {
    return correlationMap.has(messageId);
}

/**
 * Get all messages for a specific correlation number
 * Useful for highlighting related messages
 */
export function getRelatedMessages(
    correlationNumber: number,
    correlationMap: Map<string | number, CorrelationData>
): Array<string | number> {
    const relatedIds: Array<string | number> = [];

    correlationMap.forEach((data, messageId) => {
        if (data.correlationNumber === correlationNumber) {
            relatedIds.push(messageId);
        }
    });

    return relatedIds;
}

export default useMessageCorrelation;
