import gspread
import pandas as pd
import datetime as dt
import streamlit as st
from io import BytesIO
import zipfile
import os
from dotenv import load_dotenv
import base64
from weasyprint import HTML
import base64
import datetime as dt
from jinja2 import Environment, FileSystemLoader
import time
load_dotenv()
CREDENTIALS_FILE = 'credentials.json'

# Define Google Sheet and Sheet Names
SHEET_NAME = 'Esslingen'  # Name of the Google Sheets document

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('report_template.html')

@st.cache_data(ttl="15min")
def load_google_sheets_data(sheet_name: str, credentials_file: str = None) -> pd.DataFrame:
    creds = {
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY"),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL")
    }
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open(sheet_name).get_worksheet(0)
    df = pd.DataFrame(sh.get_all_records())
    df["Checkpoint-ID"] = df["Checkpoint-ID"].str.strip()
    df["Checkpoint-ID"] = df["Checkpoint-ID"].replace({"nan": None, "": None})
    df = df.dropna(subset=["Checkpoint-ID"])
    return df

@st.cache_data(ttl="15min")
def load_second_sheet_data(sheet_name: str, credentials_file: str = None) -> pd.DataFrame:
    creds = {
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY"),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL")
    }
    
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open(sheet_name).get_worksheet(1)
    
    df = pd.DataFrame(sh.get_all_records())
    
    # Clean up the data (optional: strip whitespace from all column names)
    df.columns = df.columns.str.strip()
    
    return df

@st.cache_data(ttl="15min")
def load_third_sheet_data(sheet_name: str, credentials_file: str = None) -> pd.DataFrame:
    creds = {
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY"),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL")
    }
    
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open(sheet_name).get_worksheet(2)  # Index 2 is the third sheet
    
    df = pd.DataFrame(sh.get_all_records())
    
    # Clean up the data
    df.columns = df.columns.str.strip()
    
    return df


def convert_to_datetime(df: pd.DataFrame, column_name: str, date_format: str) -> pd.DataFrame:
    df[column_name] = pd.to_datetime(df[column_name], format=date_format, errors='coerce')
    df[column_name] = pd.to_datetime(df[column_name].dt.strftime('%d.%m.%Y %H:%M:%S'), errors='coerce')
    return df

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('report_template.html')

def encode_image_to_base64(image_path):
    """Encodes an image to a Base64 string."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def generate_pdf(df, month, year, selected_checkpoints, custom_input):
    logo_base64 = encode_image_to_base64("sg-logo.png")

    html_content = template.render(
        title=f"Checkpoint Report - {int(year)}/{month:02d}",
        date=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        checkpoints=", ".join(selected_checkpoints),
        dataframe=df,
        custom_input=custom_input,
        logo_base64=logo_base64
    )

    return HTML(string=html_content).write_pdf()


def generate_zip(pdfs, year):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for month, pdf_data in pdfs:
            zip_file.writestr(f"checkpoint_report_{year}_{month:02d}.pdf", pdf_data)
    zip_buffer.seek(0)
    return zip_buffer

# Streamlit App
st.title("Checkpoint Report Generator")

# Load data for both sheets (Sheet0 and Sheet1)
# data_sheet0 = load_google_sheets_data(SHEET_NAME, CREDENTIALS_FILE)
data_sheet1 = load_second_sheet_data(SHEET_NAME, CREDENTIALS_FILE)

# data_sheet0 = convert_to_datetime(data_sheet0, 'Sendezeitstempel', '%d.%m.%Y %H:%M:%S')
data_sheet1 = convert_to_datetime(data_sheet1, 'Sendezeitstempel', '%Y-%m-%d %H:%M:%S')
# Load data for all three sheets
data_sheet2 = load_third_sheet_data(SHEET_NAME, CREDENTIALS_FILE)
data_sheet2 = convert_to_datetime(data_sheet2, 'Sendezeitstempel', '%Y-%m-%d %H:%M:%S')
print(data_sheet1.info())
print(data_sheet2.info())
# Tabs for the two sheets
# Change this line


tab1, tab2, tab3 = st.tabs(["Sheet0 Report", "Sheet1 Report", "Sheet2 Report"])
if st.session_state.get('trigger_rerun', False):
    st.session_state.trigger_rerun = False
    st.rerun()

with tab1:
    st.header("Sheet0 Report")

# Add these at the top with other imports
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx

# Initialize session state variables (place near top before tabs)
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'pdfs' not in st.session_state:
    st.session_state.pdfs = None

# Add this function definition with your other functions
from streamlit.runtime.scriptrunner import RerunData, RerunException

# Modified generate_pdfs_background function
def generate_pdfs_background(filtered_data, months, year, selected_checkpoints, custom_input):
    try:
        pdfs = []
        total_months = len(months)
        
        for i, month in enumerate(months):
            st.session_state.progress = (i / total_months) * 100
            month_data = filtered_data[filtered_data["Sendezeitstempel"].dt.month == month]
            if not month_data.empty:
                pdf_data = generate_pdf(month_data, month, year, selected_checkpoints, custom_input)
                pdfs.append((month, pdf_data))
        
        # Update session state with completed data
        st.session_state.pdfs = pdfs
        st.session_state.processing = False
        st.session_state.progress = 100
        st.session_state.trigger_rerun = True
        # Remove the st.rerun() call from here - it's unreliable in threads
    except Exception as e:
        st.session_state.processing = False
        st.session_state.trigger_rerun = True


# Modified Sheet1 Report tab (tab2)
with tab2:
    st.header("Sheet1 Report (Bewachung)")
    
    # Create a form for Sheet1
    with st.form(key="sheet1_form"):
        months = st.multiselect("Select Months", options=range(1, 13), format_func=lambda x: f"{x:02d}")
        year = st.selectbox("Select Year", options=sorted(data_sheet1["Sendezeitstempel"].dt.year.unique()))
        selected_checkpoints = st.multiselect("Select Checkpoints", options=data_sheet1["Checkpoint"].unique())
        custom_input = st.text_input("Custom Input", value="")
        
        submit_button = st.form_submit_button(label="Generate PDFs for Selected Months")

    # Process form submission
    if submit_button:
        if not st.session_state.processing:
            filtered_data_sheet1 = data_sheet1[
                (data_sheet1["Sendezeitstempel"].dt.year == year) & 
                (data_sheet1["Checkpoint"].isin(selected_checkpoints))
            ]
            
            filtered_data_sheet1 = filtered_data_sheet1.drop(columns=[col for col in filtered_data_sheet1.columns if "Drop" in col])
            
            if filtered_data_sheet1.empty:
                st.warning("No data to generate PDFs for Sheet1.")
            else:
                st.session_state.processing = True
                st.session_state.progress = 0
                st.session_state.pdfs = None
                
                # Start background thread
                thread = threading.Thread(
                    target=generate_pdfs_background,
                    args=(filtered_data_sheet1, months, year, selected_checkpoints, custom_input)
                )
                add_script_run_ctx(thread)
                thread.daemon = True
                thread.start()
        else:
            st.warning("PDF generation is already in progress!")

    # Show progress and download outside the form
    if st.session_state.processing:
        st.progress(st.session_state.progress / 100)
        st.info("Processing PDFs in background. Please wait...")
        time.sleep(10)
        st.rerun()
    elif st.session_state.pdfs:
        with st.container():
            st.success("PDF generation completed successfully!")
            zip_data = generate_zip(st.session_state.pdfs, year)
            st.download_button(
                label="Download All PDFs as ZIP",
                data=zip_data,
                file_name=f"checkpoint_reports_{year}.zip",
                mime="application/zip"
            )


with tab3:
    st.header("Sheet2 Report")
    
    # Create a form for Sheet2
    with st.form(key="sheet2_form"):
        months = st.multiselect("Select Months", options=range(1, 13), format_func=lambda x: f"{x:02d}")
        year = st.selectbox("Select Year", options=sorted(data_sheet2["Sendezeitstempel"].dt.year.unique()))
        
        # Use the appropriate checkpoint column name for Sheet2
        checkpoint_column = "Checkpoint"  # Change this if different in Sheet2
        selected_checkpoints = st.multiselect("Select Checkpoints", options=data_sheet2[checkpoint_column].unique())
        custom_input = st.text_input("Custom Input", value="")
        
        submit_button = st.form_submit_button(label="Generate PDFs for Selected Months")
        
    # Process form submission
    if submit_button:
        filtered_data_sheet2 = data_sheet2[ 
            (data_sheet2["Sendezeitstempel"].dt.year == year) & 
            (data_sheet2[checkpoint_column].isin(selected_checkpoints))
        ]
        
        # Drop columns where "Drop" is in the column name (if needed)
        filtered_data_sheet2 = filtered_data_sheet2.drop(columns=[col for col in filtered_data_sheet2.columns if "Drop" in col])
        
        if filtered_data_sheet2.empty:
            st.warning("No data to generate PDFs for Sheet2.")
        else:
            pdfs = []
            for month in months:
                # Filter data for the specific month
                month_data = filtered_data_sheet2[filtered_data_sheet2["Sendezeitstempel"].dt.month == month]
                if not month_data.empty:
                    pdf_data = generate_pdf(month_data, month, year, selected_checkpoints, custom_input)
                    pdfs.append((month, pdf_data))

            if pdfs:
                zip_data = generate_zip(pdfs, year)
                st.download_button(
                    label="Download All PDFs as ZIP",
                    data=zip_data,
                    file_name=f"checkpoint_reports_{year}.zip",
                    mime="application/zip"
                )
            else:
                st.warning("No data available for the selected months in Sheet2.")
