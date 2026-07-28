import gspread
from numpy import var
import pandas as pd
import streamlit as st
import datetime
import time
from google.oauth2.service_account import Credentials
st.markdown(
    """
    <style>
    /* Keeps header block accessible for the sidebar button but clears visible graphics */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        box-shadow: none !important;
    }
    
    /* Nukes the entire toolbar/fork button block while leaving the sidebar space alone */
    header[data-testid="stHeader"] > div:first-child {
        display: none !important;
    }
    
    /* Explicit backup override specifically targeting the deployment/fork cluster buttons */
    [data-testid="stHeaderActionElements"], .stAppDeployButton, [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
    }
         
    /* Cleans up the top blank margin left over by the hidden header */
    .main .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Configure the Streamlit page layout
st.set_page_config(page_title="Bbwenda Fashion", layout="wide")
st.markdown("""
    <style>
    /* 1. Base Editor Wrapper: Adds card styling and smooth glow on interaction */
    div[data-testid="stDataEditor"] {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        padding: 6px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* 2. Focused Interaction: Changes border color to your brand signature color when editing */
    div[data-testid="stDataEditor"]:focus-within,
    div[data-testid="stDataEditor"]:hover {
        border-color: #ff4b4b;
        box-shadow: 0 10px 15px -3px rgba(255, 75, 75, 0.08), 0 4px 6px -2px rgba(255, 75, 75, 0.04);
    }

    /* 3. Toolbar and Add Row Action Button Customization */
    div[data-testid="stDataEditor"] button {
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stDataEditor"] button:hover {
        background-color: #fff5f5 !important;
        color: #ff4b4b !important;
    }

    /* 4. Streamlit Metric Cards Cohesiveness Layout */
    div[data-testid="stMetricValue"] {
        font-family: 'Segoe UI Mono', monospace !important;
        font-weight: 700 !important;
        color: #1a202c;
    }
    </style>
""", unsafe_allow_html=True)


# Standard modern API scope list
SCOPE = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# --- 1. SINGLE POINT INITIALIZATION FUNCTION ---
@st.cache_resource
def get_google_sheet_workbook(workbook_name):
    """
    Authenticates and opens a global persistent workbook connection reference.
    Returns BOTH the authorized client and the opened workbook.
    """
    try:
        # Fetch dictionary from st.secrets
        service_account_info = st.secrets["gcp_service_account"]
        
        # Build strict v4 API credentials
        credentials = Credentials.from_service_account_info(
            service_account_info, 
            scopes=SCOPE
        )
        
        # Explicit authorization pipeline sequence
        gspread_client = gspread.authorize(credentials)
        
        # Open the specific workbook
        opened_workbook = gspread_client.open(workbook_name)
        
        # Return both elements so they are globally accessible to your save functions
        return gspread_client, opened_workbook
        
    except Exception as api_err:
        st.error("🔒 Google API Authentication Failed. Please verify your secrets configuration.")
        st.exception(api_err)
        st.stop()

# --- 2. INSTANTIATE WORKBOOK AND WORKSHEETS ---
# Unpack both variables from our single cached resource function call
client, sheet = get_google_sheet_workbook("Bb_Fasion")

# Reference sheets using the verified global sheet object
financial_sheet = sheet.worksheet("BBFASION")


# --- SIDEBAR NAVIGATION ---
#st.sidebar.title("Navigation")
selection = st.sidebar.radio(
    "Go to page:", ["Home","New Transaction Entry"]
)

# --- PAGE 1: HOME ---
if selection == "Home":
    st.write(
        '<p style="font-family: Chiller; color: #42c8f5; font-size: 60px; font-weight: bold; text-align: center; margin-bottom: 20px;">📊 Bbwenda Fashion</p>',
        unsafe_allow_html=True,
    )
    
    # 1. Google Sheets Connection
    try:
        client, sheet = get_google_sheet_workbook("Bb_Fasion")
        financial_sheet = sheet.worksheet("BBFASION")
        data = financial_sheet.get_all_records()
        df = pd.DataFrame(data)
    except NameError:
        # FIXED: Restored valid Google OAuth endpoints for Sheets and Drive.
        scope = [
            'https://googleapis.com',
            'https://googleapis.com'
        ]
        service_account_info = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("Bb_Fasion")
        financial_sheet = sheet.worksheet("BBFASION")
        data = financial_sheet.get_all_records()
        df = pd.DataFrame(data)

    # Clean date data types safely
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        valid_dates = df["Date"].dropna()
    else:
        valid_dates = pd.Series()

    # 1. Initialize session state keys safely
    if "col_sel_key" not in st.session_state:
        st.session_state.col_sel_key = "None"

    # Optimized clear function using State Callback Pattern
    def clear_all_filters():
        # Reset standard inputs
        st.session_state.col_sel_key = "None"
        st.session_state.start_date_key = valid_dates.min().date() if not valid_dates.empty else None
        st.session_state.end_date_key = valid_dates.max().date() if not valid_dates.empty else None
    
        # Flush out all dynamic multiselect states to avoid memory drift
        for key in list(st.session_state.keys()):
            if key.startswith("val_sel_key_"):
                del st.session_state[key]

    # 2. Sidebar Configuration Layout
    st.sidebar.header("⏳ Date Options")

    start_date = st.sidebar.date_input(
        "Start Date", 
        value=valid_dates.min().date() if not valid_dates.empty else None,
        key="start_date_key"
    )

    end_date = st.sidebar.date_input(
        "End Date", 
        value=valid_dates.max().date() if not valid_dates.empty else None,
        key="end_date_key"
    )

    #st.sidebar.markdown("---")
    st.sidebar.header("🎯 Filter by Record Type")

    # Copy the DataFrame to keep operations isolated
    filtered_df = df.copy()

    # Exclude Date column from being picked as a text filter
    ignore_cols = ["Date"]
    available_filter_columns = [col for col in filtered_df.columns if col not in ignore_cols]

    selected_column = st.sidebar.selectbox(
        "Select Column to Filter By",
        options=["None"] + available_filter_columns,
        key="col_sel_key"
    )

    # Multi-Select Values Configuration
    selected_values = []
    if selected_column != "None":
        unique_values = filtered_df[selected_column].astype(str).str.strip().unique()
        unique_values = [v for v in unique_values if v != ""]
        unique_values.sort()
    
        selected_values = st.sidebar.multiselect(
            f"Select Values for {selected_column}",
            options=unique_values,
            key=f"val_sel_key_{selected_column}"
        )

    #st.sidebar.markdown("---")
    # Reset Action Button (Triggers rerun instantly via callback)
    st.sidebar.button("🧹 Clear All Filters", on_click=clear_all_filters, use_container_width=True)

    # [Keep your previous Session State and Sidebar Filter logic here]

    # 3. Apply Multi-Stage Filtering Logic
    if selected_column != "None" and selected_values:
        filtered_df = filtered_df[filtered_df[selected_column].astype(str).str.strip().isin(selected_values)]

    if "Date" in filtered_df.columns and start_date and end_date:
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)
        filtered_df = filtered_df[
            (filtered_df["Date"] >= start_datetime) & 
            (filtered_df["Date"] <= end_datetime)
        ]

    # Explicitly target your confirmed dataframe column keys
    type_col = "Transaction"
    amount_col = "Amount"

    # 4. Main Page Display & Download Action
    st.write(
            '<p style="font-family: Arial Nova Cond; color: #695e82; font-size: 25px; font-weight: bold; text-align: left; margin-bottom: 20px;">📋 Transaction Records</p>',
            unsafe_allow_html=True,
        )

    if not filtered_df.empty:
        # --- METRICS SECTION START ---
        total_count = len(filtered_df)
        total_sum = 0.0

        if amount_col in filtered_df.columns:
            total_sum = pd.to_numeric(filtered_df[amount_col], errors='coerce').fillna(0).sum()

        metric_label = f"{', '.join(selected_values)}" if selected_values else "All Categories"
        if len(metric_label) > 30:
            metric_label = metric_label[:27] + "..."

        # 1. Determine dynamic theme colors based on financial performance
        if total_sum > 0:
            # Theme for positive returns (Green)
            text_color = "#2e7d32"      
            border_color = "#a5d6a7"    
            hover_border = "#2e7d32"    
            bg_glow = "rgba(46, 125, 50, 0.05)"
        elif total_sum < 0:
            # Theme for negative returns (Red)
            text_color = "#d32f2f"      
            border_color = "#ef9a9a"    
            hover_border = "#d32f2f"    
            bg_glow = "rgba(211, 47, 47, 0.05)"
        else:
            # Default Theme for zero balance (Neutral grey)
            text_color = "#1c1c1c"      
            border_color = "#e0e0e0"    
            hover_border = "#ff4b4b"    
            bg_glow = "rgba(0,0,0,0.05)"

        # 2. Injecting modern responsive layout CSS with dynamic color hooks
        st.markdown(
            f"""
            <style>
            .metric-container {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
                transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
            }}
            .metric-container:hover {{
                transform: translateY(-4px);
                box-shadow: 4px 8px 15px rgba(0,0,0,0.1);
                border-color: #ff4b4b;
            }}
            /* Target customized class for dynamic conditional coloring */
            .financial-metric {{
                border-color: {border_color};
                background-color: {bg_glow};
            }}
            .financial-metric:hover {{
                border-color: {hover_border} !important;
            }}
            .metric-title {{ font-size: 14px; color: #6c757d; text-transform: uppercase; letter-spacing: 1px; }}
            .metric-value {{ font-size: 28px; font-weight: bold; color: #1c1c1c; margin-top: 5px; }}
            .metric-value-dynamic {{ font-size: 28px; font-weight: bold; color: {text_color}; margin-top: 5px; }}
            .metric-subtitle {{ font-size: 12px; color: #888888; margin-top: 5px; }}
            </style>
            """,
            unsafe_allow_html=True
        )

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.markdown(f'<div class="metric-container"><div class="metric-title">Transactions Count</div><div class="metric-value">{total_count:,}</div><div class="metric-subtitle">Matching scope rows</div></div>', unsafe_allow_html=True)
        with m_col2:
            # Format the value cleanly, making sure negative signs are handled beautifully
            formatted_sum = f"Ugx{total_sum:,}" if total_sum >= 0 else f"-Ugx{abs(total_sum):,}"
        
            # Apply the unique 'financial-metric' class to the second container box
            st.markdown(
                f"""
                <div class="metric-container financial-metric">
                    <div class="metric-title">Total Amount</div>
                    <div class="metric-value-dynamic">{formatted_sum}</div>
                    <div class="metric-subtitle">Filtered by: {metric_label}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Detailed Table view display
        display_df = filtered_df.copy()
        if "Date" in display_df.columns:
            display_df["Date"] = display_df["Date"].dt.strftime('%Y-%m-%d')
        st.dataframe(display_df, use_container_width=True)

        # CSV Exporter Component
        csv = filtered_df.to_csv(index=False)
        st.download_button(label="Export as CSV", data=csv, file_name="filtered_transactions.csv", mime="text/csv")

        # --- GRAPH GENERATION START ---
        st.markdown("---")
        st.write(
                    '<p style="font-family: Arial Nova Cond; color: #695e82; font-size: 30px; font-weight: bold; text-align: left; margin-bottom: 20px;">📊 BB_Fashion Financial Position</p>',
                    unsafe_allow_html=True,
                )
    
        if type_col in filtered_df.columns and amount_col in filtered_df.columns:
            chart_df = filtered_df.copy()
            chart_df[type_col] = chart_df[type_col].astype(str).str.strip().str.lower()
            chart_df[amount_col] = pd.to_numeric(chart_df[amount_col], errors='coerce').fillna(0)
        
            # Parse based on explicit keyword variations inside your "Transaction" data rows
            sales_total = chart_df[chart_df[type_col].str.contains("sale", na=False)][amount_col].sum()
            purchases_total = chart_df[chart_df[type_col].str.contains("purchase", na=False)][amount_col].sum()
            expenses_total = chart_df[chart_df[type_col].str.contains("expense", na=False)][amount_col].sum()
        
            # Net balance calculation logic
            net_amount = sales_total + (purchases_total + expenses_total)
        
            plot_data = pd.DataFrame({
                "Transaction Type": ["Net Amount","Sales", "Purchases", "Expenses" ],
                "Total Amount (Ugx)": [net_amount, sales_total, purchases_total, expenses_total]
            })
        
            st.bar_chart(data=plot_data, x="Transaction Type", y="Total Amount (Ugx)", color="Transaction Type", use_container_width=True)
        
            if net_amount >= 0:
                st.success(f"🟢 **Net Position:** Surplus of **Ugx{net_amount:}**")
            else:
                st.error(f"🔴 **Net Position:** Deficit of **Ugx{abs(net_amount):}**")
        else:
            st.warning(f"⚠️ Missing columns. Please verify that your file has `{type_col}` and `{amount_col}` fields.")
    else:
        st.warning("No financial transactions match your current sidebar criteria.")



# --- PAGE 3: CAPTURE A TRANSACTION ---
elif selection == "New Transaction Entry":
    import streamlit.components.v1 as components

    # --- MOBILE OPTIMIZATION: Inject CSS to force smooth mobile scrolling & clean column widths ---
    st.html(
        """
        <style>
        /* Force table container to adapt nicely on small mobile screens */
        [data-testid="stDataEditor"] {
            overflow-x: auto !important;
            max-width: 100% !important;
        }
        /* Make metrics readable on vertical mobile screens */
        [data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
        }
        </style>
        """
    )
    
    st.write(
            '<p style="font-family: Chiller; color: #695e82; font-size: 35px; font-weight: bold; text-align: center; margin-bottom: 20px;">Bbwenda Fashion_Sales, Purchases & Expenses entry section</p>',
            unsafe_allow_html=True,
        )
    # Initialize key session states safely
    if "editor_session_id" not in st.session_state:
        st.session_state.editor_session_id = 0

    if "last_saved_summary" not in st.session_state:
        st.session_state.last_saved_summary = None

    TRANSACTION_OPTIONS = [
        "--Select Transaction--",
        "Sales",
        "Purchases",
        "Expenses",
    ]

    baseline_df = pd.DataFrame(
        [{
            "Customer Name": "Optional",
            "Item/Particulars": "",
            "Quantity": 1,
            "Price (Ugx)": 0,
            "Contact Number": "",
            "Description / Notes": ""
        }]
    )

    # --- 1. BATCH CONFIGURATION LINE ---
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        tx_date = st.date_input("Transaction Date", datetime.date.today())
    with col_d2:
        global_tx_type = st.selectbox(
            "Transaction Type",
            TRANSACTION_OPTIONS,
            key=f"tx_type_{st.session_state.editor_session_id}"
        )

    # --- 2. RENDER THE DATA EDITOR ---
    editor_key = f"tx_editor_{st.session_state.editor_session_id}"
    st.caption("✨ **Tip:** Double-click any cell to modify values, or use the bottom row to add entries.")

    edited_df = st.data_editor(
        baseline_df,
        key=editor_key,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Customer Name": st.column_config.TextColumn("👤 Customer Name"),
            "Item/Particulars": st.column_config.TextColumn("📦 Particulars"),
            "Quantity": st.column_config.NumberColumn("🔢 Quantity", min_value=1, step=1),
            "Price (Ugx)": st.column_config.NumberColumn("🏷️ Price (Ugx)", min_value=0, step=500),
            "Amount (Ugx)": None,  # Hides the column completely from user view
            "Contact Number": st.column_config.TextColumn(
                "📞 Contact Number",
                help="Enter customer or vendor phone number"
            ),
            "Description / Notes": st.column_config.TextColumn(
                "📝 Description / Notes",
                help="Enter meaningful transaction breakdown notes or leave blank"
            ),
        },
    )

    # --- 3. LIVE METRICS SUMMARY ---
    live_editor_state = st.session_state.get(editor_key, {})
    live_df = baseline_df.copy()
    
    live_edited = live_editor_state.get("edited_rows", {})
    live_added = live_editor_state.get("added_rows", [])
    live_deleted = live_editor_state.get("deleted_rows", [])

    for r_idx, changes in live_edited.items():
        act_idx = int(r_idx) if isinstance(r_idx, str) else r_idx
        for col, val in changes.items():
            live_df.at[act_idx, col] = val

    for added_row in live_added:
        live_df = pd.concat([live_df, pd.DataFrame([added_row])], ignore_index=True)

    if live_deleted:
        live_df = live_df.drop(index=[int(i) for i in live_deleted]).reset_index(drop=True)

    total_rows = len(live_df)
    live_total_amount = 0.0
    for _, row in live_df.iterrows():
        r_qty = int(row.get("Quantity", 1)) if pd.notna(row.get("Quantity")) else 1
        r_price = float(row.get("Price (Ugx)", 0)) if pd.notna(row.get("Price (Ugx)")) else 0.0
        live_total_amount += (r_qty * r_price)

    is_negative_type = global_tx_type in ["Purchases", "Expenses"]
    display_amount = -live_total_amount if is_negative_type else live_total_amount

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="Total Entries in Batch", value=f"{total_rows} rows")
    with col_m2:
        st.metric(label="Total Transaction Amount", value=f"Ugx {int(display_amount):,}")

    st.caption("⚠️ Review rows and metrics carefully before submission.")

    # --- 4. SUBMIT BUTTON ---
    submit_btn = st.button("Save All Transactions", type="primary")

    # --- 5. PROCESSING LOGIC RUNS POST-CLICK ---
    if submit_btn:
        if live_df.empty:
            st.error("❌ Please add at least one transaction row.")
        elif global_tx_type == "--Select Transaction--":
            st.error("❌ Please select a valid Transaction Type at the top dropdown.")
        else:
            has_errors = False
            rows_to_append = []
            summary_rows_markdown = []
            current_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for idx, row in live_df.iterrows():
                cust_name = str(row.get("Customer Name", "Optional")) if pd.notna(row.get("Customer Name")) else "Optional"
                item_part = str(row.get("Item/Particulars", "")) if pd.notna(row.get("Item/Particulars")) else "--Select Item--"
                
                raw_qty = row.get("Quantity", 1)
                qty = int(raw_qty) if pd.notna(raw_qty) else 1
                
                raw_price = row.get("Price (Ugx)", 0)
                price = float(raw_price) if pd.notna(raw_price) else 0.0
                
                # Skip accidental empty rows at bottom
                if price == 0 and item_part in ["--Select Item--", ""]:
                    continue
                
                if is_negative_type:
                    price = -abs(price)
                    amount = float(qty * price)
                else:
                    price = abs(price)
                    amount = float(qty * price)

                raw_contact = row.get("Contact Number", "")
                contact_num = str(raw_contact).strip() if pd.notna(raw_contact) else ""
                if contact_num.lower() == "none":
                    contact_num = ""

                raw_desc = row.get("Description / Notes", "")
                desc = str(raw_desc).strip() if pd.notna(raw_desc) else ""
                if desc.lower() == "none":
                    desc = ""
                
                if abs(amount) <= 0:
                    st.error(f"❌ Row {idx+1}: Price must be greater than 0 Ugx.")
                    has_errors = True

                if not has_errors:
                    rows_to_append.append([
                        tx_date.strftime("%Y-%m-%d"),
                        cust_name,
                        global_tx_type,
                        item_part,
                        qty,
                        price,
                        amount,
                        contact_num,
                        desc,
                        current_ts
                    ])
                    receipt_contact = contact_num if contact_num != "" else "*N/A*"
                    receipt_desc = desc if desc != "" else "*No notes*"
                    summary_rows_markdown.append(
                        f"| {cust_name} | {item_part} | {qty} | Ugx {int(price):,} | Ugx {int(amount):,} | {receipt_contact} | {receipt_desc} |"
                    )

            # If completely clean, push to Google Sheets API
            if not has_errors and len(rows_to_append) > 0:
                with st.spinner("⏳ Safely writing batch to Google Sheets..."):
                    try:
                        spreadsheet = client.open("Bb_Fasion")
                        worksheet = spreadsheet.worksheet("BBFASION")
                        worksheet.append_rows(rows_to_append)
                        
                        # FIX: Target only index position 6 (amount field column) inside the individual inner row data lists
                        total_appended_amount = sum(float(row[6]) for row in rows_to_append)
                        
                        markdown_table = (
                            f"### 📋 Brenda Fashion Receipt\n"
                            f"**Date:** {tx_date.strftime('%Y-%m-%d')} | **Type:** {global_tx_type}\n\n"
                            f"| Customer Name | Particulars | Qty | Unit Price | Total Amount | Contact | Description / Notes |\n"
                            f"| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
                        ) + "\n".join(summary_rows_markdown) + f"\n\n**Total Amount:** Ugx {int(total_appended_amount):,}"

                        st.session_state.last_saved_summary = markdown_table
                        st.session_state.editor_session_id += 1
                        st.success("🎉 All rows successfully saved to Google Sheets!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Transaction aborted due to a connection issue: {str(e)}")
            elif len(rows_to_append) == 0 and not has_errors:
                st.error("❌ Please input data details before attempting to save.")

    # --- 6. PERSISTENT SUMMARY RECEIPT VIEW ---
    if st.session_state.last_saved_summary:
        st.divider()
        st.subheader("📄 Saved Receipt")
        st.markdown(st.session_state.last_saved_summary)

        # Display the receipt in markdown
        st.code(st.session_state.last_saved_summary, language="markdown")
        st.caption("☝️ Click the copy icon in the top-right corner of the box above to copy the markdown.")
    
        action_col1, action_col2 = st.columns(2)
    
        with action_col1:
            if st.button("Clear Receipt View", key="clear_receipt_layout_bottom"):
                st.session_state.last_saved_summary = None
                st.rerun()
            
        with action_col2:
            # Prepare content for JS by escaping backticks and quotes
            receipt_js_safe = (
                st.session_state.last_saved_summary
                .replace("`", "\\`")
                .replace("'", "\\'")
                .replace('"', '\\"')
                .replace("\n", "<br>")
            )
        
            # Inject the HTML/JS component for isolated printing
            #components.html(f"""
            #<html>
                #<head>
                    #<title>Transaction Receipt</title>
                    #<style>
                       # body {{
                            #font-family: monospace;
                            #white-space: pre-wrap;
                            #padding: 20px;
                            ##line-height: 1.4;
                            #color: #000;
                        #}}
                    #</style>
                    #<script>
                        #function printReceiptOnly() {{
                           # var printWindow = window.open('', '_blank', 'height=600,width=800');
                            #printWindow.document.write('<html><head><title>Transaction Receipt</title>');
                           # printWindow.document.write('<style>body {{ font-family: monospace; white-space: pre-wrap; padding: 20px; line-height: 1.4; }}</style>');
                            #printWindow.document.write('</head><body>');
                            ##printWindow.document.write('{receipt_js_safe}');
                            #printWindow.document.write('</body></html>');
                            #printWindow.document.close();
                            #printWindow.focus();
                            #printWindow.print();
                            #printWindow.close();
                        #}}
                   # </script>
                ##</head>
                #<body>
                    #<button onclick="printReceiptOnly()" style="
                        ##background-color: #ff4b4b; 
                       # color: white; 
                        #border: none; 
                        #padding: 0.5rem 1rem; 
                        ##border-radius: 4px; 
                        #cursor: pointer;
                        #font-family: sans-serif;
                        ##font-size: 14px;
                        #font-weight: 500;
                        #box-sizing: border-box;
                       ## width: 100%;
                   # ">🖨️ Print Receipt Only</button>
                #</body>
            #</html>
           # """, height=50, scrolling=False)

    
