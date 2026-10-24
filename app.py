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


@st.cache_data(ttl=60)
def fetch_funding_data():
    url = "https://api.delta.exchange/v2/tickers"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get("result", [])
        parsed_data = []

        for item in data:
            symbol = item.get("symbol", "")
            if item.get("contract_type") == "perpetual_futures":
                funding_rate = float(item.get("funding_rate", 0) or 0)
                price = float(item.get("mark_price", 0) or 0)
                interval_hours = item.get("funding_interval_hours", 8)

                rate_8h = (
                    f"{funding_rate:.4f}%" if interval_hours == 8 else "-"
                )
                rate_4h = (
                    f"{funding_rate:.4f}%" if interval_hours == 4 else "-"
                )
                rate_1h = (
                    f"{funding_rate:.4f}%" if interval_hours == 1 else "-"
                )

                # TradingView Link for the coin
                tv_url = f"https://www.tradingview.com/chart/?symbol=DELTA:{symbol}"

                parsed_data.append(
                    {
                        "Coin Symbol": symbol,
                        "Price ($)": f"${price:,.4f}",
                        "Funding (8h)": rate_8h,
                        "Funding (4h)": rate_4h,
                        "Funding (1h)": rate_1h,
                        "Chart": tv_url,
                        "raw_rate": funding_rate,
                    }
                )

        df = pd.DataFrame(parsed_data)
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

    # Display DataFrame with Clickable Link Column for Charts
    st.dataframe(
        df,
        column_config={
            "Coin Symbol": st.column_config.TextColumn("Coin Symbol"),
            "Price ($)": st.column_config.TextColumn("Price ($)"),
            "Funding (8h)": st.column_config.TextColumn("Funding (8h)"),
            "Funding (4h)": st.column_config.TextColumn("Funding (4h)"),
            "Funding (1h)": st.column_config.TextColumn("Funding (1h)"),
            "Chart": st.column_config.LinkColumn(
                "TradingView Chart",
                help="Click to open chart",
                display_text="📈 View Chart",
            ),
            "raw_rate": None,
        },
        use_container_width=True,
        hide_index=True,
    )
else:
    st.error("डेटा लोड नहीं हो पाया। कृपया रिफ्रेश करें।")
