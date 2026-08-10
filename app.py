"""
╔══════════════════════════════════════════════════════════════╗
║     🟢 THREE CAP — First Green Candle + Volume Scanner      ║
║     THREE CAP © 2026 | fb.com/threecap                      ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="THREE CAP — First Green Scanner",
    page_icon="🟢",
    layout="wide"
)

# ══════════════════════════════════════════════════════════════
# STYLE — Navy/Gold
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }

.main { background-color: #0a1628; color: #f0f0f0; }

.title-box {
    background: linear-gradient(135deg, #0d1f3c, #1a3a6b);
    border: 1px solid #c9a84c;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
}
.title-box h1 { color: #c9a84c; font-size: 26px; margin: 0; }
.title-box p  { color: #aac4e8; font-size: 14px; margin: 4px 0 0; }

.metric-card {
    background: #0d1f3c;
    border: 1px solid #1e3a6e;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}
.metric-card .label { color: #7a9cc4; font-size: 13px; }
.metric-card .value { color: #c9a84c; font-size: 28px; font-weight: 600; }

.signal-row {
    background: #0d1f3c;
    border-left: 4px solid #27ae60;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="title-box">
    <h1>🟢 VITALi — First Green Candle Scanner</h1>
    <p>สแกนหา "เขียวแท่งแรก" พร้อม Volume พิเศษ | VITALi © 2026</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PRESET LISTS
# ══════════════════════════════════════════════════════════════
@st.cache_data
def load_stock_list(filename):
    """อ่านรายชื่อหุ้นจาก CSV (1 คอลัมน์ ไม่มี header)"""
    try:
        df = pd.read_csv(filename, header=None)
        return df.iloc[:, 0].dropna().str.strip().str.upper().tolist()
    except Exception as e:
        st.warning(f"⚠️ โหลด {filename} ไม่ได้: {e}")
        return []

SET_STOCKS    = load_stock_list("SET.csv")
SET100_STOCKS = load_stock_list("SET100.csv")
SP500_STOCKS  = load_stock_list("SP500.csv")
US_STOCKS     = load_stock_list("US_Stock.csv")

# ══════════════════════════════════════════════════════════════
# SIDEBAR — CONFIG
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ ตั้งค่าการสแกน")

    lookback = st.slider("ดูย้อนหลัง (แท่งเทรดล่าสุด)", 1, 30, 5)
    change_th = st.slider("บวก >= (%)", 5, 20, 10)
    vol_mult  = st.slider("Volume >= (x เท่า)", 1.0, 10.0, 3.0, step=0.5)
    quiet_days = st.slider("Quiet period (วัน)", 10, 60, 30)
    quiet_th   = st.slider("Quiet threshold (%)", 3, 15, 7)

    st.markdown("---")
    st.markdown("### 📋 รายชื่อหุ้น")

    stock_source = st.radio(
        "เลือกรายชื่อหุ้น",
        ["SET", "SET100", "S&P500", "US Stock", "พิมพ์เอง", "อัปโหลด CSV"]
    )

    stock_list = []

    if stock_source == "SET":
        stock_list = SET_STOCKS
        st.caption(f"✅ {len(stock_list)} ตัว")

    elif stock_source == "SET100":
        stock_list = SET100_STOCKS
        st.caption(f"✅ {len(stock_list)} ตัว")

    elif stock_source == "S&P500":
        stock_list = SP500_STOCKS
        st.caption(f"✅ {len(stock_list)} ตัว")

    elif stock_source == "US Stock":
        stock_list = US_STOCKS
        st.caption(f"✅ {len(stock_list)} ตัว")

    elif stock_source == "พิมพ์เอง":
        raw = st.text_area(
            "พิมพ์ชื่อหุ้น (คั่นด้วย , หรือขึ้นบรรทัดใหม่)",
            placeholder="เช่น\nXO.BK\nKGEN.BK\nPTT.BK"
        )
        if raw.strip():
            stock_list = [
                s.strip().upper()
                for s in raw.replace("\n", ",").split(",")
                if s.strip()
            ]
            st.caption(f"✅ {len(stock_list)} ตัว")

    elif stock_source == "อัปโหลด CSV":
        uploaded = st.file_uploader("CSV (1 คอลัมน์ = ชื่อหุ้น)", type="csv")
        if uploaded:
            df_upload = pd.read_csv(uploaded, header=None)
            stock_list = df_upload.iloc[:, 0].dropna().str.strip().str.upper().tolist()
            st.caption(f"✅ {len(stock_list)} ตัว")

    st.markdown("---")
    run_btn = st.button("🚀 เริ่มสแกน", use_container_width=True, type="primary")

# ══════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════
# TRADING VALUE — market detection + liquidity threshold
# ══════════════════════════════════════════════════════════════
# เกณฑ์เส้นแบ่งสภาพคล่องต่อวัน แยกตามตลาด (ไม่ใช้ตัด/กรองทิ้ง
# แค่ใช้ทำเครื่องหมายเตือนในตาราง เพราะสกุลเงินคนละหน่วยเทียบตรงๆ ไม่ได้)
MARKET_CONFIG = {
    "TH": {"suffix": ".BK", "currency": "THB", "threshold": 50_000_000},
    "HK": {"suffix": ".HK", "currency": "HKD", "threshold": 20_000_000},
    "US": {"suffix": "",    "currency": "USD", "threshold": 5_000_000},
}

def get_market(symbol):
    if symbol.endswith(".BK"):
        return "TH"
    elif symbol.endswith(".HK"):
        return "HK"
    else:
        return "US"


def fmt_trading_value(value, currency):
    """แปลง Trading Value เป็นข้อความ M พร้อมสกุลเงิน"""
    if value >= 1_000_000_000:
        return f"{value/1_000_000_000:,.2f}B {currency}"
    return f"{value/1_000_000:,.1f}M {currency}"


def is_quiet_before(df_full, current_iloc, quiet_days, quiet_threshold):
    start_i = max(0, current_iloc - quiet_days)
    prior   = df_full.iloc[start_i:current_iloc]
    if len(prior) < 5:
        return False
    green_pct = (prior['Close'] - prior['Open']) / prior['Open']
    return float(green_pct.max()) < quiet_threshold


def scan_one_stock(symbol, config):
    found = []
    try:
        end   = datetime.today()
        start = end - timedelta(days=config["lookback_days"] + 90)
        df = yf.download(symbol, start=start, end=end,
                         progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < config["volume_ma_period"] + 10:
            return found

        df = df.copy()
        vm = config["volume_ma_period"]
        # แก้ไข: shift(1) ก่อน rolling เพื่อให้ Vol_MA คิดจาก "vm วันก่อนหน้า"
        # เท่านั้น ไม่รวม volume ของวันที่เกิดสัญญาณ (กันไม่ให้ spike ของ
        # วันนั้นไปดันค่าเฉลี่ยของตัวเองให้สูงเทียม เหมือนหลักการ volume[1]
        # ในโค้ด Pine Script)
        df['Vol_MA']   = df['Volume'].shift(1).rolling(vm).mean()
        df['Chg_OC']   = (df['Close'] - df['Open']) / df['Open']
        df['Vol_Ratio'] = df['Volume'] / df['Vol_MA']

        # ใช้ .tail() นับเป็น "แท่งเทรดจริง" ล่าสุด ไม่ใช่นับตามวันปฏิทิน
        # (กันปัญหาวันหยุด/เสาร์-อาทิตย์ ทำให้ได้แท่งน้อยกว่าที่ตั้งไว้)
        df_scan = df.tail(config["lookback_days"])

        for dt, row in df_scan.iterrows():
            if not (row['Close'] > row['Open']):
                continue
            if float(row['Chg_OC']) < config["change_threshold"]:
                continue
            if pd.isna(row['Vol_Ratio']):
                continue
            if float(row['Vol_Ratio']) < config["volume_multiplier"]:
                continue
            global_i = df.index.get_loc(dt)
            if not is_quiet_before(df, global_i,
                                   config["quiet_period_days"],
                                   config["quiet_threshold"]):
                continue

            market       = get_market(symbol)
            currency     = MARKET_CONFIG[market]["currency"]
            liq_th       = MARKET_CONFIG[market]["threshold"]
            trading_val  = float(row['Close']) * float(row['Volume'])

            found.append({
                "Symbol":         symbol.replace(".BK", "").replace(".HK", ""),
                "Full_Symbol":    symbol,
                "Market":         market,
                "Date":           dt.strftime("%Y-%m-%d"),
                "Open":           round(float(row['Open']),  2),
                "Close":          round(float(row['Close']), 2),
                "Change_%":       round(float(row['Chg_OC']) * 100, 2),
                "Volume":         int(row['Volume']),
                "Vol_MA20":       int(row['Vol_MA']) if not pd.isna(row['Vol_MA']) else 0,
                "Vol_Ratio_x":    round(float(row['Vol_Ratio']), 1),
                "Trading_Value":  trading_val,
                "Currency":       currency,
                "Liq_Threshold":  liq_th,
                "Below_Liq":      trading_val < liq_th,
            })
    except:
        pass
    return found


def load_chart(symbol, signal_date):
    """โหลดข้อมูลกราฟ 90 วัน รอบวันสัญญาณ"""
    try:
        sig_dt = datetime.strptime(signal_date, "%Y-%m-%d")
        start  = sig_dt - timedelta(days=80)
        end    = sig_dt + timedelta(days=10)
        df = yf.download(symbol, start=start, end=end,
                         progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()


def plot_chart(df, symbol, signal_date, vol_ma_period=20):
    """วาดกราฟ Candlestick + Volume"""
    if df.empty:
        return None

    df = df.copy()
    # แก้ไขให้ตรงกับตรรกะเดียวกับตอนสแกน: ไม่รวมวันปัจจุบันในค่าเฉลี่ย
    df['Vol_MA'] = df['Volume'].shift(1).rolling(vol_ma_period).mean()

    sig_dt = pd.Timestamp(signal_date)

    fig = go.Figure()

    # --- Candlestick ---
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'],   close=df['Close'],
        name="ราคา",
        increasing_line_color="#27ae60",
        decreasing_line_color="#e74c3c",
        increasing_fillcolor="#27ae60",
        decreasing_fillcolor="#e74c3c",
    ))

    # --- Marker วันสัญญาณ ---
    if sig_dt in df.index:
        sig_row = df.loc[sig_dt]
        fig.add_trace(go.Scatter(
            x=[sig_dt],
            y=[float(sig_row['High']) * 1.03],
            mode="markers+text",
            marker=dict(symbol="triangle-down", size=14, color="#c9a84c"),
            text=["🟢 สัญญาณ"],
            textposition="top center",
            textfont=dict(color="#c9a84c", size=12),
            name="วันสัญญาณ",
        ))

    fig.update_layout(
        title=dict(text=f"📈 {symbol} — {signal_date}", font=dict(color="#c9a84c", size=16)),
        paper_bgcolor="#0a1628",
        plot_bgcolor="#0d1f3c",
        font=dict(color="#aac4e8", family="Kanit"),
        xaxis=dict(gridcolor="#1e3a6e", showgrid=True, rangeslider_visible=False),
        yaxis=dict(gridcolor="#1e3a6e", showgrid=True),
        height=420,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(bgcolor="#0d1f3c", bordercolor="#1e3a6e"),
    )

    # --- Volume subplot (ใช้ secondary y) ---
    vol_colors = ["#27ae60" if c >= o else "#e74c3c"
                  for c, o in zip(df['Close'], df['Open'])]

    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        name="Volume",
        marker_color=vol_colors,
        opacity=0.5,
        yaxis="y2",
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Vol_MA'],
        name=f"Vol MA{vol_ma_period}",
        line=dict(color="#c9a84c", width=1.5, dash="dot"),
        yaxis="y2",
    ))

    fig.update_layout(
        yaxis2=dict(
            overlaying="y", side="right",
            showgrid=False,
            title="Volume",
            title_font=dict(color="#7a9cc4"),
        )
    )

    return fig

# ══════════════════════════════════════════════════════════════
# MAIN — RUN SCANNER
# ══════════════════════════════════════════════════════════════

if run_btn:
    if not stock_list:
        st.warning("⚠️ กรุณาเลือกหรือใส่รายชื่อหุ้นก่อนครับ")
        st.stop()

    config = {
        "change_threshold":  change_th / 100,
        "volume_multiplier": vol_mult,
        "volume_ma_period":  20,
        "quiet_period_days": quiet_days,
        "quiet_threshold":   quiet_th / 100,
        "lookback_days":     lookback,
    }

    all_signals = []
    progress_bar = st.progress(0, text="กำลังสแกน...")
    status_text  = st.empty()

    for i, sym in enumerate(stock_list):
        pct = (i + 1) / len(stock_list)
        progress_bar.progress(pct, text=f"กำลังสแกน {sym} ({i+1}/{len(stock_list)})")
        signals = scan_one_stock(sym, config)
        all_signals.extend(signals)

    progress_bar.empty()
    status_text.empty()

    # บันทึก session
    st.session_state["signals"] = all_signals
    st.session_state["config"]  = config


# ══════════════════════════════════════════════════════════════
# SHOW RESULTS
# ══════════════════════════════════════════════════════════════

if "signals" in st.session_state and st.session_state["signals"] is not None:
    signals = st.session_state["signals"]

    # --- Metric Cards ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">พบสัญญาณ</div>
            <div class="value">{len(signals)}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        unique_sym = len(set(s['Symbol'] for s in signals)) if signals else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">จำนวนหุ้น</div>
            <div class="value">{unique_sym}</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        avg_vol = round(np.mean([s['Vol_Ratio_x'] for s in signals]), 1) if signals else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">Vol Ratio เฉลี่ย</div>
            <div class="value">{avg_vol}x</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not signals:
        st.info("ℹ️ ไม่พบสัญญาณในช่วงที่กำหนด ลองเพิ่ม lookback หรือลด threshold ดูครับ")
    else:
        # เรียงตาม Trading Value จากมากไปน้อยเป็นค่าเริ่มต้น
        # (หุ้นสภาพคล่องสูง/มีมูลค่าเทรดจริงเยอะ ขึ้นก่อน — กันไม่ให้หุ้น
        # เกรดต่ำที่ปั่นง่ายไปโผล่ปนอยู่ด้านบนของผลลัพธ์)
        df_result = pd.DataFrame(signals).sort_values("Trading_Value", ascending=False).reset_index(drop=True)
        df_result.index = df_result.index + 1

        # --- ตารางผลลัพธ์ ---
        st.markdown("### 📋 ผลการสแกน")
        st.caption(
            "🔴 แถวพื้นสีแดงอ่อน = Trading Value ต่ำกว่าเกณฑ์สภาพคล่องแนะนำของตลาดนั้นๆ "
            "(TH < 50M บาท · HK < 20M HKD · US < 5M USD) — ไม่ได้ตัดออก แค่เตือนให้ระวังความเสี่ยงถูกปั่นราคา"
        )

        display_df = df_result[["Symbol","Market","Date","Open","Close","Change_%","Vol_Ratio_x"]].copy()
        display_df["Trading Value"] = [
            fmt_trading_value(v, c) for v, c in zip(df_result["Trading_Value"], df_result["Currency"])
        ]
        display_df.columns = ["หุ้น","ตลาด","วันที่","Open","Close","บวก (%)","Vol Ratio","Trading Value"]
        display_df["บวก (%)"] = display_df["บวก (%)"].apply(lambda x: f"+{x:.1f}%")
        display_df["Vol Ratio"] = display_df["Vol Ratio"].apply(lambda x: f"{x:.1f}x")

        below_liq = df_result["Below_Liq"].values  # ใช้ align แถวกับ display_df

        def highlight_low_liquidity(row):
            idx = display_df.index.get_loc(row.name)
            if below_liq[idx]:
                return ["background-color: #4a1414; color: #ff9999"] * len(row)
            return [""] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_low_liquidity, axis=1),
            use_container_width=True,
            height=min(400, 60 + len(display_df) * 38),
        )

        # --- ดูกราฟแต่ละตัว ---
        st.markdown("### 📈 ดูกราฟ")

        options = [f"{s['Symbol']} — {s['Date']}" for s in signals]
        selected = st.selectbox("เลือกหุ้นที่ต้องการดู", options)

        if selected:
            idx = options.index(selected)
            sig = signals[idx]

            with st.spinner(f"กำลังโหลดกราฟ {sig['Symbol']}..."):
                df_chart = load_chart(sig["Full_Symbol"], sig["Date"])
                fig = plot_chart(df_chart, sig["Symbol"], sig["Date"])

            if fig:
                st.plotly_chart(fig, use_container_width=True)

                # Detail card
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Open",      f"{sig['Open']:.2f}")
                c2.metric("Close",     f"{sig['Close']:.2f}")
                c3.metric("บวก",       f"+{sig['Change_%']:.1f}%")
                c4.metric("Vol Ratio", f"{sig['Vol_Ratio_x']:.1f}x")
            else:
                st.error("โหลดข้อมูลกราฟไม่ได้ครับ")

elif not run_btn:
    st.markdown("""
    <div style="text-align:center; padding: 60px; color: #4a6a9a;">
        <div style="font-size: 48px;">🟢</div>
        <div style="font-size: 18px; margin-top: 12px;">ตั้งค่าและกด <b style="color:#c9a84c">เริ่มสแกน</b> ได้เลยครับ</div>
    </div>
    """, unsafe_allow_html=True)
