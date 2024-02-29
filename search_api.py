#library to remove unecessary warnings
import warnings
warnings.filterwarnings("ignore")

import streamlit as st

# Libraries to get data from PDF correctly
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

try:
    from cStringIO import StringIO ## for Python 2
except ImportError:
    from io import StringIO ## for Python 3

# Function to highlight words in text
def highlight_words(paragraph, words):
    highlighted_paragraph = ""
    for word in paragraph.split():
        if word.lower() in words:
            highlighted_paragraph += f"<span style='color:red'>{word}</span> "
        else:
            highlighted_paragraph += f"{word} "
    return highlighted_paragraph

def search_words_in_paragraph(paragraph, words):
    """
    Search for words in a paragraph.

    Parameters:
    - paragraph (str): The paragraph to search within.
    - words (list): A list of words to search for.

    Returns:
    - bool: True if any, some, or all of the words exist in the paragraph, False otherwise.
    """
    # Convert the paragraph to lowercase for case-insensitive matching
    paragraph_lower = paragraph.lower()
    
    # Convert the words to lowercase as well
    words_lower = [word.lower() for word in words]
    
    # Check if any of the words exist in the paragraph
    for word in words_lower:
        if word in paragraph_lower:
            return True
    return False
        
def convertPDFToText(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()
    res= 0
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        if res == 1000:
            break
        else:
            res = res + 1
        interpreter.process_page(page)
    fp.close()
    device.close()
    string = retstr.getvalue()
    retstr.close()
    return string
    
# Main Streamlit app
def main():
    st.title("Extract Paragraphs with Specific Words Only")

    # File uploader
    uploaded_file = st.file_uploader("Upload File", type=["pdf","txt"])

    # Textbox for specifying words
    words = st.text_input("Enter Keywords Separated by Comma (,)")
    
    if words == "":
        words = 'must,shall,provide'
        
    words = words.lower().replace(" ", "").split(",")
    
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}

        # Process the uploaded file
        if uploaded_file.type == "application/pdf":
            paragraph = convertPDFToText(uploaded_file.name)
        elif uploaded_file.type == "text/plain":
            paragraph = uploaded_file.getvalue().decode("utf-8")
        
        for para in paragraph.split("\n\n"):
            if search_words_in_paragraph(para, words):
                highlighted_text = highlight_words(para, words)
                st.markdown(highlighted_text, unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
