import streamlit as st
import requests
from readability import Document
import pdfkit
import io
import zipfile
import re

st.set_page_config(page_title="Batch Article to PDF", page_icon="📄")

st.title("📄 Reader-Mode PDF Converter")
st.markdown("Build your reading list below, then convert them all into a ZIP file of clean, AI-ready PDFs.")

# --- Session State Initialization ---
# We use this to remember the list of URLs and the generated ZIP file between button clicks
if 'url_list' not in st.session_state:
    st.session_state.url_list = []
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None

# Callback function to add a URL and clear the input box
def add_url_to_list():
    new_url = st.session_state.url_input.strip()
    if new_url and new_url not in st.session_state.url_list:
        st.session_state.url_list.append(new_url)
    # Clear the input box after adding
    st.session_state.url_input = ""

# --- URL Input UI ---
col1, col2 = st.columns([4, 1])
with col1:
    # Notice the 'key' argument. This binds the input to st.session_state.url_input
    st.text_input("Enter Article URL:", key="url_input", on_change=add_url_to_list)
with col2:
    st.write("") # Spacing to align the button with the text box
    st.write("")
    st.button("➕ Add", on_click=add_url_to_list, use_container_width=True)

# --- Display the Reading List Queue ---
if st.session_state.url_list:
    st.subheader("📋 Your Reading Queue")
    
    # Display each URL as a neat little block
    for url in st.session_state.url_list:
        st.code(url, language="text")
    
    # Button to clear the queue
    if st.button("🗑️ Clear Queue"):
        st.session_state.url_list = []
        st.session_state.zip_data = None
        st.rerun()

st.divider()

# --- Conversion Logic ---
if st.session_state.url_list:
    if st.button("🚀 Extract and Convert All", type="primary"):
        zip_buffer = io.BytesIO()
        
        with st.status(f"Processing {len(st.session_state.url_list)} articles...", expanded=True) as status:
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for i, url in enumerate(st.session_state.url_list):
                    try:
                        st.write(f"⏳ Fetching: {url}")
                        
                        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                        response = requests.get(url, headers=headers, timeout=10)
                        response.raise_for_status()

                        doc = Document(response.text)
                        title = doc.title()
                        cleaned_html = doc.summary()

                        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
                        if not safe_title:
                            safe_title = f"article_{i+1}"

                        full_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <title>{title}</title>
                            <base href="{url}"> 
                            <style>
                                body {{ font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                                img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; border-radius: 8px; }}
                            </style>
                        </head>
                        <body>
                            <h1>{title}</h1>
                            {cleaned_html}
                        </body>
                        </html>
                        """

                        options = {
                            'page-size': 'A4',
                            'margin-top': '0.75in',
                            'margin-right': '0.75in',
                            'margin-bottom': '0.75in',
                            'margin-left': '0.75in',
                            'encoding': "UTF-8",
                            'no-outline': None,
                            'enable-local-file-access': None
                        }
                        
                        # Cloud Ready! No paths needed.
                        pdf_bytes = pdfkit.from_string(full_html, False, options=options)

                        zip_file.writestr(f"{safe_title}.pdf", pdf_bytes)
                        st.write(f"✅ Success: `{safe_title}.pdf`")

                    except Exception as e:
                        st.error(f"❌ Failed on {url} - Error: {e}")
            
            status.update(label="All processing complete!", state="complete", expanded=False)

        # Save to session state so the download button works
        st.session_state.zip_data = zip_buffer.getvalue()

# --- Download Button ---
if st.session_state.zip_data is not None:
    st.success("🎉 Your ZIP file is ready!")
    st.download_button(
        label="📦 Download All as ZIP",
        data=st.session_state.zip_data,
        file_name="cleaned_articles.zip",
        mime="application/zip",
        type="primary"
    )
