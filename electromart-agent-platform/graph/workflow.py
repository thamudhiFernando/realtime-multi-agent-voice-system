"""
LangGraph Workflow Definition for ElectroMart Multi-Agent System
Refactored with meaningful naming conventions
Now using Multi-Prompt Agents with Sequence Support (V2)
"""
from langgraph.graph import StateGraph, END
from typing import Dict, Any
from .state import AgentConversationState
from ..agents.orchestrator import OrchestratorAgent
from ..agents.sales_agent import SalesAgentV2
from ..agents.marketing_agent import MarketingAgentV2
from ..agents.support_agent import SupportAgentV2
from ..agents.logistics_agent import LogisticsAgentV2
from ..utils.logger import logger


def create_agent_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for multi-agent routing
    Now using V2 agents with multi-step sequences (Seq1, Seq2) and prompt chaining (P1, P2)

    Returns:
        Compiled StateGraph
    """
    # Initialize agents (V2 with multi-prompt support)
    orchestrator = OrchestratorAgent()
    sales_agent = SalesAgentV2()
    marketing_agent = MarketingAgentV2()
    support_agent = SupportAgentV2()
    logistics_agent = LogisticsAgentV2()

    logger.info("Initialized V2 agents with multi-step sequence support")

    # Create graph
    workflow = StateGraph(AgentConversationState)

    # Add nodes (agents)
    workflow.add_node("orchestrator", orchestrator.process)
    workflow.add_node("sales", sales_agent.process)
    workflow.add_node("marketing", marketing_agent.process)
    workflow.add_node("support", support_agent.process)
    workflow.add_node("logistics", logistics_agent.process)

    # Set entry point
    workflow.set_entry_point("orchestrator")

    # Define routing logic
    def route_after_orchestrator(state: AgentConversationState) -> str:
        """Route from orchestrator to appropriate sub-agent"""
        if state.get("should_end_conversation_turn"):
            return END

        classified_intent = state.get("classified_intent")

        if classified_intent == "sales":
            return "sales"
        elif classified_intent == "marketing":
            return "marketing"
        elif classified_intent == "support":
            return "support"
        elif classified_intent == "orders":
            return "logistics"
        else:
            # If no clear intent, end and let orchestrator respond
            return END

    def route_after_agent(state: AgentConversationState) -> str:
        """Route after sub-agent processing"""
        if state.get("should_end_conversation_turn"):
            return END

        # Check if handoff is needed
        if state.get("requires_agent_handoff"):
            target_agent = state.get("target_handoff_agent")
            if target_agent in ["sales", "marketing", "support", "logistics"]:
                logger.info(f"Handoff to {target_agent} agent")
                return target_agent

        return END

    # Add conditional edges from orchestrator
    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "sales": "sales",
            "marketing": "marketing",
            "support": "support",
            "logistics": "logistics",
            END: END
        }
    )

    # Add conditional edges from each sub-agent
    for agent_name in ["sales", "marketing", "support", "logistics"]:
        workflow.add_conditional_edges(
            agent_name,
            route_after_agent,
            {
                "sales": "sales",
                "marketing": "marketing",
                "support": "support",
                "logistics": "logistics",
                END: END
            }
        )

    # Compile the graph
    return workflow.compile()


# Global workflow instance
agent_workflow = None


def get_workflow() -> StateGraph:
    """
    Get or create the workflow instance

    Returns:
        Compiled workflow
    """
    global agent_workflow

    if agent_workflow is None:
        agent_workflow = create_agent_workflow()
        logger.info("Agent workflow compiled successfully")

    return agent_workflow


async def process_message(
    session_id: str,
    message: str,
    customer_id: int = None,
    existing_state: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process a user message through the agent workflow

    Args:
        session_id: Session identifier
        message: User message
        customer_id: Optional customer ID
        existing_state: Existing conversation state

    Returns:
        Updated state after processing
    """
    workflow = get_workflow()

    # Create or update state
    if existing_state:
        state = existing_state
        # Add user message
        from .state import append_message_to_conversation
        state = append_message_to_conversation(
            state,
            message_role="user",
            message_content=message
        )
    else:
        from .state import create_initial_conversation_state, append_message_to_conversation
        state = create_initial_conversation_state(session_id, customer_id)
        state = append_message_to_conversation(
            state,
            message_role="user",
            message_content=message
        )

    # Reset turn-specific flags
    state["should_end_conversation_turn"] = False
    state["generated_response"] = None

    try:
        # Run the workflow
        result = await workflow.ainvoke(state)

        logger.info(
            f"Message processed successfully",
            extra={
                "session_id": session_id,
                "intent": result.get("classified_intent"),
                "final_agent": result.get("current_active_agent")
            }
        )

        return result

    except Exception as e:
        logger.error(
            f"Error processing message: {str(e)}",
            extra={"session_id": session_id},
            exc_info=True
        )

        # Return error state
        state["generated_response"] = "I apologize, but I encountered an error processing your request. Please try again."
        state["should_end_conversation_turn"] = True
        return state
