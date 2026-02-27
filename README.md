# macro_regime_dashboard

Let’s make this README look **clean, technical, and resume-ready**.

You can paste this directly into a `README.md` file in your project root.

---

# 📈 Macro Regime Detector & Dynamic Allocation Engine

A Python-based macro regime classification and portfolio allocation dashboard built with Streamlit.

This project identifies economic regimes using market-based indicators, evaluates historical asset performance across regimes, and dynamically allocates capital based on macro conditions.

---

## 🚀 Overview

This application:

* Classifies macro regimes using:

  * 6-month equity momentum
  * Rolling volatility
* Analyzes asset returns across regimes
* Backtests a dynamic allocation strategy
* Compares performance vs passive S&P 500 exposure
* Displays results in an interactive Streamlit dashboard

The goal is to simulate how a discretionary macro fund might systematically adjust asset exposure across economic cycles.

---

## 🧠 Regime Classification Logic

Regimes are determined using:

* **Growth proxy** → 6-month momentum of SPDR S&P 500 ETF Trust
* **Risk proxy** → 30-day rolling volatility

| Growth | Volatility | Regime     |
| ------ | ---------- | ---------- |
| ↑      | Low        | Expansion  |
| ↓      | High       | Recession  |
| ↑      | High       | Late Cycle |
| ↓      | Low        | Recovery   |

This rule-based system approximates macro phase transitions using market-implied signals.

---

## 📊 Assets Tracked

* SPDR S&P 500 ETF Trust (Equities)
* iShares 20+ Year Treasury Bond ETF (Long-duration bonds)
* SPDR Gold Shares (Gold)
* United States Oil Fund (Oil)
* Invesco DB US Dollar Index Bullish Fund (Dollar proxy)

---

## 💰 Dynamic Allocation Strategy

Each macro regime maps to a predefined asset allocation:

Example:

* **Expansion** → 70% equities, 20% bonds, 10% gold
* **Recession** → 20% equities, 60% bonds, 20% gold

The strategy dynamically rebalances daily based on the detected regime.

Performance is benchmarked against passive SPY buy-and-hold.

---

## 📈 Outputs

The dashboard displays:

* Annualized returns by regime
* Annualized volatility by regime
* Cumulative strategy vs benchmark performance
* Current macro regime
* Current recommended allocation

---

## 🛠 Tech Stack

* Python
* Pandas
* NumPy
* yFinance
* Matplotlib
* Streamlit
* scikit-learn (optional extension)

---

## ▶️ Installation & Usage

### 1. Clone repository

```bash
git clone <your-repo-url>
cd macro_regime_dashboard
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run dashboard

```bash
streamlit run app.py
```

The app will launch locally in your browser.

---

## 🔬 Possible Extensions

* Add yield curve spread (2Y–10Y) as a feature
* Train a logistic regression regime classifier
* Implement risk-parity weighting
* Add Sharpe ratios & drawdown analysis
* Integrate FRED macroeconomic data
* Deploy to Streamlit Cloud

---

## 📌 Motivation

Modern macro investing often blends discretionary insight with systematic signals.
This project explores how market-implied indicators can serve as a rules-based approximation of economic regimes and inform tactical asset allocation decisions.

---

## ⚠️ Disclaimer

This project is for educational and research purposes only.
It does not constitute investment advice.

---
