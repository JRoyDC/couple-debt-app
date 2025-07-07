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

uploaded_files = st.file_uploader("Upload one or more Excel files", type=["xlsx"], accept_multiple_files=True)

# Load from saved CSVs if they exist
saved_files = [f for f in os.listdir(SAVE_DIR) if f.endswith(".csv")]
for filename in saved_files:
    if filename not in st.session_state.uploaded_files:
        filepath = os.path.join(SAVE_DIR, filename)
        st.session_state.uploaded_files[filename] = filepath
        st.session_state.dataframes[filename] = pd.read_csv(filepath)

# Process new uploads
for file in uploaded_files:
    if file.name not in st.session_state.uploaded_files:
        df = pd.read_excel(file, sheet_name=0)
        st.session_state.uploaded_files[file.name] = file
        st.session_state.dataframes[file.name] = df

if st.session_state.uploaded_files:
    selected_filename = st.selectbox("Select a file to view/edit", list(st.session_state.uploaded_files.keys()))
    df = st.session_state.dataframes[selected_filename]

    st.subheader("Editable Data")

    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="data_editor")
    st.session_state.dataframes[selected_filename] = edited_df

    # Save changes to CSV
    save_path = os.path.join(SAVE_DIR, selected_filename.replace(".xlsx", ".csv"))
    edited_df.to_csv(save_path, index=False)
    st.success(f"Changes saved to `{save_path}`")

    if st.button("➕ Add Empty Row"):
        empty_row = pd.Series({col: None for col in edited_df.columns})
        edited_df = pd.concat([edited_df, pd.DataFrame([empty_row])], ignore_index=True)
        st.session_state.dataframes[selected_filename] = edited_df
        edited_df.to_csv(save_path, index=False)
        st.rerun()

    st.subheader("Preview")
    row_height = 35
    max_height = 1000
    table_height = min(max_height, 50 + len(edited_df) * row_height)
    st.dataframe(edited_df, use_container_width=True, height=table_height)
else:
    st.info("Upload an Excel file to begin.")
