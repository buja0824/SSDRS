import streamlit as st
from datetime import datetime


st.set_page_config(
    page_title= "RAG Testing Home Page",
    
)

st.title("RAG Testing Home Page")


# 마크다운 파일 링크

st.markdown(
    """
    
# This is RAG test pages.
            
It contains:
            
- [ ] [GPT Based RAG](/GPT_BASED_RAG)
- [ ] [Claude Based RAG](/Claude_BASED_RAG)
- [ ] [Gemini Based RAG](/Gemini_Based_RAG)

"""


)