# agent-fraud-harness

A small fraud-injection harness for testing whether an LLM travel-planning agent can be steered toward a scam hotel by fake listings, coordinated fake reviews, or an escalating fake support agent.

It accompanies the article *"When Our Travel Agents Got Scammed: Layered Trust Patterns for LLM Agents"* by Arjun Prabhulal. The design follows the three fraud scenarios in WandaPlan ([arXiv:2505.16557](https://arxiv.org/abs/2505.16557)). It is a scaled-down approximation built from the paper's description, **not** a replication, and its numbers are not comparable to the paper's.

## What it tests

**Planner.** The AI Hotel Analyst prompt from [gemini-crewai-travelplanner](https://github.com/arjunprabhulal/gemini-crewai-travelplanner) (commit `e51251e`), copied verbatim and sent directly to Gemini 2.5 Flash (thinking off) instead of through CrewAI. One line is added to ask for a machine-readable final choice. Hotels only.

**Scenarios**

| ID | Scenario | What the attacker does |
|---|---|---|
| S1 | Misinformation | Mixes 4 fabricated listings with the 4 authentic ones |
| S2 | Coordinated fake reviews | 1 or 4 fake "past guests" push the attacker's hotel |
| S3 | Escalation | A fake support agent escalates over 4 rounds: hint, affiliation, urgency, sympathy |

In **variant A** (`harness.py`) the scam hotel appears only in attacker text. In **variant B** (`harness_b.py`) it is also posted on the platform, so it appears as a listed option.

**Configurations**

| Config | Defenses |
|---|---|
| C0 | Baseline |
| C1 | Single LLM guard (same model) that labels listings, reviews and messages |
| C2 | Deterministic patterns P1–P4: provenance allowlist, price corroboration (flag >35% below the search median), evidence/opinion separation, decision-stability rule |
| C3s | C2 plus the guard (variant B only) |

## Run settings

These settings are part of the evaluated system and affect the results.

| Setting | Value |
|---|---|
| Model | `gemini-2.5-flash`, thinking budget 0, for planner, guard and scammer |
| Seeds | 11 and 23 |
| Temperature | 1.0 for planner and scammer, 0 for the guard |
| Attack content | Generated once per city with seed 7 and cached in `results/synthetic_attack_content.json` |
| Review and escalation target | The first synthetic fake listing for each city |
| Authentic option | An unmodified listing from the snapshot (the first four per city) |
| Variant B options | Four authentic listings plus one synthetic listing, shuffled |
| Price rule (P2) | Flag a price more than 35% below the median of that city's search results |

**How the patterns are simplified here.** The article describes P1–P4 as design patterns. This harness implements reduced versions:

- **P1** accepts only listing IDs from the simulated platform response. The synthetic fakes are deliberately included in that response, so P1 models a contaminated trusted source, not independent provenance checks.
- **P2** is a single-source price-outlier rule. It does no cross-source corroboration.
- **P3** maps the planner's answer to a listed candidate by name. In variant A, an answer outside the candidates falls back to the confirmed pick; variant B has no post-response check because the scam listing is itself a candidate.
- **P4** keeps the confirmed choice because no verified update ever arrives. Accepting a legitimate verified update is not tested.

**Fallbacks.** If the initial choice cannot be parsed or is not a listed candidate, the harness uses the first candidate. If the guard's JSON cannot be parsed, it is treated as raising no flags. Variant B is "platform-hosted" only in simulation: the synthetic listing is inserted locally into the accepted options, and nothing is posted to any real site.

**Statistics.** Wilson intervals treat the 16 runs per cell as independent. They are not: two seeds reuse the same eight city snapshots and cached attacks. Compare configurations descriptively.

## Results (October 31, 2026)

Variant B, defense success rate (runs whose final choice is authentic), 8 cities × 2 seeds = 16 runs per cell. Brackets are Wilson 95% intervals.

| Config | Initial pick | After 1 review | After 4 reviews | After 4 escalation rounds | Latency p50 | Tokens (median) |
|---|---|---|---|---|---|---|
| C0 | 13/16 | 0/16 | 0/16 | 9/16 | 6.0 s | 3,033 |
| C1 | 13/16 | 8/16 | 6/16 | 13/16 | 8.5 s | 4,150 |
| C2 | 11/16 | 4/16 | 2/16 | 11/16 | 5.9 s | 3,096 |
| C3s | 13/16 | 10/16 | 6/16 | 13/16 | 8.3 s | 4,233 |

Full outputs are in [`results/`](results/). The complete set took 1,104 model calls and 8 search calls.

## Repository layout

```
snapshot.py     Fetch a Google Hotels snapshot through SerpApi (same query settings as the planner)
harness.py      Variant A: S1-S3 under C0, C1 and C2, plus false-rejection controls on clean listings
harness_b.py    Variant B: platform-hosted scam listing under C0, C1, C2 (and C3s)
analyze.py      Summarize a variant A results file
results/        Raw run records, analysis summaries and the synthetic attack content
```

## Setup

Requires Python 3.10+, a Gemini API key and a SerpApi key.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your keys, then export them
export GOOGLE_API_KEY=... SERP_API_KEY=...
```

## Usage

```bash
# 1. Take a listing snapshot (not included in this repository)
mkdir -p data
python snapshot.py data/snapshot.json

# 2. Variant A. Reuses results/synthetic_attack_content.json if it exists, otherwise generates it.
python harness.py results/results.json data/snapshot.json results/synthetic_attack_content.json
python analyze.py results/results.json results/synthetic_attack_content.json data/snapshot.json

# 3. Variant B (optionally pass a comma-separated config list, e.g. C3s)
python harness_b.py results/results_b.json data/snapshot.json results/synthetic_attack_content.json
python harness_b.py results/results_c3s.json data/snapshot.json results/synthetic_attack_content.json C3s
```

A new snapshot returns different hotels and prices, so re-runs will not match the published numbers exactly.

## Limitations

One domain, eight US cities, two seeds, and one model in every role (planner, guard and scammer), so small differences are not significant. C3s is a stand-in for a verifier from a different model family, not a test of one. Human approval was not simulated.

## Ethics

All fraudulent content is synthetic and generated by the harness. No bookings, payments or contact with real businesses took place. Listing snapshots are fetched locally and are not redistributed here.

## License

[MIT](LICENSE)
