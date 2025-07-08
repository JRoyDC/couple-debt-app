import streamlit as st
import pandas as pd
import numpy as np
import os

# --- Setup ---
st.set_page_config(page_title="Couple Debt Splitter", layout="wide")
st.title("🍽️ Couple Debt Splitter")

SAVE_DIR = "saved_data"
SAVE_FILE = os.path.join(SAVE_DIR, "latest.csv")
os.makedirs(SAVE_DIR, exist_ok=True)

# --- File Upload ---
st.markdown("### 📤 Upload Excel File")

uploaded_file = st.file_uploader("Upload a single Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0)
    df.to_csv(SAVE_FILE, index=False)
    st.success("✅ File uploaded and saved. The app will now use this file.")
    st.rerun()

# --- Load saved data if available ---
if os.path.exists(SAVE_FILE):
    df = pd.read_csv(SAVE_FILE)

    df.columns = [col.strip() for col in df.columns]
    required_cols = ['Restaurant', 'Total']
    if not all(col in df.columns for col in required_cols):
        st.warning("Missing required columns like 'Restaurant' and 'Total'.")
        st.stop()

    couple_columns = df.columns[3:]
    selected_couples = couple_columns.tolist()
    if not selected_couples:
        st.warning("No couple columns found (expected columns after the third one).")
        st.stop()

    # --- Filter UI ---
    st.markdown("### 🔍 Filter: See Which Couple Owes Which Couple")
    selected_view = st.selectbox("Choose a couple", selected_couples)

    # --- Build Debt Matrix ---
    debt_matrix = pd.DataFrame(0.0, index=selected_couples, columns=selected_couples)

    for _, row in df.iterrows():
        payer = None
        for couple in selected_couples:
            try:
                if pd.notnull(row[couple]) and float(row[couple]) < 0:
                    payer = couple
                    break
            except:
                continue
        if not payer:
            continue

        for couple in selected_couples:
            try:
                value = float(row[couple])
                if pd.notnull(value) and value > 0:
                    debt_matrix.loc[couple, payer] += value
            except:
                continue

    net_debt = debt_matrix.subtract(debt_matrix.T)

    # --- Filtered Result ---
    if selected_view:
        filtered_row = net_debt.loc[[selected_view]].copy()
        filtered_row = filtered_row.applymap(lambda v: v if v > 0 else np.nan)

        st.subheader(f"💳 What {selected_view} Owes Others")
        st.dataframe(
            filtered_row.style
            .format("${:,.2f}")
            .set_properties(**{"font-weight": "bold"})
            .set_caption(f"{selected_view} — Owes These Couples")
        )

    # --- Full Table ---
    st.subheader("📄 Transaction Table")
    st.dataframe(df, use_container_width=True)

    # --- Raw Debt Matrix ---
    st.subheader("📊 Raw Debt Matrix")
    st.dataframe(debt_matrix.style.format("${:,.2f}"))

    # --- Net Debt Matrix ---
    styled_net = net_debt.style \
        .format("${:,.2f}") \
        .applymap(lambda v: 'color: green;' if v > 0 else 'color: red;' if v < 0 else 'color: gray;') \
        .set_properties(**{'font-weight': 'bold'}) \
        .set_caption("💸 Net Debt Matrix — Positive = Row Owes Column")

    st.subheader("💸 Net Debt Matrix")
    st.dataframe(styled_net)

    st.markdown("""
    ✅ **Positive values** = row couple owes column couple  
    ✅ **Negative values** = row couple is owed by column couple
    """)
else:
    st.info("📂 Please upload a file to begin.")
