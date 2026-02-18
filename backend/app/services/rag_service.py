"""RAG pipeline service.

Handles document ingestion, chunking, embedding, vector storage in Qdrant,
and retrieval with Cohere reranking. Directly adapted from AIE9 Sessions 2, 4, and 10.

Usage:
    rag = RAGService()
    await rag.ingest_documents("/path/to/pdfs")
    results = await rag.query("Ce este TEZAUR?")
    context = await rag.get_context_for_prompt("Ce este TEZAUR?")
"""

import logging
import os
from typing import Optional

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore

from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """RAG pipeline for Romanian financial documents.

    Handles the full lifecycle: load PDFs → chunk → embed → store in Qdrant → retrieve → rerank.

    Architecture follows AIE9 patterns:
    - Session 2: OpenAI embeddings (text-embedding-3-small)
    - Session 4: RecursiveCharacterTextSplitter + Qdrant vector store
    - Session 10: Cohere reranking for improved precision

    Attributes:
        embeddings: OpenAI embedding model instance.
        text_splitter: Chunking strategy for documents.
        vector_store: Qdrant vector store for similarity search.
        reranker: Cohere reranking model for improved retrieval.
    """

    def __init__(self) -> None:
        """Initialize RAG service components."""
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._qdrant_client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self.vector_store: Optional[QdrantVectorStore] = None
        self.reranker = CohereRerank(
            model="rerank-multilingual-v3.0",
            cohere_api_key=settings.cohere_api_key,
            top_n=settings.rag_rerank_top_n,
        )
        self._initialized = False

    def _ensure_vector_store(self) -> QdrantVectorStore:
        """Get or create the Qdrant vector store.

        Returns:
            QdrantVectorStore instance connected to the configured collection.
        """
        if self.vector_store is None:
            self.vector_store = QdrantVectorStore(
                client=self._qdrant_client,
                collection_name=settings.qdrant_collection,
                embedding=self.embeddings,
            )
        return self.vector_store

    async def ingest_documents(self, folder_path: Optional[str] = None) -> dict:
        """Load, chunk, embed, and store documents from a folder.

        Processes all PDF files in the specified folder. Each document is split
        into chunks, embedded via OpenAI, and stored in Qdrant.

        Args:
            folder_path: Path to folder containing PDF files.
                Defaults to settings.documents_path.

        Returns:
            Summary dict with documents_processed, total_chunks, and collection name.

        Raises:
            FileNotFoundError: If the folder path doesn't exist.
            ValueError: If no PDF files are found in the folder.
        """
        folder_path = folder_path or settings.documents_path

        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Documents folder not found: {folder_path}")

        # Find all PDF files
        pdf_files = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith(".pdf")
        ]

        if not pdf_files:
            raise ValueError(f"No PDF files found in {folder_path}")

        logger.info(f"Found {len(pdf_files)} PDF files to ingest")

        # Load and chunk all documents
        all_chunks: list[Document] = []
        for pdf_path in pdf_files:
            logger.info(f"Loading: {os.path.basename(pdf_path)}")
            loader = PyMuPDFLoader(pdf_path)
            documents = loader.load()

            # Add source metadata
            for doc in documents:
                doc.metadata["source_file"] = os.path.basename(pdf_path)

            # Chunk the documents
            chunks = self.text_splitter.split_documents(documents)
            logger.info(
                f"  → {len(documents)} pages → {len(chunks)} chunks"
            )
            all_chunks.extend(chunks)

        logger.info(f"Total chunks to embed: {len(all_chunks)}")

        # Store in Qdrant (creates collection if it doesn't exist)
        self.vector_store = QdrantVectorStore.from_documents(
            documents=all_chunks,
            embedding=self.embeddings,
            url=f"http://{settings.qdrant_host}:{settings.qdrant_port}",
            collection_name=settings.qdrant_collection,
            force_recreate=True,  # Recreate collection on each ingestion
        )

        summary = {
            "documents_processed": len(pdf_files),
            "total_chunks": len(all_chunks),
            "collection": settings.qdrant_collection,
        }
        logger.info(f"Ingestion complete: {summary}")
        return summary

    async def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        use_reranking: bool = True,
    ) -> list[Document]:
        """Retrieve relevant document chunks for a question.

        Performs similarity search in Qdrant, optionally followed by
        Cohere reranking for improved precision.

        Args:
            question: The user's question.
            top_k: Number of initial results to retrieve before reranking.
                Defaults to settings.rag_top_k.
            use_reranking: Whether to apply Cohere reranking.
                Set to False for baseline evaluation comparison.

        Returns:
            List of relevant Document chunks, ordered by relevance.
        """
        top_k = top_k or settings.rag_top_k
        store = self._ensure_vector_store()
        base_retriever = store.as_retriever(
            search_kwargs={"k": top_k},
        )

        if use_reranking:
            # Cohere reranking: retrieve top_k → rerank → return top_n
            retriever = ContextualCompressionRetriever(
                base_compressor=self.reranker,
                base_retriever=base_retriever,
            )
            results = await retriever.ainvoke(question)
        else:
            # Baseline: no reranking (for eval comparison)
            results = await base_retriever.ainvoke(question)

        logger.info(
            f"Query: '{question[:50]}...' → {len(results)} results "
            f"(reranking={'on' if use_reranking else 'off'})"
        )
        return results

    async def get_context_for_prompt(
        self,
        question: str,
        use_reranking: bool = True,
    ) -> str:
        """Retrieve and format context for inclusion in an LLM prompt.

        Combines retrieved chunks into a formatted context string with
        source citations.

        Args:
            question: The user's question.
            use_reranking: Whether to apply Cohere reranking.

        Returns:
            Formatted context string with numbered chunks and sources.
        """
        results = await self.query(question, use_reranking=use_reranking)

        if not results:
            return "Nu am găsit informații relevante în documentele indexate."

        context_parts = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source_file", "unknown")
            page = doc.metadata.get("page", "?")
            context_parts.append(
                f"[{i}] (Source: {source}, Page: {page})\n{doc.page_content}"
            )

        return "\n\n---\n\n".join(context_parts)

    async def get_collection_info(self) -> dict:
        """Get information about the current Qdrant collection.

        Returns:
            Dict with collection name, point count, and status.
        """
        try:
            info = self._qdrant_client.get_collection(settings.qdrant_collection)
            return {
                "collection": settings.qdrant_collection,
                "points_count": info.points_count,
                "status": info.status.value,
            }
        except Exception:
            return {
                "collection": settings.qdrant_collection,
                "points_count": 0,
                "status": "not_found",
            }


# Singleton instance
rag_service = RAGService()


if __name__ == "__main__":
    import asyncio

    async def test():
        """Quick test: ingest and query."""
        print("Ingesting documents...")
        result = await rag_service.ingest_documents()
        print(f"Ingested: {result}")

        print("\nQuerying: 'Ce este TEZAUR?'")
        context = await rag_service.get_context_for_prompt("Ce este TEZAUR?")
        print(f"Context:\n{context}")

    asyncio.run(test())
