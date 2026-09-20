# Phase 11 — Test Log

Fill this in as you test each case through the app (frontend or /docs).
Be honest about failures — a documented limitation is more valuable to
your project than a hidden one.

## Already tested (from earlier sessions)

| # | Test case | Detected item | Category | Grounded? | Result |
|---|---|---|---|---|---|
| 1 | Plastic water bottle | plastic water bottle | Recyclable/Dry Waste | Yes | ✅ Correct |
| 2 | Glass bottle | glass bottle | Glass | No (honest gap) | ✅ Correctly flagged ungrounded |
| 3 | Composite sorting-bins graphic (multi-item) | 7 sub-items | mixed | mixed | ✅ Split correctly, but revealed the system doesn't detect "this is a diagram, not a real photo" |
| 4 | Blurry/unclear photo | — | Uncertain/Needs Verification | — | (confirm below) |

## Still to test

Fill in each row after you run the test. Leave "Result" as your honest
one-line verdict — correct / partially correct / wrong / interesting edge case.

| # | Test case | Detected item | Category | Grounded? | Result / notes |
|---|---|---|---|---|---|
| 5 | Paper or cardboard item | | | | |
| 6 | Metal can | | | | |
| 7 | Food/organic waste | | | | |
| 8 | Battery or small e-waste item | | | | |
| 9 | Blurry photo (confirm end-to-end through the app, not just the script) | | | | |
| 10 | Dark/poorly-lit photo | | | | |
| 11 | Real photo with 2-3 genuine physical items together (not a graphic) | | | | |
| 12 | A non-waste image (e.g. a photo of a person or a pet) — how does it behave on an out-of-scope input? | | | | |

## Questions to answer once the table is filled in

1. **Classification correctness:** across all clear single-item tests, how many were correctly categorized?
2. **Recommendation quality:** did the grounded recommendations make practical sense for each category?
3. **Uncertainty handling:** did blurry/dark/ambiguous images actually get flagged, or did any slip through as false-confident?
4. **Failure cases:** what genuinely went wrong, and why (as best you can tell)?
5. **Coverage gaps confirmed:** which categories lack real RAG grounding (we already know Glass and likely Metal/E-waste)?
6. **Out-of-scope handling:** what happened with the non-waste image test? Is this worth documenting as a known limitation?

This table becomes the evidence base for your Phase 12 (Responsible AI)
and Phase 14 (documentation) sections — don't discard it once you're done.
