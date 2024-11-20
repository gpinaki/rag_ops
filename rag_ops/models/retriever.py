from langchain_community.vectorstores.chroma import Chroma
from typing import List, Tuple
from langchain.schema import Document
import asyncio

class AsyncDocumentRetriever:
    def __init__(self, vector_db: Chroma):
        self.vector_db = vector_db

    async def aretrieve(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Document]:
        """Asynchronously retrieve documents."""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self.vector_db.similarity_search,
            query,
            top_k
        )

    async def aretrieve_with_scores(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """Asynchronously retrieve documents with relevance scores."""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self.vector_db.similarity_search_with_scores,
            query,
            top_k
        )

# This ensures the class is available when imported
__all__ = ['AsyncDocumentRetriever']