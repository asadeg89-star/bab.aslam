import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

doc = fitz.open("Volume IV.pdf")

for page_num in range(len(doc)):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes()))
    
    text = pytesseract.image_to_string(img)
    if "932" in text or "PSV" in text:
        print(f"Found on Page {page_num + 1}")
