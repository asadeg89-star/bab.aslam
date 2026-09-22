import fitz  # PyMuPDF
import pytesseract
import streamlit as st
from PIL import Image
import io

st.set_page_config(page_title="P&ID Tag Search", layout="wide")
st.title("P&ID Equipment Tag Search")

# Define the PDF filename located in your GitHub repository
PDF_FILE_PATH = "Volume IV.pdf"

search_tag = st.text_input("Enter valve tag or line number to search:", "932")

if st.button("Search Document"):
    if not search_tag.strip():
        st.warning("Please enter a search term.")
    else:
        try:
            # Open the PDF preloaded in the repository
            doc = fitz.open(PDF_FILE_PATH)
            st.info(f"Scanning {len(doc)} pages for tag: **{search_tag}**...")
            
            found = False
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Render page to image at 150 DPI for OCR
                pix = page.get_pixmap(dpi=150)
                img = Image.open(io.BytesIO(pix.tobytes()))
                
                # Run Tesseract OCR on the page
                text = pytesseract.image_to_string(img)
                
                if search_tag.lower() in text.lower():
                    st.success(f"Match found on **Page {page_num + 1}**!")
                    # Display the matched page image
                    st.image(img, caption=f"Page {page_num + 1}", use_column_width=True)
                    found = True
            
            if not found:
                st.error(f"Tag **'{search_tag}'** was not found in {PDF_FILE_PATH}.")
                
        except FileNotFoundError:
            st.error(f"File **'{PDF_FILE_PATH}'** not found in the root directory. Please check the file name in your GitHub repo.")
