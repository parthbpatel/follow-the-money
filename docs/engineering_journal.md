# FOLLOW THE MONEY – ENGINEERING JOURNAL

## Milestone 1 – Local AI Setup

Problem:
Needed a zero-cost LLM solution.

Decision:
Use Ollama + Qwen3:4b.

Reason:

* Free
* Runs locally
* No OpenAI costs
* Portfolio friendly

Result:
Successful.

Lessons:
Local inference is slower than cloud APIs.

---

## Milestone 2 – Reuters RSS Failure

Problem:
Reuters RSS returned 0 headlines.

Evidence:
Logs showed:

Fetched 0 Reuters headlines

Root Cause:
Reuters RSS endpoint deprecated/unreliable.

Decision:
Replace Reuters RSS with Tavily Search.

Result:
24 real news items collected.

Lessons:
Do not rely on a single RSS feed.

---

## Milestone 3 – Hallucinated Reports

Problem:
Report generated fake dates and fake macro statistics.

Examples:

* October 2024 report date
* Invented Fed statistics
* Invented oil market events

Root Cause:
Insufficient grounding.

Decision:
Add Tavily Search.

Result:
Report now references real sources.

Lessons:
LLMs analyze data well.
LLMs generate facts poorly.

---

## Milestone 4 – Framework Ignored

Problem:
Model generated essays instead of Follow The Money framework.

Root Cause:
Context overwhelmed instructions.

Decision:
Add framework validation and retry logic.

Result:
Framework sections now appear.

Lessons:
Prompting alone is insufficient.
Validation layers are required.

---

## Current Bottlenecks

1. Context Compression
2. Structured Macro Data
3. Date Injection
4. Source Attribution
5. Faster Generation
6. Better Search Queries

---

## Next Milestone

Build Context Summarizer.

Goal:

22544 chars
↓
3000–5000 chars

Expected Impact:

Generation:
40 min
↓
2–5 min

Quality:
Higher

Hallucinations:
Lower
