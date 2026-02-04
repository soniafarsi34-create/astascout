import streamlit as st
import pdfplumber
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import statistics

st.set_page_config(page_title="AstaScout AI", layout="wide")

st.title("🤖 AstaScout – Smart Auction Analyzer")

# ----------------------------
# Price Search Functions
# ----------------------------

def search_ebay(query):
    url = f"https://www.ebay.com/sch/i.html?_nkw={query}&LH_Sold=1&LH_Complete=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)

    prices = []

    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")

        for item in soup.select(".s-item__price"):
            txt = item.text
            nums = re.findall(r"\d+[,.]?\d*", txt)

            if nums:
                price = float(nums[0].replace(",", "").replace("€",""))
                prices.append(price)

    return prices[:10]


def search_google(query):
    url = f"https://www.google.com/search?q={query}+auction+sold+price"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)

    prices = []

    if r.status_code == 200:
        nums = re.findall(r"\d+[,.]?\d*", r.text)

        for n in nums[:10]:
            prices.append(float(n.replace(",", "")))

    return prices


def estimate_price(query):

    prices = []

    try:
        prices += search_ebay(query)
    except:
        pass

    try:
        prices += search_google(query)
    except:
        pass

    if len(prices) >= 3:
        return round(statistics.median(prices), 2)

    if prices:
        return round(statistics.mean(prices), 2)

    return 0


# ----------------------------
# App UI
# ----------------------------

uploaded_file = st.file_uploader("Upload Auction Catalog (PDF)", type="pdf")

lots = []

if uploaded_file:

    with pdfplumber.open(uploaded_file) as pdf:
        text = ""

        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"

    lines = text.split("\n")

    for line in lines:
        if len(line) > 25:
            lots.append(line.strip()[:120])

    st.success(f"Found {len(lots)} possible lots")

    df = pd.DataFrame({
        "Lot": lots,
        "Buy Price (€)": [0]*len(lots),
        "Expected Sell (€)": [0]*len(lots)
    })

    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button("🔍 Auto Estimate Prices"):

        with st.spinner("Searching online prices..."):

            for i, row in edited_df.iterrows():

                if row["Expected Sell (€)"] == 0:

                    price = estimate_price(row["Lot"])
                    edited_df.at[i, "Expected Sell (€)"] = price

        st.success("Automatic estimation completed!")

        st.data_editor(edited_df, num_rows="dynamic")

    if st.button("📊 Analyze Profit"):

        edited_df["Profit (€)"] = (
            edited_df["Expected Sell (€)"] -
            edited_df["Buy Price (€)"]
        )

        def advice(p):
            if p > 150:
                return "🟢 BUY"
            elif p > 0:
                return "🟡 MAYBE"
            else:
                return "🔴 SKIP"

        edited_df["Advice"] = edited_df["Profit (€)"].apply(advice)

        st.dataframe(edited_df)
