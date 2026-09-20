# Phase 12 — Responsible AI Evaluation

## AI WasteWise

This document evaluates the system against the five Responsible AI
principles named in the original project brief: Fairness, Transparency,
Ethics, Privacy, and Uncertainty. Every claim below is grounded in what
has actually been built and tested (Phases 5–10) — where testing is
incomplete, that's stated plainly rather than assumed.

---

## 1. Transparency

**Principle:** the system should make clear that its output is
AI-assisted, and explain its reasoning rather than acting as a black box.

**What's implemented:**
- Every classification traces to an explicit, inspectable rule (Phase 6's
  material→category mapping table), not an opaque model decision. This
  can be shown and explained line-by-line in an interview.
- Every disposal recommendation carries a `grounded_in_sources` flag and
  a list of the actual source documents used (Phase 7). The user sees
  exactly which of the 3 real government documents informed the answer —
  never an unsourced claim presented as fact.
- The frontend footer explicitly states: *"AI-assisted classification —
  recommendations are grounded in the sources shown above, not
  guaranteed accurate for every case."*
- When the knowledge base doesn't cover an item (e.g. the glass bottle
  test), the system says so via `coverage_note` instead of hiding the
  gap.

**Evidence:** the plastic bottle test showed all 3 sources cited
correctly; the glass bottle test showed `grounded_in_sources: false`
with an honest explanation, confirmed via real screenshots.

**Limitation:** the *classification* step (Phase 6) itself isn't shown
to the end user in the UI — only the final recommendation and its
sources are. A future version could expose the classification reasoning
too, not just the RAG grounding.

---

## 2. Uncertainty

**Principle:** the system must not present confident-looking answers
when it can't reliably identify or classify something.

**What's implemented:**
- Phase 5's prompt explicitly instructs the model to report low
  confidence and describe *why* (blur, ambiguity, poor lighting) rather
  than guess.
- Phase 6 has a hard rule: any image flagged `image_is_clear: false`
  routes straight to "Uncertain/Needs Verification" — classification is
  skipped entirely rather than attempted on bad input.
- Separately, Phase 7's RAG layer has its *own* uncertainty signal:
  `grounded_in_sources`. This means the system can be confident about
  *what* an item is, but honest about *not knowing* how to dispose of it
  if the knowledge base doesn't cover it. These are two independent,
  intentional uncertainty checks — not one blanket "confidence score."

**Evidence:**
- The glass bottle test is the clearest proof point: the system
  correctly identified the item (high confidence) but correctly flagged
  the *disposal advice* as ungrounded, rather than inventing plausible
  glass-disposal instructions the way a plain LLM call would.
- The composite sorting-bins graphic test revealed a *different* kind of
  uncertainty gap: the system has no check for whether an image is a
  real photo versus an illustrative diagram. It classified all 7 items
  in the graphic correctly, but presented that with the same confidence
  it would give a real photo — which is misleading in a different way.
  This is logged as an open limitation, not fixed yet.

**Not yet fully tested:** the blurry-image path was confirmed working
in isolated script testing (Phase 5/6) but not yet re-confirmed through
the full frontend→backend flow end-to-end. This is flagged as
outstanding in the Phase 11 test log.

---

## 3. Privacy

**Principle:** don't unnecessarily collect, store, or expose personal
information.

**What's implemented:**
- The analytics database (Phase 10) stores only: detected item name,
  waste category, a grounded/ungrounded flag, an uncertain/not flag, and
  a timestamp.
- It explicitly does **not** store: the uploaded image itself, any user
  identifier, IP address, or session data. There is nothing in the log
  that connects a record back to a specific person.
- Uploaded images are written to a temporary file only for the duration
  of one request (Phase 8's backend) and deleted immediately after
  processing (`os.unlink` runs even if an error occurs, via a
  `finally` block) — images are never persisted to disk long-term.

**Evidence:** confirmed via direct code review of `analytics_db.py` and
`main.py`; the dashboard screenshot shows only aggregate counts and
category names, nothing item-specific to a person.

**Limitation:** the Gemini API itself is a third-party service — images
are sent to Google's servers for processing, which is disclosed here but
not yet surfaced to the end user in the UI itself. A production version
should say this explicitly in the interface, not just in project docs.

---

## 4. Ethics

**Principle:** don't provide unsafe disposal recommendations.

**What's implemented:**
- Recommendations are grounded *only* in real government (CPCB / SWM
  Rules 2026) guidance — not invented advice. This directly reduces the
  risk of unsafe suggestions, since the source material itself is
  authoritative and was written with safety in mind (e.g. explicit
  "don't burn plastic," "don't mix sanitary waste" instructions carried
  through from the source documents).
- The system is explicitly instructed (Phase 7's prompt) not to
  supplement retrieved passages with the model's own general knowledge —
  reducing the chance of a plausible-sounding but wrong or unsafe
  suggestion slipping in.

**Not yet tested:** there is no dedicated adversarial test yet for
whether the system could be prompted or tricked into giving unsafe
advice (e.g. via a misleading image or unusual item). This is worth
adding to Phase 11 testing before claiming this is fully verified —
right now it's a design-level safeguard, not an empirically tested one.

---

## 5. Fairness

**Principle:** test across different items, backgrounds, lighting, and
image quality.

**What's been tested so far:**
- Clear, well-lit single item (plastic bottle) — correct.
- A different material class (glass) — correctly identified, honestly
  flagged as ungrounded for disposal advice.
- A complex composite image (7 items in one frame) — correctly split
  and classified per-item.
- Blurry image handling — confirmed at the script level.

**Not yet tested (real gap, not hidden):**
- Paper/cardboard, metal, food/organic waste, and e-waste individually
  through the full app.
- Different lighting conditions (dark photo) through the full app.
- A *real* multi-item photo (not a graphic).
- Out-of-scope, non-waste images (e.g. a photo of a person).

This is an honest, incomplete picture — fairness testing is ongoing as
of this document, tracked in `test_log_template.md`. Claiming full
fairness validation before this table is filled in would violate the
project's own rule against claiming unmeasured accuracy.

---

## Summary table

| Principle | Status | Confidence in claim |
|---|---|---|
| Transparency | Implemented and evidenced | High — directly observed in test outputs |
| Uncertainty | Implemented, two independent mechanisms evidenced | High for tested cases; blurry-path needs full-stack re-confirmation |
| Privacy | Implemented, verified by code review | High |
| Ethics | Design-level safeguard in place | Medium — not adversarially tested yet |
| Fairness | Partially tested | Medium-low — real gap, testing ongoing |

This honesty about what's proven versus what's designed-but-untested is
itself part of demonstrating Responsible AI practice — not a weakness to
hide in the final documentation or interview.
