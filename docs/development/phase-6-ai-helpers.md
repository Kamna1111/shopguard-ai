# Phase 6: AI helpers

## What this phase adds

The shop now has two AI practice tools:

1. **Support helper:** ask a question about shop policies. It searches the approved FAQ notes and shows which notes it used. If it cannot find a useful note, it says so instead of inventing a policy.
2. **Test-case helper:** write a feature requirement and receive draft test ideas. The drafts include a title, setup, steps, expected result, category, and suggested automation type. Similar repeated titles are marked as duplicates.

The drafts are saved in PostgreSQL. A person with the admin role must approve or reject each draft. Approval only changes its review status; it does not run the test.

## Try it in IntelliJ

1. Open the project Terminal.
2. Apply the database change once: `make db-migrate`.
3. In one Terminal tab, start the backend with `make api`.
4. In another Terminal tab, start the website with `make web`.
5. Open `http://127.0.0.1:5173`, create an account or sign in, and scroll below the shop content to **Support & quality lab**.
6. Ask a shop question or enter a requirement, then inspect the returned FAQ source or test drafts.

The API can also be explored at `http://127.0.0.1:8000/docs` under **AI helpers**. These routes require a signed-in user. Reviewing drafts requires an account with the `admin` role.

## Practice mode and live model

By default, `AI_PROVIDER=mock`. This provider returns predictable demo answers and sample test cases, costs nothing, and makes no network calls. It is useful while learning the screens and API.

An optional OpenAI provider is included. In your private `.env` file set `AI_PROVIDER=openai` and set `OPENAI_API_KEY` to your own key, then restart `make api`. Keep the key in `.env` only; it is read by the backend and is never sent to the browser. This live mode can incur API charges. The implementation uses the official OpenAI Python SDK Responses API; structured test-case output is parsed into the project's Pydantic schema. See the [OpenAI quickstart](https://developers.openai.com/api/docs/quickstart) and [structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs).

## Where the logic lives

- `apps/api/app/ai/providers.py` chooses the mock or OpenAI provider.
- `apps/api/app/ai/support.py` looks up FAQ evidence before composing an answer.
- `apps/api/app/ai/test_case_generator.py` removes duplicate titles and saves drafts.
- `apps/api/app/api/ai.py` defines the four `/ai` HTTP routes and access rules.
- `data/knowledge_base/shop_faq.json` contains the approved shop FAQ notes.
- `apps/api/app/domain/models.py` and `apps/api/migrations/versions/410f0a8c97b8_add_ai_test_case_drafts.py` define and create the draft table.
- `apps/web/src/ai-tools.tsx` builds the two customer-facing forms.
- `apps/api/tests/test_ai_features.py` checks FAQ answers, unknown questions, draft generation, and admin review using the mock provider.

FAQ matching in this phase is a small local word search. Phase 7 is where the project adds vector search/RAG evaluation and measures answer quality.

## Checks

```bash
in simpl
```

The AI tests use the separate `shopguard_test` database and the mock provider. They do not contact an AI service.
