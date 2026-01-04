"""
Marketing Agent V2 - Multi-Prompt with Sequence Support
Implements SP2 → P1, P2 pattern from diagram
"""
import json
from typing import Dict, Any
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from app.utils.message_utils import get_user_message, get_message_content, is_user_message

from app.agents.multi_prompt_agent import MultiPromptAgent, PromptChain
from app.graph.state import AgentConversationState
from app.utils.logger import logger


class MarketingAgentV2(MultiPromptAgent):
    """
    Marketing Agent with multi-step processing:
    - Seq1 (P1): Analyze customer segment, purchase history, preferences
    - Seq2 (P2): Generate personalized marketing offers and promotions
    """

    # -----------------------------
    # Paths
    # -----------------------------
    BASE_DIR = Path(__file__).resolve().parent.parent.parent  # points to 'app' parent
    KB_PATH = BASE_DIR / "data/knowledge" / "marketing_kb.json"

    def __init__(self):
        # Load knowledge base safely
        if not self.KB_PATH.exists():
            logger.warning(f"Marketing knowledge base not found at {self.KB_PATH}, using empty KB")
            self.knowledge_base = {"promotions": []}
        else:
            with open(self.KB_PATH, "r", encoding="utf-8") as f:
                self.knowledge_base = json.load(f)

        super().__init__(agent_name="marketing")

    # -----------------------------
    # Build Prompt Chain
    # -----------------------------
    def _build_prompt_chain(self) -> PromptChain:
        # P1: Customer Segment Analysis
        p1_template = ChatPromptTemplate.from_messages([
            ("system", """You are a customer segment analyst for ElectroMart marketing team.

Your task (P1 - Segment Analysis):
1. Analyze the customer's query and conversation to determine their segment
2. Identify their interests, past behavior, and purchase intent
3. Determine which promotions would be most relevant
4. Assess customer lifetime value potential

Respond with a JSON object containing:
{{
    "customer_segment": "budget_hunter|premium_buyer|tech_enthusiast|casual_shopper",
    "interests": ["interest1", "interest2"],
    "purchase_intent": "high|medium|low",
    "preferred_categories": ["category1", "category2"],
    "price_sensitivity": "high|medium|low",
    "promotion_triggers": ["trigger1", "trigger2"],
    "recommended_offers": ["offer_type1", "offer_type2"]
}}

Conversation history:
{history}"""),
            ("human", "{query}")
        ])

        # P2: Personalized Offer Generation
        p2_template = ChatPromptTemplate.from_messages([
            ("system", """You are a marketing specialist for ElectroMart electronics store.

Your task (P2 - Offer Generation):
Create personalized marketing offers and promotions based on customer analysis.

Customer Analysis (from P1):
{customer_analysis}

Available Promotions:
{promotions}

Guidelines:
- Present offers that match the customer's segment and interests
- Highlight value propositions that resonate with their priorities
- Use urgency and scarcity when appropriate
- Include specific discount codes or promotion details
- Mention loyalty program benefits
- Make it personal and relevant
- Keep tone enthusiastic but not pushy

Format:
1. Acknowledge their interest
2. Present relevant promotions with specifics
3. Explain benefits clearly
4. Call to action

Conversation history:
{history}"""),
            ("human", "Generate personalized marketing offers")
        ])

        prompts = [
            {"name": "P1", "template": p1_template, "description": "Analyze customer segment and preferences", "sequence": 1},
            {"name": "P2", "template": p2_template, "description": "Generate personalized marketing offers", "sequence": 2}
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
            customer_analysis = json.loads(llm_response.content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse P1 JSON response, using fallback")
            customer_analysis = {
                "customer_segment": "casual_shopper",
                "interests": ["electronics"],
                "purchase_intent": "medium",
                "preferred_categories": ["general"],
                "price_sensitivity": "medium",
                "promotion_triggers": ["discount", "value"],
                "recommended_offers": ["percentage_discount", "bundle_deal"]
            }

        relevant_promotions = self._find_relevant_promotions(customer_analysis)

        return {"customer_analysis": customer_analysis, "relevant_promotions": relevant_promotions, "user_query": get_message_content(user_message)}

    async def _execute_sequence_2(self, state: AgentConversationState, seq1_results: Dict[str, Any]) -> str:
        p2_config = self.prompt_chain.get_prompt(2)
        history = self._build_history(state["conversation_messages"])

        customer_analysis = json.dumps(seq1_results.get("customer_analysis", {}), indent=2)
        promotions = json.dumps(seq1_results.get("relevant_promotions", []), indent=2)

        formatted_prompt = p2_config["template"].format_messages(
            customer_analysis=customer_analysis,
            promotions=promotions,
            history=history
        )

        llm_response = await self.llm.ainvoke(formatted_prompt)
        return llm_response.content

    # -----------------------------
    # Find Relevant Promotions
    # -----------------------------
    def _find_relevant_promotions(self, customer_analysis: Dict[str, Any]) -> list:
        try:
            promotions = self.knowledge_base.get("promotions", [])
            recommended_offer_types = customer_analysis.get("recommended_offers", [])
            customer_segment = customer_analysis.get("customer_segment", "")
            interests = customer_analysis.get("interests", [])

            relevant = []

            for promo in promotions:
                score = 0

                promo_type = promo.get("type", "").lower()
                if any(offer_type in promo_type for offer_type in recommended_offer_types):
                    score += 3

                target_segments = [s.lower() for s in promo.get("target_segments", [])]
                if customer_segment.lower() in target_segments or "all" in target_segments:
                    score += 2

                promo_categories = [c.lower() for c in promo.get("categories", [])]
                for interest in interests:
                    if interest.lower() in promo_categories:
                        score += 1

                if score > 0:
                    relevant.append({**promo, "relevance_score": score})

            relevant.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            for promo in relevant:
                promo.pop("relevance_score", None)

            return relevant[:3]

        except Exception as e:
            logger.error(f"Error finding promotions: {str(e)}")
            return []
