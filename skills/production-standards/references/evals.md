# LLM-eval standards

Distilled from Anthropic eval docs + "Demystifying evals for AI agents" +
"A statistical approach to model evaluations", Zheng et al. 2023
(arXiv:2306.05685), tau-bench (arXiv:2406.12045), Zhou et al. 2023
(arXiv:2311.01964), OpenAI evals guide, and Google SRE canarying. Rule IDs
are stable — cite them when flagging. Sources verified in
`.vibe/research/2026-07-14-evals-standards.md`.

## The suite

- **EV-1 (MUST)** A golden set exists before the feature ships — "20-50
  simple tasks drawn from real failures is a great start"; house
  discipline: it lives in version control so EV-4 is reproducible.
  Prevents vibes-driven "it seems better" [Anthropic define-success +
  agent-evals; OpenAI evals-as-BDD].
- **EV-6 (MUST)** Golden sets stay out of prompts, few-shots, and
  training material; hold out a slice. A model that has seen the test item
  scores inflated and "unreliable" [Zhou et al. 2023; Anthropic held-out
  criterion].
- **EV-9 (MUST)** Every production failure becomes an eval case —
  "converting user-reported failures into test cases ensures your suite
  reflects actual usage". Prevents repeat incidents [Anthropic
  agent-evals, "eval-driven development"].

## Grading

- **EV-2 (MUST)** Grade with the most deterministic check available —
  "automate when possible", "volume over quality"; an LLM judge only where
  code cannot grade, and then calibrated against human experts [Anthropic
  define-success + agent-evals].
- **EV-3 (MUST)** LLM-judge hygiene: swap answer positions and require
  agreement in both orders; control verbosity and self-preference bias; a
  structured rubric per criterion [Zheng et al. 2023 — position,
  verbosity, self-enhancement biases].
- **EV-5 (MUST)** Report uncertainty before declaring a win: standard
  errors/CIs on scores, paired differences for A-vs-B, power analysis for
  suite size. A single-run delta is a coin flip [Anthropic statistical
  approach to evals].
- **EV-8 (SHOULD; MUST when the promise is reliability)** Measure pass^k
  (all k trials succeed), not pass@k (any one succeeds) — "pass@k for
  tools where one success matters, pass^k for agents where consistency is
  essential" [tau-bench; Anthropic agent-evals].

## The gate

- **EV-4 (MUST)** Every prompt, model, or tool change runs the suite
  before ship — "running on each agent change and model upgrade as the
  first line of defense". A prompt edit is an untested code change until
  evaled [Anthropic agent-evals; OpenAI].
- **EV-7 (MUST)** Offline pass is not a live pass: pair the suite with
  production monitoring and staged/canary rollout, especially on model
  swaps ("one-shot coding evals didn't capture the gains"; canarying =
  partial, time-limited, evaluated deployment) [Anthropic agent-evals +
  migration guide; Google SRE Workbook ch. 16].

## Examples

Bad (violates EV-4, EV-5): edit the system prompt, run one favorite query,
ship because "it looks better".

Good:

    make eval        # golden set, code-graded where possible
    # report: 84% -> 89% (n=120, paired diff +5.0pp, 95% CI [1.8, 8.2])
    # then canary 5% of traffic for a day before full rollout

Bad (violates EV-3): one judge call, fixed answer order, no rubric — the
judge favors the longer answer and its own outputs.
