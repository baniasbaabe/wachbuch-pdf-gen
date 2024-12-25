import gspread
import pandas as pd
import datetime as dt
import streamlit as st
import time
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import zipfile
import os
from dotenv import load_dotenv
from ast import literal_eval
load_dotenv()
CREDENTIALS_FILE = 'credentials.json'
SHEET_NAME = 'Esslingen'

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('report_template.html')

@st.cache_data(ttl="30min")
def load_google_sheets_data(sheet_name: str, credentials_file: str = None) -> pd.DataFrame:
    creds = os.getenv("CREDENTIALS")
    gc = gspread.service_account_from_dict(literal_eval(creds))
    sh = gc.open(sheet_name).get_worksheet(0)
    df = pd.DataFrame(sh.get_all_records())
    df["Checkpoint-ID"] = df["Checkpoint-ID"].str.strip()
    return df

def convert_to_datetime(df: pd.DataFrame, column_name: str, date_format: str) -> pd.DataFrame:
    df[column_name] = pd.to_datetime(df[column_name], format=date_format)
    return df

data = load_google_sheets_data(SHEET_NAME, CREDENTIALS_FILE)
data = convert_to_datetime(data, 'Sendezeitstempel', '%d.%m.%Y %H:%M:%S')

st.title("Checkpoint Report Generator")

# Inputs: Month, Year, Checkpoints
months = st.multiselect("Select Months", options=range(1, 13), format_func=lambda x: f"{x:02d}")
year = st.selectbox("Select Year", options=sorted(data["Sendezeitstempel"].dt.year.unique()))
selected_checkpoints = st.multiselect("Select Checkpoints", options=data["Checkpoint-ID"].unique())

# Filter data
filtered_data = data[
    (data["Sendezeitstempel"].dt.year == year) &
    (data["Checkpoint-ID"].isin(selected_checkpoints))
]

def html_to_pdf(html_content):
    result = BytesIO()
    htmldoc = HTML(string=html_content, base_url='.')
    return htmldoc.write_pdf()

def generate_pdf(df, month):
    html_content = template.render(
        title=f"Checkpoint Report - {int(year)}/{month:02d}",
        date=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        checkpoints=selected_checkpoints,
        dataframe=df
    )
    return html_to_pdf(html_content)

def generate_zip(pdfs):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for month, pdf_data in pdfs:
            zip_file.writestr(f"checkpoint_report_{year}_{month:02d}.pdf", pdf_data)
    zip_buffer.seek(0)
    return zip_buffer

if st.button("Generate PDFs for Selected Months"):
    if filtered_data.empty:
        st.warning("No data to generate PDFs.")
    else:
        pdfs = []
        for month in months:
            # Filter data for the specific month
            month_data = filtered_data[filtered_data["Sendezeitstempel"].dt.month == month]
            if not month_data.empty:
                pdf_data = generate_pdf(month_data, month)
                pdfs.append((month, pdf_data))

        if pdfs:
            zip_data = generate_zip(pdfs)
            st.download_button(
                label="Download All PDFs as ZIP",
                data=zip_data,
                file_name=f"checkpoint_reports_{year}.zip",
                mime="application/zip"
            )
        else:
            st.warning("No data available for the selected months.")
