import yfinance as yf
import pandas as pd
from fredapi import Fred
import numpy as np

# --- SETUP ---
import os
FRED_KEY = os.getenv("FRED_API_KEY")
fred = Fred(api_key=FRED_KEY)

def get_risk_score():
    print("Fetching market data... this may take a moment.")
    
    # 1. Define our Indicators: (Ticker, Direction, Weight)
    # Direction -1 means HIGHER value = MORE RISK (Risk-Off)
    # Direction +1 means HIGHER value = BETTER MARKET (Risk-On)
    # --- UPDATED LEAD-HEAVY WEIGHTS ---
    indicators = {
        "VIX": {"ticker": "^VIX", "w": 0.12, "dir": -1},          # Volatility (High = Bad)
        "DXY": {"ticker": "DX-Y.NYB", "w": 0.15, "dir": -1},      # Dollar (High = Bad for Liquidity)
        "10Y_Yield": {"ticker": "TNX", "w": 0.08, "dir": -1, "source": "yahoo"}, # Adjusted Yield
        "HY_Spread": {"ticker": "BAMLH0A0HYM2", "w": 0.20, "dir": -1, "source": "fred"}, # MAJOR LEAD
        "Gold": {"ticker": "GC=F", "w": 0.05, "dir": -1},         # Defensive Anchor
        "BTC": {"ticker": "BTC-USD", "w": 0.07, "dir": 1},        # Risk Appetite Proxy
        "Copper": {"ticker": "HG=F", "w": 0.08, "dir": 1},        # Global Growth
        "SPY": {"ticker": "SPY", "w": 0.05, "dir": 1},            # Price (Reduced to avoid lagging)
        "RSP": {"ticker": "RSP", "w": 0.10, "dir": 1},            # Market Breadth
        "IWM": {"ticker": "IWM", "w": 0.10, "dir": 1}             # Small Cap Health
    }

    scores = []
    
# 2. Fetch Data and Calculate Normalization (The Math)
    for name, info in indicators.items():
        try:
            if info.get('source') == 'fred':
                data = fred.get_series(info['ticker']).dropna()
            else:
                # Updated to handle the new yfinance format
                downloaded = yf.download(info['ticker'], period="1y", interval="1d", progress=False)
                if isinstance(downloaded, pd.DataFrame) and not downloaded.empty:
                    # This ensures we get a single column of data regardless of formatting
                    data = downloaded['Close'].squeeze()
                else:
                    continue

            current_val = float(data.iloc[-1])
            mean_val = data.mean()
            std_val = data.std()
            
            # This is the N_i calculation from our equation
            z_score = (current_val - mean_val) / (std_val * 3)
            normalized_score = max(min(z_score * info['dir'], 1), -1)
            
            weighted_contribution = normalized_score * info['w']
            scores.append(weighted_contribution)
            print(f"✔ {name}: {current_val:.2f} (Contrib: {weighted_contribution:.2f})")
            
        except Exception as e:
            print(f"✘ Error fetching {name}: {e}")

    # 3. Final Calculation
    crss = sum(scores) * 100
    return round(crss, 2)

# Run it!
final_score = get_risk_score()
print("\n" + "="*30)
print(f"FINAL CRSS SCORE: {final_score}")

if final_score > 35:
    print("SENTIMENT: RISK-ON 🟢")
elif final_score < -35:
    print("SENTIMENT: RISK-OFF 🔴")
else:
    print("SENTIMENT: NEUTRAL 🟡")
print("="*30)
# ... (at the bottom of your existing code)
import json
from datetime import datetime

# Create a data dictionary
data_to_save = {
    "crss": final_score,
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "RISK-ON" if final_score > 35 else "RISK-OFF" if final_score < -35 else "NEUTRAL"
}

# Save it as a file named 'data.json'
with open('data.json', 'w') as f:
    json.dump(data_to_save, f)

print("Data saved to data.json")