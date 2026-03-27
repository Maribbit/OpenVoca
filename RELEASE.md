# Release Guide

This project uses a single repository-level version in `VERSION`.

## Current Version Source
- `VERSION` is the single source of truth.
- Keep package metadata in sync:
  - `frontend/package.json` -> `version`
  - `backend/pyproject.toml` -> `[project].version`

## Release Steps
1. Run full local checks.

```bash
cd frontend
pnpm run check

cd ../backend
uv run ruff format --check .; uv run ruff check .; uv run pytest
```

2. Update version files.
- Bump `VERSION`.
- Sync the same version into frontend and backend package metadata.

3. Update release notes.
- Add a short summary of user-visible changes.
- Mention breaking changes explicitly.

4. Tag the release.
- Create a git tag like `v0.2.0`.

## Versioning Rule (SemVer)
- PATCH: bug fixes only.
- MINOR: backward-compatible features.
- MAJOR: breaking changes.

## v0.4.5

Date: 2026-03-27

### Highlights
- Refactored duplicate route logic: the two reading-sentence endpoints (`/api/reading-sentence` and `/api/reading-sentence/next`) now share a single `_generate_reading_response` helper for prompt building, Ollama calling, tokenization, and response construction.

### Backend
- Extracted `_generate_reading_response()` private async helper in `main.py`, eliminating ~25 duplicated lines.
- Each route retains only its unique word-selection strategy.
- No behavior changes; 38 tests still passing.

### Frontend
- No changes.

## v0.4.4

Date: 2026-03-27

### Highlights
- Added `lemma` field to `SentenceToken`, exposing spaCy's lemmatization (e.g., "running" → "run"). This unblocks dictionary integration and vocabulary normalization for upcoming features.
- Fixed POS-aware word marking in the frontend: clicking "well" (NOUN) no longer highlights a separate "well" (ADV) in the same sentence. The `markedWords` set now keys on `word/POS` instead of just the word string.

### Backend
- `SentenceToken` dataclass gains a `lemma: str | None` field, populated from `token.lemma_.lower()` for alphabetic tokens.
- `ReadingSentenceToken` Pydantic model updated to include `lemma` in API responses.
- Added `test_tokens_include_lemma` test (cats→cat, running→run, punctuation→None).
- 38 tests passing (16 tokenizer, 4 prompt builder, 18 integration).

### Frontend
- `ReadingSentenceToken` interface updated with optional `lemma` field.
- `markedWords` keyed on `text.toLowerCase()/pos` composite instead of plain text, preventing cross-POS highlight bleeding.
- Test fixture tokens updated with `pos` values for accurate assertions.
- 5 tests passing.

## v0.4.3

Date: 2026-03-27

### Highlights
- Fixed hyphenated target words (e.g., `*well-known*`) being silently dropped — the target regex now captures hyphens and splits compounds into sub-tokens for correct matching.
- Added missing endpoint tests for `/api/reading-sentence/next`, `DELETE /api/vocabulary`, and the 502 error path.

### Backend
- Expanded `_TARGET_PATTERN` regex to include hyphens in the character class.
- Added compound target splitting: hyphenated captures like "well-known" are decomposed into ["well", "known"] so each sub-token is correctly marked `is_target=True`.
- Added `test_hyphenated_target_word` to tokenizer tests.
- Added 3 new integration tests: `test_next_sentence_endpoint_picks_from_vocabulary`, `test_delete_vocabulary_endpoint`, `test_reading_sentence_returns_502_on_ollama_failure`.
- 37 tests passing (15 tokenizer, 4 prompt builder, 18 integration).

### Frontend
- No changes.

## v0.4.2

Date: 2026-03-27

### Highlights
- Replaced the static stopword list with POS-aware function-word filtering, fixing false positives where content words like "well" (noun), "can" (noun), "will" (noun), "shell" (noun) were incorrectly blocked.
- The system now uses spaCy's Universal POS tags to decide which tokens are non-clickable function words (DET, PRON, ADP, AUX, CCONJ, SCONJ, PART, NUM), making the filter context-aware.
- Removed ~200 lines of dead stopword entries (stripped contractions that never matched under spaCy tokenization).

### Backend
- Rewrote `stopwords.py`: replaced `ENGLISH_STOP_WORDS` word set with `FUNCTION_POS` frozenset of 8 Universal POS tags.
- Updated `tokenizer.py` to filter by POS tag instead of word string: `pos not in FUNCTION_POS`.
- Added 5 new regression tests covering ambiguous words (well/NOUN, can/NOUN, will/NOUN) and function-word POS filtering.
- 33 tests passing (14 tokenizer, 4 prompt builder, 15 integration).

### Frontend
- No changes.

### Breaking Changes
- Some high-frequency adverbs (e.g., "very", "also", "just") are now clickable. This is by design: false negatives (blocking real content words) are worse than false positives (allowing common adverbs).

## v0.4.1

Date: 2026-03-27

### Highlights
- Unified tokenization pipeline: replaced the two-stage regex+spaCy architecture with a single spaCy-based tokenizer that handles tokenization, POS tagging, target-word markup parsing, and stopword filtering in one pass.
- Added context-aware POS (part-of-speech) tagging to every word token, enabling the system to distinguish "leaves" (noun) from "leaves" (verb).
- Upgraded the vocabulary store to a composite `(word, pos)` primary key so that the same spelling with different parts of speech tracks independent familiarity.
- Added a POS column to the Stats page.

### Backend
- Rewrote `tokenizer.py` to use spaCy as the sole tokenizer. Regex is now only used to extract `*target*` markers from raw LLM output before stripping asterisks.
- Removed the `pos_tagger.py` module; its alignment logic is no longer needed.
- Updated `main.py` routes to call `tokenize_sentence()` directly instead of the former two-step `tokenize_sentence()` + `enrich_tokens_with_pos()`.
- Updated `word_store.py` with composite `(word, pos)` primary key on `WordRecord`.
- Updated `apply_feedback` to accept `(word, pos)` tuples; `pick_target_words` deduplicates by word string.
- 28 tests passing (9 tokenizer, 4 prompt builder, 15 integration).

### Frontend
- API types (`ReadingSentenceToken`, `FeedbackRequest`, `WordRecordOut`) now include `pos` fields.
- `HomeView` extracts `(word, pos)` pairs from tokens when submitting feedback.
- `StatsView` displays a POS pill badge column.
- i18n keys added for POS label (EN: "POS", ZH: "词性").
- 5 tests passing.

### Breaking Changes
- `POST /api/feedback` body now requires `targetWords` and `markedWords` as `[{word, pos}]` instead of `[string]`.
- `GET /api/vocabulary` response items now include a `pos` field.

## v0.4.0

Date: 2026-03-23

### Highlights
- Added backend stop-word filtering to reduce vocabulary noise from high-frequency structural words.
- Preserved model-driven target-word behavior using Markdown markers while ensuring marked targets remain clickable.
- Fixed reading text spacing for non-clickable word-like tokens and dash-like punctuation edge cases.
- Simplified the reading header by removing model label text and keeping settings access available in the top-right controls.
- Reached the planned Phase 1 objective: the full loop (pick words -> generate sentence -> mark words -> update familiarity) is stable and release-ready.

### Backend
- Added `backend/src/services/stopwords.py` with a static English stop-word set.
- Updated tokenizer logic to downgrade stop words to `isWord=false` while preserving explicit Markdown-marked targets as `isTarget=true`.
- Added tokenizer and API regression coverage for stop-word behavior and target-word override behavior.

### Frontend
- Updated sentence spacing logic to keep natural spacing for non-clickable but word-like tokens.
- Fixed dash-related spacing behavior for `-`, `–`, `—`, and `‑`.
- Removed the `gemma3:4b` header text while keeping the settings trigger discoverable and accessible.

### Breaking Changes
- None.

## v0.3.3

Date: 2026-03-23

### Highlights
- Added model-driven target-word annotation using Markdown emphasis markers instead of frontend word matching.
- Made sentence highlighting resilient to inflections, synonyms, empty target-word cases, and over-eager model annotations.
- Stripped Markdown marker characters from rendered reading text while preserving explicit target-word metadata.

### Backend
- Added fixed prompt instruction that requires the model to mark review words with Markdown emphasis.
- Updated the tokenizer to parse both `*word*` and `**word**` as target-word annotations and expose `isTarget` in token payloads.
- Added service and endpoint coverage for Markdown-marked target tokens and markup stripping behavior.

### Frontend
- Switched reading underline rendering to trust backend token metadata instead of matching target-word strings in the sentence.
- Kept rendered reading text free of raw `*` characters while preserving dotted underline cues on explicit target tokens.
- Added regression coverage for backend-provided `isTarget` rendering behavior.

### Breaking Changes
- `POST /api/reading-sentence` token items now include `isTarget` in the response contract.

## v0.3.2

Date: 2026-03-23

### Highlights
- Added configurable per-sentence review word count (1-5) in Preferences.
- Removed the frontend concept of initial target words from user settings.
- Kept target-word visual cues (dotted underlines) aligned with backend-selected words.

### Backend
- Updated reading sentence request schema to accept `targetWordCount` (1-5).
- Updated `/api/reading-sentence/next` to select vocabulary words with dynamic `limit=targetWordCount` instead of hardcoded 3.
- Kept `targetWords` as a compatibility fallback field for older clients.
- Ensured that a sentence is generated without target words if the vocabulary is empty, maintaining the original fallback behavior.

### Frontend
- Added a 1-5 slider in Preferences (`Words Per Sentence` / `单轮取词量`) and persisted it to local storage.
- Removed initial target words input and related validation in menu flow.
- Unified initial sentence load and next-sentence flow to the same backend endpoint for consistent vocabulary-first behavior.

### Breaking Changes
- None.

## v0.3.1

Date: 2026-03-22

### Highlights
- Improved reading clarity by reducing sentence size and line/letter spacing presets.
- Improved hold-to-continue affordance with a more visible centered capsule interaction.
- Added a persistent interface font-size control for system UI labels and controls.
- Added target-word visual cue in sentence rendering with dotted underlines.
- Clarified wording in preferences: target words are now labeled as initial target words.

### Backend
- No API contract changes.
- Confirmed next-sentence target-word strategy remains: vocabulary-first (least familiar), fallback to initial target words only when vocabulary is empty.

### Frontend
- Reworked next-sentence interaction UI from edge/footer hints to a centered capsule with progress and release feedback.
- Added interface size settings in menu and persisted selection to local storage.
- Updated target-word label and hint text in i18n messages for both English and Chinese.
- Added dotted underline cue for current target words in reading sentence tokens.

### Breaking Changes
- None.

## v0.3.0

Date: 2026-03-22

### Highlights
- Delivered the core learning loop for seen vocabulary: mark words in-context, submit feedback, update familiarity, and generate the next sentence from least-familiar words.
- Added a vocabulary stats page with familiarity levels and clear-all support.
- Upgraded "next sentence" into a safer hold-to-confirm interaction: users must hold and then release to advance.

### Backend
- Added persistent word familiarity storage with SQLModel in `backend/src/services/word_store.py`.
- Added `POST /api/reading-sentence/next` to pick target words from the vocabulary store.
- Added `POST /api/feedback` to apply familiarity updates from user markings.
- Added `GET /api/vocabulary` and `DELETE /api/vocabulary` for stats page data and reset.
- Added tests for familiarity boundaries, selection strategy, and clear-all behavior in `backend/tests/test_main.py`.

### Frontend
- Added word marking toggle in reading view and feedback submission on sentence advance.
- Added long-press confirmation flow for advancing sentences (right arrow, footer area, and Space key).
- Added progress feedback for hold interaction and clearer instructional text.
- Added stats route and vocabulary table UI in `frontend/src/views/StatsView.vue`.
- Expanded API typings and i18n strings for feedback, vocabulary, and new reading interaction prompts.
- Added frontend regression test for "hold complete + release to advance" behavior.

### Breaking Changes
- Added new backend endpoints: `/api/reading-sentence/next`, `/api/feedback`, `/api/vocabulary`.

## v0.2.0

Date: 2026-03-22

### Highlights
This version focuses on two things: simple tokenization and reading page settings.

### Backend
- Added a tokenizer service at `backend/src/services/tokenizer.py`.
- `POST /api/reading-sentence` now returns tokenized output (`tokens`) in addition to `sentence` and `words`.
- Added/updated tokenizer and endpoint tests in `backend/tests/test_main.py`.

### Frontend
- Updated reading API typing to consume backend tokens and render per-token content.
- Added an inline reading settings panel (size/spacing/theme) and click-outside-to-close behavior.
- Added page-level settings improvements:
  - Header interaction for the settings trigger.
  - Language and system font controls in MENU.
  - Reading theme support (light/dark) and UI theme variable updates.
- Expanded i18n text for settings labels and updated tests in `frontend/tests/HomeView.spec.ts`.

### Breaking Changes
- `POST /api/reading-sentence` response contract now includes a `tokens` field.

---

## v0.1.0

Date: 2026-03-22

### Highlights
- Delivered the Phase 1 minimal closed loop for sentence generation with local Ollama (`gemma3:4b`).
- Added a focused Reading page with Zen-style layout and single-sentence rendering.
- Added a Preferences menu to configure target words and generation prompt from the frontend.
- Moved prompt and target word ownership to the frontend and persisted settings with local storage.
- Added lightweight i18n support with automatic locale detection (`zh`/`en`) and manual language switch.

### Backend
- Added an Ollama integration layer for `/api/generate` calls.
- Added `POST /api/reading-sentence` to generate one sentence from frontend-provided words and prompt template.
- Added tests for Ollama request construction, payload validation, and endpoint behavior.

### Frontend
- Implemented Reading view with sentence request-on-load flow.
- Implemented Preferences overlay based on the design draft.
- Added i18n regression test for switching UI language and persisting locale.

### Breaking Changes
- None.
