---
description: Ask Perplexity to attack a hypothesis, then triage the criticism
argument-hint: <hypothesis id, e.g. H02>
---
1. Read `research/hypotheses/$ARGUMENTS*.md`.
2. Call `find_counter_evidence` with its statement, design and validation plan.
3. Also call `critique_strategy` with the experiment design.
4. Then follow `prompts/claude_critique_triage.md`. Save the critique summary to
   `research/critiques/$ARGUMENTS_<date>.md` and update the hypothesis file.
