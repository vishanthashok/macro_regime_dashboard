import copy
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# PAGE CONFIG & CUSTOM CSS
# ─────────────────────────────────────────────

st.set_page_config(page_title="Macro Regime Engine", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');
:root {
    --bg:#0a0d12; --surface:#111520; --border:#1e2535;
    --accent1:#00e5c3; --accent2:#ff6b35; --accent3:#7b61ff;
    --text:#e8ecf4; --muted:#5a6480;
}
html,body,[class*="css"]{font-family:'Syne',sans-serif;background-color:var(--bg);color:var(--text);}
.stApp{background-color:var(--bg);}
#MainMenu,footer,header{visibility:hidden;}
.hero{background:linear-gradient(135deg,#0a0d12 0%,#111a2e 50%,#0a0d12 100%);border:1px solid var(--border);border-radius:16px;padding:40px 48px;margin-bottom:32px;position:relative;overflow:hidden;}
.hero::before{content:'';position:absolute;top:-60px;right:-60px;width:300px;height:300px;background:radial-gradient(circle,rgba(0,229,195,0.08) 0%,transparent 70%);border-radius:50%;}
.hero-tag{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:3px;color:var(--accent1);text-transform:uppercase;margin-bottom:12px;}
.hero-title{font-size:42px;font-weight:800;line-height:1.1;margin:0 0 12px;background:linear-gradient(90deg,#e8ecf4 0%,#00e5c3 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.hero-sub{font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--muted);max-width:540px;}
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:28px;}
.metric-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px 24px;position:relative;overflow:hidden;}
.metric-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--accent-color,var(--accent1));}
.metric-label{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:8px;}
.metric-value{font-size:28px;font-weight:700;line-height:1;}
.metric-sub{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);margin-top:6px;}
.regime-badge{display:inline-flex;align-items:center;gap:10px;padding:14px 24px;border-radius:12px;font-weight:700;font-size:18px;letter-spacing:0.5px;margin-bottom:8px;}
.regime-dot{width:10px;height:10px;border-radius:50%;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1);}50%{opacity:0.6;transform:scale(1.3);}}
.badge-Expansion{background:rgba(0,229,195,0.12);border:1px solid rgba(0,229,195,0.3);color:#00e5c3;}
.badge-Recession{background:rgba(255,77,109,0.12);border:1px solid rgba(255,77,109,0.3);color:#ff4d6d;}
.badge-LateCycle{background:rgba(255,193,7,0.12);border:1px solid rgba(255,193,7,0.3);color:#ffc107;}
.badge-Recovery{background:rgba(123,97,255,0.12);border:1px solid rgba(123,97,255,0.3);color:#7b61ff;}
.alloc-row{display:flex;align-items:center;gap:12px;margin-bottom:10px;}
.alloc-label{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted);width:60px;flex-shrink:0;}
.alloc-bar-bg{flex:1;height:6px;background:var(--border);border-radius:3px;overflow:hidden;}
.alloc-bar-fill{height:100%;border-radius:3px;}
.alloc-pct{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:500;width:36px;text-align:right;flex-shrink:0;}
.section-header{display:flex;align-items:baseline;gap:12px;margin:36px 0 16px;}
.section-title{font-size:20px;font-weight:700;}
.section-line{flex:1;height:1px;background:var(--border);}
.section-tag{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:2px;color:var(--muted);}
.info-box{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent1);border-radius:8px;padding:16px 20px;font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted);line-height:1.7;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# THEME HELPER
# ─────────────────────────────────────────────

_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono, monospace", color="#5a6480", size=11),
    xaxis=dict(gridcolor="#1e2535", linecolor="#1e2535", zeroline=False),
    yaxis=dict(gridcolor="#1e2535", linecolor="#1e2535", zeroline=False),
    margin=dict(l=16, r=16, t=32, b=16),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2535"),
)

def theme(**overrides):
    """Deep-merge overrides into base theme — no duplicate keyword args."""
    result = copy.deepcopy(_BASE)
    for k, v in overrides.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = {**result[k], **v}
        else:
            result[k] = v
    return result


# ─────────────────────────────────────────────
# DATA DOWNLOAD
# ─────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_data():
    tickers = {"SPY": "SPY", "Bonds": "TLT", "Gold": "GLD", "Oil": "USO", "Dollar": "UUP"}
    data = {}
    for name, ticker in tickers.items():
        df = yf.download(ticker, start="2005-01-01", auto_adjust=True, progress=False)
        if df.empty:
            st.error(f"No data for {ticker}")
            st.stop()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        col = "Close" if "Close" in df.columns else df.columns[0]
        data[name] = df[col]
    return pd.DataFrame(data).dropna()


# ─────────────────────────────────────────────
# REGIME DETECTION
# ─────────────────────────────────────────────

def compute_regimes(data):
    returns    = data.pct_change().dropna()
    momentum   = data["SPY"].pct_change(126)
    volatility = returns["SPY"].rolling(30).std()
    mv = pd.concat([momentum.rename("momentum"), volatility.rename("volatility")], axis=1).dropna()
    med = mv["volatility"].median()
    conditions = [
        (mv["momentum"] >  0) & (mv["volatility"] <= med),
        (mv["momentum"] <= 0) & (mv["volatility"] >  med),
        (mv["momentum"] >  0) & (mv["volatility"] >  med),
        (mv["momentum"] <= 0) & (mv["volatility"] <= med),
    ]
    regime = pd.Series(
        np.select(conditions, ["Expansion", "Recession", "Late Cycle", "Recovery"], default="Recovery"),
        index=mv.index,
    )
    df = pd.concat([returns, regime.rename("Regime")], axis=1).dropna()
    df = df[~df.index.duplicated(keep="last")]
    return df, mv, regime


# ─────────────────────────────────────────────
# PORTFOLIO MATH
# ─────────────────────────────────────────────

ALLOCATIONS = {
    "Expansion":  {"SPY": 0.70, "Bonds": 0.20, "Gold": 0.10},
    "Recession":  {"SPY": 0.20, "Bonds": 0.60, "Gold": 0.20},
    "Late Cycle": {"SPY": 0.40, "Bonds": 0.30, "Gold": 0.30},
    "Recovery":   {"SPY": 0.60, "Bonds": 0.30, "Gold": 0.10},
}
REGIME_COLORS = {
    "Expansion": "#00e5c3", "Recession": "#ff4d6d",
    "Late Cycle": "#ffc107", "Recovery": "#7b61ff",
}
ASSET_COLORS = {"SPY": "#00e5c3", "Bonds": "#7b61ff", "Gold": "#ffc107"}

def build_portfolio(df):
    ws = df["Regime"].map({k: v["SPY"]   for k, v in ALLOCATIONS.items()})
    wb = df["Regime"].map({k: v["Bonds"] for k, v in ALLOCATIONS.items()})
    wg = df["Regime"].map({k: v["Gold"]  for k, v in ALLOCATIONS.items()})
    ret = df["SPY"] * ws.values + df["Bonds"] * wb.values + df["Gold"] * wg.values
    return pd.to_numeric(ret, errors="coerce").dropna()

def sharpe(r):
    v = r.std() * np.sqrt(252)
    return (r.mean() * 252) / v if v > 0 else 0.0

def max_dd(cum):
    return ((cum - cum.cummax()) / cum.cummax()).min()


# ─────────────────────────────────────────────
# LOAD & COMPUTE
# ─────────────────────────────────────────────

with st.spinner("Pulling market data…"):
    data = load_data()

df, mv, regime  = compute_regimes(data)
port_ret        = build_portfolio(df)
port_cum        = (1 + port_ret).cumprod()
spy_cum         = (1 + df["SPY"]).cumprod()
current_regime  = regime.iloc[-1]
current_alloc   = ALLOCATIONS[current_regime]
rc              = REGIME_COLORS[current_regime]
badge_class     = "badge-" + current_regime.replace(" ", "")
port_ann        = port_ret.mean() * 252
spy_ann         = df["SPY"].mean() * 252
alpha           = port_ann - spy_ann
reg_clean       = regime[~regime.index.duplicated(keep="last")]


# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────

st.markdown("""
<div class="hero">
  <div class="hero-tag">// quantitative macro strategy</div>
  <div class="hero-title">Macro Regime Engine</div>
  <div class="hero-sub">Regime detection · Dynamic allocation · Performance attribution<br>
  Market data via yFinance · 2005 → present</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────

st.markdown(f"""
<div class="metric-grid">
  <div class="metric-card" style="--accent-color:{rc}">
    <div class="metric-label">Current Regime</div>
    <div class="regime-badge {badge_class}">
      <div class="regime-dot" style="background:{rc}"></div>
      {current_regime}
    </div>
    <div class="metric-sub">as of {regime.index[-1].strftime('%b %d, %Y')}</div>
  </div>
  <div class="metric-card" style="--accent-color:#00e5c3">
    <div class="metric-label">Strategy Return (Ann.)</div>
    <div class="metric-value" style="color:#00e5c3">{port_ann:+.1%}</div>
    <div class="metric-sub">vs SPY {spy_ann:+.1%} &middot; alpha {alpha:+.1%}</div>
  </div>
  <div class="metric-card" style="--accent-color:#7b61ff">
    <div class="metric-label">Sharpe Ratio</div>
    <div class="metric-value" style="color:#7b61ff">{sharpe(port_ret):.2f}</div>
    <div class="metric-sub">SPY Sharpe {sharpe(df["SPY"]):.2f}</div>
  </div>
  <div class="metric-card" style="--accent-color:#ff4d6d">
    <div class="metric-label">Max Drawdown</div>
    <div class="metric-value" style="color:#ff4d6d">{max_dd(port_cum):.1%}</div>
    <div class="metric-sub">Strategy worst peak&#8594;trough</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ALLOCATION + REGIME HISTORY
# ─────────────────────────────────────────────

col_a, col_b = st.columns([1, 2])

with col_a:
    st.markdown('<div class="section-header"><span class="section-title">Current Allocation</span>'
                '<div class="section-line"></div><span class="section-tag">ACTIVE</span></div>',
                unsafe_allow_html=True)
    bars = ""
    for asset, pct in current_alloc.items():
        color = ASSET_COLORS.get(asset, "#5a6480")
        bars += (f'<div class="alloc-row">'
                 f'<div class="alloc-label">{asset}</div>'
                 f'<div class="alloc-bar-bg"><div class="alloc-bar-fill" '
                 f'style="width:{pct*100:.0f}%;background:{color}"></div></div>'
                 f'<div class="alloc-pct" style="color:{color}">{pct:.0%}</div></div>')
    st.markdown(bars, unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box" style="margin-top:16px">
      REGIME LOGIC<br>&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;&#x2500;<br>
      Expansion &nbsp; &#x2192; high mom, low vol<br>
      Recession &nbsp; &#x2192; low mom, high vol<br>
      Late Cycle &#x2192; high mom, high vol<br>
      Recovery &nbsp; &#x2192; low mom, low vol
    </div>""", unsafe_allow_html=True)

with col_b:
    st.markdown('<div class="section-header"><span class="section-title">Regime History</span>'
                '<div class="section-line"></div><span class="section-tag">2005&#x2192;NOW</span></div>',
                unsafe_allow_html=True)
    rnum  = reg_clean.map({"Expansion": 1, "Late Cycle": 0.5, "Recovery": -0.5, "Recession": -1})
    rcols = reg_clean.map(REGIME_COLORS)

    fig_r = go.Figure()
    fig_r.add_trace(go.Scatter(
        x=rnum.index, y=rnum.values, fill="tozeroy",
        fillcolor="rgba(0,229,195,0.05)", line=dict(width=0), hoverinfo="skip",
    ))
    fig_r.add_trace(go.Scatter(
        x=rnum.index, y=rnum.values, mode="markers",
        marker=dict(color=list(rcols.values), size=3, opacity=0.7),
        text=reg_clean.values,
        hovertemplate="%{x|%Y-%m-%d}<br><b>%{text}</b><extra></extra>",
    ))
    fig_r.update_layout(**theme(
        height=220, showlegend=False,
        yaxis=dict(tickvals=[-1, -0.5, 0.5, 1],
                   ticktext=["Recession", "Recovery", "Late Cycle", "Expansion"]),
    ))
    st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# CUMULATIVE PERFORMANCE
# ─────────────────────────────────────────────

st.markdown('<div class="section-header"><span class="section-title">Cumulative Performance</span>'
            '<div class="section-line"></div><span class="section-tag">BACKTEST</span></div>',
            unsafe_allow_html=True)

fig_p = go.Figure()
fig_p.add_trace(go.Scatter(
    x=port_cum.index, y=port_cum.values, name="Dynamic Strategy",
    line=dict(color="#00e5c3", width=2),
    hovertemplate="%{x|%Y-%m-%d}<br><b>Strategy: %{y:.2f}x</b><extra></extra>",
))
fig_p.add_trace(go.Scatter(
    x=spy_cum.index, y=spy_cum.values, name="SPY Buy &amp; Hold",
    line=dict(color="#ff6b35", width=2, dash="dot"),
    hovertemplate="%{x|%Y-%m-%d}<br>SPY: %{y:.2f}x<extra></extra>",
))
fig_p.update_layout(**theme(height=340))
fig_p.update_yaxes(title_text="Growth of $1", title_font=dict(size=11))
st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# REGIME STATS TABLES
# ─────────────────────────────────────────────

st.markdown('<div class="section-header"><span class="section-title">Asset Performance by Regime</span>'
            '<div class="section-line"></div><span class="section-tag">ANN.</span></div>',
            unsafe_allow_html=True)

num_cols    = [c for c in df.columns if c != "Regime"]
performance = df.groupby("Regime")[num_cols].mean() * 252
volatility  = df.groupby("Regime")[num_cols].std()  * np.sqrt(252)

tab1, tab2 = st.tabs(["📈 Annualized Returns", "📉 Annualized Volatility"])
with tab1:
    st.dataframe(performance.style.format("{:.1%}").background_gradient(cmap="RdYlGn", axis=None),
                 use_container_width=True)
with tab2:
    st.dataframe(volatility.style.format("{:.1%}").background_gradient(cmap="RdYlGn_r", axis=None),
                 use_container_width=True)


# ─────────────────────────────────────────────
# DISTRIBUTION PIE + BAR
# ─────────────────────────────────────────────

st.markdown('<div class="section-header"><span class="section-title">Regime Distribution</span>'
            '<div class="section-line"></div><span class="section-tag">FREQUENCY</span></div>',
            unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    counts = reg_clean.value_counts()
    fig_pie = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.62,
        marker=dict(colors=[REGIME_COLORS[r] for r in counts.index]),
        textfont=dict(family="JetBrains Mono", size=11),
        hovertemplate="<b>%{label}</b><br>%{value} days (%{percent})<extra></extra>",
    ))
    fig_pie.update_layout(**theme(
        height=260, showlegend=True,
        legend=dict(orientation="v", x=1.0, y=0.5),
    ))
    fig_pie.add_annotation(
        text=f"{len(reg_clean):,}<br>days", x=0.5, y=0.5,
        font=dict(size=14, color="#e8ecf4", family="Syne"), showarrow=False,
    )
    st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

with col2:
    ret_by_regime = df.groupby("Regime")["SPY"].mean() * 252
    fig_bar = go.Figure(go.Bar(
        x=ret_by_regime.values, y=ret_by_regime.index, orientation="h",
        marker=dict(color=[REGIME_COLORS[r] for r in ret_by_regime.index]),
        text=[f"{v:+.1%}" for v in ret_by_regime.values],
        textfont=dict(family="JetBrains Mono", size=11, color="#e8ecf4"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>SPY ann. return: %{x:.1%}<extra></extra>",
    ))
    fig_bar.update_layout(**theme(
        height=260,
        title_text="SPY Avg Ann. Return by Regime",
        xaxis=dict(tickformat=".0%"),
    ))
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────

st.markdown("""
<div class="info-box" style="margin-top:32px;border-left-color:#1e2535">
  &#x26A0; DISCLAIMER &#x2014; For educational and research purposes only. Past performance does not
  guarantee future results. Regime labels are rule-based approximations using market-implied
  signals and do not constitute financial advice.
</div>
""", unsafe_allow_html=True)
