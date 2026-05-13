# Frontend spec — AI-assisted form filling (text / voice)

Status: draft · Backend: implemented (`OpenAiTranscriptionService` + `POST /ai/transcribe-audio`;
`FormAiFillService` + `POST /form/{id}/fill-from-text`). Framework-agnostic — applies to the
Angular web app and to gws Streamlit/Reflex apps alike.

---

## 0. The generic pattern (read this first)

This feature is built on a deliberately generic split that any "AI action with text-or-voice
input" should follow:

1. **Transcription is a separate, shared step.** Audio is just an alternative way of
   producing the instruction text. There is **one** endpoint for it — `POST /ai/transcribe-audio`
   — used by every voice-enabled feature. It takes an audio file and returns `{ text }`.
2. **Each AI action is a plain text-in endpoint.** It never knows about audio. For forms
   that's `POST /form/{id}/fill-from-text` with `{ text, current_values }`.

So the frontend needs **one reusable "AI input" component**: it gathers text — either from a
textbox the user typed in, or by recording audio and calling `/ai/transcribe-audio` — and
then hands that text to whatever action the caller wants. Voice features = "transcribe, then
act"; text features just skip step 1.

```
[voice]  record → POST /ai/transcribe-audio (file) → { text }  ─┐
                                                                ├─→  POST /<action>-from-text  →  <action result>
[text]   user types instruction  ──────────────────────────────┘
```

Recommended UX: after transcribing, **show the transcription in an editable textbox** before
the user runs the action. They can fix mishearings, and it makes the two-step nature obvious.
(You *can* auto-run the action right after transcription if you prefer one tap — but then a
bad transcription means a wasted LLM round-trip.)

---

## 1. Goal & UX summary (forms)

On a form edit screen, give the user a way to fill the form by **typing a free-text
instruction** or **dictating it** (voice). The backend turns the instruction into a complete
`values` dict for the form. **The result is not saved** — it is loaded into the form editor so
the user can review, tweak, and then save with the normal Save button.

Typical flow:

1. User opens a form (DRAFT or SUBMITTED) and has edited some fields (or none).
2. User clicks "Fill with AI" → types an instruction, or records one.
3. If recorded: frontend uploads the audio to `POST /ai/transcribe-audio`, gets `{ text }`,
   shows it in an editable box.
4. Frontend sends `{ text, current_values }` to `POST /form/{id}/fill-from-text` —
   `current_values` is the form's current editor state.
5. Backend returns a `FormSaveResultDTO` (same shape as `GET /form/{id}/content`).
6. Frontend replaces the in-editor values with the returned values, **does not persist**,
   shows an "AI-filled — review and save" hint, and re-renders fields + computed-cell errors.
7. User reviews/edits and clicks Save → existing `POST /form/{id}/save` flow.

Key principle: this feature only ever **pre-fills the editor**. Persistence stays with the
existing Save path. If the user navigates away without saving, nothing changed server-side.

---

## 2. Endpoints

All require the standard user auth header (same as the rest of the API).

### 2.1 `POST /ai/transcribe-audio` (generic — used by any voice feature)

`multipart/form-data`:

- `file` (audio file, required) — the recording. **Max 10 MB.** WAV/webm/mp3/m4a etc. are
  fine (it's handed to Whisper). Smaller/shorter = faster.

Response (JSON):

```ts
interface TranscriptionResultDTO { text: string; }
```

Whisper auto-detects the spoken language (French, Spanish, English, …) and transcribes in
that language; no `language` parameter is exposed. Errors: a `4xx`/`5xx` with a message
(notably oversized file, or upstream/OpenAI unavailable).

### 2.2 `POST /form/{id}/fill-from-text`

Request body (JSON):

```json
{
  "text": "patient is 42 years old, weight 78 kg, blood type O+, no known allergies",
  "current_values": { /* the form's current values, as currently in the editor */ }
}
```

- `text` (string, required) — the user's instruction (typed, or the transcription from 2.1).
  Must be non-empty/non-whitespace.
- `current_values` (object, optional, default `{}`) — the values dict the editor currently
  holds, **in the same shape the editor uses for `POST /form/{id}/save`** (bare scalars for
  user fields; ParamSet fields as arrays of row objects; include `__item_id` on existing
  rows if you have it). Send computed cells either omitted or as bare scalars — they're
  recomputed server-side regardless. If the form is brand-new and untouched, send `{}`.

### 2.3 Response — `FormSaveResultDTO`

Identical to the body of `GET /form/{id}/content`:

```ts
interface FormSaveResultDTO {
  values: { [key: string]: any } | null;   // union of user + computed values
  specs:  { [key: string]: ParamSpecDTO }; // the form's ConfigSpecs, serialized
}
```

- `values`: user-input cells are bare scalars; **computed cells are wrapped** as
  `{ "value": <scalar|null>, "errors": <string|null> }` — at the top level and inside
  ParamSet rows. ParamSet rows carry a server-minted `__item_id`. This is the **same shape**
  the editor already renders from `/content` and `/save`, so reuse that rendering path verbatim.
- `specs`: present so a consumer can render fields without a separate template fetch. If your
  editor already has the specs loaded, you can ignore this and just take `values`.

**The frontend must NOT call `/save` automatically.** Load `values` into the editor state
(dirty), let the user act.

---

## 3. UI requirements

### 3.1 Entry points

- A "Fill with AI" affordance on the form edit screen (button / menu item), enabled whenever
  the form is editable (DRAFT, or SUBMITTED-and-re-editing — same condition as the fields
  being editable).
- It opens the reusable AI-input surface with two modes:
  - **Text**: a multiline textbox + "Generate" button.
  - **Voice**: a record button (press-and-hold or toggle). On stop → upload to
    `/ai/transcribe-audio` (show a brief "Transcribing…" state) → drop the returned text into
    the textbox (now editable) → user reviews → clicks "Generate". Disable/grey out voice mode
    if no mic permission. Optionally pre-check `blob.size` against 10 MB before uploading.

### 3.2 In-flight state

- During transcription: disable controls, show "Transcribing your recording…".
- During the fill call: disable controls, show "Filling the form…". This round-trip includes
  an LLM call — expect a few seconds, sometimes longer. Use a generous client timeout (≥ 60 s)
  and don't auto-retry.
- Keep the rest of the form visible; consider locking field editing while the fill request is
  in flight to avoid a race with the incoming values.

### 3.3 On success (fill)

- Replace the editor's `values` with `response.values`. Re-run the editor's normal
  render-from-values + computed-error display.
- Mark the form dirty (unsaved-changes state) so the user is prompted if they navigate away.
- Show a non-blocking, dismissible notice: e.g. "Form filled by AI from your instruction —
  review the fields and click Save to keep the changes."
- Optional nice-to-have: diff against the `current_values` you sent and visually flag changed
  fields.
- Per-field computed errors (the `errors` string on a computed cell) render exactly as they do
  today after a normal save.

### 3.4 On error

Backend returns standard error responses (4xx/5xx with a message). Map and surface:

| Situation | Where | Frontend message |
|---|---|---|
| Empty/whitespace `text` | fill | Inline validation — block the request client-side too. |
| Audio file > 10 MB | transcribe | "Recording too long — please keep it under 10 MB / ~a few minutes." Ideally also pre-check `blob.size` before upload. |
| Transcription upstream failure / OpenAI unavailable | transcribe | "Couldn't transcribe the recording, try again." (User can also type the instruction instead.) |
| AI returned non-JSON / non-object | fill | "The AI couldn't produce a valid result. Try rephrasing your instruction." Offer a Retry button (re-uses the same text). |
| AI produced values that don't fit the form (e.g. a number where text is expected, validation rejects it) | fill | Same — "couldn't fill the form from that instruction; try being more specific." |
| OpenAI not configured / upstream failure | fill | Generic "AI service unavailable, try again later." |
| Auth expired | any | Standard re-auth flow. |

On any error, **leave the editor untouched** (don't partially apply anything) and keep the
user's text so they can edit and retry.

---

## 4. Sequencing notes / edge cases

- **Always send the freshest `current_values`** — read the editor state at the moment the user
  clicks Generate, not a stale snapshot. The AI is told to start from those values and only
  change what the instruction mentions, so stale input leads to surprising overwrites.
- The AI returns the **complete** values dict (all fields), so the response replaces the editor
  values wholesale — don't merge it field-by-field on the client.
- Transcription and the fill call are independent requests. If the user edits the transcription
  text before clicking Generate, that edited text is what gets sent — good.
- ParamSet `__item_id`s: if you send them on existing rows, the AI is instructed to preserve
  them verbatim; rows it adds won't have one, but the server mints ids for any row missing one
  before returning — so the response always has stable ids.
- Calling fill on a SUBMITTED form just pre-fills the editor; status is unaffected until the
  user saves (and re-saving a SUBMITTED form keeps it SUBMITTED, per the existing save rules).
- No new permissions/roles — same access check as the rest of the API.
- Concurrency: disable the button while a request is in flight; if two fire anyway, last
  response wins, never apply two.
- Languages: both transcription and the fill work in many languages (French, Spanish, …);
  Whisper auto-detects, GPT handles the instruction in whatever language it's in. Enum/option
  matching is most reliable when the instruction's language is close to the form's field labels
  (which are in whatever language the template author wrote), but cross-language matching
  usually works.

---

## 5. Minimal client contract (pseudo-types)

```ts
// (voice only) transcribe — generic, reusable for any AI feature
POST /ai/transcribe-audio   (multipart/form-data)
fields: { file: Blob /* audio, <=10MB */ }
-> 200 { text: string } | 4xx/5xx { /* error with message */ }

// the form AI action — text in, renderable form out
POST /form/{id}/fill-from-text
body: { text: string; current_values?: Record<string, any> }
-> 200 FormSaveResultDTO | 4xx { /* error with message */ }

// then, when the user is happy (UNCHANGED, existing flow):
POST /form/{id}/save
body: { values, status_transition? }
```

A reusable client helper, roughly:

```ts
async function aiInstruction(input: { mode: 'text'; text: string } | { mode: 'voice'; audio: Blob }) {
  if (input.mode === 'voice') {
    const { text } = await postMultipart('/ai/transcribe-audio', { file: input.audio });
    return text; // show in editable box, let user confirm/edit
  }
  return input.text;
}
// then: fillFormFromText(formId, await aiInstruction(...), currentValues)
```

---

## 6. Out of scope (this iteration)

- Streaming/partial fills, multi-turn refinement ("no, change only the weight").
- Server-side persistence of the AI suggestion or an audit trail of AI-assisted fills.
- Field-level "ask AI for just this field" — current API fills the whole form.
- A generic `POST /ai/action/{name}` dispatcher — actions stay explicit per-feature endpoints
  that all happen to follow the `{ text, ...context } -> result` shape; only transcription is
  generalized.
- Forcing a transcription language / passing a `language` hint to Whisper.
- OpenAI structured-output (`response_format`) — backend uses prompt-engineered JSON for now
  (matches the codebase convention); behaviour from the frontend's side is unaffected if/when
  that changes.
