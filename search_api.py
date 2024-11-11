#library to remove unecessary warnings
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import streamlit as st
import os
from io import BytesIO

# Libraries to get data from PDF correctly
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import re
from transformers import pipeline

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
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
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

def split_text_into_paragraphs(text):
    # Split the text by double newline characters
    paragraphs = text.split("\n\n")
    # Remove any leading or trailing whitespace from each paragraph
    extracted_paragraphs = []
    for para in paragraphs:
        if para.strip():
            extracted_paragraphs.append(para.strip())
    return extracted_paragraphs
    
# Main page
def main():
    st.title("PDF Extraction - Search Terms and Extract Paragraphs")

    if st.button("Search Paragraph with Terms"):
        st.session_state.page = "page1"
        st.rerun()

    if st.button("Extract Paragraphs and Save to Excel"):
        st.session_state.page = "page2"
        st.rerun()
    
    if st.button("Extract Paragraphs and Summarize"):
        st.session_state.page = "page3"
        st.rerun()

def clean_text_cid(text):
    """Cleans the text by replacing (cid:xxx) patterns with potential replacements.

    Args:
        text: The input text with (cid:xxx) patterns.

    Returns:
        The cleaned text.
    """

    # A simple mapping of common (cid:xxx) patterns to their potential replacements
    replacements = {
        r"\(cid:415\)": "ti",
        r"\(cid:425\)": "tt",
        r"\(cid:414\)": "tf",
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    return text
    
# Page 1
def page1():
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
        
        
        # Save the uploaded file to the same directory as the script
        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
            
        # Process the uploaded file
        if uploaded_file.type == "application/pdf":
            paragraph = convertPDFToText(file_path)
        elif uploaded_file.type == "text/plain":
            paragraph = uploaded_file.getvalue().decode("utf-8")
        
        for para in paragraph.split("\n\n"):
            if search_words_in_paragraph(para, words):
                highlighted_text = highlight_words(para, words)
                st.markdown(highlighted_text, unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("Go back to Main"):
        st.session_state.page = "main"
        st.rerun()
        
# Page 2
def page2():
    st.title("Extract Paragraphs and Store in Excel File")

    # File uploader
    uploaded_file = st.file_uploader("Upload File", type=["pdf","txt"])

    # Textbox for specifying words
    words = st.text_input("Enter minimum words you want in paragraph (eg. 5 or 10 or default is all length paras)")
    
    if words == "":
        words = 1
    else:
        words = int(words)
        
    extracted_paras = []
    
    if uploaded_file is not None:
        
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}
        
        # Save the uploaded file to the same directory as the script
        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
            
        # Process the uploaded file
        if uploaded_file.type == "application/pdf":
            paragraph = convertPDFToText(uploaded_file.name)
        elif uploaded_file.type == "text/plain":
            paragraph = uploaded_file.getvalue().decode("utf-8")
        
        for para in split_text_into_paragraphs(paragraph):
            
            if len(para.split(" ")) >= words:
                
                extracted_paras.append([para])
                
    if extracted_paras:
        
        extracted_paras_df = pd.DataFrame(data=extracted_paras, columns=['Paragraphs_from_PDF']) 
        
        # Save file to an Excel file
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            extracted_paras_df.to_excel(writer, index=False, sheet_name='Paragraphs')
        
        st.success("Paragraphs extracted successfully and stored in Excel file.")

        # Button to download the Excel file
        st.download_button(
            label="Download Excel",
            data=excel_buffer,
            file_name="extracted_paras.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Clean up the buffer
        excel_buffer.close()
        
    if st.button("Go back to Main"):
        st.session_state.page = "main"
        st.rerun()
        
# Page 3
def page3():
    st.title("Extract Paragraphs and Summarize")

    # File uploader
    uploaded_file = st.file_uploader("Upload File", type=["pdf","txt"])
        
    extracted_paras = []
    
    if uploaded_file is not None:
        
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}
        
        # Save the uploaded file to the same directory as the script
        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
            
        # Process the uploaded file
        if uploaded_file.type == "application/pdf":
            paragraph = convertPDFToText(uploaded_file.name)
        elif uploaded_file.type == "text/plain":
            paragraph = uploaded_file.getvalue().decode("utf-8")
        
        for para in split_text_into_paragraphs(paragraph):
            
            extracted_paras.append([para])
                
    if extracted_paras:
        
        extracted_paras_df = pd.DataFrame(data=extracted_paras, columns=['Paragraphs_from_PDF']) 
        
        # Load the summarization pipeline
        summarizer = pipeline("summarization")
        
        # Function to summarize text
        def summarize_text(text):
            if isinstance(text, str) and len(text.split()) > 50:  # Summarize only if the text is long enough
                summary = summarizer(text, max_length=50, min_length=25, do_sample=False)
                res = clean_text_cid(summary[0]['summary_text']) 
            else:
                res = clean_text_cid(text)
            return res
        
        # Apply the summarization to the [Cleaned Paragraph] column
        extracted_paras_df['Summary'] = extracted_paras_df['Paragraphs_from_PDF'].apply(summarize_text)

        # Save file to an Excel file
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            extracted_paras_df.to_excel(writer, index=False, sheet_name='Paragraphs')
        
        st.success("Paragraphs extracted successfully and stored in Excel file.")

        # Button to download the Excel file
        st.download_button(
            label="Download Excel",
            data=excel_buffer,
            file_name="summarized_paras.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Clean up the buffer
        excel_buffer.close()
        
    if st.button("Go back to Main"):
        st.session_state.page = "main"
        st.rerun()

# Check which page to display
if 'page' not in st.session_state:
    st.session_state.page = "main"

if st.session_state.page == "main":
    main()
elif st.session_state.page == "page1":
    page1()
elif st.session_state.page == "page2":
    page2()
elif st.session_state.page == "page3":
    page3()