import streamlit as st
import pandas as pd

st.set_page_config(page_title="Couple Debt Splitter", layout="wide")

st.title("🍽️ Couple Debt Splitter")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0)
    st.subheader("Original Data")
    
    # Format Total as currency
    formatted_df = df.copy()
    if 'Total' in formatted_df.columns:
        formatted_df['Total'] = formatted_df['Total'].map("${:,.2f}".format)
    st.dataframe(formatted_df)

    # Extract couple columns
    couple_columns = df.columns[3:]
    couple_list = couple_columns.tolist()

    # Add helper columns
    def identify_payer(row):
        for couple in couple_list:
            if row[couple] < 0:
                return couple
        return None

    df['Payer'] = df.apply(identify_payer, axis=1)
    df['Share Per Couple'] = df['Total'] / df['Couples to include']

    calc_df = df[['Restaurant', 'Total', 'Couples to include', 'Payer', 'Share Per Couple']].copy()
    calc_df['Total'] = calc_df['Total'].map("${:,.2f}".format)
    calc_df['Share Per Couple'] = calc_df['Share Per Couple'].map("${:,.2f}".format)

    st.subheader("Calculated Payers & Share")
    st.dataframe(calc_df)

    # Create debt matrix
    debt_matrix = pd.DataFrame(0.0, index=couple_list, columns=couple_list)

    for _, row in df.iterrows():
        payer = row['Payer']
        if payer:
            share = row['Share Per Couple']
            for couple in couple_list:
                if row[couple] > 0:
                    debt_matrix.loc[couple, payer] += share

    st.subheader("Raw Debt Matrix (Before Netting)")
    st.dataframe(debt_matrix.style.format("${:,.2f}"))

    # Net the debts
    net_debt = debt_matrix.subtract(debt_matrix.T)
    st.subheader("Net Debt Matrix (Final)")
    st.dataframe(net_debt.style.format("${:,.2f}"))

    st.markdown("✅ **Positive numbers** mean the row couple owes the column couple.")
else:
    st.info("Please upload an Excel file to begin.")
