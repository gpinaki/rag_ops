import aiofiles
import pandas as pd
import fitz
import os
from typing import Optional
import asyncio
from langchain.schema import Document

class AsyncFileProcessor:
    @staticmethod
    async def aprocess_pdf(file_path: str) -> str:
        """Asynchronously process PDF files."""
        text = ""
        # PyMuPDF operations are CPU-bound, run in thread pool
        def read_pdf():
            with fitz.open(file_path) as pdf_reader:
                return "\n".join(page.get_text() for page in pdf_reader)
                
        return await asyncio.get_event_loop().run_in_executor(None, read_pdf)

    @staticmethod
    async def aprocess_csv(file_path: str) -> str:
        """Asynchronously process CSV files."""
        def read_csv():
            return pd.read_csv(file_path).to_string()
        return await asyncio.get_event_loop().run_in_executor(None, read_csv)

    @staticmethod
    async def aprocess_excel(file_path: str) -> str:
        """Asynchronously process Excel files."""
        def read_excel():
            return pd.read_excel(file_path).to_string()
        return await asyncio.get_event_loop().run_in_executor(None, read_excel)

    @staticmethod
    async def aprocess_file(uploaded_file) -> Optional[Document]:
        """Process an uploaded file and return a Document object."""
        temp_file_path = os.path.join("/tmp", uploaded_file.name)
        
        # Save uploaded file
        async with aiofiles.open(temp_file_path, 'wb') as f:
            await f.write(uploaded_file.getbuffer())

        try:
            if uploaded_file.type == "application/pdf":
                text = await AsyncFileProcessor.aprocess_pdf(temp_file_path)
            elif uploaded_file.type == "text/csv":
                text = await AsyncFileProcessor.aprocess_csv(temp_file_path)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                text = await AsyncFileProcessor.aprocess_excel(temp_file_path)
            else:
                return None

            return Document(
                page_content=text,
                metadata={"file_name": uploaded_file.name}
            )
        finally:
            # Cleanup temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

# This ensures the class is available when imported
__all__ = ['AsyncFileProcessor']