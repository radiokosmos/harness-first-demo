# Reflections

One line per mistake worth learning from — JSONL, one file per month. Appended
after a review, an incident or a failed run. `bin/reflections-report` groups
them; a class seen twice in a repo (or three times anywhere) is a candidate
for an automated check.

```json
{"date":"2026-10-14","repo":"demo","severity":"major","class":"edge-case",
 "finding":"one sentence: what went wrong",
 "caught_by":"what caught it","missed_by":"what should have",
 "candidate_check":"the mechanical check that would catch it, or none",
 "promoted":""}
```

Rules: describe, don't paste data (no PII). No one-off typos — the bar is
"could this happen again". Never edit a line afterwards, except to fill `promoted`.
