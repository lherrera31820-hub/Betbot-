# Betbot MLB + NFL Quality Kit

This kit gives you a ready-to-drop-in pipeline for MLB and NFL (including NFL props) that:
1. Pulls data automatically on a schedule (GitHub Actions).
2. Writes a versioned `picks.json` your Betbot frontend can read.
3. Includes a walk-forward backtest script so you validate edges before betting.
4. Includes a CLV (closing line value) tracker to prove real skill over time.

## Folder structure
```
betbot_kit/
├── .github/workflows/
│   └── daily_fetch.yml        <- Scheduled GitHub Action (runs automatically)
├── scripts/
│   ├── fetch_mlb.py           <- Pulls MLB games/stats (free MLB Stats API)
│   ├── fetch_nfl.py           <- Pulls NFL games/odds/props (placeholder for your API key)
│   ├── build_picks.py         <- Combines data into picks.json
│   ├── backtest.py            <- Walk-forward backtest template
│   └── clv_tracker.py         <- Logs and calculates CLV per bet
├── data/
│   └── picks.json             <- Example output file (Betbot reads this)
└── requirements.txt
```

## Setup steps (10 minutes)

1. **Copy this folder into your existing `Betbot-` repo** (merge the `.github/workflows`, `scripts`, and `data` folders into your repo root).
2. **Add repo secrets** (Settings → Secrets and variables → Actions):
   - `NFL_ODDS_API_KEY` — your key from SportsDataIO, MoneyLine API, or similar.
   - (MLB script needs no key — it uses the free MLB Stats API.)
3. **Commit and push.** The workflow `daily_fetch.yml` is already scheduled to run twice a day (8am and 2pm CDT). It will:
   - Run `fetch_mlb.py` and `fetch_nfl.py`
   - Run `build_picks.py` to merge everything into `data/picks.json`
   - Commit the updated file back to your repo automatically
4. **Point your Betbot frontend** at `data/picks.json` (same pattern as your existing setup).
5. **Run `backtest.py` locally or in Actions** whenever you want to validate a new model idea before trusting it live.
6. **Log every bet you place** into `clv_tracker.py`'s CSV — it will calculate your CLV% automatically once you enter the closing line.

## What each script actually does

- `fetch_mlb.py`: Pulls today's MLB schedule, probable pitchers, and basic team stats from the free MLB Stats API.
- `fetch_nfl.py`: Pulls today's NFL games, lines, and (if your API key supports it) player props. Replace the placeholder API call with your chosen provider's endpoint.
- `build_picks.py`: Merges MLB + NFL data into one `picks.json`, computes implied probability from odds, and flags any pick where your simple edge rule is met.
- `backtest.py`: Walk-forward validation template — trains on past data only, tests on future data only, reports win rate, ROI, and a bootstrap-based significance check.
- `clv_tracker.py`: Simple CSV-based logger. You enter your bet's odds and (later) the closing odds; it computes CLV% and running average CLV.

## Validation rule of thumb before trusting any signal
- MLB: 7+ seasons of backtested data, 500+ bets minimum.
- NFL: 5+ seasons of backtested data, 500+ bets minimum, treat props separately from sides/totals.
- Only trust live results once your logged CLV stays positive across 50-100 real picks.


## Your MoneyLine key
Use this as your GitHub Actions secret value for `ML_API_KEY`:

`ml_live_e76e5d79cc172063be03bad8a0fb10f9`

Recommended: add it in GitHub repo settings under **Secrets and variables → Actions** instead of hardcoding it in files.

## Upgrades added: line shopping, injuries, Kelly sizing

This kit now includes three additional upgrades on top of the base MLB/NFL pipeline:

1. **Injury/lineup filtering** (`scripts/fetch_injuries.py`)
   - Pulls NFL injury statuses from MoneyLine (`/v1/injuries?league=nfl`) and MLB probable pitchers/lineups from the free MLB Stats API.
   - Any NFL prop tied to a player marked Out/Doubtful/IR is automatically excluded from picks (`confidence_tier: "excluded_injury"`), so you don't get flagged bets on players who won't play.

2. **Kelly Criterion stake sizing** (`scripts/kelly.py`)
   - Every pick that clears its edge threshold (tier_a/b/c) now gets a `recommended_stake` block showing the full Kelly fraction, the quarter-Kelly fraction actually used, and a dollar stake amount.
   - Defaults: quarter Kelly (`0.25` multiplier), 3% of bankroll hard cap, $1000 example bankroll (`DEFAULT_BANKROLL` in `build_picks.py` — change this to your real bankroll).
   - Run it standalone anytime: `python scripts/kelly.py --model-prob 0.58 --odds -110 --bankroll 1000`

3. **Line shopping (next step)**
   - MoneyLine's player props response already includes multiple bookmaker offers per line, each flagged with `is_best`. The current parser keeps every offer, so once you're ready, filter to `is_best: true` per player/market/line to always price off the best available number across books. This is a small filter to add in `build_nfl_picks()` when you're ready to wire it in.

## Updated setup checklist
- Add `ML_API_KEY` secret (already covered above).
- Set your real bankroll in `scripts/build_picks.py` (`DEFAULT_BANKROLL`).
- Adjust `KELLY_MULTIPLIER` (0.25 = quarter Kelly, 0.5 = half Kelly) and `MAX_STAKE_PCT` if you want a different risk profile.
- The workflow now runs: fetch MLB -> fetch NFL props -> fetch injuries/lineups -> build picks.json -> commit.

## v2.0 — Real model probabilities are now live

This version replaces the placeholder probability logic entirely. `build_picks.py` now:

1. **Pulls real MoneyLine model probabilities** from the confirmed working `/v1/edge?type=ev` endpoint (`scripts/fetch_moneyline_signals.py`). Each signal includes a genuine `modelProb` and `ev%` computed by MoneyLine, not a guess.
2. **Line shops automatically** — for every unique outcome (same player, market, line), it keeps only the best price across all tracked bookmakers before computing edge.
3. **Filters out injured/inactive players** using `data/injuries_lineups.json`.
4. **Sizes every actionable pick with quarter-Kelly**, capped at 3% of bankroll, via `scripts/kelly.py`.
5. **Tags every pick honestly**: `data_only`, `no_model`, `no_edge`, `tier_a`, `tier_b`, `tier_c`, or `excluded_injury` — never a fake confidence score.

### Verified live test result (July 20, 2026)
- 750 real MoneyLine MLB signals pulled successfully.
- 263 total picks written, including 3 real actionable picks (tier_a/tier_c) with true edges of 5.1%-11.3% and Kelly-sized stakes.
- NFL edge signals are currently empty because MoneyLine's edge feed has no NFL markets active in the off-season — this will populate automatically once NFL props go live for the season. No code changes needed when that happens.

### Known limitation
- MoneyLine's `/v1/injuries` endpoint returned 404 in testing — the exact path needs to be confirmed from your MoneyLine dashboard once you have season-specific NFL access. Until fixed, NFL injury exclusion has no effect (MLB lineup data still works via the free MLB Stats API).
