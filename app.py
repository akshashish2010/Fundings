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
            if item.get("contract_type") == "perpetual_futures":
                # Delta API returns funding_rate in decimal (e.g. -0.018093 = -1.8093%)
                raw_rate = float(item.get("funding_rate", 0) or 0)
                rate_pct = raw_rate * 100

                price = float(item.get("mark_price", 0) or 0)

                # Fetch interval: converts seconds or hours to standard 8, 4, 1
                interval = item.get("funding_interval_hours") or item.get(
                    "funding_interval"
                )
                if interval == 28800 or interval == 8:
                    hours = 8
                elif interval == 14400 or interval == 4:
                    hours = 4
                elif interval == 3600 or interval == 1:
                    hours = 1
                else:
                    hours = 8  # default fallback

                rate_8h = f"{rate_pct:.4f}%" if hours == 8 else "-"
                rate_4h = f"{rate_pct:.4f}%" if hours == 4 else "-"
                rate_1h = f"{rate_pct:.4f}%" if hours == 1 else "-"

                tv_url = f"https://www.tradingview.com/chart/?symbol=DELTA:{symbol}"

                parsed_data.append(
                    {
                        "Coin Symbol": symbol,
                        "Price ($)": f"${price:,.4f}",
                        "Funding (8h)": rate_8h,
                        "Funding (4h)": rate_4h,
                        "Funding (1h)": rate_1h,
                        "Chart": tv_url,
                        "raw_rate": rate_pct,
                    }
                )

        df = pd.DataFrame(parsed_data)
        if not df.empty:
            # Sort by most negative funding rate first (matching Delta screen)
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
    st.error("Data load nahi ho paya. Kripya refresh karein.")
