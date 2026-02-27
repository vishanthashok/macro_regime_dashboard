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
        data[name] = df["Adj Close"]

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

# Regime logic
regime = []

for i in range(len(momentum)):
    if momentum.iloc[i] > 0 and volatility.iloc[i] < volatility.median():
        regime.append("Expansion")
    elif momentum.iloc[i] < 0 and volatility.iloc[i] > volatility.median():
        regime.append("Recession")
    elif momentum.iloc[i] > 0 and volatility.iloc[i] > volatility.median():
        regime.append("Late Cycle")
    else:
        regime.append("Recovery")

regime = pd.Series(regime, index=momentum.index)

# Align everything
df = pd.concat([returns, regime], axis=1).dropna()
df.columns = list(returns.columns) + ["Regime"]

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
