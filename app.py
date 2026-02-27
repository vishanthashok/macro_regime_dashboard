import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression

st.set_page_config(page_title="Macro Regime Dashboard", layout="wide")

st.title("📈 Macro Regime Detector & Allocation Engine")

# ----------------------------------------
# DATA DOWNLOAD
# ----------------------------------------

@st.cache_data
def load_data():
    tickers = {
        "SPY": "SPY",
        "Bonds": "TLT",
        "Gold": "GLD",
        "Oil": "USO",
        "Dollar": "UUP"
    }

    data = pd.DataFrame()

    for name, ticker in tickers.items():
        df = yf.download(ticker, start="2005-01-01")

        # Handle both normal and MultiIndex column formats from yfinance
        cols = df.columns
        series = None

        if "Adj Close" in cols:
            series = df["Adj Close"]
        elif "Close" in cols:
            # Fallback if only non-adjusted close is available
            series = df["Close"]
        elif isinstance(cols, pd.MultiIndex):
            # Try common MultiIndex layouts
            if ("Adj Close", ticker) in cols:
                series = df[("Adj Close", ticker)]
            elif (ticker, "Adj Close") in cols:
                series = df[(ticker, "Adj Close")]
            elif ("Close", ticker) in cols:
                series = df[("Close", ticker)]
            elif (ticker, "Close") in cols:
                series = df[(ticker, "Close")]

        if series is None:
            # As a very last resort, just take the first numeric column
            numeric_cols = df.select_dtypes(include="number").columns
            if len(numeric_cols) == 0:
                st.error(f"Could not find a price column for {ticker}. Columns: {list(cols)}")
                st.stop()
            series = df[numeric_cols[0]]

        data[name] = series

    data = data.dropna()
    return data

data = load_data()

# ----------------------------------------
# FEATURE ENGINEERING
# ----------------------------------------

returns = data.pct_change().dropna()

# Growth proxy: SPY 6m momentum
momentum = data["SPY"].pct_change(126)

# Volatility proxy
volatility = returns["SPY"].rolling(30).std()

# Align momentum & volatility on common dates and drop NaNs
mv = pd.concat(
    [momentum.rename("momentum"), volatility.rename("volatility")],
    axis=1
).dropna()

# Regime logic (vectorized)
median_vol = mv["volatility"].median()

regime = pd.Series(index=mv.index, dtype="object")
regime[(mv["momentum"] > 0) & (mv["volatility"] < median_vol)] = "Expansion"
regime[(mv["momentum"] < 0) & (mv["volatility"] > median_vol)] = "Recession"
regime[(mv["momentum"] > 0) & (mv["volatility"] > median_vol)] = "Late Cycle"
regime[regime.isna()] = "Recovery"

# Align everything
df = pd.concat([returns, regime.rename("Regime")], axis=1).dropna()

# ----------------------------------------
# REGIME PERFORMANCE
# ----------------------------------------

st.header("📊 Asset Performance by Regime")

performance = df.groupby("Regime").mean() * 252
vol = df.groupby("Regime").std() * np.sqrt(252)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Annualized Returns")
    st.dataframe(performance)

with col2:
    st.subheader("Annualized Volatility")
    st.dataframe(vol)

# ----------------------------------------
# DYNAMIC ALLOCATION
# ----------------------------------------

st.header("💰 Dynamic Allocation Strategy")

allocations = {
    "Expansion": {"SPY": 0.7, "Bonds": 0.2, "Gold": 0.1},
    "Recession": {"SPY": 0.2, "Bonds": 0.6, "Gold": 0.2},
    "Late Cycle": {"SPY": 0.4, "Bonds": 0.3, "Gold": 0.3},
    "Recovery": {"SPY": 0.6, "Bonds": 0.3, "Gold": 0.1},
}

portfolio_returns = []

for date in df.index:
    reg = df.loc[date, "Regime"]
    weights = allocations[reg]
    r = (
        df.loc[date, "SPY"] * weights["SPY"] +
        df.loc[date, "Bonds"] * weights["Bonds"] +
        df.loc[date, "Gold"] * weights["Gold"]
    )
    portfolio_returns.append(r)

portfolio = pd.Series(portfolio_returns, index=df.index)
portfolio_cum = (1 + portfolio).cumprod()
spy_cum = (1 + df["SPY"]).cumprod()

# ----------------------------------------
# PERFORMANCE CHART
# ----------------------------------------

st.subheader("📈 Strategy vs SPY")

fig, ax = plt.subplots()
portfolio_cum.plot(ax=ax, label="Dynamic Strategy")
spy_cum.plot(ax=ax, label="SPY Buy & Hold")
ax.legend()
st.pyplot(fig)

# ----------------------------------------
# CURRENT REGIME
# ----------------------------------------

st.header("🔍 Current Regime")

current_regime = regime.iloc[-1]
st.metric("Current Macro Regime", current_regime)

st.write("Latest Allocation:")
st.json(allocations[current_regime])
