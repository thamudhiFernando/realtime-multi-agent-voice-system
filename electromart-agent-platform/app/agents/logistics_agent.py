"""
Logistics Agent V2 - Multi-Prompt with Sequence Support
Implements SP4 → P1, P2 pattern from diagram
"""
import json
from typing import Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session

from app.utils.message_utils import get_user_message, get_message_content, is_user_message
from langchain_core.prompts import ChatPromptTemplate

from app.agents.multi_prompt_agent import MultiPromptAgent, PromptChain
from app.database.connection import SessionLocal
from app.graph.state import AgentConversationState, log_database_operation
from app.utils.logger import logger


class LogisticsAgentV2(MultiPromptAgent):
    """
    Logistics Agent with multi-step processing:
    - Seq1 (P1): Extract order details, query database for tracking info
    - Seq2 (P2): Generate order status and delivery updates
    """

    # -----------------------------
    # Paths
    # -----------------------------
    BASE_DIR = Path(__file__).resolve().parent.parent.parent  # points to 'app' parent
    KB_PATH = BASE_DIR / "data/knowledge" / "logistics_kb.json"

    def __init__(self):
        # Load knowledge base safely
        if not self.KB_PATH.exists():
            logger.warning(f"Logistics knowledge base not found at {self.KB_PATH}, using empty KB")
            self.knowledge_base = {"policies": {}, "sample_orders": []}
        else:
            with open(self.KB_PATH, "r", encoding="utf-8") as f:
                self.knowledge_base = json.load(f)

        super().__init__(agent_name="logistics")

    # -----------------------------
    # Build Prompt Chain
    # -----------------------------
    def _build_prompt_chain(self) -> PromptChain:
        # P1: Order Information Extraction
        p1_template = ChatPromptTemplate.from_messages([
            ("system", """You are an order information analyst for ElectroMart logistics team.

Your task (P1 - Order Information Extraction):
1. Extract order numbers, tracking numbers, or order details from query
2. Identify what information the customer is seeking
3. Determine the type of logistics inquiry
4. Extract any specific concerns or issues

Respond with a JSON object containing:
{{
    "inquiry_type": "order_status|tracking|delivery_time|return|refund|modification",
    "order_number": "order number if mentioned or null",
    "tracking_number": "tracking number if mentioned or null",
    "customer_concern": "main concern or question",
    "urgency": "high|medium|low",
    "requires_order_lookup": true|false,
    "action_needed": "track|update|cancel|return|modify|info"
}}

Conversation history:
{history}"""),
            ("human", "{query}")
        ])

        # P2: Order Status Response Generation
        p2_template = ChatPromptTemplate.from_messages([
            ("system", """You are a logistics specialist for ElectroMart electronics store.

Your task (P2 - Status Update Generation):
Provide clear, helpful order and delivery information based on the extracted details.

Order Inquiry Details (from P1):
{order_inquiry}

Order Information from Database:
{order_data}

Logistics Policies:
{policies}

Guidelines:
- Be clear and specific about order status
- Provide tracking links when available
- Give realistic delivery timeframes
- Explain any delays with empathy
- Offer proactive solutions for issues
- Include return/refund policy information when relevant
- Be reassuring and professional
- Provide next steps or actions customer can take

Format:
1. Acknowledge their inquiry
2. Current order status with specifics
3. Tracking/delivery information
4. Any actions needed or available options
5. Contact information for urgent issues

Conversation history:
{history}"""),
            ("human", "Provide order status and delivery information")
        ])

        prompts = [
            {"name": "P1", "template": p1_template, "description": "Extract order details and identify inquiry type", "sequence": 1},
            {"name": "P2", "template": p2_template, "description": "Generate order status and delivery updates", "sequence": 2}
        ]

        return PromptChain(prompts)

    # -----------------------------
    # Execute Sequences
    # -----------------------------
    async def _execute_sequence_1(self, state: AgentConversationState) -> Dict[str, Any]:
        user_message = get_user_message(state.get("conversation_messages", []))
        if not user_message:
            return {"error": "No user message found"}

        p1_config = self.prompt_chain.get_prompt(1)
        history = self._build_history(state["conversation_messages"])
        formatted_prompt = p1_config["template"].format_messages(history=history, query=get_message_content(user_message))

        llm_response = await self.llm.ainvoke(formatted_prompt)

        try:
            order_inquiry = json.loads(llm_response.content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse P1 JSON response, using fallback")
            order_inquiry = {
                "inquiry_type": "order_status",
                "order_number": None,
                "tracking_number": None,
                "customer_concern": get_message_content(user_message),
                "urgency": "medium",
                "requires_order_lookup": True,
                "action_needed": "info"
            }

        order_data = None
        if order_inquiry.get("requires_order_lookup"):
            order_data = await self._lookup_order(
                order_inquiry.get("order_number"),
                order_inquiry.get("tracking_number"),
                state.get("customer_identifier")
            )

            if order_data:
                state = log_database_operation(
                    state,
                    operation_type="READ",
                    database_table_name="orders",
                    operation_details={
                        "query": "order_lookup",
                        "order_number": order_inquiry.get("order_number"),
                        "found": order_data is not None
                    }
                )

        return {"order_inquiry": order_inquiry, "order_data": order_data, "user_query": get_message_content(user_message)}

    async def _execute_sequence_2(self, state: AgentConversationState, seq1_results: Dict[str, Any]) -> str:
        p2_config = self.prompt_chain.get_prompt(2)
        history = self._build_history(state["conversation_messages"])

        order_inquiry = json.dumps(seq1_results.get("order_inquiry", {}), indent=2)
        order_data = seq1_results.get("order_data")

        order_data_str = json.dumps(order_data, indent=2) if order_data else "No order found. Customer may need to provide order number."
        policies = json.dumps(self.knowledge_base.get("policies", {}), indent=2)

        formatted_prompt = p2_config["template"].format_messages(
            order_inquiry=order_inquiry,
            order_data=order_data_str,
            policies=policies,
            history=history
        )

        llm_response = await self.llm.ainvoke(formatted_prompt)
        return llm_response.content

    # -----------------------------
    # Lookup Order
    # -----------------------------
    async def _lookup_order(self, order_number: str, tracking_number: str, customer_id: int) -> Dict[str, Any]:
        try:
            db: Session = SessionLocal()
            order = None

            orders = self.knowledge_base.get("sample_orders", [])

            if order_number:
                order = next((o for o in orders if o.get("order_number") == order_number), None)
            elif tracking_number:
                order = next((o for o in orders if o.get("tracking_number") == tracking_number), None)
            elif customer_id:
                customer_orders = [o for o in orders if o.get("customer_id") == customer_id]
                order = customer_orders[0] if customer_orders else None

            db.close()
            return order
        except Exception as e:
            logger.error(f"Error looking up order: {str(e)}")
            return None
