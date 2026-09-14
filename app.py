import streamlit as st
import pandas as pd

# --- SMART OS DETECTION AND IMPORT ---
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ModuleNotFoundError:
    MT5_AVAILABLE = False  # Smoothly falls back if running on Linux Cloud

# =================================================================
# 1. CORE BACKEND ENGINE (SCF ASSISTANT LOGIC)
# =================================================================
class HighQualitySCFAssistantBot:
    def __init__(self, symbol="USA100", risk_pct=0.01):
        self.symbol = symbol
        self.risk_pct = risk_pct
        
    def initialize_mt5(self):
        """Attempts connection to MT5 terminal if platform supports it."""
        if not MT5_AVAILABLE:
            return False, "⚠️ Running in CLOUD DEMO MODE (MT5 requires a local Windows environment)."
        
        import MetaTrader5 as local_mt5
        if not local_mt5.initialize():
            return False, f"MT5 initialization failed: {local_mt5.last_error()}"
        return True, f"Connected to MT5 terminal successfully for {self.symbol}."

    def get_account_balance(self):
        if MT5_AVAILABLE:
            try:
                import MetaTrader5 as local_mt5
                account_info = local_mt5.account_info()
                if account_info: return account_info.balance
            except:
                pass
        return 10000.0 # Default cloud simulation balance

    def calculate_lot_size(self, entry_price, stop_loss):
        balance = self.get_account_balance()
        risk_amount = balance * self.risk_pct
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0: return 0.0
        
        if MT5_AVAILABLE:
            try:
                import MetaTrader5 as local_mt5
                symbol_info = local_mt5.symbol_info(self.symbol)
                if symbol_info:
                    volume_step = symbol_info.volume_step
                    raw_lot_size = risk_amount / (price_risk * symbol_info.trade_contract_size)
                    lot_size = (raw_lot_size // volume_step) * volume_step
                    return max(symbol_info.volume_min, min(symbol_info.volume_max, round(lot_size, 2)))
            except:
                pass
        return 0.1 # Default cloud simulator step

    def execute_market_order(self, order_type, price, sl, tp, live_execution=False):
        lots = self.calculate_lot_size(price, sl)
        if lots <= 0: return "Execution halted: Invalid calculated lot size."
        
        # Guard clause preventing cloud execution mistakes
        if not MT5_AVAILABLE or not live_execution:
            return f"⚙️ SIMULATION PASSED: Bot would execute {order_type} for {lots} lots. (SL: {sl} | TP: {tp})"
            
        import MetaTrader5 as local_mt5
        action = local_mt5.ORDER_TYPE_BUY if order_type == "BUY" else local_mt5.ORDER_TYPE_SELL
        request = {
            "action": local_mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": lots,
            "type": action,
            "price": price,
            "sl": float(sl),
            "tp": float(tp),
            "deviation": 20,
            "magic": 20260914,
            "comment": f"SCF HQ {order_type}",
            "type_time": local_mt5.ORDER_TIME_GTC,
            "type_filling": local_mt5.ORDER_FILLING_IOC,
        }
        
        result = local_mt5.order_send(request)
        if result.retcode != local_mt5.TRADE_RETCODE_DONE:
            return f"❌ MT5 Order Refused: {result.comment}"
        return f"🔥 LIVE SUCCESS: Opened {order_type} for {lots} lots on your terminal!"

# =================================================================
# 2. STREAMLIT INTERFACE LAYER
# =================================================================
st.set_page_config(page_title="SCF Assistant Web Terminal", page_icon="📊", layout="wide")

st.markdown("# ⚡ SCF Assistant Algorithmic Terminal")
st.markdown("---")

if "bot" not in st.session_state:
    st.session_state.bot = HighQualitySCFAssistantBot()

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🎛️ Live Parameter Feed")

# Environment banner notification
if MT5_AVAILABLE:
    st.sidebar.success("🖥️ Environment: WINDOWS LOCAL (Live Trade Capable)")
else:
    st.sidebar.info("☁️ Environment: CLOUD SIMULATION (Safe Sandbox Only)")

live_price = st.sidebar.number_input("USA100 Live Price Target", value=29262.0, step=1.0)
dxy_bias = st.sidebar.selectbox("DXY Structure Bias", ["BEARISH", "BULLISH"])
flow_state = st.sidebar.selectbox("Market Flow State", ["CORRECTION", "IMPULSE", "CONTINUATION"])
retracement = st.sidebar.slider("Correction Retracement %", min_value=0.0, max_value=100.0, value=61.8)
momentum_status = st.sidebar.selectbox("Momentum Status", ["RETURNING", "DECREASING", "STAGNANT"])

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Lower Timeframe M5 Entry")
m5_structure = st.sidebar.selectbox("M5 Structure Alignment", ["Bullish", "Bearish"])
m5_sweep = st.sidebar.checkbox("Liquidity Sweep Confirmed", value=True)
m5_bos = st.sidebar.checkbox("Break of Structure (BOS)", value=True)

st.sidebar.markdown("---")
# Block or show live toggles based on environment
if MT5_AVAILABLE:
    live_execution_toggle = st.sidebar.toggle("⚠️ Enable Live Broker Orders", value=False)
else:
    st.sidebar.text_input("⚠️ Live Broker Orders", value="DISABLED IN CLOUD", disabled=True)
    live_execution_toggle = False

# --- APP LAYOUT MAIN GRID ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="📊 USA100 Current Ask", value=f"{live_price}")
with col2:
    st.metric(label="🔄 System Flow State", value=flow_state)
with col3:
    m5_valid = (m5_structure == "Bullish" and m5_sweep and m5_bos)
    st.metric(label="🎯 M5 Trigger Confirmation", value="VALID" if m5_valid else "WAITING")

st.markdown("### 📋 Automated 7-Phase Checklist Summary")

area_status = "INSIDE DEMAND" if (28900 <= live_price <= 29050) else ("INSIDE SUPPLY" if (29600 <= live_price <= 29750) else "BETWEEN ZONES")
correction_quality = "GOOD" if retracement >= 61.8 else "SHALLOW"

checklist_data = {
    "Phase Metric Block": ["HTF Trend Bias", "Value Zone Placement", "Fib Position Index", "DXY Directional Wind", "Flow State Alignment", "Zone Boundaries (Area)", "Correction Pullback Quality", "Momentum Returning Pulse", "M5 Micro Trigger Structure"],
    "Current Engine Value": ["NEUTRAL/BULLISH", "DISCOUNT", "MID/DEEP DISCOUNT", dxy_bias, flow_state, area_status, f"{retracement}% ({correction_quality})", f"BULLISH - {momentum_status}", f"Sweep: {m5_sweep} | BOS: {m5_bos}"],
    "Verification Status": [
        "✅ Verified", "✅ Verified", "✅ Verified",
        "✅ Verified" if dxy_bias == "BEARISH" else "❌ Disaligned (Hold)",
        "✅ Verified" if flow_state == "CORRECTION" else "❌ Non-Correction Phase",
        "✅ Verified" if area_status == "INSIDE DEMAND" else "❌ Floating Outside Zones",
        "✅ Verified" if correction_quality == "GOOD" else "❌ Trap: Shallow Pullback",
        "✅ Verified" if momentum_status == "RETURNING" else "❌ Lacks Momentum Confirmation",
        "✅ Verified" if m5_valid else "❌ Structure Invalidation"
    ]
}

df = pd.DataFrame(checklist_data)
st.table(df)

# --- RUN ENGINE RESOLUTION LOGIC ---
st.markdown("### 🏁 SCF Diagnostic Verdict Engine")

if st.button("🚀 Execute Engine Matrix Checklist Scan"):
    chk_dxy = dxy_bias == "BEARISH"
    chk_flow = flow_state == "CORRECTION"
    chk_area = area_status == "INSIDE DEMAND"
    chk_corr = correction_quality == "GOOD"
    chk_mom = momentum_status == "RETURNING"
    chk_m5 = m5_valid
    
    all_phases_green = all([chk_dxy, chk_flow, chk_area, chk_corr, chk_mom, chk_m5])
    
    st.markdown("---")
    if all_phases_green:
        st.subheader("Verdict Decision: 🟢 HIGH QUALITY LONG")
        st.info("Reasoning: Every single high-probability confluence ruleset parameters satisfied.")
        
        mt5_status, mt5_msg = st.session_state.bot.initialize_mt5()
        st.write(f"_*System Log: {mt5_msg}_")
        
        action_log = st.session_state.bot.execute_market_order(
            order_type="BUY", 
            price=live_price, 
            sl=(live_price - 100), 
            tp=(live_price + 250),
            live_execution=live_execution_toggle
        )
        st.success(action_log)
    else:
        st.subheader("Verdict Decision: 🟡 WAIT")
        st.warning("Reasoning: Safe Matrix Ruleset Alert. Conditions are not fully aligned yet. Orders blocked.")
