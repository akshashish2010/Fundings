import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Delta Funding Rates", layout="wide")

st.markdown(
    """
    <style>
    th {
        font-size: 16px !important;
        font-weight: 800 !important;
        color: #1E293B !important;
    }
    td {
        font-size: 15px !important;
        font-weight: 600 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("⚡ Delta Exchange Funding Rates")

if st.button("🔄 Refresh Data"):
    st.rerun()


@st.cache_data(ttl=30)
def fetch_funding_data():
  url = "https://api.delta.exchange/v2/tickers"
  response = requests.get(url)
  if response.status_code == 200:
    data = response.json().get("result", [])
    parsed_data = []

    for item in data:
      symbol = item.get("symbol", "")
      # Saare valid perpetual contracts capture karne ke liye funding_rate check karenge
      if "funding_rate" in item and item.get("funding_rate") is not None:
        raw_rate = float(item.get("funding_rate", 0) or 0)
        rate_pct = raw_rate * 100
        price = float(item.get("mark_price", 0) or 0)

        # Interval check
        interval = item.get("funding_interval") or item.get(
            "funding_interval_hours"
        )
        if interval in [14400, 4]:
          hours = 4
        elif interval in [3600, 1]:
          hours = 1
        else:
          hours = 8

        # Single column formatting with interval suffix
        funding_str = f"{rate_pct:.4f}% / {hours}h"

        # Direct Delta Exchange trade link taaki wahi coin khule
        delta_url = f"https://www.delta.exchange/app/trade/perpetual/{symbol}"

        parsed_data.append({
            "Coin Symbol": symbol,
            "Price ($)": f"${price:,.4f}",
            "Funding Rate": funding_str,
            "Chart": delta_url,
            "raw_rate": rate_pct,
        })

    df = pd.DataFrame(parsed_data)
    if not df.empty:
      # Sabse negative funding rate sabse upar aayegi (Ascending order)
      df = df.sort_values(by="raw_rate", ascending=True)
    return df
  return pd.DataFrame()


df = fetch_funding_data()

if not df.empty:
  filter_option = st.selectbox(
      "🎯 Filter Coins:",
      ["All Coins", "Negative Funding Only 🔴", "Positive Funding Only 🟢"],
  )

  if filter_option == "Negative Funding Only 🔴":
    df = df[df["raw_rate"] < 0]
  elif filter_option == "Positive Funding Only 🟢":
    df = df[df["raw_rate"] > 0]

  st.dataframe(
      df,
      column_config={
          "Coin Symbol": st.column_config.TextColumn("Coin Symbol"),
          "Price ($)": st.column_config.TextColumn("Price ($)"),
          "Funding Rate": st.column_config.TextColumn("Funding Rate"),
          "Chart": st.column_config.LinkColumn(
              "Delta Chart",
              help="Click to open chart",
              display_text="📈 View Chart",
          ),
          "raw_rate": None,
      },
      use_container_width=True,
      hide_index=True,
  )
else:
  st.error("Data load nahi ho paya. Kripya refresh karein.")
