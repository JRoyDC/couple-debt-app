import streamlit as st
import pandas as pd

st.set_page_config(page_title="Couple Debt Splitter", layout="wide")
st.title("🍽️ Couple Debt Splitter")

# Initialize uploaded files dictionary in session state
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

# Upload section
uploaded_files = st.file_uploader("Upload one or more Excel files", type=["xlsx"], accept_multiple_files=True)

# Store uploaded files in session_state
for file in uploaded_files:
    if file.name not in st.session_state.uploaded_files:
        st.session_state.uploaded_files[file.name] = file

# If any files are uploaded
if st.session_state.uploaded_files:
    selected_filename = st.selectbox("Select a file to analyze", list(st.session_state.uploaded_files.keys()))
    file = st.session_state.uploaded_files[selected_filename]

    df = pd.read_excel(file, sheet_name=0)
    st.subheader("Original Data")

    # Format Total as currency if it exists
    formatted_df = df.copy()
    if 'Total' in formatted_df.columns:
        formatted_df['Total'] = formatted_df['Total'].map("${:,.2f}".format)
    st.dataframe(formatted_df)

    # Extract couple columns
    couple_columns = df.columns[3:]
    couple_list = couple_columns.tolist()

    # Sidebar checkboxes to include/exclude couples
    st.sidebar.header("👥 Select Couples to Include")
    selected_couples = [
        couple for couple in couple_list
        if st.sidebar.checkbox(couple, value=True)
    ]

    if not selected_couples:
        st.warning("Please select at least one couple to include.")
        st.stop()

    # Identify payer
    def identify_payer(row):
        for couple in selected_couples:
            if couple in row and row[couple] < 0:
                return couple
        return None

    df['Payer'] = df.apply(identify_payer, axis=1)

    # Protect against division errors
    df['Share Per Couple'] = df.apply(
        lambda row: row['Total'] / row['Couples to include'] if row['Couples to include'] > 0 else 0, axis=1
    )

    # Filter out rows where payer isn't in selected couples
    filtered_df = df[df['Payer'].isin(selected_couples)].copy()

    # Display payer and share breakdown
    calc_df = filtered_df[['Restaurant', 'Total', 'Couples to include', 'Payer', 'Share Per Couple']].copy()
    calc_df['Total'] = calc_df['Total'].map("${:,.2f}".format)
    calc_df['Share Per Couple'] = calc_df['Share Per Couple'].map("${:,.2f}".format)

    st.subheader("Calculated Payers & Share (Filtered)")
    st.dataframe(calc_df)

    # Create debt matrix
    debt_matrix = pd.DataFrame(0.0, index=selected_couples, columns=selected_couples)

    for _, row in filtered_df.iterrows():
        payer = row['Payer']
        share = row['Share Per Couple']
        if payer:
            for couple in selected_couples:
                if couple in row and row[couple] > 0:
                    debt_matrix.loc[couple, payer] += share

    st.subheader("Raw Debt Matrix (Before Netting)")
    st.dataframe(debt_matrix.style.format("${:,.2f}"))

    # Net the debts
    net_debt = debt_matrix.subtract(debt_matrix.T)

    # Style the net matrix
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
