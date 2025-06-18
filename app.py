import streamlit as st
from veryfi import Client
import tempfile
import json
import os
import fitz  # PyMuPDF

# === LOAD VERYFI CREDENTIALS FROM ENVIRONMENT VARIABLES ===
VERYFI_CLIENT_ID = os.getenv("VERYFI_CLIENT_ID")
VERYFI_CLIENT_SECRET = os.getenv("VERYFI_CLIENT_SECRET")
VERYFI_USERNAME = os.getenv("VERYFI_USERNAME")
VERYFI_API_KEY = os.getenv("VERYFI_API_KEY")

client = Client(VERYFI_CLIENT_ID, VERYFI_CLIENT_SECRET, VERYFI_USERNAME, VERYFI_API_KEY)

st.title("Invoice to JSON & Text Converter")

uploaded_file = st.file_uploader("Upload an invoice PDF", type=["pdf"])

def remove_logo_field(obj):
    if isinstance(obj, dict):
        return {k: remove_logo_field(v) for k, v in obj.items() if k != "logo"}
    elif isinstance(obj, list):
        return [remove_logo_field(item) for item in obj]
    else:
        return obj

def split_pdf(input_pdf_path, chunk_size=3):
    doc = fitz.open(input_pdf_path)
    chunks = []
    for i in range(0, len(doc), chunk_size):
        subdoc = fitz.open()
        for j in range(i, min(i + chunk_size, len(doc))):
            subdoc.insert_pdf(doc, from_page=j, to_page=j)
        chunk_path = f"{input_pdf_path}_chunk_{i//chunk_size}.pdf"
        subdoc.save(chunk_path)
        subdoc.close()
        chunks.append(chunk_path)
    doc.close()
    return chunks

if uploaded_file:
    st.success("File uploaded. Processing...")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        all_cleaned_data = []
        full_ocr_text = ""
        chunks = split_pdf(tmp_path, chunk_size=3)

        for chunk_path in chunks:
            response = client.process_document(chunk_path, ["Invoices"])

            cleaned_response = {
                k: v for k, v in response.items()
                if k not in ["meta", "img_thumbnail_url", "img_url", "pdf_url"]
            }
            cleaned_response = remove_logo_field(cleaned_response)
            all_cleaned_data.append(cleaned_response)

            text_output = cleaned_response.get("ocr_text", "")
            full_ocr_text += text_output + "\n\n"

        # Save merged cleaned data if needed
        merged_data = {
            "invoices": all_cleaned_data,
            "combined_ocr_text": full_ocr_text.strip()
        }

        st.download_button(
            "Download Merged JSON",
            data=json.dumps(merged_data, indent=2),
            file_name="invoice_data_combined.json",
            mime="application/json"
        )

        st.download_button(
            "Download Merged TXT",
            data=full_ocr_text.strip(),
            file_name="invoice_data_combined.txt",
            mime="text/plain"
        )

    except Exception as e:
        st.error(f"Error: {e}")
