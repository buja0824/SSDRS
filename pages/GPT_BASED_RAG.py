import os
import time
import streamlit as st
from langchain.document_loaders import UnstructuredFileLoader
from langchain.embeddings import CacheBackedEmbeddings, OpenAIEmbeddings
from langchain.storage import LocalFileStore
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from dotenv import load_dotenv
from langchain.callbacks.base import BaseCallbackHandler
from langchain.prompts import ChatPromptTemplate
from langchain.document_loaders import UnstructuredFileLoader
from langchain.embeddings import CacheBackedEmbeddings, OpenAIEmbeddings
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.storage import LocalFileStore
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
import streamlit as st

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === Callback Handler definition ===
class ChatCallbackHandler(BaseCallbackHandler):
    message = ""

    def on_llm_start(self, *args, **kwargs):
        self.message_box = st.empty()

    def on_llm_end(self, *args, **kwargs):
        save_message(self.message, "ai")
        self.message = ""  # message initialize (important)

    def on_llm_new_token(self, token, *args, **kwargs):
        self.message += token
        self.message_box.markdown(self.message)

llm = ChatOpenAI(
    model_name="gpt-4o",
    openai_api_key = OPENAI_API_KEY,
    temperature=0.1,
    streaming=True,
    callbacks=[ChatCallbackHandler()],
)

def embed_multiple_files(file_paths):
    """
    여러 파일을 한꺼번에 임베딩하여
    단일 VectorStore(FAISS)를 만들어 retriever를 반환
    """
    all_docs = []
    splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator="\n",
        chunk_size=600,
        chunk_overlap=100,
    )

    for file_path in file_paths:
        loader = UnstructuredFileLoader(file_path)
        docs = loader.load_and_split(text_splitter=splitter)
        all_docs.extend(docs)

    cache_dir = LocalFileStore("./.cache/embeddings")

    embeddings = OpenAIEmbeddings()  # Usin Embedding Model
    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
        embeddings, 
        cache_dir
    )

    vectorstore = FAISS.from_documents(all_docs, cached_embeddings)
    retriever = vectorstore.as_retriever()
    return retriever

# === save messages / rendering fuctions ===
def save_message(message, role):
    st.session_state["messages"].append({"message": message, "role": role})

def send_message(message, role, save=True):
    with st.chat_message(role):
        st.markdown(message)
    if save:
        save_message(message, role)

def paint_history():
    for message in st.session_state["messages"]:
        send_message(
            message["message"],
            message["role"],
            save=False,
        )

def format_docs(docs):
    """RAG 단계에서 불러온 문서를 단일 문자열로 합침."""
    return "\n\n".join(document.page_content for document in docs)

# === Prompt definition ===
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a helpful, knowledgeable AI assistant.
            You have two sources of knowledge:
            1) The context from the user-provided documents.
            2) Your own general knowledge (pre-trained model).

            Instruction:
            - First, check if the question can be answered from the given context.
            - If the context is relevant and contains the answer, prioritize it.
            - If the context does NOT contain the information, then rely on your own knowledge.
            - When you produce your final answer, explicitly indicate which source of knowledge you used:
              * If the needed information was found in the context, say "Source: Official Documents."
              * If the context didn't contain the information but you answered from your general knowledge, say "Source: LLM knowledge."
              * If you're not certain at all, say "I don't know."
            """
        ),
        (
            "human",
            """
            Context:
            {context}

            Question:
            {question}
            """
        ),
    ]
)

# === Streamlit App ===
st.title("GPT_Stroke Assistant Bot")
st.markdown(
    """
Welcome!
Please tell me about your Stroke Symptoms. If symptoms persist, see a doctor immediately.
"""
)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# file paths
predefined_file_paths = [
    ".cache/files/(eng)ictus_criteri-diagnostici.pdf",
    ".cache/files/(eng)MNG_D1_1. Clinical guideline of Acute Stroke .pdf",
    ".cache/files/1.pdf",
    ".cache/files/2.pdf",
    ".cache/files/3.pdf",
    ".cache/files/4.pdf",
    ".cache/files/이수형 (1).pdf",
    ".cache/files/이수형 (2).pdf",
    ".cache/files/alise (1).pdf",
    ".cache/files/alise (2).pdf",
    ".cache/files/alise (3).pdf",
]

retriever = embed_multiple_files(predefined_file_paths)

send_message("I'm ready! Ask away!", "ai", save=False)
paint_history()

message = st.chat_input("Ask anything about Stroke...")
if message:
    send_message(message, "human")
    chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
    )

    with st.chat_message("ai"):
        # execute chains (RAG + LLM)
        response = chain.invoke(message)
else:
    st.session_state["messages"] = []
