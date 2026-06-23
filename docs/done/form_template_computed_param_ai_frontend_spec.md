# Frontend spec — AI-assisted ComputedParam expression authoring

Status: draft · Backend: implemented (`FormTemplateAiService` + `POST /form-template/{id}/version/{version_id}/computed-param/generate-with-ai`).
Companion to [form_ai_fill_frontend_spec.md](form_ai_fill_frontend_spec.md) (same generic pattern,
applied to a different action). Framework-agnostic — applies to the Angular web app and to gws
Streamlit/Reflex apps alike.

---

## 0. The generic pattern (recap)

Same "AI action with text-or-voice input" split as the form-fill feature:

1. **Transcription is shared.** Audio → text via `POST /ai/transcribe-audio` (returns `{ text }`).
2. **Each AI action is text-in.** For computed-param expression generation that's
   `POST /form-template/{id}/version/{version_id}/computed-param/generate-with-ai` with
   `{ description, param_set_key? }`.

Reuse the same "AI input" component you built for form-fill — it shouldn't care what action it
feeds.

```
[voice]  record → POST /ai/transcribe-audio (file) → { text }  ─┐
                                                                ├─→  POST .../generate-with-ai  →  { expression, validation }
[text]   user types description  ──────────────────────────────┘
```

---

## 1. Goal & UX summary

In the **form template editor** (DRAFT version), when the user is authoring a `ComputedParam`
field, give them a way to **generate the expression from a free-text description** ("average mass
across samples", "if weight is over 50, mark heavy, else light", "sum of all sample masses
divided by total volume"). The backend asks GPT for a single expression in the ComputedParam
grammar and runs it through the same validator the editor already calls.

The result is **never auto-applied**. It is loaded into the expression textbox so the user can
review (and tweak) before clicking the normal "Save field" / "Validate" they already use.

Typical flow:

1. User is editing or creating a `computed_param` field in a DRAFT version (either at outer scope
   or inside a `ParamSet`).
2. User clicks "Suggest with AI" next to the expression input.
3. They type (or dictate) a description.
4. (Voice only) frontend uploads audio to `/ai/transcribe-audio`, gets `{ text }`, shows it in
   an editable box.
5. Frontend sends `{ description, param_set_key }` to
   `POST /form-template/{id}/version/{version_id}/computed-param/generate-with-ai`.
   `param_set_key` is the key of the enclosing `ParamSet` when authoring an inner-row formula,
   `null` otherwise.
6. Backend returns `{ expression, validation }` where `validation` is the same
   `ValidateComputedParamResultDTO` as the existing `.../computed-param/validate` endpoint.
7. Frontend writes `expression` into the expression textbox, **does not persist**, and renders
   the `validation` block (valid → ok hint; invalid → error message + `referenced_keys`).
8. The user reviews, edits if needed, and saves the field through the normal Save path.

Key principle: this only ever **pre-fills the expression input**. Saving the field is unchanged
(`POST .../field/{field_name}` with the normal `ParamSpecDTO`). If the user navigates away
without saving, nothing changed.

---

## 2. Endpoints

All require the standard user auth header.

### 2.1 `POST /ai/transcribe-audio` (generic)

Unchanged — see [§2.1 of the form-fill spec](form_ai_fill_frontend_spec.md). Reuse verbatim.

### 2.2 `POST /form-template/{id}/version/{version_id}/computed-param/generate-with-ai`

Request body (JSON):

```json
{
  "description": "average mass across all samples divided by total volume",
  "param_set_key": null
}
```

- `description` (string, required) — the user's free-text description (typed, or the
  transcription from 2.1). Must be non-empty/non-whitespace; reject client-side too.
- `param_set_key` (string | null, optional, default `null`) —
  - `null` → the AI generates an outer-scope expression. Both `@field` and aggregate sugar
    `@key[].field` are allowed.
  - the key of a `ParamSet` field in the same version → the AI generates a **per-row** formula
    valid inside that `ParamSet`. Aggregate sugar (`@key[].field`) is forbidden in this scope and
    will be flagged in `validation`.

The version may be `DRAFT` (it normally is — the user is authoring). The endpoint does not
mutate the version; the param need not (and usually does not) yet exist in the schema.

### 2.3 Response — `GenerateComputedParamResultDTO`

```ts
interface GenerateComputedParamResultDTO {
  expression: string;                        // the AI's verbatim suggestion (always present)
  validation: ValidateComputedParamResultDTO;
}

interface ValidateComputedParamResultDTO {
  valid: boolean;                            // true ⇒ ready to use as-is
  referenced_keys: string[];                 // keys the expression references (best-effort, even when invalid)
  error: string | null;                      // null when valid; human-readable diagnostic otherwise
}
```

Notes:

- `expression` is **always returned**, even when `validation.valid` is `false`. The point is to
  show the user the suggestion alongside the error so they can fix it.
- The validation is exactly what the existing `.../computed-param/validate` endpoint would
  return for that expression at that scope — same checks (syntax, allowed references, cycle
  detection, ParamSet-aggregate-sugar scoping). You can drop the suggestion straight into the
  field's expression input and skip an extra validate call if it came back valid.
- HTTP status is **200** even when `validation.valid` is `false`. A non-2xx means something
  upstream failed (empty description, unknown `param_set_key`, OpenAI unavailable, version not
  found, …).

---

## 3. UI requirements

### 3.1 Entry point

- Next to the expression input on the computed-param field editor, add a "Suggest with AI"
  affordance (button or icon). Visible whenever the version is `DRAFT` and the field is a
  `computed_param` (or the user is about to make one).
- Clicking opens the reusable AI-input surface with **text** and **voice** modes, identical to
  the form-fill feature ([§3.1 of the form-fill spec](form_ai_fill_frontend_spec.md)).
- Provide a placeholder/hint in the description textbox showing the kind of input the model
  handles well. Examples:
  - "average mass across samples"
  - "weight divided by height squared"
  - "if pH is below 7 then 'acid' else 'base'"
  - "sum of all sample masses"

### 3.2 In-flight state

- During transcription: disable controls, show "Transcribing your recording…" (same as form-fill).
- During the generate call: disable controls, show "Generating expression…". This is one LLM
  round-trip — usually a few seconds; use a generous client timeout (≥ 60 s) and don't
  auto-retry.
- Don't lock the rest of the editor — the call is read-only on the server.

### 3.3 On success

- Write `response.expression` into the expression input field. Mark the field as dirty (unsaved).
- Render `response.validation` next to the expression:
  - `validation.valid === true` → small "Valid expression" confirmation (and optionally a chip
    list of `referenced_keys`).
  - `validation.valid === false` → show `validation.error` verbatim (it's already human-readable)
    with the same styling as the manual-validate error path. Suggest the user edit the
    expression or rephrase the description and try again.
- Show a non-blocking, dismissible notice: "Expression generated by AI — review and validate
  before saving."

The user then proceeds through the normal field-save flow (`POST
/form-template/{id}/version/{version_id}/field/{field_name}` with the `ParamSpecDTO` whose
`expression` they just got). The existing manual `.../computed-param/validate` button can stay
exactly as it is — the AI-generate just gives the user a starting point.

### 3.4 On error

| Situation | Frontend message |
|---|---|
| Empty/whitespace `description` | Inline validation; block client-side too. |
| Unknown `param_set_key` (field renamed/deleted concurrently, etc.) | "The ParamSet '<key>' no longer exists in this version — refresh and try again." (Backend 400.) |
| AI returned empty / unusable text | "The AI couldn't produce a suggestion. Try rephrasing your description." Offer Retry (re-uses the same description). |
| OpenAI not configured / upstream failure | Generic "AI service unavailable, try again later." |
| Auth expired | Standard re-auth flow. |
| Transcription errors (file too big, upstream failure) | Same as the form-fill spec. |

On any error, **leave the expression input untouched** and keep the user's description so they
can edit and retry.

### 3.5 What to render alongside the validation

Frontends already know how to render `ValidateComputedParamResultDTO` (it's the result of the
existing `.../computed-param/validate` route). Reuse that component verbatim — this feature just
feeds it the same DTO from a different source.

---

## 4. Sequencing notes / edge cases

- **Send the right `param_set_key`.** It's `null` for top-level computed fields and the
  enclosing ParamSet's key when authoring a per-row formula. Mixing these up is the easiest way
  to get a `valid: false` ("aggregate sugar not allowed in a row formula" / "unknown name").
- **The version may be DRAFT.** The endpoint does not require the param to already be saved —
  in fact, it usually isn't.
- **Don't auto-save the field.** This feature only pre-fills the expression input; the
  field-save POST stays a user gesture.
- **Concurrency.** Disable the "Suggest with AI" button while a request is in flight; if two
  fire anyway, last response wins, never apply two.
- **Languages.** The description can be in any language; the generated expression is purely
  symbolic so the output is language-agnostic. Field references match by exact key (not by
  human name), so the AI inspects the keys in the served scope spec rather than guessing.
- **Voice mode.** Identical handling to the form-fill spec — record, upload to
  `/ai/transcribe-audio`, drop into the editable description box, let the user review before
  clicking Generate.
- **Re-runs are cheap.** A bad first suggestion is normal; encourage iteration ("rephrase and
  try again"). Don't try to multi-turn refine on the server — the endpoint is stateless.

---

## 5. Minimal client contract (pseudo-types)

```ts
// (voice only) transcribe — reused, unchanged
POST /ai/transcribe-audio   (multipart/form-data)
fields: { file: Blob /* audio, <=10MB */ }
-> 200 { text: string } | 4xx/5xx { /* error with message */ }

// the new AI action — description in, expression + validation out
POST /form-template/{id}/version/{version_id}/computed-param/generate-with-ai
body: { description: string; param_set_key?: string | null }
-> 200 GenerateComputedParamResultDTO | 4xx/5xx { /* error with message */ }

// existing — manual lint of a hand-written or AI-suggested expression
POST /form-template/{id}/version/{version_id}/computed-param/validate
body: { expression: string; param_set_key?: string | null; key?: string | null }
-> 200 ValidateComputedParamResultDTO

// existing — saving the field once the user is happy with the expression
POST  /form-template/{id}/version/{version_id}/field/{field_name}     (ParamSpecDTO)
PUT   /form-template/{id}/version/{version_id}/field/{field_name}     (ParamSpecDTO)
```

A reusable client helper, roughly:

```ts
async function suggestComputedParamExpression(
  templateId: string,
  versionId: string,
  description: string,
  paramSetKey: string | null,
): Promise<GenerateComputedParamResultDTO> {
  return postJson(
    `/form-template/${templateId}/version/${versionId}/computed-param/generate-with-ai`,
    { description, param_set_key: paramSetKey },
  );
}
```

---

## 6. Out of scope (this iteration)

- Multi-turn refinement ("no, sum the weights not the masses") — stateless single-shot for now.
- Per-field "explain this expression" reverse mode (expression → English).
- Generating multiple alternative expressions in one call. The endpoint returns one suggestion;
  the user re-runs for another.
- Auto-saving the field after a `valid: true` suggestion — UX choice deliberately kept manual.
- Generating the `type` / `human_name` / `description` of the computed-param field — only the
  expression. The rest of the `ParamSpecDTO` is authored in the field editor as today.
- A generic `POST /ai/action/{name}` dispatcher — same rationale as the form-fill spec.
