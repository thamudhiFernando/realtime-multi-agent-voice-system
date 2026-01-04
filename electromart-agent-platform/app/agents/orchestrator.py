"""
Orchestrator Agent - Main routing agent for intent classification
Refactored with meaningful naming conventions
"""
import json
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.graph.state import AgentConversationState
from app.utils.config import settings
from app.utils.logger import log_agent_activity, logger


class OrchestratorAgent:
    """
    Orchestrator Agent responsible for:
    - Intent classification
    - Agent routing
    - Context management
    - Handling ambiguous queries
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,
            api_key=settings.openai_api_key
        )

        self.intent_classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent routing agent for ElectroMart, an electronic consumer store.
Your role is to analyze customer messages and determine their intent.

Available intents:
- SALES: Product inquiries, pricing, availability, recommendations, comparisons
- MARKETING: Promotions, discounts, loyalty programs, campaigns, newsletter
- SUPPORT: Troubleshooting, warranties, repairs, technical issues, setup help
- ORDERS: Order tracking, shipping, returns, refunds, delivery scheduling
- GENERAL: Greetings, general questions that don't fit other categories

Analyze the user's message and conversation history to classify the intent.

Respond with a JSON object containing:
{{
    "intent": "sales|marketing|support|orders|general",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "entities": {{"key": "value"}} // Extract relevant entities like product names, order numbers
}}

Be accurate - 85%+ confidence required for routing. If unsure (confidence < 0.85), classify as GENERAL."""),
            ("human", "Conversation history:\n{history}\n\nCurrent message: {message}\n\nClassify the intent:")
        ])

    async def process(self, state: AgentConversationState) -> AgentConversationState:
        """
        Process the user message and classify intent

        Args:
            state: Current agent conversation state

        Returns:
            Updated agent state with intent classification
        """
        log_agent_activity(
            agent_name="orchestrator",
            activity="classifying_intent",
            session_id=state.get("unique_session_id", "unknown_session")
        )

        try:
            # Get the latest user message (support both dicts and HumanMessage objects)
            user_message = next(
                (
                    msg for msg in reversed(state.get("conversation_messages", []))
                    if (getattr(msg, "type", None) == "human" or getattr(msg, "role", None) == "user")
                ),
                None
            )

            if not user_message:
                state["should_end_conversation_turn"] = True
                state["generated_response"] = "I didn't receive a message. How can I help you?"
                return state

            # Get message content safely
            message_content = user_message.get("content", "") if isinstance(user_message, dict) else getattr(user_message, "content", "")


            # Build conversation history (exclude current message)
            history = self._build_history(state.get("conversation_messages", [])[:-1])

            # Call LLM for intent classification
            prompt = self.intent_classification_prompt.format_messages(
                history=history,
                message=message_content
            )

            response = await self.llm.ainvoke(prompt)
            classification = self._parse_classification(response.content)

            # Update state with classification
            state["classified_intent"] = classification.get("intent", "general")
            state["intent_confidence_score"] = classification.get("confidence", 0.0)
            state["conversation_context"].update(classification.get("entities", {}))

            log_agent_activity(
                agent_name="orchestrator",
                activity="intent_classified",
                session_id=state.get("unique_session_id", "unknown_session"),
                metadata={
                    "intent": classification.get("intent"),
                    "confidence": classification.get("confidence"),
                    "reasoning": classification.get("reasoning")
                }
            )

            # Handle general or low-confidence queries directly
            if classification.get("intent") == "general" or classification.get("confidence", 0.0) < 0.70:
                state["generated_response"] = await self._handle_general_query(message_content, state)
                state["should_end_conversation_turn"] = True
            else:
                # Route to appropriate agent
                state["current_active_agent"] = "orchestrator"  # This can be updated by routing logic

            return state

        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}", exc_info=True)
            state["generated_response"] = (
                "I apologize, but I'm having trouble understanding your request. "
                "Could you please rephrase it?"
            )
            state["should_end_conversation_turn"] = True
            return state

    def _build_history(self, messages: list) -> str:
        """
        Build a formatted conversation history string from message list

        Args:
            messages (list): List of conversation messages to format

        Returns:
            str: Formatted conversation history with role labels, or "No previous conversation" if empty

        Note:
            Only includes the last 5 messages to keep context manageable
        """
        if not messages:
            return "No previous conversation"

        history_parts = []
        for msg in messages[-5:]:  # Last 5 messages for context
            # Use getattr to support HumanMessage or other objects
            role_attr = getattr(msg, "role", None)
            content_attr = getattr(msg, "content", "")

            role = "Customer" if role_attr == "user" else "Agent"
            history_parts.append(f"{role}: {content_attr}")

        return "\n".join(history_parts)

    def _parse_classification(self, response: str) -> Dict[str, Any]:
        """
        Parse and validate LLM classification response into structured dictionary

        Args:
            response (str): Raw LLM response string, potentially containing JSON with markdown code blocks

        Returns:
            Dict[str, Any]: Parsed classification containing:
                - intent (str): Classified intent (sales, marketing, support, orders, or general)
                - confidence (float): Confidence score between 0.0 and 1.0
                - reasoning (str): Explanation for the classification
                - entities (dict): Extracted entities from the user message

        Note:
            Falls back to default values if parsing fails or intent is invalid
        """
        try:
            # Try to parse as JSON
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            classification = json.loads(response_clean.strip())

            # Validate and normalize
            intent = classification.get("intent", "general").lower()
            if intent not in ["sales", "marketing", "support", "orders", "general"]:
                intent = "general"

            return {
                "intent": intent,
                "confidence": float(classification.get("confidence", 0.5)),
                "reasoning": classification.get("reasoning", ""),
                "entities": classification.get("entities", {})
            }

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse classification response: {response}")
            return {
                "intent": "general",
                "confidence": 0.5,
                "reasoning": "Failed to parse response",
                "entities": {}
            }

    async def _handle_general_query(self, message: str, state: AgentConversationState) -> str:
        """
        Handle general queries that don't require routing to specialized agents

        Args:
            message (str): User's message text
            state (AgentConversationState): Current conversation state

        Returns:
            str: Generated response for general inquiries, greetings, and basic store information

        Note:
            Handles queries with low confidence or classified as "general" intent
        """
        general_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful customer service agent for ElectroMart.
Handle general inquiries, greetings, and provide basic information about the store.

Store information:
- We sell electronics: phones, laptops, TVs, audio equipment, tablets, smart home devices
- We have sales, marketing, technical support, and order tracking services
- Operating hours: Mon-Sat 9AM-7PM, Sun 10AM-6PM
- Contact: support@electromart.com or (555) 123-4567

Be friendly, concise, and helpful."""),
            ("human", "{message}")
        ])

        prompt = general_prompt.format_messages(message=message)
        response = await self.llm.ainvoke(prompt)

        return response.content
