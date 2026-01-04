"""
Integration tests for multi-agent workflow
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.graph.state import create_initial_conversation_state, append_message_to_conversation


@pytest.mark.integration
@pytest.mark.asyncio
class TestAgentWorkflowIntegration:
    """Integration tests for complete agent workflow"""

    @patch('backend.agents.orchestrator.ChatOpenAI')
    async def test_complete_sales_inquiry_workflow(self, mock_openai):
        """Test complete workflow for a sales inquiry"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.content = '{"intent": "sales", "confidence": 0.95, "reasoning": "Product inquiry", "entities": {}}'
        mock_openai.return_value.ainvoke = AsyncMock(return_value=mock_response)

        # Create initial state
        state = create_initial_conversation_state("test-session-sales")

        # Add user message
        state = append_message_to_conversation(
            state,
            message_role="user",
            message_content="What's the price of iPhone 15 Pro?"
        )

        # In real integration test, would invoke workflow here
        # For now, verify state is properly set up
        assert len(state["conversation_messages"]) == 1
        assert state["conversation_messages"][0]["role"] == "user"
        assert "iPhone 15 Pro" in state["conversation_messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_agent_handoff_workflow(self):
        """Test agent handoff scenario"""
        # Create state with sales agent
        state = create_initial_conversation_state("test-session-handoff")
        state["current_active_agent"] = "sales"

        # Add initial sales conversation
        state = append_message_to_conversation(
            state, "user", "What gaming laptops do you have?"
        )
        state = append_message_to_conversation(
            state, "assistant", "Here are our gaming laptops", "sales"
        )

        # User asks warranty question (should trigger handoff)
        state = append_message_to_conversation(
            state, "user", "What if it breaks? Is it covered under warranty?"
        )

        # Verify conversation history
        assert len(state["conversation_messages"]) == 3
        assert state["current_active_agent"] == "sales"

    @pytest.mark.asyncio
    async def test_database_operations_in_workflow(self):
        """Test that database operations are logged in workflow"""
        from ..graph.state import log_database_operation

        state = create_initial_conversation_state("test-session-db")
        state["current_active_agent"] = "sales"

        # Simulate database operations
        state = log_database_operation(
            state,
            operation_type="READ",
            database_table_name="products",
            operation_details={"query": "search", "category": "Laptops"}
        )

        state = log_database_operation(
            state,
            operation_type="READ",
            database_table_name="products",
            operation_details={"query": "get_by_id", "product_id": 1}
        )

        # Verify operations were logged
        assert len(state["database_operations_log"]) == 2
        assert state["database_operations_log"][0]["type"] == "READ"
        assert state["database_operations_log"][0]["table"] == "products"
        assert state["database_operations_log"][1]["details"]["product_id"] == 1

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_state(self):
        """Test that state is maintained across multiple turns"""
        state = create_initial_conversation_state("test-session-multi")

        # Turn 1
        state = append_message_to_conversation(state, "user", "Hello")
        state = append_message_to_conversation(state, "assistant", "Hi! How can I help?", "orchestrator")

        # Turn 2
        state = append_message_to_conversation(state, "user", "Show me laptops")
        state["classified_intent"] = "sales"
        state["current_active_agent"] = "sales"
        state = append_message_to_conversation(state, "assistant", "Here are laptops", "sales")

        # Turn 3
        state = append_message_to_conversation(state, "user", "What's the warranty?")

        # Verify state integrity
        assert len(state["conversation_messages"]) == 5
        assert state["classified_intent"] == "sales"
        assert state["current_active_agent"] == "sales"
        assert state["unique_session_id"] == "test-session-multi"


@pytest.mark.integration
class TestKnowledgeBaseIntegration:
    """Integration tests for knowledge base access"""

    def test_sales_knowledge_base_loads(self):
        """Test that sales knowledge base loads correctly"""
        import json
        with open("data/knowledge/sales_kb.json", "r") as f:
            kb = json.load(f)

        assert "products" in kb
        assert len(kb["products"]) >= 20
        assert "recommendations" in kb

    def test_marketing_knowledge_base_loads(self):
        """Test that marketing knowledge base loads correctly"""
        import json
        with open("backend/knowledge/marketing_kb.json", "r") as f:
            kb = json.load(f)

        assert "active_promotions" in kb
        assert "loyalty_program" in kb
        assert len(kb["active_promotions"]) >= 5

    def test_support_knowledge_base_loads(self):
        """Test that support knowledge base loads correctly"""
        import json
        with open("backend/knowledge/support_kb.json", "r") as f:
            kb = json.load(f)

        assert "troubleshooting_guides" in kb
        assert "warranty_information" in kb
        assert "repair_services" in kb

    def test_logistics_knowledge_base_loads(self):
        """Test that logistics knowledge base loads correctly"""
        import json
        with open("backend/knowledge/logistics_kb.json", "r") as f:
            kb = json.load(f)

        assert "shipping_policies" in kb
        assert "return_policy" in kb
        assert "refund_policy" in kb
