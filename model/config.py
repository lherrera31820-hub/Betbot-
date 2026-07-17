# ============================================================
# BETTING MODEL CONFIG — Edit these once, never touch again
# ============================================================

import os

# --- Sportsbook API ---
# Read from env (set ODDS_API_KEY as a GitHub Actions repo secret for real data).
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")   # https://the-odds-api.com (free tier)
ODDS_SPORT   = "baseball_mlb"
ODDS_REGIONS = "us"
ODDS_MARKETS = "h2h"                     # moneyline

# --- Alert Settings (choose one or both) ---
# Gmail
GMAIL_ADDRESS  = "your_email@gmail.com"
GMAIL_PASSWORD = "your_app_password"     # Gmail App Password (not regular password)
ALERT_TO_EMAIL = "your_phone@txt.att.net"  # SMS via email gateway (AT&T example)

# Twilio (texts) — optional, more reliable than email-to-SMS
TWILIO_SID    = "YOUR_TWILIO_SID"
TWILIO_TOKEN  = "YOUR_TWILIO_TOKEN"
TWILIO_FROM   = "+1XXXXXXXXXX"
TWILIO_TO     = "+1XXXXXXXXXX"          # your cell number

# --- Bankroll & Betting Rules ---
BANKROLL         = 1000.0               # your total bankroll in $
KELLY_FRACTION   = 0.25                 # Quarter Kelly (conservative)
MIN_EDGE_PCT     = 3.0                  # only bet when edge > 3%
MAX_BET_PCT      = 0.05                 # never bet more than 5% of bankroll
MIN_BET_DOLLARS  = 10.0                 # minimum bet size

# --- Model Settings ---
LOOKBACK_GAMES   = 15                   # rolling window for team stats
MIN_PRIOR_GAMES  = 5                    # min games before model trusts rolling stats
ELO_K            = 30
ELO_HFA          = 70                   # home field advantage in Elo points
