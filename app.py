selected_filename = st.selectbox("Select a file to work with", list(st.session_state.uploaded_files.keys()))
df = st.session_state.dataframes[selected_filename]

st.subheader("📝 Editable Table")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="data_editor")
st.session_state.dataframes[selected_filename] = edited_df

# Save to disk
save_path = os.path.join(SAVE_DIR, selected_filename.replace(".xlsx", ".csv"))
edited_df.to_csv(save_path, index=False)

# --- Normalize & Prep Columns Early ---
edited_df.columns = [col.strip() for col in edited_df.columns]
required_cols = ['Restaurant', 'Total']
if not all(col in edited_df.columns for col in required_cols):
    st.warning("Missing required columns like 'Restaurant' and 'Total'.")
    st.stop()

couple_columns = edited_df.columns[3:]
selected_couples = couple_columns.tolist()
if not selected_couples:
    st.warning("No couple columns found (expected columns after the third one).")
    st.stop()

# --- Early Filter ---
st.markdown("### 🔍 Filter: See Who a Couple Owes")
selected_view = st.selectbox("Choose a couple to view only their debts (ignore what others owe them)", selected_couples)
