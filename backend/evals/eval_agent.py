"""Agent evaluation script (programmatic).

Tests the financial agent's tool routing, response quality, and topic adherence.

Usage:
    docker compose exec backend python evals/eval_agent.py
"""

import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI

from app.config import settings
from app.services.agent_service import agent_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================================================================
# Test Scenarios
# ===================================================================

TEST_SCENARIOS = [
    {
        "category": "RAG Query",
        "message": "Ce este TEZAUR?",
        "expected_tool": "rag_query",
        "expected_topics": ["TEZAUR", "titluri de stat", "garantat"],
        "should_have_disclaimer": True,
    },
    {
        "category": "Market Search",
        "message": "Care este cursul EUR/RON astazi?",
        "expected_tool": "market_search",
        "expected_topics": ["EUR", "RON", "curs"],
        "should_have_disclaimer": False,
    },
    {
        "category": "Goals Query",
        "message": "Care sunt obiectivele mele financiare?",
        "expected_tool": "goals_summary",
        "expected_topics": ["obiectiv", "RON"],
        "should_have_disclaimer": False,
    },
    {
        "category": "Goal Creation",
        "message": "Vreau sa creez un obiectiv de 10000 RON pentru o bicicleta",
        "expected_tool": "create_goal",
        "expected_topics": ["obiectiv", "creat", "biciclet"],
        "should_have_disclaimer": False,
    },
    {
        "category": "Language Detection (English)",
        "message": "What are the main differences between TEZAUR and FIDELIS?",
        "expected_tool": "rag_query",
        "expected_topics": ["TEZAUR", "FIDELIS"],
        "should_have_disclaimer": True,
        "expected_language": "en",
    },
]

DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"


async def evaluate_agent():
    """Run agent evaluation scenarios."""
    logger.info("Starting Agent Evaluation")
    logger.info(f"Test scenarios: {len(TEST_SCENARIOS)}\n")

    results = []
    total_score = 0
    max_score = 0

    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        logger.info(f"--- Scenario {i}: {scenario['category']} ---")
        logger.info(f"Message: {scenario['message']}")

        try:
            response = await agent_service.chat(
                message=scenario["message"],
                user_id=DEMO_USER_ID,
                session_id=f"eval-{i}",
            )

            # Evaluate topic adherence
            topic_hits = sum(
                1 for topic in scenario["expected_topics"]
                if topic.lower() in response.lower()
            )
            topic_score = topic_hits / len(scenario["expected_topics"])

            # Evaluate MiFID II disclaimer
            has_disclaimer = "MiFID" in response or "recomandare de investiții" in response.lower()
            disclaimer_correct = has_disclaimer == scenario["should_have_disclaimer"]

            # Overall score for this scenario
            scenario_score = (topic_score * 0.7) + (1.0 if disclaimer_correct else 0.0) * 0.3
            total_score += scenario_score
            max_score += 1

            result = {
                "category": scenario["category"],
                "topic_score": round(topic_score, 2),
                "disclaimer_correct": disclaimer_correct,
                "overall_score": round(scenario_score, 2),
                "response_length": len(response),
                "response_preview": response[:150] + "..." if len(response) > 150 else response,
            }
            results.append(result)

            logger.info(f"  Topic adherence: {topic_score:.0%}")
            logger.info(f"  Disclaimer correct: {disclaimer_correct}")
            logger.info(f"  Score: {scenario_score:.2f}/1.00")
            logger.info(f"  Response: {response[:100]}...\n")

        except Exception as e:
            logger.error(f"  ERROR: {e}")
            results.append({
                "category": scenario["category"],
                "error": str(e),
                "overall_score": 0,
            })
            max_score += 1

    # Summary
    final_score = total_score / max_score if max_score > 0 else 0
    logger.info(f"\n{'='*50}")
    logger.info(f"AGENT EVALUATION SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"Total Score: {total_score:.2f} / {max_score:.2f} ({final_score:.0%})")
    logger.info(f"Scenarios Passed: {sum(1 for r in results if r.get('overall_score', 0) >= 0.7)}/{len(results)}")

    # Save results
    output = {
        "total_score": round(total_score, 2),
        "max_score": max_score,
        "final_percentage": round(final_score * 100, 1),
        "scenarios": results,
    }
    output_path = os.path.join(os.path.dirname(__file__), "agent_eval_results.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info(f"\nResults saved to {output_path}")

    return output


if __name__ == "__main__":
    asyncio.run(evaluate_agent())
