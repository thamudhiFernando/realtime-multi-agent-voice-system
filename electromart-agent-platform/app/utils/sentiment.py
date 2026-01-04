"""
Sentiment Analysis for Customer Messages
Analyzes customer sentiment to improve agent responses and trigger escalation
"""
from typing import Dict, Any, Tuple
from textblob import TextBlob
from app.utils.logger import logger


class SentimentAnalyzer:
    """
    Analyzes customer message sentiment using TextBlob

    Sentiment Categories:
    - Very Negative: polarity < -0.5
    - Negative: -0.5 <= polarity < -0.1
    - Neutral: -0.1 <= polarity <= 0.1
    - Positive: 0.1 < polarity <= 0.5
    - Very Positive: polarity > 0.5

    Subjectivity:
    - Objective: subjectivity < 0.3
    - Mixed: 0.3 <= subjectivity <= 0.7
    - Subjective: subjectivity > 0.7
    """

    def __init__(self):
        """Initialize sentiment analyzer"""
        self.negative_keywords = [
            "angry", "frustrated", "terrible", "awful", "worst", "horrible",
            "disappointed", "upset", "furious", "mad", "annoyed", "hate",
            "useless", "poor", "bad", "wrong", "broken", "failed", "error"
        ]

        self.urgent_keywords = [
            "urgent", "emergency", "immediately", "asap", "critical",
            "important", "serious", "now", "help", "please help"
        ]

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of customer message

        Args:
            text (str): Customer message text

        Returns:
            Dict[str, Any]: Sentiment analysis results containing:
                - polarity (float): Sentiment polarity from -1 (negative) to 1 (positive)
                - subjectivity (float): Subjectivity from 0 (objective) to 1 (subjective)
                - sentiment_label (str): Human-readable sentiment label
                - subjectivity_label (str): Human-readable subjectivity label
                - requires_escalation (bool): Whether message should trigger human handoff
                - escalation_reason (str): Reason for escalation if required
                - urgency_level (str): Urgency level (low, medium, high, critical)

        Example:
            >>> analyzer = SentimentAnalyzer()
            >>> result = analyzer.analyze("I'm very frustrated with this product!")
            >>> print(result["sentiment_label"])
            "negative"
            >>> print(result["requires_escalation"])
            True
        """
        try:
            # Basic sentiment analysis with TextBlob
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Determine sentiment label
            sentiment_label = self._get_sentiment_label(polarity)
            subjectivity_label = self._get_subjectivity_label(subjectivity)

            # Check for negative keywords
            text_lower = text.lower()
            has_negative_keywords = any(keyword in text_lower for keyword in self.negative_keywords)

            # Check for urgent keywords
            has_urgent_keywords = any(keyword in text_lower for keyword in self.urgent_keywords)

            # Determine urgency level
            urgency_level = self._determine_urgency(
                polarity,
                has_negative_keywords,
                has_urgent_keywords
            )

            # Determine if escalation is needed
            requires_escalation, escalation_reason = self._check_escalation_needed(
                polarity,
                has_negative_keywords,
                has_urgent_keywords,
                urgency_level
            )

            result = {
                "polarity": round(polarity, 3),
                "subjectivity": round(subjectivity, 3),
                "sentiment_label": sentiment_label,
                "subjectivity_label": subjectivity_label,
                "requires_escalation": requires_escalation,
                "escalation_reason": escalation_reason,
                "urgency_level": urgency_level,
                "has_negative_keywords": has_negative_keywords,
                "has_urgent_keywords": has_urgent_keywords
            }

            logger.debug(f"Sentiment analysis: {sentiment_label} (polarity: {polarity:.2f})")

            return result

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            # Return neutral sentiment on error
            return {
                "polarity": 0.0,
                "subjectivity": 0.5,
                "sentiment_label": "neutral",
                "subjectivity_label": "mixed",
                "requires_escalation": False,
                "escalation_reason": None,
                "urgency_level": "low",
                "has_negative_keywords": False,
                "has_urgent_keywords": False
            }

    def _get_sentiment_label(self, polarity: float) -> str:
        """
        Convert polarity score to human-readable label

        Args:
            polarity (float): Sentiment polarity from -1 to 1

        Returns:
            str: Sentiment label
        """
        if polarity < -0.5:
            return "very_negative"
        elif polarity < -0.1:
            return "negative"
        elif polarity <= 0.1:
            return "neutral"
        elif polarity <= 0.5:
            return "positive"
        else:
            return "very_positive"

    def _get_subjectivity_label(self, subjectivity: float) -> str:
        """
        Convert subjectivity score to human-readable label

        Args:
            subjectivity (float): Subjectivity from 0 to 1

        Returns:
            str: Subjectivity label
        """
        if subjectivity < 0.3:
            return "objective"
        elif subjectivity <= 0.7:
            return "mixed"
        else:
            return "subjective"

    def _determine_urgency(
        self,
        polarity: float,
        has_negative_keywords: bool,
        has_urgent_keywords: bool
    ) -> str:
        """
        Determine urgency level based on sentiment and keywords

        Args:
            polarity (float): Sentiment polarity
            has_negative_keywords (bool): Whether message contains negative keywords
            has_urgent_keywords (bool): Whether message contains urgent keywords

        Returns:
            str: Urgency level (low, medium, high, critical)
        """
        if polarity < -0.5 and has_urgent_keywords:
            return "critical"
        elif polarity < -0.3 or has_urgent_keywords:
            return "high"
        elif polarity < -0.1 or has_negative_keywords:
            return "medium"
        else:
            return "low"

    def _check_escalation_needed(
        self,
        polarity: float,
        has_negative_keywords: bool,
        has_urgent_keywords: bool,
        urgency_level: str
    ) -> Tuple[bool, str]:
        """
        Check if message should be escalated to human agent

        Args:
            polarity (float): Sentiment polarity
            has_negative_keywords (bool): Whether message contains negative keywords
            has_urgent_keywords (bool): Whether message contains urgent keywords
            urgency_level (str): Calculated urgency level

        Returns:
            Tuple[bool, str]: (requires_escalation, escalation_reason)
        """
        # Critical urgency always escalates
        if urgency_level == "critical":
            return True, "Critical urgency detected with very negative sentiment"

        # Very negative sentiment escalates
        if polarity < -0.6:
            return True, "Very negative customer sentiment"

        # Combination of negative and urgent
        if has_negative_keywords and has_urgent_keywords:
            return True, "Negative sentiment with urgent request"

        return False, None

    def get_response_modifier(self, sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get suggestions for modifying agent response based on sentiment

        Args:
            sentiment (Dict[str, Any]): Sentiment analysis results

        Returns:
            Dict[str, Any]: Response modification suggestions containing:
                - tone (str): Suggested tone for response
                - empathy_level (str): How empathetic the response should be
                - urgency_acknowledgment (bool): Whether to acknowledge urgency
                - apology_needed (bool): Whether to include an apology

        Note:
            Use these suggestions to adjust agent response templates
        """
        sentiment_label = sentiment["sentiment_label"]
        urgency_level = sentiment["urgency_level"]

        # Default settings
        modifier = {
            "tone": "professional",
            "empathy_level": "standard",
            "urgency_acknowledgment": False,
            "apology_needed": False
        }

        # Adjust based on sentiment
        if sentiment_label in ["very_negative", "negative"]:
            modifier["tone"] = "apologetic"
            modifier["empathy_level"] = "high"
            modifier["apology_needed"] = True

        # Adjust based on urgency
        if urgency_level in ["high", "critical"]:
            modifier["urgency_acknowledgment"] = True

        # Very positive sentiment
        if sentiment_label in ["positive", "very_positive"]:
            modifier["tone"] = "friendly"
            modifier["empathy_level"] = "standard"

        return modifier


# Global sentiment analyzer instance
_sentiment_analyzer: SentimentAnalyzer = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """
    Get the global sentiment analyzer instance

    Returns:
        SentimentAnalyzer: Global sentiment analyzer instance
    """
    global _sentiment_analyzer

    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()

    return _sentiment_analyzer
