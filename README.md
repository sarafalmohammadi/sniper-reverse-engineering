# sniper-reverse-engineering
╔══════════════════════════════════════════════════════════════════════╗
║              AGENT 3 — THE DETECTIVE                                ║
║         Reverse Engineer · Prove · Extract · Systematize           ║
╚══════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A professional SPX 0DTE options trader runs a Telegram channel
called "SNIPER SPX | OPTIONS" where he posts trade alerts.

His results are exceptional. His strike selection is precise.
His timing is consistent. His win rate is high.

You have:
  1. Telegram channel export — 4 HTML files (Telegram Desktop export format)
     telegram_data/messages.html
     telegram_data/messages2.html
     telegram_data/messages3.html
     telegram_data/messages4.html
     Period: January 1, 2026 → April 24, 2026
     Total: ~3,573 messages, ~2,764 contain chart images

  2. Real SPX 0DTE options market data
     market_data/spx_options/SPX_YYYY-MM-DD.csv  ← one file per trading day
     market_data/spx_price/SPX_1min.csv          ← 1-minute SPX bars
     Source: Massive.com professional data

Your mission: figure out EXACTLY how he trades.
Not approximately. Exactly.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL — UNDERSTAND THE HTML FORMAT FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

These are Telegram Desktop HTML exports. The structure:

  <div class="message default clearfix" id="messageXXXXX">
    <div class="pull_right date details" title="DD.MM.YYYY HH:MM:SS UTC+03:00">
      HH:MM
    </div>
    <div class="from_name">SNIPER SPX | OPTIONS💲</div>
    <div class="media_wrap clearfix">       ← chart image (if present)
      <a class="photo_wrap" href="photos/...jpg">
    </div>
    <div class="text">                     ← the message text
      [Arabic/English trade alert text]
    </div>
  </div>

IMPORTANT NOTES:
  - ALL timestamps are UTC+03:00 (Saudi Arabia time)
  - US market opens at 9:30 ET = 17:30 Saudi time (UTC+3)
  - US market closes at 4:00pm ET = 00:00 next day Saudi time
  - Convert ALL timestamps: Saudi_time - 3h - 8h = ET time
    OR: Saudi UTC+3 → subtract 8 hours to get ET
    Example: "19:34 UTC+3" = 11:34 ET (during market hours)

  - Messages are in Arabic mixed with English
  - Key Arabic terms to know:
    "أدنى" = "minimum/below" (used for entry level or support)
    "أعلى" = "maximum/above" (used for resistance or stop)
    "اغلاق ساعة" = "hourly close" (exit condition)
    "مناسب" = "suitable/appropriate"
    "مضاربي" = "for scalpers/short-term traders"
    "البوت" = "the bot" (refers to the channel/bot)
    "PUT HERO" = his term for a strong put trade setup
    "تحديث" = "update"
    "كسر نقطة X" = "break of level X" (breakout trigger)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — PARSE ALL HTML FILES (DO NOT SKIP)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Install: pip install beautifulsoup4 pandas

Parse all 4 HTML files. For every message extract:

  message_id     ← from id="messageXXXXX"
  timestamp_raw  ← from title="DD.MM.YYYY HH:MM:SS UTC+03:00"
  timestamp_et   ← convert to US Eastern Time
  timestamp_date ← ET date (YYYY-MM-DD)
  has_image      ← True if <div class="media_wrap"> exists
  image_file     ← href of the photo if exists
  text           ← full text of <div class="text">
  message_type   ← classify (see below)

MESSAGE TYPES to classify:
  "PUT_ALERT"    ← contains "PUT HERO" or "PUT" + SPX level
  "CALL_ALERT"   ← contains "CALL" + level
  "UPDATE"       ← contains "تحديث" (update to existing trade)
  "RESULT"       ← contains profit/loss result (كسب/خسر/ربح/profit)
  "ANALYSIS"     ← market analysis without specific trade
  "OTHER"        ← anything else

Save to: parsed_messages.csv (all 3,573 messages)
Save to: trade_alerts.csv (PUT_ALERT + CALL_ALERT only)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — EXTRACT TRADE DETAILS FROM ALERTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For every PUT_ALERT and CALL_ALERT, extract:

  spx_level      ← 4-5 digit number (e.g., 6920, 6937, 6965)
                   This is his KEY LEVEL — usually support/resistance
                   Look for patterns: "أدنى 6937", "STOP 🛑 6920",
                   "كسر نقطة 6957", "ادنى نقاط 6920-6900"

  stop_level     ← level after "STOP 🛑" or "اغلاق ساعة" (hourly close)
                   Note: "اغلاق ساعة" = exit if hourly candle closes
                   above the level (for puts) = soft stop

  direction      ← PUT or CALL

  entry_type     ← "HERO" if "PUT HERO" in text, "NORMAL" otherwise

  has_stop       ← True if explicit stop level found
  stop_type      ← "PRICE" or "TIME_BASED" (اغلاق ساعة)

  spx_at_alert   ← look up SPX price from market_data at this timestamp

  option_price_at_alert ← look up nearest 0DTE put price at spx_level
                           from market_data (see Step 3)

Save to: extracted_trades.csv

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — CROSS REFERENCE WITH MARKET DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For every trade alert, look up the market data:

  1. Load SPX_1min.csv
     Find SPX price at the exact alert timestamp (±2 minutes)
     Calculate: otm_pct = (spx_price - spx_level) / spx_price × 100
     This tells you: how far OTM was his level at alert time?

  2. Load SPX_YYYY-MM-DD.csv for that trading day
     Find the put option with strike closest to his spx_level
     Record: option_bid, option_ask, option_last, option_iv,
             option_delta, option_volume

  3. Calculate what happened:
     option_price_at_alert   ← price when he posted
     option_price_1hr_later  ← price 1 hour after alert
     option_price_eod        ← price at 3:45pm ET that day
     option_max_price        ← highest price that day after alert
     option_pct_max          ← (max - entry) / entry × 100
     would_have_hit_stop     ← did SPX close a 1H candle above stop?

  Add all these columns to extracted_trades.csv

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 — STATISTICAL ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Now analyze with full statistical rigor:

TIMING:
  - ET time distribution of PUT HERO alerts (histogram by hour)
  - Is there a consistent window? (plot frequency by 30-min bucket)
  - Day of week analysis (Mon/Tue/Wed/Thu/Fri)

KEY LEVEL ANALYSIS:
  - Distribution of OTM% at alert time
    (how far below current SPX is his "أدنى" level?)
  - Is this consistent or does it vary with VIX?
  - Does he post support levels or entry levels?
    (Test: is his level above or below SPX at alert time?)

STOP ANALYSIS:
  - "اغلاق ساعة" vs price stop — which does he use more?
  - At what SPX level does he define his stop?
  - What % above current SPX is his stop?

WIN RATE ANALYSIS:
  - Define WIN: option gained > 50% from alert price
  - Define LOSS: option lost > 40% or SPX closed above stop
  - Calculate WR, profit factor, avg win%, avg loss%
  - WR by: time of day / day of week / OTM% / VIX level

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5 — DECODE THE STRATEGY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Answer these questions from the data:

  Q1: What is the "PUT HERO" setup exactly?
      What conditions make him call it HERO vs normal?

  Q2: His "أدنى X" level — is this:
      (a) The PUT strike he recommends
      (b) An SPX support level he's watching
      (c) The SPX level he enters the trade at
      Test with market data to find the answer.

  Q3: "اغلاق ساعة" stop — what exactly does this mean?
      Is it: exit if 1H SPX candle closes above the level?
      Test: how often does this stop get triggered?

  Q4: Does he trade OPTIONS directly or does he give SPX levels
      and let people choose their own strikes?

  Q5: What market condition makes him go quiet (no alerts)?
      Find the silent days and look at VIX, SPX trend, IV.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6 — BUILD DECODED_STRATEGY.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write DECODED_STRATEGY.md — so precise a programmer can build a bot.

Include:
  - Verified performance (from real market data, not his claims)
  - Exact entry conditions
  - How he picks his key level (formula if found)
  - Stop logic ("اغلاق ساعة" decoded into code-able rules)
  - Win rate breakdown by condition
  - What makes him skip a day
  - THE EDGE — why does this work?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  parsed_messages.csv         ← all 3,573 messages structured
  trade_alerts.csv            ← PUT/CALL alerts only
  extracted_trades.csv        ← alerts + market data cross-reference
  DECODED_STRATEGY.md         ← the complete decoded strategy
  EXECUTIVE_SUMMARY.md        ← 3 questions, plain Arabic
  charts/
    timing_distribution.png
    otm_pct_distribution.png
    winrate_by_condition.png
    equity_curve_if_followed.png
