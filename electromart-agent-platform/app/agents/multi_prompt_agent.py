"""
Base Multi-Prompt Agent with Sequence Support
Implements prompt chaining (P1→P2) and sequence tracking (Seq1, Seq2)
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Any, Dict, Optional

from langchain_openai import ChatOpenAI

from app.graph.state import AgentConversationState
from app.utils.config import settings
from app.utils.logger import log_agent_activity, logger


class PromptChain:
    """
    Represents a chain of prompts to be executed sequentially
    Each prompt corresponds to a sequence step (Seq1, Seq2, etc.)
    """

    def __init__(self, prompts: List[Dict[str, Any]]):
        """
        Initialize prompt chain

        Args:
            prompts: List of prompt configurations, each containing:
                - name: Prompt identifier (e.g., "P1", "P2")
                - template: ChatPromptTemplate
                - description: What this prompt does
                - sequence: Sequence number (1, 2, etc.)
        """
        self.prompts = sorted(prompts, key=lambda x: x['sequence'])
        self.total_steps = len(prompts)

    def get_prompt(self, sequence_step: int) -> Optional[Dict[str, Any]]:
        """Get prompt configuration for a specific sequence step"""
        for prompt in self.prompts:
            if prompt['sequence'] == sequence_step:
                return prompt
        return None

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts in order"""
        return self.prompts


class MultiPromptAgent(ABC):
    """
    Base class for agents that use multiple prompts in sequence

    Each agent implements:
    - Seq1 (P1): Information extraction and analysis
    - Seq2 (P2): Response generation using extracted info
    """

    def __init__(self, agent_name: str):
        """
        Initialize multi-prompt agent

        Args:
            agent_name: Name of the agent (e.g., "sales", "marketing")
        """
        self.agent_name = agent_name
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,
            api_key=settings.openai_api_key
        )

        # Initialize prompt chain (to be defined by subclasses)
        self.prompt_chain = self._build_prompt_chain()

    @abstractmethod
    def _build_prompt_chain(self) -> PromptChain:
        """
        Build the prompt chain for this agent
        Must be implemented by subclasses

        Returns:
            PromptChain with all prompts for this agent
        """
        pass

    @abstractmethod
    async def _execute_sequence_1(self, state: AgentConversationState) -> Dict[str, Any]:
        """
        Execute Sequence 1 (P1): Information extraction and analysis

        Args:
            state: Current conversation state

        Returns:
            Dict containing extracted information and metadata
        """
        pass

    @abstractmethod
    async def _execute_sequence_2(self, state: AgentConversationState, seq1_results: Dict[str, Any]) -> str:
        """
        Execute Sequence 2 (P2): Response generation

        Args:
            state: Current conversation state
            seq1_results: Results from sequence 1

        Returns:
            Generated response string
        """
        pass

    async def process(self, state: AgentConversationState) -> AgentConversationState:
        """
        Main processing method that executes the prompt chain

        Args:
            state: Current agent conversation state

        Returns:
            Updated agent state after processing all sequences
        """
        log_agent_activity(
            agent_name=self.agent_name,
            activity="starting_multi_sequence_processing",
            session_id=state["unique_session_id"],
            metadata={
                "total_sequences": self.prompt_chain.total_steps,
                "current_sequence": state.get("current_sequence_step", 1)
            }
        )

        try:
            # Get the latest user message safely
            user_message = next(
                (
                    msg for msg in reversed(state["conversation_messages"])
                    if getattr(msg, "role", None) == "user"  # works for HumanMessage
                       or (isinstance(msg, dict) and msg.get("role") == "user")  # works for dicts
                ),
                None
            )

            if not user_message:
                state["generated_response"] = f"How can I help you?"
                state["should_end_conversation_turn"] = True
                return state

            # Initialize sequence tracking if needed
            if "current_sequence_step" not in state or state["current_sequence_step"] == 0:
                state["current_sequence_step"] = 1
                state["total_sequence_steps"] = self.prompt_chain.total_steps
                state["prompt_chain_results"] = {}
                state["sequence_metadata"] = {}

            # Execute Sequence 1 (P1): Information Extraction
            if state["current_sequence_step"] == 1:
                log_agent_activity(
                    agent_name=self.agent_name,
                    activity="executing_sequence_1",
                    session_id=state["unique_session_id"]
                )

                seq1_start = datetime.now(timezone.utc)
                seq1_results = await self._execute_sequence_1(state)
                seq1_duration = (datetime.now(timezone.utc) - seq1_start).total_seconds()

                # Store Seq1 results
                state["prompt_chain_results"]["seq1_p1"] = seq1_results
                state["sequence_metadata"]["seq1"] = {
                    "duration_seconds": seq1_duration,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "prompt_name": "P1",
                    "description": "Information extraction and analysis"
                }

                logger.info(
                    f"{self.agent_name}: Seq1 completed in {seq1_duration:.2f}s",
                    extra={
                        "session_id": state["unique_session_id"],
                        "agent": self.agent_name,
                        "sequence": 1
                    }
                )

                # Move to sequence 2
                state["current_sequence_step"] = 2

            # Execute Sequence 2 (P2): Response Generation
            if state["current_sequence_step"] == 2:
                log_agent_activity(
                    agent_name=self.agent_name,
                    activity="executing_sequence_2",
                    session_id=state["unique_session_id"]
                )

                seq2_start = datetime.now(timezone.utc)
                seq1_results = state["prompt_chain_results"].get("seq1_p1", {})
                response = await self._execute_sequence_2(state, seq1_results)
                seq2_duration = (datetime.now(timezone.utc) - seq2_start).total_seconds()

                # Store Seq2 results
                state["prompt_chain_results"]["seq2_p2"] = {
                    "response": response,
                    "duration_seconds": seq2_duration
                }
                state["sequence_metadata"]["seq2"] = {
                    "duration_seconds": seq2_duration,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "prompt_name": "P2",
                    "description": "Response generation"
                }

                logger.info(
                    f"{self.agent_name}: Seq2 completed in {seq2_duration:.2f}s",
                    extra={
                        "session_id": state["unique_session_id"],
                        "agent": self.agent_name,
                        "sequence": 2
                    }
                )

                # Set final response
                state["generated_response"] = response
                state["current_active_agent"] = self.agent_name

                # Check if handoff is needed
                handoff_check = await self._check_handoff_needed(user_message["content"], response)
                if handoff_check["needs_handoff"]:
                    state["requires_agent_handoff"] = True
                    state["target_handoff_agent"] = handoff_check["target_agent"]
                    state["should_end_conversation_turn"] = False
                else:
                    state["should_end_conversation_turn"] = True

                # Add response to messages
                from app.graph import append_message_to_conversation
                state = append_message_to_conversation(
                    state,
                    message_role="assistant",
                    message_content=response,
                    originating_agent=self.agent_name,
                    extra_metadata={
                        "sequence_processing": {
                            "seq1_duration": state["sequence_metadata"]["seq1"]["duration_seconds"],
                            "seq2_duration": seq2_duration,
                            "total_duration": state["sequence_metadata"]["seq1"]["duration_seconds"] + seq2_duration
                        }
                    }
                )

                # Reset sequence for next turn
                state["current_sequence_step"] = 1

                log_agent_activity(
                    agent_name=self.agent_name,
                    activity="multi_sequence_completed",
                    session_id=state["unique_session_id"],
                    metadata={
                        "total_duration": state["sequence_metadata"]["seq1"]["duration_seconds"] + seq2_duration,
                        "response_length": len(response)
                    }
                )

            return state

        except Exception as e:
            logger.error(
                f"{self.agent_name} multi-sequence error: {str(e)}",
                exc_info=True,
                extra={"session_id": state["unique_session_id"]}
            )
            state["generated_response"] = f"I apologize, but I encountered an error. Please try again."
            state["should_end_conversation_turn"] = True
            state["current_sequence_step"] = 1
            return state

    async def _check_handoff_needed(self, query: str, response: str) -> Dict[str, Any]:
        """
        Determine if the query should be handed off to a different agent
        Can be overridden by subclasses for specific handoff logic

        Args:
            query: User's query text
            response: Generated response

        Returns:
            Dict with needs_handoff (bool) and target_agent (str or None)
        """
        return {"needs_handoff": False, "target_agent": None}

    def _build_history(self, messages: list) -> str:
        """
        Build a formatted conversation history string

        Args:
            messages: List of conversation messages

        Returns:
            Formatted conversation history
        """
        if not messages or len(messages) <= 1:
            return "No previous conversation"

        history_parts = []
        for msg in messages[-6:-1]:  # Last 5 messages excluding current
            role = "Customer" if msg["role"] == "user" else "Agent"
            history_parts.append(f"{role}: {msg['content']}")

        return "\n".join(history_parts) if history_parts else "No previous conversation"
