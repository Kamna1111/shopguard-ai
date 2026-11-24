import { useEffect, useState, type FormEvent } from "react";

type SupportReply = { answer: string; source_documents: string[]; provider: string };
type DraftCase = {
  test_case_id: string;
  category: string;
  title: string;
  preconditions: string[];
  steps: string[];
  expected_result: string;
  automation_type: string;
  status: string;
  duplicate_of: string | null;
};
type ApiError = { detail?: string };

async function post<T>(path: string, token: string, body: object): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as ApiError;
    throw new Error(error.detail ?? `Request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

async function get<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`/api${path}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) {
    const error = (await response.json().catch(() => ({}))) as ApiError;
    throw new Error(error.detail ?? `Request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export function AITools({ token }: { token: string }) {
  const [question, setQuestion] = useState("");
  const [reply, setReply] = useState<SupportReply | null>(null);
  const [requirement, setRequirement] = useState("");
  const [drafts, setDrafts] = useState<DraftCase[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void get<DraftCase[]>("/ai/test-cases", token)
      .then(setDrafts)
      .catch((reason: Error) => setError(reason.message));
  }, [token]);

  async function askSupport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      setReply(await post<SupportReply>("/ai/support/chat", token, { question }));
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function generate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await post<{ test_cases: DraftCase[] }>("/ai/test-cases/generate", token, { requirement });
      setDrafts(result.test_cases);
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="ai-section section" id="ai-tools">
      <div className="section-heading"><div><p className="eyebrow">A little help from AI</p><h2>Support & <em>quality lab.</em></h2></div></div>
      <div className="ai-grid">
        <section className="ai-card" aria-labelledby="support-heading">
          <p className="eyebrow">Shop helper</p><h3 id="support-heading">Ask about the demo shop</h3>
          <p className="muted">Answers use approved shop notes about shipping, cancellations, payment, and discounts.</p>
          <form onSubmit={(event) => void askSupport(event)}>
            <label htmlFor="support-question">Your question</label>
            <textarea id="support-question" value={question} onChange={(event) => setQuestion(event.target.value)} minLength={3} maxLength={1000} placeholder="How does the demo discount work?" required />
            <button className="button button-dark" disabled={busy}>Ask the helper <span>→</span></button>
          </form>
          {reply && <div className="ai-reply" role="status"><p>{reply.answer}</p><small>Provider: {reply.provider} · Sources: {reply.source_documents.join(", ") || "no matching approved note"}</small></div>}
        </section>
        <section className="ai-card" aria-labelledby="generator-heading">
          <p className="eyebrow">QA workbench</p><h3 id="generator-heading">Turn a requirement into test ideas</h3>
          <p className="muted">Generated ideas are drafts. A QA reviewer must check them before anyone uses them.</p>
          <form onSubmit={(event) => void generate(event)}>
            <label htmlFor="qa-requirement">Requirement or user story</label>
            <textarea id="qa-requirement" value={requirement} onChange={(event) => setRequirement(event.target.value)} minLength={10} maxLength={4000} placeholder="As a customer, I can add a product to my basket." required />
            <button className="button button-dark" disabled={busy}>Generate draft tests <span>→</span></button>
          </form>
          {drafts.length > 0 && <div className="draft-list" aria-live="polite"><h4>{drafts.length} saved test ideas</h4>{drafts.map((draft) => <article className="draft-case" key={draft.test_case_id}><div className="draft-meta"><span>{draft.category}</span><span>{draft.automation_type.toUpperCase()}</span><span>{draft.status === "draft" ? "Needs review" : draft.status}</span></div><h4>{draft.title}</h4><ol>{draft.steps.map((step, index) => <li key={`${draft.test_case_id}-${index}`}>{step}</li>)}</ol><p><strong>Expected:</strong> {draft.expected_result}</p>{draft.duplicate_of && <small>Possible duplicate of another draft in this batch.</small>}</article>)}</div>}
        </section>
      </div>
      {error && <p className="ai-error" role="alert">{error}</p>}
    </section>
  );
}
