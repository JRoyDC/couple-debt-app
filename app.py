import streamlit as st
import pandas as pd
import numpy as np
import os

# --- Setup ---
st.set_page_config(page_title="Couple Debt Splitter", layout="wide")
st.title("🍽️ Couple Debt Splitter")

SAVE_DIR = "saved_data"
os.makedirs(SAVE_DIR, exist_ok=True)

# --- Upload Files ---
uploaded_files = st.file_uploader("Upload Excel files", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    if "initial_upload_handled" not in st.session_state:
        st.session_state.uploaded_files = {}
        st.session_state.dataframes = {}

        for f in os.listdir(SAVE_DIR):
            if f.endswith(".csv"):
                os.remove(os.path.join(SAVE_DIR, f))

        for file in uploaded_files:
            df = pd.read_excel(file, sheet_name=0)
            st.session_state.uploaded_files[file.name] = file
            st.session_state.dataframes[file.name] = df

        st.session_state.initial_upload_handled = True
        st.info("🔄 New file uploaded. Previous data cleared.")
        st.rerun()

# --- Load Saved Files if No Upload ---
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}

saved_files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".csv")]
for filename in saved_files:
    if filename not in st.session_state.uploaded_files:
        filepath = os.path.join(SAVE_DIR, filename)
        st.session_state.uploaded_files[filename] = filepath
        st.session_state.dataframes[filename] = pd.read_csv(filepath)

# --- Main Interface ---
if st.session_state.uploaded_files:
    selected_filename = st.selectbox("Select a file to work with", list(st.session_state.uploaded_files.keys()))
    df = st.session_state.dataframes[selected_filename]

    # Normalize column names
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

    # --- Filter UI Above All ---
    st.markdown("### 🔍 Filter: See Which Couple owes Which Couple")
    selected_view = st.selectbox("Choose a couple to view only their debts", selected_couples)

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

    # --- Filtered Table Right Below Filter ---
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

    # --- Full Table (Read-only) ---
    st.subheader("📄 Transaction Table (Read-Only)")
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
    st.info("Upload at least one Excel file to begin.")
