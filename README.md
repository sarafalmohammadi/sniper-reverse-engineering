╔══════════════════════════════════════════════════════════════════════╗
║              AGENT 3 — THE DETECTIVE                                ║
║         Reverse Engineer · Prove · Extract · Systematize           ║
╚══════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SETUP — DO THIS FIRST BEFORE ANYTHING ELSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Install all required packages:
  pip install beautifulsoup4 pandas requests matplotlib seaborn mibian

API key is in environment variable: C5z3c4yphrBDGbIt3M0TqPJ0Ltu2Ekt4
Base URL: https://api.polygon.io
This is Polygon.io rebranded as Massive.com — same API, same endpoints.

CONFIRMED working endpoints (tested):
  ✓ SPY 1-min bars:   /v2/aggs/ticker/SPY/range/1/minute/{from}/{to}
  ✓ Options ref:      /v3/reference/options/contracts
  ✓ Options snapshot: /v3/snapshot/options/SPX
  ✗ I:SPX bars:       403 NOT_AUTHORIZED (plan limitation)
  ✗ I:SPX 1-min:      403 NOT_AUTHORIZED (plan limitation)

CONFIRMED option ticker format:
  O:SPX{YYMMDD}{P/C}{8-digit-strike×1000}
  Example: SPX put at strike 6920, expiring 2026-01-06:
  → O:SPX260106P06920000

CONFIRMED from test:
  reference/contracts with expiration_date returns 0 results for
  past dates — this endpoint is forward-looking only.
  Solution: build tickers manually using the format above.

SPX vs SPY:
  I:SPX is not available on current plan.
  Use SPY 1-min bars instead. SPY × 10 ≈ SPX (99.97% accurate).
  Sniper's levels are in SPX (e.g., 6920).
  Convert: spy_equivalent = spx_level / 10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR MISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A professional SPX 0DTE options trader runs a Telegram channel
called "SNIPER SPX | OPTIONS" since January 1, 2026.

His results are exceptional. His timing is consistent.
His win rate is high. His strike selection is precise.

You have:
  1. Telegram channel export — 4 HTML files
     telegram_data/messages.html    ← Jan 2026
     telegram_data/messages2.html   ← Feb 2026
     telegram_data/messages3.html   ← Mar 2026
     telegram_data/messages4.html   ← Apr 2026
     Total: ~3,573 messages

  2. SPY 1-min price bars (downloaded via API)
     Already available or download with:
       GET /v2/aggs/ticker/SPY/range/1/minute/2026-01-01/2026-04-24
       params: apiKey, limit=50000, sort=asc

  3. Individual SPX option prices (fetch per trade via API)
     Build ticker: O:SPX{YYMMDD}P{strike×1000 zero-padded to 8 digits}
     Fetch:  GET /v2/aggs/ticker/{option_ticker}/range/1/minute/{date}/{date}

Your mission: decode EXACTLY how he trades.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UNDERSTAND THE DATA — READ THIS CAREFULLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HTML STRUCTURE (Telegram Desktop export):
  <div class="message default clearfix" id="messageXXXXX">
    <div class="pull_right date details"
         title="DD.MM.YYYY HH:MM:SS UTC+03:00">HH:MM</div>
    <div class="from_name">SNIPER SPX | OPTIONS💲</div>
    <div class="media_wrap clearfix">  ← chart image (if present)
      <a class="photo_wrap" href="photos/photo_XXXXX.jpg">
    </div>
    <div class="text">[message text in Arabic/English]</div>
  </div>

TIMEZONE CONVERSION (critical):
  All timestamps = UTC+3 (Saudi Arabia)
  US Eastern Time = UTC+3 minus 8 hours
  Examples:
    "19:34 UTC+3" → 11:34 ET  (middle of US trading day)
    "21:00 UTC+3" → 13:00 ET  (1pm ET)
    "23:30 UTC+3" → 15:30 ET  (30min before close)
    "00:10 next day UTC+3" → 16:10 ET previous day (after close)

  US market hours in Saudi time: 17:30 - 00:00 (next day)

KEY ARABIC TERMS:
  "PUT HERO"      → his strongest put setup label
  "أدنى X"        → "below X" — key SPX support level to watch
  "أعلى X"        → "above X" — resistance or stop level
  "STOP 🛑 X"     → hard stop loss at level X
  "اغلاق ساعة"   → "hourly candle close" — soft time-based exit
                     exit if 1H SPX candle CLOSES above this level
  "كسر نقطة X"   → "break of level X" — entry trigger on breakout
  "مناسب"         → "suitable" — confirms setup is valid now
  "مضاربي"        → "for scalpers" — short-term trade
  "البوت"         → refers to his channel/system
  "تحديث"         → "update" — update to existing trade
  "$SPX⚡️"       → his standard opening for SPX trade alerts
  "🩸"            → blood emoji — used when market drops (bearish)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — DOWNLOAD SPY PRICE DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import requests, pandas as pd, os, time

API_KEY = os.environ["POLYGON_API_KEY"]
BASE    = "https://api.polygon.io"

def download_spy_1min():
    fname = "market_data/SPY_1min.csv"
    if os.path.exists(fname):
        return pd.read_csv(fname)

    os.makedirs("market_data", exist_ok=True)
    bars, url = [], f"{BASE}/v2/aggs/ticker/SPY/range/1/minute/2026-01-01/2026-04-24"
    params = {"apiKey": API_KEY, "limit": 50000, "sort": "asc", "adjusted": "false"}

    while url:
        r = requests.get(url, params=params)
        data = r.json()
        bars.extend(data.get("results", []))
        next_url = data.get("next_url")
        url = next_url + f"&apiKey={API_KEY}" if next_url else None
        params = {}
        time.sleep(0.1)

    df = pd.DataFrame(bars)
    df.rename(columns={"t":"timestamp","o":"open","h":"high",
                        "l":"low","c":"close","v":"volume"}, inplace=True)
    df["datetime_et"] = (pd.to_datetime(df["timestamp"], unit="ms", utc=True)
                           .dt.tz_convert("America/New_York"))
    df["spx_approx"] = df["close"] * 10  # SPY×10 ≈ SPX
    df.to_csv(fname, index=False)
    return df

spy_df = download_spy_1min()
print(f"SPY bars: {len(spy_df)} rows")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — PARSE ALL HTML FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

HTML_FILES = [
    "telegram_data/messages.html",
    "telegram_data/messages2.html",
    "telegram_data/messages3.html",
    "telegram_data/messages4.html",
]

def classify_message(text):
    t = text.upper()
    if "PUT HERO" in t or ("PUT" in t and re.search(r'\b6[5-9]\d{2}\b|\b7[0-4]\d{2}\b', t)):
        return "PUT_ALERT"
    if "CALL" in t and re.search(r'\b6[5-9]\d{2}\b|\b7[0-4]\d{2}\b', t):
        return "CALL_ALERT"
    if "تحديث" in text:
        return "UPDATE"
    if any(w in text for w in ["ربح","خسر","كسب","profit","win","loss"]):
        return "RESULT"
    if re.search(r'\b6[5-9]\d{2}\b|\b7[0-4]\d{2}\b', text):
        return "ANALYSIS"
    return "OTHER"

def parse_all_html():
    all_messages = []
    for fpath in HTML_FILES:
        if not os.path.exists(fpath):
            print(f"WARNING: {fpath} not found")
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        for msg in soup.find_all("div", class_="message"):
            if "default" not in msg.get("class", []):
                continue
            text_div  = msg.find("div", class_="text")
            date_div  = msg.find("div", class_="date")
            media_div = msg.find("div", class_="media_wrap")
            if not date_div:
                continue

            text     = text_div.get_text(strip=True) if text_div else ""
            time_raw = date_div.get("title", "")
            msg_id   = msg.get("id", "").replace("message", "")

            # Parse timestamp
            try:
                dt_utc3 = datetime.strptime(time_raw[:19], "%d.%m.%Y %H:%M:%S")
                dt_et   = dt_utc3 - timedelta(hours=8)
            except:
                continue

            # Extract image
            image_file = ""
            if media_div:
                img_a = media_div.find("a", class_="photo_wrap")
                if img_a:
                    image_file = img_a.get("href", "")

            # Extract SPX levels
            levels = re.findall(r'\b(6[5-9]\d{2}|7[0-4]\d{2})\b', text)

            # Extract stop level
            stop_match = re.search(r'STOP\s*[🛑]?\s*(\d{4,5})', text)
            stop_level = int(stop_match.group(1)) if stop_match else None

            all_messages.append({
                "msg_id":       msg_id,
                "timestamp_raw": time_raw,
                "timestamp_et": dt_et.strftime("%Y-%m-%d %H:%M:%S"),
                "date_et":      dt_et.strftime("%Y-%m-%d"),
                "time_et":      dt_et.strftime("%H:%M"),
                "hour_et":      dt_et.hour,
                "day_of_week":  dt_et.strftime("%A"),
                "has_image":    bool(media_div),
                "image_file":   image_file,
                "text":         text,
                "msg_type":     classify_message(text),
                "spx_levels":   ",".join(levels),
                "main_level":   int(levels[0]) if levels else None,
                "stop_level":   stop_level,
                "is_hero":      "PUT HERO" in text.upper(),
                "has_hourly_stop": "اغلاق" in text or "ساعة" in text,
                "source_file":  fpath,
            })

    df = pd.DataFrame(all_messages)
    df.to_csv("output/parsed_messages.csv", index=False)
    alerts = df[df["msg_type"].isin(["PUT_ALERT","CALL_ALERT"])]
    alerts.to_csv("output/trade_alerts.csv", index=False)
    print(f"Total messages: {len(df)}")
    print(f"PUT/CALL alerts: {len(alerts)}")
    print(f"PUT HERO alerts: {df['is_hero'].sum()}")
    return df, alerts

os.makedirs("output", exist_ok=True)
df_all, df_alerts = parse_all_html()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — CROSS REFERENCE: ALERTS + MARKET DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_option_ticker(date_str, strike, opt_type="P"):
    dt   = datetime.strptime(date_str, "%Y-%m-%d")
    code = f"{dt.strftime('%y%m%d')}{opt_type}{str(int(strike*1000)).zfill(8)}"
    return f"O:SPX{code}"

def get_spy_price_at(spy_df, dt_et_str, window_minutes=2):
    target = pd.Timestamp(dt_et_str, tz="America/New_York")
    spy_df["datetime_et"] = pd.to_datetime(spy_df["datetime_et"],
                                           utc=True).dt.tz_convert("America/New_York")
    diff = (spy_df["datetime_et"] - target).abs()
    idx  = diff[diff <= pd.Timedelta(minutes=window_minutes)].idxmin()
    if pd.isna(idx):
        return None, None
    row = spy_df.loc[idx]
    return float(row["close"]), float(row["spx_approx"])

def get_option_1min(date_str, strike, opt_type="P"):
    ticker = build_option_ticker(date_str, strike, opt_type)
    url    = f"{BASE}/v2/aggs/ticker/{ticker}/range/1/minute/{date_str}/{date_str}"
    r      = requests.get(url, params={"apiKey": API_KEY, "limit": 500,
                                        "sort": "asc", "adjusted": "false"})
    if r.status_code == 200:
        results = r.json().get("results", [])
        if results:
            df = pd.DataFrame(results)
            df.rename(columns={"t":"ts","o":"open","h":"high",
                                "l":"low","c":"close","v":"volume"}, inplace=True)
            df["datetime_et"] = (pd.to_datetime(df["ts"], unit="ms", utc=True)
                                    .dt.tz_convert("America/New_York"))
            return df
    return None

def enrich_trade(row, spy_df):
    date_str = row["date_et"]
    time_str = row["timestamp_et"]
    level    = row["main_level"]

    if not level or not date_str:
        return {}

    # SPY/SPX at alert time
    spy_px, spx_approx = get_spy_price_at(spy_df, time_str)

    # OTM calculation
    otm_pct = None
    if spx_approx and level:
        otm_pct = round((spx_approx - level) / spx_approx * 100, 3)

    # Option price (try level exactly, then ±25 in 5pt steps)
    opt_bars = None
    best_strike = level
    for delta_s in [0, -5, -10, -15, -20, -25, 5, 10, 15, 20, 25]:
        test_strike = level + delta_s
        bars = get_option_1min(date_str, test_strike)
        if bars is not None and len(bars) > 0:
            opt_bars    = bars
            best_strike = test_strike
            break
        time.sleep(0.05)

    if opt_bars is None:
        return {
            "spy_at_alert": spy_px,
            "spx_approx_at_alert": spx_approx,
            "otm_pct": otm_pct,
        }

    # Find price at alert time
    alert_ts = pd.Timestamp(time_str, tz="America/New_York")
    after    = opt_bars[opt_bars["datetime_et"] >= alert_ts]
    eod      = opt_bars[opt_bars["datetime_et"].dt.hour >= 15]

    price_at_alert  = float(after.iloc[0]["close"]) if len(after) > 0 else None
    price_eod       = float(eod.iloc[-1]["close"])  if len(eod)  > 0 else None
    price_max       = float(opt_bars["high"].max())
    price_max_after = float(after["high"].max())    if len(after) > 0 else None

    pct_max = None
    if price_at_alert and price_max_after:
        pct_max = round((price_max_after - price_at_alert) / price_at_alert * 100, 1)

    return {
        "spy_at_alert":          spy_px,
        "spx_approx_at_alert":   spx_approx,
        "otm_pct":               otm_pct,
        "option_strike_used":    best_strike,
        "option_ticker":         build_option_ticker(date_str, best_strike),
        "option_price_at_alert": price_at_alert,
        "option_price_eod":      price_eod,
        "option_max_after_alert":price_max_after,
        "option_pct_gain_max":   pct_max,
        "is_winner":             (pct_max or 0) >= 50,
        "is_loser":              (pct_max or 0) <= -40,
    }

print("Enriching alerts with market data...")
enriched = []
for i, (_, row) in enumerate(df_alerts.iterrows()):
    extra = enrich_trade(row, spy_df)
    enriched.append({**row.to_dict(), **extra})
    if i % 10 == 0:
        print(f"  {i}/{len(df_alerts)} processed...")
    time.sleep(0.1)

df_enriched = pd.DataFrame(enriched)
df_enriched.to_csv("output/extracted_trades.csv", index=False)
print(f"Saved {len(df_enriched)} enriched trades")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 — FULL STATISTICAL ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run ALL of these. Save each chart to output/charts/

import matplotlib.pyplot as plt
import seaborn as sns
os.makedirs("output/charts", exist_ok=True)

df = pd.read_csv("output/extracted_trades.csv")

# 1. TIMING ANALYSIS
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
df["hour_et"].value_counts().sort_index().plot(kind="bar", ax=axes[0],
    title="Alert Frequency by Hour (ET)", color="steelblue")
df["day_of_week"].value_counts().plot(kind="bar", ax=axes[1],
    title="Alert Frequency by Day of Week", color="coral")
plt.tight_layout()
plt.savefig("output/charts/timing_distribution.png", dpi=150)
plt.close()

# 2. OTM% DISTRIBUTION
df["otm_pct"].dropna().plot(kind="hist", bins=30, figsize=(10,5),
    title="OTM% Distribution (how far below SPX is his level?)",
    color="purple", edgecolor="white")
plt.axvline(df["otm_pct"].median(), color="red", linestyle="--",
            label=f"Median: {df['otm_pct'].median():.2f}%")
plt.legend()
plt.savefig("output/charts/otm_distribution.png", dpi=150)
plt.close()

# 3. WIN RATE ANALYSIS
winners = df["is_winner"].sum()
losers  = df["is_loser"].sum()
total   = df["option_price_at_alert"].notna().sum()
wr      = winners / total * 100 if total > 0 else 0

print(f"\n=== WIN RATE ANALYSIS ===")
print(f"Total trades with option data: {total}")
print(f"Winners (>50% gain): {winners} ({wr:.1f}%)")
print(f"Losers (>40% loss):  {losers}")
print(f"Avg max gain: {df['option_pct_gain_max'].mean():.1f}%")
print(f"Median max gain: {df['option_pct_gain_max'].median():.1f}%")

# WR by hour
df.groupby("hour_et")["is_winner"].mean().mul(100).plot(
    kind="bar", figsize=(12,5), color="green",
    title="Win Rate % by Hour (ET)", ylabel="Win Rate %")
plt.savefig("output/charts/winrate_by_hour.png", dpi=150)
plt.close()

# WR by hero vs normal
hero_wr   = df[df["is_hero"]==True]["is_winner"].mean()*100
normal_wr = df[df["is_hero"]==False]["is_winner"].mean()*100
print(f"\nPUT HERO win rate:   {hero_wr:.1f}%")
print(f"Normal PUT win rate: {normal_wr:.1f}%")

# 4. STOP ANALYSIS
hourly_stop_pct = df["has_hourly_stop"].mean() * 100
price_stop_pct  = df["stop_level"].notna().mean() * 100
print(f"\nStop types:")
print(f"  'اغلاق ساعة' (hourly close): {hourly_stop_pct:.1f}%")
print(f"  Price stop: {price_stop_pct:.1f}%")

# 5. EQUITY CURVE (simulated $1,000 following every alert)
df_sorted = df.dropna(subset=["option_pct_gain_max"]).sort_values("timestamp_et")
equity = [1000]
for _, row in df_sorted.iterrows():
    gain = min(row["option_pct_gain_max"] / 100, 2.0)  # cap at 200% per trade
    risk = 0.05  # 5% of equity per trade
    last = equity[-1]
    new  = last + (last * risk * gain)
    equity.append(max(new, last * 0.95))

plt.figure(figsize=(14, 6))
plt.plot(equity, color="green", linewidth=1.5)
plt.title("Simulated Equity Curve ($1,000 start, 5% per trade, following every alert)")
plt.ylabel("Portfolio Value ($)")
plt.xlabel("Trade #")
plt.grid(True, alpha=0.3)
plt.savefig("output/charts/equity_curve_simulated.png", dpi=150)
plt.close()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5 — ANSWER THESE 5 QUESTIONS (with data evidence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For each question, show the statistical evidence:

Q1: What is "PUT HERO" exactly?
    Compare: hero trades vs normal PUT trades
    Look at: timing, OTM%, option price, gain%
    Find: what makes him label something HERO?

Q2: Is his "أدنى X" level the strike OR the SPX trigger?
    Test: at time of alert, is SPX above or below his level?
    If SPX is ABOVE level → it's a support/watch level
    If SPX is AT/BELOW level → it's the entry price
    Calculate for all alerts and show distribution.

Q3: Decode "اغلاق ساعة" into exact code:
    Hypothesis: exit put if 1H SPX candle CLOSES above his level
    Test: look at SPY 1H candles on days with this stop
    How often does SPX close above his level? = stop trigger rate

Q4: Does he give SPX levels or option strikes?
    His messages say "أدنى 6920" — is 6920:
    (a) The PUT strike → look for O:SPX...P06920000 volume spike
    (b) SPX support level → actual option strike is different
    Test: does option volume spike at exact level or nearby?

Q5: What makes him silent?
    Find days with zero alerts during market hours.
    Look at SPY on those days: was it trending up strongly?
    Look at VIX: was it very low or very high?
    Pattern: he likely avoids trending-up markets and
             extreme volatility days.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6 — WRITE DECODED_STRATEGY.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write output/DECODED_STRATEGY.md in this exact format:

  ## STRATEGY: [your name for his approach]
  ## CONFIDENCE: [High/Medium/Low]
  ## SAMPLE: [X alerts analyzed across Y trading days]

  ### REAL PERFORMANCE (from market data):
  Win Rate:         XX.X%
  Avg Max Gain:     +XXX%
  Avg Loss:         -XX%
  Best trade:       +XXXX% (date, level, conditions)
  Worst trade:      -XX%
  Hero WR:          XX.X% vs Normal WR: XX.X%

  ### ENTRY CONDITIONS:
  Time window:     [exact ET hours based on data]
  Trigger:         [SPX breaks below level? touches level?]
  Level selection: [formula or rule if found]
  Volatility:      [VIX condition if found]

  ### STRIKE / LEVEL:
  [Is أدنى X the strike or the SPX level? Data answer here]

  ### STOP LOSS:
  "اغلاق ساعة" decoded: [exact rule in code form]
  Price stop: [when used vs hourly stop]

  ### DAYS HE AVOIDS:
  [conditions found from silent days analysis]

  ### THE EDGE (why this works):
  #1: [biggest edge source — X% of alpha]
  #2: [second edge source]
  #3: [third edge source]

  ### CAN IT BE AUTOMATED?
  [Yes/No + what's needed]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 7 — EXECUTIVE SUMMARY (plain Arabic)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write output/EXECUTIVE_SUMMARY.md — answer only 3 questions:

  1. ما استراتيجية هذا المتداول بالعربي البسيط؟ (5 جمل كحد أقصى)
  2. ما ميزته الحقيقية؟ (جملتان فقط)
  3. هل يمكن أتمتة هذه الاستراتيجية؟ وماذا تحتاج؟

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FILES REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  output/parsed_messages.csv
  output/trade_alerts.csv
  output/extracted_trades.csv
  output/DECODED_STRATEGY.md
  output/EXECUTIVE_SUMMARY.md
  output/charts/timing_distribution.png
  output/charts/otm_distribution.png
  output/charts/winrate_by_hour.png
  output/charts/equity_curve_simulated.png
  market_data/SPY_1min.csv

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOP CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stop and report if:
  - HTML files not found → ask for correct path
  - API returns 401/403 → report which endpoint failed
  - Less than 50 alerts extracted → HTML parsing has a bug
  - More than 80% trades show "no option data" → ticker
    format is wrong, try different strike ranges
