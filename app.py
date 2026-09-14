import streamlit as st
import pandas as pd
import time

# --- SMART OS DETECTION AND IMPORT ---
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ModuleNotFoundError:
    MT5_AVAILABLE = False

# =================================================================
# 1. CORE BACKEND ENGINE (SCF ASSISTANT LOGIC)
# =================================================================
class HighQualitySCFAssistantBot:
    def __init__(self, symbol="USA100", risk_pct=0.01):
        self.symbol = symbol
        self.risk_pct = risk_pct
        self.mt5_initialized = False
        
    def initialize_mt5(self):
        if not MT5_AVAILABLE:
            return False, "⚠️ Running in CLOUD DEMO MODE (MT5 requires a local Windows environment)."
        if not self.mt5_initialized:
            if not mt5.initialize():
                return False, f"MT5 initialization failed: {mt5.last_error()}"
            self.mt5_initialized = True
        return True, f"Connected to MT5 terminal successfully for {self.symbol}."

    def fetch_live_price(self):
        success, msg = self.initialize_mt5()
        if not success: return None
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None: return None
        return tick.ask 

    def calculate_fib_retracement(self, timeframe=1, lookback_candles=50):
        """Calculates macro high, low, 61.8% line and live pullback metrics."""
        success, msg = self.initialize_mt5()
        if not success:
            # Safe basic values for cloud tracking sandbox
            return {
                "high": 29500.0, 
                "low": 28900.0, 
                "level_618": 29128.0, 
                "current_retracement": 61.8
            }
            
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, lookback_candles)
        if rates is None or len(rates) == 0:
            return {"high": 0.0, "low": 0.0, "level_618": 0.0, "current_retracement": 0.0}
            
        df_rates = pd.DataFrame(rates)
        swing_high = float(df_rates['high'].max())
        swing_low = float(df_rates['low'].min())
        total_range = swing_high - swing_low
        
        if total_range == 0:
            return {"high": swing_high, "low": swing_low, "level_618": swing_high, "current_retracement": 0.0}
            
        live_price = self.fetch_live_price()
        if not live_price: live_price = swing_high
        
        current_retracement = ((swing_high - live_price) / total_range) * 100
        level_618 = swing_high - (total_range * 0.618)
        
        return {
            "high": round(swing_high, 2), 
            "low": round(swing_low, 2), 
            "level_618": round(level_618, 2), 
            "current_retracement": round(current_retracement, 2)
        }

    def check_momentum_reversal(self, timeframe=5):
        """Evaluates candle body ratios to confirm buy pressure intensity."""
        success, msg = self.initialize_mt5()
        if not success:
            return {"momentum": "BULLISH", "status": "RETURNING", "confirmed": True}
            
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 1, 2)
        if rates is None or len(rates) < 2:
            return {"momentum": "BEARISH", "status": "STAGNANT", "confirmed": False}
            
        # Using explicit list indexing to safely parse local MT5 numpy arrays
        prev_candle = rates[0]
        last_candle = rates[1]
        
        prev_body = prev_candle['close'] - prev_candle['open']
        last_body = last_candle['close'] - last_candle['open']
        
        is_prev_bearish = prev_body < 0
        is_last_bullish = last_body > 0
        engulfs_range = abs(last_body) >= abs(prev_body)
        
        if is_prev_bearish and is_last_bullish and engulfs_range:
            return {"momentum": "BULLISH", "status": "RETURNING", "confirmed": True}
        elif is_last_bullish:
            return {"momentum": "BULLISH", "status": "STABILIZING", "confirmed": False}
        else:
            return {"momentum": "BEARISH", "status": "DECREASING", "confirmed": False}

    def get_account_balance(self):
        if MT5_AVAILABLE and self.mt5_initialized:
            account_info = mt5.account_info()
            if account_info: return account_info.balance
        return 10000.0 

    def calculate_lot_size(self, entry_price, stop_loss):
        balance = self.get_account_balance()
        risk_amount = balance * self.risk_pct
        price_risk = abs(entry_price - stop_loss)
        if price_risk == 0: return 0.0
        
        if MT5_AVAILABLE and self.mt5_initialized:
            try:
                symbol_info = mt5.symbol_info(self.symbol)
                if symbol_info:
                    volume_step = symbol_info.volume_step
                    raw_lot_size = risk_amount / (price_risk * symbol_info.trade_contract_size)
                    lot_size = (raw_lot_size // volume_step) * volume_step
                    return max(symbol_info.volume_min, min(symbol_info.volume_max, round(lot_size, 2)))
            except:
                pass
        return 0.1 

    def execute_market_order(self, order_type, price, sl, tp, live_execution=False):
        lots = self.calculate_lot_size(price, sl)
        if lots <= 0: return "Execution halted: Invalid calculated lot size."
        
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

if MT5_AVAILABLE:
    st.sidebar.success("🖥️ Environment: WINDOWS LOCAL (Live Trade Capable)")
    fetched_price = st.session_state.bot.fetch_live_price()
    if fetched_price:
        live_price = fetched_price
        st.sidebar.metric(label="🔄 Live Feed Price Status", value="ACTIVE", delta="Streaming Tick Data")
    else:
        st.sidebar.warning("⚠️ Terminal Open but Symbol Not Found.")
        live_price = st.sidebar.number_input("USA100 Live Price Target", value=29262.0, step=1.0)
else:
    st.sidebar.info("☁️ Environment: CLOUD SIMULATION (Safe Sandbox Only)")
    live_price = st.sidebar.number_input("USA100 Live Price Target", value=29262.0, step=1.0)

# --- LOOKBACK WINDOW SETTINGS ---
st.sidebar.markdown("---")
st.sidebar.header("📐 Fibonacci Lookback Setup")
tf_choice = st.sidebar.selectbox("Fib Lookback Timeframe", ["1 Hour (H1)", "15 Minute (M15)", "4 Hour (H4)"])
tf_map = {"1 Hour (H1)": 16385, "15 Minute (M15)": 15, "4 Hour (H4)": 16388}

lookback_input = st.sidebar.slider("Historical Candle Lookback Depth", min_value=10, max_value=200, value=50, step=5)

fib_metrics = st.session_state.bot.calculate_fib_retracement(timeframe=tf_map[tf_choice] if MT5_AVAILABLE else 1, lookback_candles=lookback_input)
retracement = fib_metrics["current_retracement"]

# --- MOMENTUM SETTINGS ---
st.sidebar.markdown("---")
st.sidebar.header("🔥 Momentum Validation Window")
m_tf_choice = st.sidebar.selectbox("Momentum Evaluation TF", ["5 Minute (M5)", "1 Minute (M1)", "15 Minute (M15)"])
m_tf_map = {"5 Minute (M5)": 5, "1 Minute (M1)": 1, "15 Minute (M15)": 15}

momentum_metrics = st.session_state.bot.check_momentum_reversal(timeframe=m_tf_map[m_tf_choice] if MT5_AVAILABLE else 5)

dxy_bias = st.sidebar.selectbox("DXY Structure Bias", ["BEARISH", "BULLISH"])
flow_state = st.sidebar.selectbox("Market Flow State", ["CORRECTION", "IMPULSE", "CONTINUATION"])

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Lower Timeframe M5 Entry")
m5_structure = st.sidebar.selectbox("M5 Structure Alignment", ["Bullish", "Bearish"])
m5_sweep = st.sidebar.checkbox("Liquidity Sweep Confirmed", value=True)
m5_bos = st.sidebar.checkbox("Break of Structure (BOS)", value=True)

st.sidebar.markdown("---")
if MT5_AVAILABLE:
    live_execution_toggle = st.sidebar.toggle("⚠️ Enable Live Broker Orders", value=False)
    auto_refresh = st.sidebar.checkbox("🔄 Auto-Refresh Tick Stream (1s)", value=False)
else:
    live_execution_toggle = False
    auto_refresh = False

# --- APP LAYOUT MAIN GRID ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="📊 USA100 Real-Time Ask", value=str(round(live_price, 2)))
with col2:
    st.metric(label="🔄 System Flow State", value=str(flow_state))
with col3:
    m5_valid = (m5_structure == "Bullish" and m5_sweep and m5_bos)
    st.metric(label="🎯 M5 Trigger Confirmation", value="VALID" if m5_valid else "WAITING")

# --- BULLETPROOF FLAT DATA SCANNER ROW ---
st.markdown("### 📈 Automated Math Scanner Data (Phase 4 & 5)")
mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("Structural High Found", str(fib_metrics.get("high", 0.0)))
