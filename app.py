import streamlit as st
import pandas as pd

st.set_page_config(page_title="Couple Debt Splitter", layout="wide")
st.title("🍽️ Couple Debt Splitter")

# Initialize session state storage
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}

# Upload section
uploaded_files = st.file_uploader("Upload one or more Excel files", type=["xlsx"], accept_multiple_files=True)

# Store uploaded files and their initial DataFrame
for file in uploaded_files:
    if file.name not in st.session_state.uploaded_files:
        st.session_state.uploaded_files[file.name] = file
        df = pd.read_excel(file, sheet_name=0)
        st.session_state.dataframes[file.name] = df

# File selection
if st.session_state.uploaded_files:
    selected_filename = st.selectbox("Select a file to analyze", list(st.session_state.uploaded_files.keys()))
    df = st.session_state.dataframes[selected_filename]

    st.subheader("Editable Data")

    # Editable data editor
    edited_df = st.experimental_data_editor(df, num_rows="dynamic", use_container_width=True, key="data_editor")

    # Update session state with edits
    st.session_state.dataframes[selected_filename] = edited_df

    # Add row functionality
    if st.button("➕ Add Empty Row"):
        empty_row = pd.Series({col: None for col in edited_df.columns})
        edited_df = pd.concat([edited_df, pd.DataFrame([empty_row])], ignore_index=True)
        st.session_state.dataframes[selected_filename] = edited_df
        st.rerun()

    # Format Total as currency if present
    formatted_df = edited_df.copy()
    if 'Total' in formatted_df.columns:
        try:
            formatted_df['Total'] = pd.to_numeric(formatted_df['Total'], errors='coerce')
            formatted_df['Total'] = formatted_df['Total'].map("${:,.2f}".format)
        except:
            pass

    st.subheader("Formatted Data View")
    st.dataframe(formatted_df)

    # Proceed with calculations only if required columns exist
    required_cols = ['Restaurant', 'Total']
    if not all(col in edited_df.columns for col in required_cols):
        st.warning("Missing required columns: 'Restaurant' and 'Total'. Please upload a valid sheet.")
        st.stop()

    couple_columns = edited_df.columns[3:]
    couple_list = couple_columns.tolist()

    st.sidebar.header("👥 Select Couples to Include")
    selected_couples = [
        couple for couple in couple_list
        if st.sidebar.checkbox(couple, value=True)
    ]

    if not selected_couples:
        st.warning("Please select at least one couple to include.")
        st.stop()

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

    filtered_df = edited_df[edited_df['Payer'].isin(selected_couples)].copy()

    calc_df = filtered_df[['Restaurant', 'Total', 'Couples to include', 'Payer', 'Share Per Couple']].copy()
    calc_df['Total'] = calc_df['Total'].map("${:,.2f}".format)
    calc_df['Share Per Couple'] = calc_df['Share Per Couple'].map("${:,.2f}".format)

    st.subheader("Calculated Payers & Share (Filtered)")
    st.dataframe(calc_df)

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

    st.subheader("Raw Debt Matrix (Before Netting)")
    st.dataframe(debt_matrix.style.format("${:,.2f}"))

    net_debt = debt_matrix.subtract(debt_matrix.T)

    styled_net_debt = net_debt.style \
        .format("${:,.2f}") \
        .applymap(lambda v: 'color: green;' if v > 0 else 'color: red;' if v < 0 else 'color: gray;') \
        .set_properties(**{'font-weight': 'bold'}) \
        .set_caption("💸 Net Debt Matrix — Positive = Row Couple Owes Column Couple")

    st.subheader("Net Debt Matrix (Final)")
    st.dataframe(styled_net_debt)

    st.markdown("✅ **Positive values** = row couple owes column couple.\
                \n✅ **Negative values** = row couple is owed by the column couple.")
else:
    st.info("Upload at least one Excel file to begin.")
