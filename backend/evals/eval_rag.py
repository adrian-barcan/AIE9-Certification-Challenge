"""RAG evaluation script (programmatic).

Tests both baseline (no reranking) and improved (Cohere reranking) pipelines
using RAGAS metrics. This is the script version of the notebook for automation.

Usage:
    docker compose exec backend python evals/eval_rag.py
"""

import asyncio
import json
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

from app.config import settings
from app.services.rag_service import rag_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================================================================
# Test Questions (synthetic-style, manually curated for the demo)
# ===================================================================

TEST_QUESTIONS = [
    {
        "question": "Ce sunt titlurile de stat TEZAUR?",
        "ground_truth": "Titlurile TEZAUR sunt instrumente financiare emise de Ministerul Finantelor din Romania, destinate exclusiv persoanelor fizice rezidente. Au maturitati de 1, 3 sau 5 ani, dobanda fixa, si sunt 100% garantate de statul roman. Sunt scutite de impozit pe venit.",
    },
    {
        "question": "Care sunt diferentele intre TEZAUR si FIDELIS?",
        "ground_truth": "TEZAUR nu se tranzactioneaza pe bursa si este scutit de impozit. FIDELIS este listat la BVB, poate fi tranzactionat pe piata secundara, si este impozitat cu 10% din 2023. TEZAUR permite rascumparare anticipata cu penalizare, FIDELIS permite vanzare pe bursa.",
    },
    {
        "question": "Ce avantaje are TEZAUR fata de depozitele bancare?",
        "ground_truth": "Nu exista risc de pierdere a capitalului investit. Dobanzile sunt mai mari decat la depozitele bancare. Scutire de impozit pe venit pentru dobanzile primite. Sunt accesibile de la 1 RON.",
    },
    {
        "question": "Cum se pot achizitiona titlurile FIDELIS?",
        "ground_truth": "Titlurile FIDELIS sunt listate la Bursa de Valori Bucuresti (BVB) si pot fi cumparate sau vandute pe piata secundara. Dobanda este fixa si platita semestrial sub forma de cupon.",
    },
    {
        "question": "Ce maturitati au titlurile de stat romanesti?",
        "ground_truth": "Titlurile de stat TEZAUR si FIDELIS au maturitati de 1 an, 3 ani sau 5 ani. FIDELIS poate fi denominat in LEI (RON) sau EURO (EUR).",
    },
]


async def run_evaluation(use_reranking: bool = True) -> dict:
    """Run RAG evaluation with RAGAS metrics.

    Args:
        use_reranking: Whether to use Cohere reranking.

    Returns:
        Dict with RAGAS metric scores.
    """
    label = "Reranked" if use_reranking else "Baseline"
    logger.info(f"\n{'='*50}")
    logger.info(f"Running {label} RAG Evaluation")
    logger.info(f"{'='*50}\n")

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    for test_case in TEST_QUESTIONS:
        question = test_case["question"]
        logger.info(f"Processing: {question}")

        # Retrieve documents
        docs = await rag_service.query(question, use_reranking=use_reranking)
        context_texts = [doc.page_content for doc in docs]

        # Generate answer using RAG context
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.specialist_model,
            api_key=settings.openai_api_key,
        )
        context_str = "\n\n".join(context_texts)
        prompt = f"Based on the following context, answer the question.\n\nContext:\n{context_str}\n\nQuestion: {question}\n\nAnswer:"
        response = await llm.ainvoke(prompt)

        questions.append(question)
        answers.append(response.content)
        contexts.append(context_texts)
        ground_truths.append(test_case["ground_truth"])

    # Create RAGAS dataset
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    # Run RAGAS evaluation
    logger.info(f"\nRunning RAGAS metrics for {label} pipeline...")
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    scores = {k: round(v, 4) for k, v in result.items() if isinstance(v, (int, float))}
    logger.info(f"\n{label} Results:")
    for metric, score in scores.items():
        logger.info(f"  {metric}: {score}")

    return scores


async def main():
    """Run both baseline and reranked evaluations and compare."""
    logger.info("Starting RAG Evaluation Pipeline")
    logger.info(f"Test questions: {len(TEST_QUESTIONS)}")

    # Baseline: no reranking
    baseline_scores = await run_evaluation(use_reranking=False)

    # Improved: with Cohere reranking
    reranked_scores = await run_evaluation(use_reranking=True)

    # Comparison
    logger.info(f"\n{'='*60}")
    logger.info("COMPARISON: Baseline vs Reranked")
    logger.info(f"{'='*60}\n")
    logger.info(f"{'Metric':<25} {'Baseline':>10} {'Reranked':>10} {'Delta':>10}")
    logger.info("-" * 60)
    for metric in baseline_scores:
        baseline = baseline_scores.get(metric, 0)
        reranked = reranked_scores.get(metric, 0)
        delta = reranked - baseline
        delta_str = f"+{delta:.4f}" if delta >= 0 else f"{delta:.4f}"
        logger.info(f"{metric:<25} {baseline:>10.4f} {reranked:>10.4f} {delta_str:>10}")

    # Save results
    results = {
        "baseline": baseline_scores,
        "reranked": reranked_scores,
    }
    output_path = os.path.join(os.path.dirname(__file__), "eval_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"\nResults saved to {output_path}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
