import streamlit as st
import pandas as pd
import io

# --- Helper Function to read file ---
def load_data(uploaded_file):
    """Loads an uploaded CSV or Excel file into a pandas DataFrame."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            # Use a buffer to avoid "ValueError: I/O operation on closed file."
            buffer = io.BytesIO(uploaded_file.getvalue())
            df = pd.read_excel(buffer)
        else:
            st.error(f"Unsupported file format: {uploaded_file.name}")
            return None
        return df
    except Exception as e:
        st.error(f"Error reading {uploaded_file.name}: {e}")
        return None

# --- Helper Function to convert df to csv for download ---
@st.cache_data
def convert_df_to_csv(df):
    """Converts a DataFrame to a CSV string for downloading."""
    return df.to_csv(index=False).encode('utf-8')

# --- Page Configuration ---
st.set_page_config(
    page_title="Data Merger App",
    page_icon="🔄",
    layout="wide"
)

# --- App Title ---
st.title("🔄 Table Merger App")
st.write("Upload 2 or 3 Excel or CSV files to merge them based on selected key columns.")

# --- Session State Initialization ---
if 'merged_df_1_2' not in st.session_state:
    st.session_state.merged_df_1_2 = None
if 'df1' not in st.session_state:
    st.session_state.df1 = None
if 'df2' not in st.session_state:
    st.session_state.df2 = None
if 'df3' not in st.session_state:
    st.session_state.df3 = None

# --- Main Layout (2 Columns) ---
col1, col2 = st.columns(2)

# --- Column 1: File 1 & 2 Upload and First Merge ---
with col1:
    st.header("Step 1: Merge First Two Files")
    
    # --- File 1 Upload ---
    with st.container(border=True):
        st.subheader("File 1 (Left Table)")
        file_1 = st.file_uploader("Upload your first file (CSV or Excel)", type=["csv", "xls", "xlsx"], key="file1")
        if file_1:
            st.session_state.df1 = load_data(file_1)
            if st.session_state.df1 is not None:
                st.dataframe(st.session_state.df1.head(), use_container_width=True)
                keys_1 = st.multiselect("Select key column(s) for File 1", st.session_state.df1.columns, key="keys1")

    # --- File 2 Upload ---
    with st.container(border=True):
        st.subheader("File 2 (Right Table)")
        file_2 = st.file_uploader("Upload your second file (CSV or Excel)", type=["csv", "xls", "xlsx"], key="file2")
        if file_2:
            st.session_state.df2 = load_data(file_2)
            if st.session_state.df2 is not None:
                st.dataframe(st.session_state.df2.head(), use_container_width=True)
                keys_2 = st.multiselect("Select key column(s) for File 2", st.session_state.df2.columns, key="keys2")

    # --- Merge 1 & 2 Logic ---
    if st.session_state.df1 is not None and st.session_state.df2 is not None:
        if keys_1 and keys_2:
            if len(keys_1) != len(keys_2):
                st.warning("Warning: You have selected a different number of key columns for each table. This is allowed, but ensure they correspond correctly.")
            
            how_merge_1_2 = st.selectbox(
                "Select merge type for Files 1 & 2",
                ("inner", "left", "right", "outer"),
                key="how12"
            )
            
            if st.button("Merge Files 1 & 2", type="primary"):
                try:
                    st.session_state.merged_df_1_2 = pd.merge(
                        st.session_state.df1,
                        st.session_state.df2,
                        left_on=keys_1,
                        right_on=keys_2,
                        how=how_merge_1_2,
                        suffixes=('_f1', '_f2') # Add suffixes to avoid column name clashes
                    )
                    st.success("Files 1 & 2 merged successfully!")
                except Exception as e:
                    st.error(f"Merge failed: {e}")
                    st.session_state.merged_df_1_2 = None
        else:
            st.info("Select key columns for both files to enable merging.")

# --- Column 2: File 3 Upload and Second Merge ---
with col2:
    st.header("Step 2: Merge with Third File (Optional)")

    if st.session_state.merged_df_1_2 is not None:
        st.subheader("Merged Table (1 & 2)")
        st.dataframe(st.session_state.merged_df_1_2.head(), use_container_width=True)
        
        # --- Download Button for Intermediate Merge ---
        csv_1_2 = convert_df_to_csv(st.session_state.merged_df_1_2)
        st.download_button(
            label="Download Merged Data (1 & 2)",
            data=csv_1_2,
            file_name="merged_1_and_2.csv",
            mime="text/csv",
        )

        # --- File 3 Upload ---
        with st.container(border=True):
            st.subheader("File 3 (Right Table)")
            file_3 = st.file_uploader("Upload your third file (CSV or Excel)", type=["csv", "xls", "xlsx"], key="file3")
            
            if file_3:
                st.session_state.df3 = load_data(file_3)
                if st.session_state.df3 is not None:
                    st.dataframe(st.session_state.df3.head(), use_container_width=True)
                    
                    # --- Merge 3 Logic ---
                    keys_merged = st.multiselect(
                        "Select key column(s) from the Merged Table (Left)", 
                        st.session_state.merged_df_1_2.columns, 
                        key="keys_merged"
                    )
                    keys_3 = st.multiselect(
                        "Select key column(s) for File 3 (Right)", 
                        st.session_state.df3.columns, 
                        key="keys3"
                    )
                    
                    if keys_merged and keys_3:
                        if len(keys_merged) != len(keys_3):
                            st.warning("Warning: You have selected a different number of key columns for each table.")
                        
                        how_merge_3 = st.selectbox(
                            "Select merge type for final merge",
                            ("inner", "left", "right", "outer"),
                            key="how3"
                        )
                        
                        if st.button("Merge with File 3", type="primary"):
                            try:
                                final_merged_df = pd.merge(
                                    st.session_state.merged_df_1_2,
                                    st.session_state.df3,
                                    left_on=keys_merged,
                                    right_on=keys_3,
                                    how=how_merge_3,
                                    suffixes=('_merged', '_f3')
                                )
                                st.success("Final merge successful!")
                                st.subheader("Final Merged Table")
                                st.dataframe(final_merged_df, use_container_width=True)
                                
                                # --- Final Download Button ---
                                csv_final = convert_df_to_csv(final_merged_df)
                                st.download_button(
                                    label="Download Final Merged Data",
                                    data=csv_final,
                                    file_name="final_merged_data.csv",
                                    mime="text/csv",
                                )
                            except Exception as e:
                                st.error(f"Final merge failed: {e}")
                    else:
                        st.info("Select key columns for both tables to enable final merge.")
    else:
        st.info("Complete Step 1 to enable merging with a third file.")
