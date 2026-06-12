"""
╔══════════════════════════════════════════════════════════════╗
║     🟢 THREE CAP — First Green Candle + Volume Scanner      ║
║     THREE CAP © 2026 | fb.com/threecap                      ║
╚══════════════════════════════════════════════════════════════╝

นิยาม "เขียวแท่งแรก + Volume พิเศษ":
  ✅ Close > Open (เขียว)
  ✅ %Change (Close vs Open) >= +10%
  ✅ Volume วันนั้น >= 3x ค่าเฉลี่ย Volume 20 วันก่อนหน้า
  ✅ ก่อนหน้า 30 วัน ไม่มีแท่งบวก >= 7% (นิ่ง หรือขาลง)

ตัวอย่าง: XO (8 มิ.ย. 2026), KGEN (27 พ.ย. 2025)

วิธีใช้:
  pip install yfinance pandas
  python first_green_scanner.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════════════════════
# ⚙️  CONFIG
# ══════════════════════════════════════════════════════════════
CONFIG = {
    "change_threshold":   0.10,   # แท่งเขียว >= +10%
    "volume_multiplier":  3.0,    # Volume >= 3x MA
    "volume_ma_period":   20,     # MA กี่วัน
    "quiet_period_days":  30,     # ดูย้อนหลังกี่วันว่า "นิ่ง"
    "quiet_threshold":    0.07,   # แท่งบวกในช่วงนิ่งห้ามเกิน 7%
    "lookback_days":      5,      # สแกนย้อนหลังกี่วัน (5 แท่ง = สัปดาห์นี้)
}

# ══════════════════════════════════════════════════════════════
# 📋  รายชื่อหุ้น SET (format: SYMBOL.BK)
# ══════════════════════════════════════════════════════════════
SET_STOCKS = [
    # ตัวอย่างจากรูป
    "XO.BK", "KGEN.BK",

    # Large Cap
    "PTT.BK", "PTTEP.BK", "PTTGC.BK", "AOT.BK", "CPALL.BK",
    "CP.BK", "SCC.BK", "KBANK.BK", "SCB.BK", "BBL.BK",
    "KTB.BK", "BAY.BK", "BDMS.BK", "BH.BK", "DELTA.BK",
    "ADVANC.BK", "GULF.BK", "GPSC.BK", "CPN.BK", "LH.BK",
    "MINT.BK", "CENTEL.BK", "IVL.BK", "TU.BK",

    # Mid / Small Cap
    "TIDLOR.BK", "MTC.BK", "SAWAD.BK",
    "SPALI.BK", "AP.BK", "LPN.BK", "QH.BK", "NOBLE.BK",
    "HANA.BK", "KCE.BK", "SVI.BK", "GFPT.BK",
    "TFMAMA.BK", "OSP.BK", "CBG.BK", "OISHI.BK", "M.BK",
    "MAJOR.BK", "RS.BK", "WORK.BK", "JMT.BK", "CHAYO.BK",
    "STGT.BK", "AAV.BK", "BA.BK", "WHA.BK", "AMATA.BK",
    "TPIPL.BK", "INTUCH.BK", "TRUE.BK",
]

# ══════════════════════════════════════════════════════════════
# 🔧  FUNCTIONS
# ══════════════════════════════════════════════════════════════

def is_quiet_before(df_full, current_iloc, quiet_days, quiet_threshold):
    """
    เช็คว่าช่วงก่อนหน้า current_iloc จำนวน quiet_days วัน
    ไม่มีแท่งบวกใหญ่ >= quiet_threshold
    → ถ้าผ่าน = หุ้นนิ่งหรือขาลงมาก่อน
    """
    start_i = max(0, current_iloc - quiet_days)
    prior = df_full.iloc[start_i:current_iloc]

    if len(prior) < 5:
        return False

    green_pct = (prior['Close'] - prior['Open']) / prior['Open']
    return green_pct.max() < quiet_threshold


def scan_one_stock(symbol, config):
    """สแกนหุ้น 1 ตัว — คืน list ของสัญญาณที่พบ"""
    found = []

    try:
        end   = datetime.today()
        start = end - timedelta(days=config["lookback_days"] + 90)

        df = yf.download(symbol, start=start, end=end,
                         progress=False, auto_adjust=True)

        # รองรับ MultiIndex column (yfinance บางเวอร์ชัน)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty or len(df) < config["volume_ma_period"] + 10:
            return found

        df = df.copy()

        # Volume MA (shift 1 = ไม่รวมวันปัจจุบัน)
        vm = config["volume_ma_period"]
        df['Vol_MA'] = df['Volume'].rolling(vm).mean()

        # % เปลี่ยนแปลง Open→Close
        df['Chg_OC'] = (df['Close'] - df['Open']) / df['Open']

        # Volume Ratio
        df['Vol_Ratio'] = df['Volume'] / df['Vol_MA']

        # กรองเฉพาะ lookback จริง
        cutoff = end - timedelta(days=config["lookback_days"])
        mask   = df.index >= pd.Timestamp(cutoff)
        df_scan = df[mask]

        for i, (dt, row) in enumerate(df_scan.iterrows()):

            # เงื่อนไข 1 — เขียวใหญ่
            if not (row['Close'] > row['Open']):
                continue
            if row['Chg_OC'] < config["change_threshold"]:
                continue

            # เงื่อนไข 2 — Volume พิเศษ
            if pd.isna(row['Vol_Ratio']):
                continue
            if row['Vol_Ratio'] < config["volume_multiplier"]:
                continue

            # เงื่อนไข 3 — นิ่ง/ขาลงมาก่อน
            global_i = df.index.get_loc(dt)
            quiet = is_quiet_before(df, global_i,
                                    config["quiet_period_days"],
                                    config["quiet_threshold"])
            if not quiet:
                continue

            # ✅ พบสัญญาณ
            found.append({
                "Symbol":      symbol.replace(".BK", ""),
                "Date":        dt.strftime("%Y-%m-%d"),
                "Open":        round(float(row['Open']),  2),
                "Close":       round(float(row['Close']), 2),
                "Change_%":    round(float(row['Chg_OC']) * 100, 2),
                "Volume":      int(row['Volume']),
                "Vol_MA20":    int(row['Vol_MA']) if not pd.isna(row['Vol_MA']) else 0,
                "Vol_Ratio_x": round(float(row['Vol_Ratio']), 1),
            })

    except Exception as e:
        print(f"  ⚠️  {symbol}: {e}")

    return found


# ══════════════════════════════════════════════════════════════
# 🚀  MAIN SCANNER
# ══════════════════════════════════════════════════════════════

def run_scanner(stock_list, config, filter_date_from=None):
    """
    สแกนทุกหุ้นในลิสต์
    filter_date_from: กรองผลเฉพาะวันที่ >= วันนี้ (YYYY-MM-DD)
    """
    print("\n" + "="*64)
    print("  🟢 THREE CAP — First Green Candle + Volume Scanner")
    print("="*64)
    print(f"  📊 หุ้น:           {len(stock_list)} ตัว")
    print(f"  📈 บวก >=          {config['change_threshold']*100:.0f}%  (Open→Close)")
    print(f"  📦 Volume >=       {config['volume_multiplier']}x  MA{config['volume_ma_period']}")
    print(f"  😴 Quiet period:   {config['quiet_period_days']} วัน")
    print(f"  🔍 ดูย้อนหลัง:    {config['lookback_days']} วัน")
    print("="*64)

    all_signals = []

    for idx, sym in enumerate(stock_list, 1):
        print(f"  [{idx:3d}/{len(stock_list)}] {sym:<15s}", end="\r")
        signals = scan_one_stock(sym, config)
        all_signals.extend(signals)

    print(" " * 60, end="\r")

    if not all_signals:
        print("\n  ❌ ไม่พบสัญญาณในช่วงที่กำหนด\n")
        return pd.DataFrame()

    df_out = pd.DataFrame(all_signals)
    df_out = df_out.sort_values("Date", ascending=False).reset_index(drop=True)

    if filter_date_from:
        df_out = df_out[df_out["Date"] >= filter_date_from].reset_index(drop=True)

    return df_out


def print_results(df):
    if df.empty:
        return

    print("\n" + "="*80)
    print("  🏆  ผลการสแกน")
    print("="*80)

    display = df.copy()
    display['Change_%']    = display['Change_%'].map(lambda x: f"+{x:.1f}%")
    display['Vol_Ratio_x'] = display['Vol_Ratio_x'].map(lambda x: f"{x:.1f}x")
    display['Volume']      = display['Volume'].map(lambda x: f"{x:,}")
    display['Vol_MA20']    = display['Vol_MA20'].map(lambda x: f"{x:,}")

    pd.set_option('display.max_rows',   200)
    pd.set_option('display.width',      120)
    pd.set_option('display.max_colwidth', 20)

    print(display.to_string(index=False))
    print("="*80)
    print(f"  รวม: {len(df)} สัญญาณ")
    print("="*80 + "\n")


# ══════════════════════════════════════════════════════════════
# ▶️  RUN
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":

    # --- สแกนทั้งหมด ---
    results = run_scanner(SET_STOCKS, CONFIG)
    print_results(results)

    if not results.empty:
        out_file = "first_green_results.csv"
        results.to_csv(out_file, index=False, encoding="utf-8-sig")
        print(f"  💾 บันทึก CSV → {out_file}\n")

    # --- ตรวจสอบเฉพาะ XO + KGEN ---
    print("\n  🔍 ทดสอบกับ XO และ KGEN (ตัวอย่างจากรูป)...")
    test = run_scanner(["XO.BK", "KGEN.BK"], CONFIG)
    print_results(test)
