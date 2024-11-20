from langchain_community.vectorstores.chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from config.config import Config
import asyncio
from typing import List
from langchain.schema import Document

class AsyncVectorStore:
    def __init__(self, embeddings_model=None):
        self.embeddings_model = embeddings_model or OpenAIEmbeddings()
        self.vectorstore_path = Config.VECTORSTORE_PATH
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE, 
            chunk_overlap=Config.CHUNK_OVERLAP
        )

    async def aprocess_documents(self, documents: List[Document]) -> List[Document]:
        """Asynchronously process documents into chunks."""
        # Text splitting is CPU-bound, run in thread pool
        return await asyncio.get_event_loop().run_in_executor(
            None, self.text_splitter.split_documents, documents
        )

    async def asetup_vectorstore(self, documents: List[Document]) -> Chroma:
        """Asynchronously set up a vectorstore from documents."""
        # Process documents
        doc_chunks = await self.aprocess_documents(documents)
        
        # Create vector store (this is I/O bound)
        vectorstore = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: Chroma.from_documents(
                documents=doc_chunks,
                embedding=self.embeddings_model,
                persist_directory=self.vectorstore_path
            )
        )
        return vectorstore

    async def aadd_documents(self, vectorstore: Chroma, documents: List[Document]):
        """Asynchronously add new documents to existing vectorstore."""
        doc_chunks = await self.aprocess_documents(documents)
        await asyncio.get_event_loop().run_in_executor(
            None,
            vectorstore.add_documents,
            doc_chunks
        )

# This ensures the class is available when imported
__all__ = ['AsyncVectorStore']