import streamlit as st
import requests
from readability import Document
import pdfkit
import io
import zipfile
import re

st.set_page_config(page_title="Batch Article to PDF", page_icon="📄")

st.title("📄 Batch Reader-Mode Converter")
st.markdown("Paste a list of URLs (one per line) to convert them into a ZIP file of clean, AI-ready PDFs.")

# Initialize session state for our ZIP data
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None

urls_input = st.text_area("Enter Article URLs (one per line):", height=200)

# 1. The Generation Button
if st.button("Extract and Convert All"):
    urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
    
    if not urls:
        st.warning("Please enter at least one URL.")
    else:
        zip_buffer = io.BytesIO()
        
        with st.status(f"Processing {len(urls)} articles...", expanded=True) as status:
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                
                for i, url in enumerate(urls):
                    try:
                        st.write(f"⏳ Fetching: {url}")
                        
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                        }
                        response = requests.get(url, headers=headers, timeout=10)
                        response.raise_for_status()

                        doc = Document(response.text)
                        title = doc.title()
                        cleaned_html = doc.summary()

                        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
                        if not safe_title:
                            safe_title = f"article_{i+1}"

                        # Added the <base> tag! This tells wkhtmltopdf how to find relative images.
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
                        
                        # --- REMEMBER YOUR WINDOWS WKHTMLTOPDF PATH CONFIG HERE ---
                        path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
                        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
                        pdf_bytes = pdfkit.from_string(full_html, False, configuration=config, options=options)

                        zip_file.writestr(f"{safe_title}.pdf", pdf_bytes)
                        st.write(f"✅ Success: Generated `{safe_title}.pdf`")

                    except Exception as e:
                        st.error(f"❌ Failed on {url} - Error: {e}")
            
            status.update(label="All processing complete!", state="complete", expanded=False)

        # Save the final ZIP file into session state so it survives the button click!
        st.session_state.zip_data = zip_buffer.getvalue()


# 2. The Download Button (Now OUTSIDE the first button's block)
if st.session_state.zip_data is not None:
    st.download_button(
        label="📦 Download All as ZIP",
        data=st.session_state.zip_data,
        file_name="cleaned_articles.zip",
        mime="application/zip",
        type="primary"
    )