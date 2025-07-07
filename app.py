import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Couple Debt Splitter", layout="wide")
st.title("🍽️ Couple Debt Splitter")

SAVE_DIR = "saved_data"
os.makedirs(SAVE_DIR, exist_ok=True)

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}

# Load previously saved CSVs
saved_files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".csv")]
for filename in saved_files:
    if filename not in st.session_state.uploaded_files:
        filepath = os.path.join(SAVE_DIR, filename)
        st.session_state.uploaded_files[filename] = filepath
        st.session_state.dataframes[filename] = pd.read_csv(filepath)

# Upload new Excel files
uploaded_files = st.file_uploader("Upload Excel files", type=["xlsx"], accept_multiple_files=True)
for file in uploaded_files:
    if file.name not in st.session_state.uploaded_files:
        df = pd.read_excel(file, sheet_name=0)
        st.session_state.uploaded_files[file.name] = file
        st.session_state.dataframes[file.name] = df

if st.session_state.uploaded_files:
    selected_filename = st.selectbox("Select a file to work with", list(st.session_state.uploaded_files.keys()))
    df = st.session_state.dataframes[selected_filename]

    st.subheader("📝 Editable Table")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="data_editor")
    st.session_state.dataframes[selected_filename] = edited_df

    # Save to CSV
    save_path = os.path.join(SAVE_DIR, selected_filename.replace(".xlsx", ".csv"))
    edited_df.to_csv(save_path, index=False)

    if st.button("➕ Add Empty Row"):
        empty_row = pd.Series({col: None for col in edited_df.columns})
        edited_df = pd.concat([edited_df, pd.DataFrame([empty_row])], ignore_index=True)
        st.session_state.dataframes[selected_filename] = edited_df
        edited_df.to_csv(save_path, index=False)
        st.rerun()

    # Display preview
    st.subheader("📋 Table Preview")
    row_height = 35
    table_height = min(1000, 50 + len(edited_df) * row_height)
    st.dataframe(edited_df, use_container_width=True, height=table_height)

    # Proceed if valid
    required_cols = ['Restaurant', 'Total']
    if not all(col in edited_df.columns for col in required_cols):
        st.warning("Missing required columns like 'Restaurant' or 'Total'.")
        st.stop()

    couple_columns = edited_df.columns[3:]
    selected_couples = couple_columns.tolist()
    if not selected_couples:
        st.warning("No couple columns found (expected columns after the third one).")
        st.stop()

    # Recalculate
    def identify_payer(row):
        for couple in selected_couples:
            try:
                if couple in row and float(row[couple]) < 0:
                    return couple
            except:
                continue
        return None

    edited_df['Payer'] = edited_df.apply(identify_payer, axis=1)
    edited_df['Couples to include'] = edited_df[selected_couples].notnull().sum(axis=1)
    edited_df['Share Per Couple'] = edited_df.apply(
        lambda row: float(row['Total']) / row['Couples to include']
        if row['Couples to include'] > 0 and pd.notnull(row['Total']) else 0, axis=1
    )

    # Filter valid rows
    filtered_df = edited_df[edited_df['Payer'].isin(selected_couples)].copy()

    # Display summary
    st.subheader("🧾 Calculated Payers & Share")
    calc_df = filtered_df[['Restaurant', 'Total', 'Couples to include', 'Payer', 'Share Per Couple']].copy()
    calc_df['Total'] = pd.to_numeric(calc_df['Total'], errors='coerce').map("${:,.2f}".format)
    calc_df['Share Per Couple'] = calc_df['Share Per Couple'].map("${:,.2f}".format)
    st.dataframe(calc_df, use_container_width=True)

    # Debt Matrix
    debt_matrix = pd.DataFrame(0.0, index=selected_couples, columns=selected_couples)
    for _, row in filtered_df.iterrows():
        payer = row['Payer']
        share = row['Share Per Couple']
        if payer:
            for couple in selected_couples:
                try:
                    if pd.notnull(row[couple]) and float(row[couple]) > 0:
                        debt_matrix.loc[couple, payer] += share
                except:
                    continue

    st.subheader("📊 Raw Debt Matrix")
    st.dataframe(debt_matrix.style.format("${:,.2f}"))

    # Net debts
    net_debt = debt_matrix.subtract(debt_matrix.T)
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
