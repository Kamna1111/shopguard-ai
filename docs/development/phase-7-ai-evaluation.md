# Phase 7: check whether the AI answers well

## The idea in simple words

We write down questions where we already know the correct shop FAQ and the important details the answer should contain. The computer asks each question, then compares the returned sources and answer with that saved answer key. This is like a small marking sheet for the support helper.

## Run it in IntelliJ

1. Open the project Terminal.
2. Run `make ai-eval`.
3. Read the scores printed in the Terminal.
4. Open `outputs/test-results/ai-evaluation-latest.json` to see each question, answer, source, and timing.

The evaluation uses the local mock provider by default. It does not need the API server, PostgreSQL, or an OpenAI key, and it does not make network calls.

## What the scores mean

- **Pass rate:** the share of questions that found the expected FAQ note and included every required answer phrase.
- **Retrieval precision:** when notes were returned, how many were the expected notes. A wrong extra note lowers this score.
- **Retrieval recall:** how many expected notes were found. Missing one lowers this score.
- **Answer checks:** the share of answers that contained the required facts. The unsupported-question example must say that no approved shop note was found.
- **p50 and p95 time:** typical and slower response times for this small run. They are measurements from your computer, not a promise about other computers.

The default command exits with an error if any golden question fails. That makes the same command useful as a regression check after changing the FAQ or search code.

## Add or change questions

Edit `automation/ai/golden_data/support_questions.json`. Each example has:

- `id`: a short unique name for the scenario.
- `question`: what the customer asks.
- `expected_sources`: the FAQ source IDs that should be returned. Use an empty list for a question outside the approved FAQ.
- `answer_must_include`: short facts that must appear in the answer.

Add examples for normal customer questions, different wording, unsupported topics, and questions that could retrieve the wrong policy. Keep the examples factual and based on `data/knowledge_base/shop_faq.json`.

## Files and current limits

- `automation/ai/evaluate_rag.py` runs the golden set and saves a JSON report.
- `automation/ai/golden_data/support_questions.json` is the answer key.
- `automation/ai/tests/test_evaluation.py` checks the mock baseline and empty-dataset behavior.
- `apps/api/app/ai/support.py` is the search being measured.

The current search is a small keyword search, not a vector database. This gives us a repeatable baseline to compare against when a richer RAG retriever is added. The mock provider confirms that the evaluation wiring works, but it cannot measure real model reasoning. A live OpenAI evaluation can be run by configuring `AI_PROVIDER=openai` and your private `.env` key before running the evaluator directly; live answers can change and may cost money. Keep the standard `make ai-eval` run deterministic.
