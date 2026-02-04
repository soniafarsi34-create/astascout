import streamlit as st
import pdfplumber
import pandas as pd

st.set_page_config(page_title="AstaScout", layout="wide")

st.title("📊 AstaScout – Auction Analyzer")

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
        if len(line) > 20:
            lots.append(line.strip())

    st.success(f"Found {len(lots)} possible lots")

    df = pd.DataFrame({
        "Lot": lots,
        "Buy Price (€)": [0]*len(lots),
        "Expected Sell (€)": [0]*len(lots)
    })

    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button("Analyze"):
        edited_df["Profit (€)"] = (
            edited_df["Expected Sell (€)"] -
            edited_df["Buy Price (€)"]
        )

        def advice(p):
            if p > 100:
                return "🟢 BUY"
            elif p > 0:
                return "🟡 MAYBE"
            else:
                return "🔴 SKIP"

        edited_df["Advice"] = edited_df["Profit (€)"].apply(advice)

        st.dataframe(edited_df)
