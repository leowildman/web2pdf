import streamlit as st
import requests
from readability import Document
from weasyprint import HTML
import re

st.set_page_config(page_title="iOS Article to PDF", page_icon="📄")

st.title("📄 Reader-Mode PDF Converter")
st.markdown("Build your reading list below, then process them into clean, AI-ready PDFs for easy downloading on iOS.")

# --- Session State Initialization ---
if 'url_list' not in st.session_state:
    st.session_state.url_list = []
if 'generated_pdfs' not in st.session_state:
    st.session_state.generated_pdfs = [] # Stores a list of dictionaries: [{"filename": "...", "data": bytes}]

def add_url_to_list():
    new_url = st.session_state.url_input.strip()
    if new_url and new_url not in st.session_state.url_list:
        st.session_state.url_list.append(new_url)
    st.session_state.url_input = ""

# --- URL Input UI ---
col1, col2 = st.columns([4, 1])
with col1:
    # On iOS, tapping this will often surface the "Paste from Safari" shortcut above the keyboard
    st.text_input("Enter Article URL:", key="url_input", on_change=add_url_to_list)
with col2:
    st.write("") 
    st.write("")
    st.button("➕ Add", on_click=add_url_to_list, use_container_width=True)

# --- Display the Reading List Queue ---
if st.session_state.url_list:
    st.subheader("📋 Your Reading Queue")
    
    for url in st.session_state.url_list:
        st.code(url, language="text")
    
    if st.button("🗑️ Clear Queue & Results"):
        st.session_state.url_list = []
        st.session_state.generated_pdfs = []
        st.rerun()

st.divider()

# --- Conversion Logic ---
if st.session_state.url_list:
    if st.button("🚀 Extract and Process All", type="primary"):
        # Reset the generated PDFs list before a new run
        st.session_state.generated_pdfs = []
        
        with st.status(f"Processing {len(st.session_state.url_list)} articles...", expanded=True) as status:
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
                    
                    # Generate PDF using WeasyPrint
                    pdf_bytes = HTML(string=full_html, base_url=url).write_pdf()

                    # Store the generated file data in session state
                    st.session_state.generated_pdfs.append({
                        "filename": f"{safe_title}.pdf",
                        "data": pdf_bytes
                    })
                    st.write(f"✅ Success: Ready to download `{safe_title}.pdf`")

                except Exception as e:
                    st.error(f"❌ Failed on {url} - Error: {e}")
            
            status.update(label="All processing complete!", state="complete", expanded=False)

# --- iOS Friendly Download Buttons ---
if st.session_state.generated_pdfs:
    st.success("🎉 Your PDFs are ready! Tap below to download them individually.")
    
    # Create a separate download button for every PDF generated
    for i, pdf in enumerate(st.session_state.generated_pdfs):
        st.download_button(
            label=f"⬇️ Download: {pdf['filename']}",
            data=pdf['data'],
            file_name=pdf['filename'],
            mime="application/pdf",
            key=f"dl_btn_{i}" # Keys must be unique in Streamlit loops!
        )
