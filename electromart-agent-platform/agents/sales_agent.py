"""
Sales Agent V2 - Multi-Prompt with Sequence Support
Implements SP1 → P1, P2 pattern from diagram
"""
import json
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session
from .multi_prompt_agent import MultiPromptAgent, PromptChain
from ..graph.state import AgentConversationState, log_database_operation
from ..database.models import Product
from ..database.connection import SessionLocal
from ..utils.logger import logger


class SalesAgentV2(MultiPromptAgent):
    """
    Sales Agent with multi-step processing:
    - Seq1 (P1): Extract product requirements, search products, analyze needs
    - Seq2 (P2): Generate personalized product recommendations
    """

    def __init__(self):
        # Load knowledge base
        with open("backend/knowledge/sales_kb.json", "r") as f:
            self.knowledge_base = json.load(f)

        super().__init__(agent_name="sales")

    def _build_prompt_chain(self) -> PromptChain:
        """
        Build the two-step prompt chain for sales agent:
        P1: Information extraction and product search
        P2: Response generation with recommendations
        """

        # P1: Information Extraction Prompt
        p1_template = ChatPromptTemplate.from_messages([
            ("system", """You are a product requirement analyst for ElectroMart electronics store.

Your task (P1 - Information Extraction):
1. Analyze the customer's query to extract product requirements
2. Identify key entities: product type, budget, features, use case
3. Determine customer priorities and constraints
4. Extract any specific brand or model preferences

Respond with a JSON object containing:
{{
    "product_type": "type of product requested",
    "budget": {{
        "min": number or null,
        "max": number or null,
        "currency": "USD"
    }},
    "required_features": ["feature1", "feature2"],
    "preferred_brands": ["brand1", "brand2"],
    "use_case": "primary use case",
    "customer_segment": "gamer|professional|student|casual",
    "priorities": ["priority1", "priority2"],
    "constraints": ["constraint1", "constraint2"]
}}

Be thorough in extraction. If information is not explicitly stated, infer from context.

Conversation history:
{history}"""),
            ("human", "{query}")
        ])

        # P2: Response Generation Prompt
        p2_template = ChatPromptTemplate.from_messages([
            ("system", """You are a knowledgeable sales agent for ElectroMart electronics store.

Your task (P2 - Response Generation):
Generate a personalized product recommendation based on the extracted customer requirements and available products.

Customer Requirements (from P1):
{extracted_requirements}

Available Products:
{products}

Guidelines:
- Present products that best match the requirements
- Highlight features that align with customer priorities
- Mention any products within or near the budget
- If no perfect match, suggest close alternatives
- Use bullet points for multiple products
- Be enthusiastic but honest about limitations
- Suggest complementary products if relevant

Format:
1. Brief acknowledgment of needs
2. Product recommendations with key specs and prices
3. Comparison if multiple options
4. Next steps or questions

Conversation history:
{history}"""),
            ("human", "Generate product recommendations")
        ])

        # Create prompt chain
        prompts = [
            {
                "name": "P1",
                "template": p1_template,
                "description": "Extract product requirements and customer needs",
                "sequence": 1
            },
            {
                "name": "P2",
                "template": p2_template,
                "description": "Generate personalized product recommendations",
                "sequence": 2
            }
        ]

        return PromptChain(prompts)

    async def _execute_sequence_1(self, state: AgentConversationState) -> Dict[str, Any]:
        """
        Seq1 (P1): Extract product requirements and search products

        Returns:
            Dict containing extracted requirements and relevant products
        """
        # Get the latest user message
        user_message = next(
            (msg for msg in reversed(state["conversation_messages"]) if msg["role"] == "user"),
            None
        )

        if not user_message:
            return {"error": "No user message found"}

        # Get P1 prompt
        p1_config = self.prompt_chain.get_prompt(1)
        history = self._build_history(state["conversation_messages"])

        # Execute P1: Extract requirements
        formatted_prompt = p1_config["template"].format_messages(
            history=history,
            query=user_message["content"]
        )

        llm_response = await self.llm.ainvoke(formatted_prompt)

        try:
            # Parse JSON response
            extracted_requirements = json.loads(llm_response.content)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse P1 JSON response, using fallback")
            # Fallback extraction
            extracted_requirements = {
                "product_type": "general electronics",
                "budget": {"min": None, "max": None, "currency": "USD"},
                "required_features": [],
                "preferred_brands": [],
                "use_case": "general",
                "customer_segment": "casual",
                "priorities": ["quality", "price"],
                "constraints": []
            }

        # Search for relevant products based on extracted requirements
        relevant_products = await self._search_products(extracted_requirements, user_message["content"])

        # Record database READ operation
        state = log_database_operation(
            state,
            operation_type="READ",
            database_table_name="products",
            operation_details={
                "query": "search_by_requirements",
                "result_count": len(relevant_products),
                "requirements": extracted_requirements
            }
        )

        return {
            "extracted_requirements": extracted_requirements,
            "relevant_products": relevant_products,
            "search_count": len(relevant_products),
            "user_query": user_message["content"]
        }

    async def _execute_sequence_2(self, state: AgentConversationState, seq1_results: Dict[str, Any]) -> str:
        """
        Seq2 (P2): Generate personalized product recommendations

        Args:
            seq1_results: Results from Seq1 containing extracted requirements and products

        Returns:
            Generated sales response with recommendations
        """
        # Get P2 prompt
        p2_config = self.prompt_chain.get_prompt(2)
        history = self._build_history(state["conversation_messages"])

        # Prepare data for P2
        extracted_requirements = json.dumps(seq1_results.get("extracted_requirements", {}), indent=2)
        products = json.dumps(seq1_results.get("relevant_products", []), indent=2)

        # Execute P2: Generate response
        formatted_prompt = p2_config["template"].format_messages(
            extracted_requirements=extracted_requirements,
            products=products if products != "[]" else "No exact matches found in current inventory",
            history=history
        )

        llm_response = await self.llm.ainvoke(formatted_prompt)
        return llm_response.content

    async def _search_products(self, requirements: Dict[str, Any], query: str) -> list:
        """
        Search for products based on extracted requirements

        Args:
            requirements: Extracted requirements from P1
            query: Original user query for fallback keyword search

        Returns:
            List of relevant products
        """
        try:
            db: Session = SessionLocal()
            products = []

            # Get products from knowledge base
            kb_products = self.knowledge_base.get("products", [])

            # Search by product type
            product_type = requirements.get("product_type", "").lower()
            budget_max = requirements.get("budget", {}).get("max")
            required_features = [f.lower() for f in requirements.get("required_features", [])]

            for product in kb_products:
                score = 0

                # Match product type/category
                if product_type:
                    product_text = f"{product['name']} {product['category']}".lower()
                    if product_type in product_text:
                        score += 3

                # Match budget
                if budget_max and product.get("price", float('inf')) <= budget_max:
                    score += 2

                # Match features
                product_features = json.dumps(product.get("specs", {})).lower()
                for feature in required_features:
                    if feature in product_features:
                        score += 1

                # Fallback: keyword matching from original query
                query_keywords = query.lower().split()
                for keyword in query_keywords:
                    if len(keyword) > 3 and keyword in f"{product['name']} {product['category']} {product_features}".lower():
                        score += 0.5

                if score > 0:
                    products.append({**product, "relevance_score": score})

            # Sort by relevance score and limit to top 3
            products.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

            # Remove relevance_score before returning
            for product in products:
                product.pop("relevance_score", None)

            db.close()
            return products[:3]

        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []

    async def _check_handoff_needed(self, query: str, response: str) -> Dict[str, Any]:
        """Check if query should be handed off to another agent"""
        query_lower = query.lower()

        # Check for order/logistics keywords
        if any(keyword in query_lower for keyword in ["order", "ship", "track", "return", "refund", "deliver"]):
            return {"needs_handoff": True, "target_agent": "logistics"}

        # Check for support keywords
        if any(keyword in query_lower for keyword in ["broken", "not working", "warranty", "repair", "fix", "problem"]):
            return {"needs_handoff": True, "target_agent": "support"}

        # Check for marketing keywords
        if any(keyword in query_lower for keyword in ["discount", "promo", "deal", "sale", "coupon"]):
            return {"needs_handoff": True, "target_agent": "marketing"}

        return {"needs_handoff": False, "target_agent": None}
