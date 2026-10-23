import pandas as pd
import requests
import streamlit as st

# मोबाइल-फ्रेंडली पेज कॉन्फ़िगरेशन
st.set_page_config(
    page_title="Delta Funding Tracker", page_icon="⚡", layout="wide"
)

# Custom CSS - मोबाइल UI को क्लीन और सुंदर बनाने के लिए
st.markdown(
    """
    <style>
    .stApp { padding: 10px; }
    .metric-card {
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("⚡ Delta Live Funding Rates")


# डेल्टा एक्सचेंज के पब्लिक API से डेटा लाना (बिना किसी Key/Login के)
@st.cache_data(ttl=15)  # हर 15 सेकंड में ऑटो-रिफ्रेश/कैश अपडेट
def get_delta_funding_data():
  # Delta India Public Ticker API Endpoint
  url = "https://api.india.delta.exchange/v2/tickers"
  headers = {"Accept": "application/json"}

  try:
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
      data = response.json().get("result", [])
      funding_list = []

      for item in data:
        # केवल Perpetual Futures कॉन्ट्रैक्ट्स को फिल्टर करना
        if item.get("contract_type") == "perpetual_futures":
          symbol = item.get("symbol")
          close_price = item.get("close", 0)

          # फंडिंग रेट निष्कर्षण (100 से गुणा करके % में बदलना)
          funding_rate = item.get("funding_rate")
          if funding_rate is not None:
            funding_rate_pct = float(funding_rate) * 100
          else:
            funding_rate_pct = 0.0

          funding_list.append({
              "Symbol": symbol,
              "Price": float(close_price),
              "Funding Rate (%)": round(funding_rate_pct, 4),
          })

      return pd.DataFrame(funding_list)
    else:
      return pd.DataFrame()
  except Exception as e:
    st.error(f"API Error: {e}")
    return pd.DataFrame()


# रिफ्रेश बटन
if st.button("🔄 Refresh Data"):
  st.cache_data.clear()

df = get_delta_funding_data()

if not df.empty:
  # मोबाइल फ्रेंडली फिल्टर्स
  col1, col2 = st.columns([1, 1])

  with col1:
    filter_type = st.selectbox(
        "🎯 Filter Coins:",
        ["All Coins", "Negative Funding Only 🔴", "Positive Funding Only 🟢"],
    )

  with col2:
    sort_order = st.selectbox(
        "📊 Sort Order:",
        [
            "Ascending (Lowest First)",
            "Descending (Highest First)",
            "Most Negative First",
        ],
    )

  # 1. फिल्टर लागू करना
  if filter_type == "Negative Funding Only 🔴":
    df_filtered = df[df["Funding Rate (%)"] < 0].copy()
  elif filter_type == "Positive Funding Only 🟢":
    df_filtered = df[df["Funding Rate (%)"] > 0].copy()
  else:
    df_filtered = df.copy()

  # 2. सॉर्टिंग लागू करना
  if (
      sort_order == "Ascending (Lowest First)"
      or sort_order == "Most Negative First"
  ):
    df_filtered = df_filtered.sort_values(
        by="Funding Rate (%)", ascending=True
    )
  else:
    df_filtered = df_filtered.sort_values(
        by="Funding Rate (%)", ascending=False
    )

  # समरी मेट्रिक्स
  st.caption(f"कुल मिले पर्पेटुअल कॉइन्स: **{len(df_filtered)}**")

  # मोबाइल-फ्रेंडली टेबल व्यू
  st.dataframe(
      df_filtered,
      column_config={
          "Symbol": st.column_config.TextColumn("Coin Symbol"),
          "Price": st.column_config.NumberColumn(
              "Price ($)", format="$%.4f"
          ),
          "Funding Rate (%)": st.column_config.NumberColumn(
              "Funding Rate (8h)", format="%.4f%%"
          ),
      },
      use_container_width=True,
      hide_index=True,
  )

else:
  st.warning("डेटा लोड हो रहा है या API से संपर्क नहीं हो पा रहा है...")