import streamlit as st
from veryfi import Client
import tempfile
import json
import os

# === LOAD VERYFI CREDENTIALS FROM ENVIRONMENT VARIABLES ===
VERYFI_CLIENT_ID = os.getenv("VERYFI_CLIENT_ID")
VERYFI_CLIENT_SECRET = os.getenv("VERYFI_CLIENT_SECRET")
VERYFI_USERNAME = os.getenv("VERYFI_USERNAME")
VERYFI_API_KEY = os.getenv("VERYFI_API_KEY")

client = Client(VERYFI_CLIENT_ID, VERYFI_CLIENT_SECRET, VERYFI_USERNAME, VERYFI_API_KEY)

st.title("Invoice to JSON Converter")

uploaded_file = st.file_uploader("Upload an invoice PDF", type=["pdf"])

def remove_logo_field(obj):
    if isinstance(obj, dict):
        return {k: remove_logo_field(v) for k, v in obj.items() if k != "logo"}
    elif isinstance(obj, list):
        return [remove_logo_field(item) for item in obj]
    else:
        return obj

if uploaded_file:
    st.success("File uploaded. Processing...")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    categories = ["Invoices"]
    try:
        response = client.process_document(tmp_path, categories)

        cleaned_response = {
            k: v for k, v in response.items()
            if k not in ["meta", "img_thumbnail_url", "img_url", "pdf_url"]
        }
        cleaned_response = remove_logo_field(cleaned_response)

        st.download_button(
            "Download JSON",
            data=json.dumps(cleaned_response, indent=2),
            file_name="invoice_data_cleaned.json",
            mime="application/json"
        )
    except Exception as e:
        st.error(f"Error: {e}")