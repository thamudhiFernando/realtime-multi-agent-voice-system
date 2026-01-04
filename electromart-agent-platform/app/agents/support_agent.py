"""
Support Agent V2 - Multi-Prompt with Sequence Support
Implements SP3 → P1, P2 pattern from diagram
"""
import json
from typing import Dict, Any
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from app.utils.message_utils import get_user_message, get_message_content

from app.agents.multi_prompt_agent import PromptChain, MultiPromptAgent
from app.graph.state import AgentConversationState
from app.utils.logger import logger


class SupportAgentV2(MultiPromptAgent):
    """
    Support Agent with multi-step processing:
    - Seq1 (P1): Diagnose problem, gather troubleshooting data
    - Seq2 (P2): Provide step-by-step solutions and support
    """

    # -----------------------------
    # Paths
    # -----------------------------
    BASE_DIR = Path(__file__).resolve().parent.parent.parent  # points to 'app' parent
    KB_PATH = BASE_DIR / "data/knowledge" / "support_kb.json"

    def __init__(self):
        # Load knowledge base
        if not self.KB_PATH.exists():
            logger.warning(f"Support knowledge base not found at {self.KB_PATH}, proceeding with empty KB")
            self.knowledge_base = {"troubleshooting": []}
        else:
            with open(self.KB_PATH, "r", encoding="utf-8") as f:
                self.knowledge_base = json.load(f)

        super().__init__(agent_name="support")

    # -----------------------------
    # Build Prompt Chain
    # -----------------------------
    def _build_prompt_chain(self) -> PromptChain:
        """
        Build the two-step prompt chain for support agent:
        P1: Problem diagnosis and data gathering
        P2: Solution generation with troubleshooting steps
        """

        # P1: Problem Diagnosis
        p1_template = ChatPromptTemplate.from_messages([
            ("system", """You are a technical support diagnostician for ElectroMart.

Your task (P1 - Problem Diagnosis):
1. Analyze the customer's issue description
2. Identify the product, problem type, and severity
3. Determine if issue is hardware, software, or user error
4. Assess urgency and need for escalation
5. Identify relevant troubleshooting knowledge base articles

Respond with a JSON object containing:
{{
    "product": "product name or type",
    "problem_type": "hardware|software|setup|connection|performance|other",
    "severity": "critical|high|medium|low",
    "symptoms": ["symptom1", "symptom2"],
    "likely_causes": ["cause1", "cause2"],
    "urgency": "immediate|within_24h|non_urgent",
    "requires_human_escalation": true|false,
    "relevant_kb_articles": ["article_id1", "article_id2"],
    "warranty_status_check_needed": true|false
}}

Conversation history:
{history}"""),
            ("human", "{query}")
        ])

        # P2: Solution Generation
        p2_template = ChatPromptTemplate.from_messages([
            ("system", """You are a technical support specialist for ElectroMart electronics store.

Your task (P2 - Solution Generation):
Provide clear, step-by-step solutions based on the diagnosed problem.

Problem Diagnosis (from P1):
{problem_diagnosis}

Relevant Knowledge Base Solutions:
{solutions}

Guidelines:
- Start with empathy and acknowledgment of the issue
- Provide numbered, step-by-step troubleshooting instructions
- Use simple, non-technical language when possible
- Include expected results for each step
- Offer multiple solutions if applicable (quick fix, then thorough fix)
- Mention warranty information if relevant
- Provide escalation path if issue persists
- Be patient and supportive in tone

Format:
1. Acknowledge the issue with empathy
2. Quick diagnostic questions if needed
3. Step-by-step solution(s)
4. Expected outcome
5. What to do if solution doesn't work

Conversation history:
{history}"""),
            ("human", "Provide troubleshooting solution")
        ])

        prompts = [
            {"name": "P1", "template": p1_template, "description": "Diagnose problem and gather troubleshooting data", "sequence": 1},
            {"name": "P2", "template": p2_template, "description": "Generate step-by-step troubleshooting solution", "sequence": 2}
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
            problem_diagnosis = json.loads(llm_response.content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse P1 JSON response, using fallback")
            problem_diagnosis = {
                "product": "unknown",
                "problem_type": "other",
                "severity": "medium",
                "symptoms": ["issue reported"],
                "likely_causes": ["unknown"],
                "urgency": "non_urgent",
                "requires_human_escalation": False,
                "relevant_kb_articles": [],
                "warranty_status_check_needed": False
            }

        relevant_solutions = self._find_relevant_solutions(problem_diagnosis, get_message_content(user_message))

        if problem_diagnosis.get("requires_human_escalation") or problem_diagnosis.get("severity") == "critical":
            state["conversation_context"]["requires_human_handoff"] = True

        return {"problem_diagnosis": problem_diagnosis, "relevant_solutions": relevant_solutions, "user_query": get_message_content(user_message)}

    async def _execute_sequence_2(self, state: AgentConversationState, seq1_results: Dict[str, Any]) -> str:
        p2_config = self.prompt_chain.get_prompt(2)
        history = self._build_history(state["conversation_messages"])

        problem_diagnosis = json.dumps(seq1_results.get("problem_diagnosis", {}), indent=2)
        solutions = json.dumps(seq1_results.get("relevant_solutions", []), indent=2)

        formatted_prompt = p2_config["template"].format_messages(
            problem_diagnosis=problem_diagnosis,
            solutions=solutions if solutions != "[]" else "No specific solution found in KB, provide general troubleshooting",
            history=history
        )

        llm_response = await self.llm.ainvoke(formatted_prompt)
        response = llm_response.content

        diagnosis = seq1_results.get("problem_diagnosis", {})
        if diagnosis.get("requires_human_escalation"):
            response += "\n\n⚠️ This issue may require specialized assistance. I can connect you with a human support specialist if the above steps don't resolve your issue."

        return response

    # -----------------------------
    # Find Relevant Solutions
    # -----------------------------
    def _find_relevant_solutions(self, diagnosis: Dict[str, Any], query: str) -> list:
        try:
            solutions = self.knowledge_base.get("troubleshooting", [])
            problem_type = diagnosis.get("problem_type", "").lower()
            symptoms = [s.lower() for s in diagnosis.get("symptoms", [])]
            relevant_kb_articles = diagnosis.get("relevant_kb_articles", [])

            relevant = []
            for solution in solutions:
                score = 0
                if problem_type and problem_type in solution.get("category", "").lower():
                    score += 3
                if solution.get("id") in relevant_kb_articles:
                    score += 5
                solution_keywords = solution.get("keywords", [])
                for symptom in symptoms:
                    if any(symptom in keyword.lower() for keyword in solution_keywords):
                        score += 2
                for keyword in solution_keywords:
                    if keyword.lower() in query.lower():
                        score += 1
                if score > 0:
                    relevant.append({**solution, "relevance_score": score})

            relevant.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            for sol in relevant:
                sol.pop("relevance_score", None)

            return relevant[:2]

        except Exception as e:
            logger.error(f"Error finding solutions: {str(e)}")
            return []
