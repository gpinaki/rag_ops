import streamlit as st
from typing import List, Optional
import asyncio
from config.config import Config
from models.vectorstore import AsyncVectorStore
from models.retriever import AsyncDocumentRetriever
from models.file_processor import AsyncFileProcessor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document

class AsyncRAGApp:
    def __init__(self):
        self.vector_store = AsyncVectorStore()
        self.file_processor = AsyncFileProcessor()
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )
        self.prompt = self._create_prompt()

    def _create_prompt(self) -> ChatPromptTemplate:
        template = """You are a helpful AI assistant. Using the following context, answer the user's question. 
        If you cannot answer the question based on the context, say so.

        Context: {context}
        Chat History: {chat_history}
        Question: {question}

        Answer the question based on the context provided. If uncertain, admit it.
        Make your response clear and well-structured.
        """
        return ChatPromptTemplate.from_template(template)

    async def aprocess_files(self, uploaded_files) -> List[Document]:
        """Process multiple files asynchronously."""
        tasks = [
            self.file_processor.aprocess_file(file)
            for file in uploaded_files
        ]
        documents = await asyncio.gather(*tasks)
        return [doc for doc in documents if doc is not None]

    async def asetup_retriever(self, documents: List[Document]) -> AsyncDocumentRetriever:
        """Set up the vector store and retriever."""
        vectordb = await self.vector_store.asetup_vectorstore(documents)
        return AsyncDocumentRetriever(vectordb)

    async def agenerate_response(
        self,
        query: str,
        retriever: AsyncDocumentRetriever,
        chat_history: List[tuple[str, str]]
    ) -> str:
        """Generate a response using the RAG pipeline."""
        # Get relevant documents
        docs = await retriever.aretrieve(query, top_k=3)
        context = "\n".join(doc.page_content for doc in docs)
        
        # Format chat history
        history_str = "\n".join([
            f"Q: {q}\nA: {a}" 
            for q, a in chat_history[-3:]
        ])
        
        # Generate response
        prompt_response = await self.prompt.ainvoke({
            "context": context,
            "chat_history": history_str,
            "question": query
        })
        llm_response = await self.llm.ainvoke(prompt_response)
        return StrOutputParser().invoke(llm_response)

async def main():
    st.set_page_config(page_title="Research Assistant Chatbot", layout="wide")
    
    # Initialize app
    app = AsyncRAGApp()
    
    # Initialize session states
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "retriever" not in st.session_state:
        st.session_state.retriever = None

    # Sidebar for file uploads
    st.sidebar.title("📁 Upload Files")
    uploaded_files = st.sidebar.file_uploader(
        "Upload PDF, Excel, or CSV files",
        type=["pdf", "xlsx", "csv"],
        accept_multiple_files=True,
        key="file_uploader"
    )

    if not uploaded_files:
        st.warning("👋 Please upload files to start chatting!")
        return

    # Process files and setup retriever
    if st.session_state.retriever is None:
        with st.spinner("🔄 Processing documents..."):
            try:
                documents = await app.aprocess_files(uploaded_files)
                if not documents:
                    st.error("No valid documents were processed.")
                    return
                
                st.session_state.retriever = await app.asetup_retriever(documents)
            except Exception as e:
                st.error(f"Error processing documents: {str(e)}")
                return

    # Chat interface
    st.title("💬 Async RAG Chatbot")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask your question..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = await app.agenerate_response(
                        prompt,
                        st.session_state.retriever,
                        st.session_state.chat_history
                    )
                    st.markdown(response)
                    
                    # Update history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    st.session_state.chat_history.append((prompt, response))
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())