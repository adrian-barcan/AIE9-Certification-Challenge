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
import pickle
from typing import Optional

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever, ParentDocumentRetriever, EnsembleRetriever
from langchain.storage import InMemoryStore
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore

from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Advanced RAG pipeline for Romanian financial documents.

    Handles the full lifecycle: load PDFs → Parent/Child chunking → store in Qdrant (child) & Memory (parent) 
    → retrieval via Ensemble (BM25 + Vector) → Cohere rerank.

    Architecture follows AIE9 Session 11 (Advanced Retrieval):
    - ParentDocumentRetriever (small-to-big retrieval)
    - BM25Retriever (exact keyword matching)
    - EnsembleRetriever (combining dense and sparse)
    - CohereRerank (contextual compression)

    Attributes:
        embeddings: OpenAI embedding model instance.
        parent_splitter: Chunking strategy for parent documents.
        child_splitter: Chunking strategy for child documents.
        vector_store: Qdrant vector store for similarity search.
        docstore: InMemoryStore for parent documents.
        bm25_retriever: BM25 keyword retriever.
        reranker: Cohere reranking model for improved retrieval.
    """

    def __init__(self) -> None:
        """Initialize Advanced RAG service components."""
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_parent_chunk_size,
            chunk_overlap=settings.rag_parent_chunk_overlap,
        )
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_child_chunk_size,
            chunk_overlap=settings.rag_child_chunk_overlap,
        )
        self._qdrant_client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        
        self.vector_store: Optional[QdrantVectorStore] = None
        self.docstore = InMemoryStore()
        self.bm25_retriever: Optional[BM25Retriever] = None
        
        self.reranker = CohereRerank(
            model="rerank-multilingual-v3.0",
            cohere_api_key=settings.cohere_api_key,
            top_n=settings.rag_rerank_top_n,
        )

    def _ensure_vector_store(self) -> QdrantVectorStore:
        """Get or create the Qdrant vector store."""
        if self.vector_store is None:
            self.vector_store = QdrantVectorStore(
                client=self._qdrant_client,
                collection_name=settings.qdrant_collection,
                embedding=self.embeddings,
            )
        return self.vector_store

    def _load_or_init_bm25(self, folder_path: str):
        """Loads BM25 and DocStore states from disk if they exist."""
        bm25_path = os.path.join(folder_path, "bm25_retriever.pkl")
        docstore_path = os.path.join(folder_path, "docstore.pkl")
        
        if os.path.exists(bm25_path) and os.path.exists(docstore_path):
            try:
                with open(bm25_path, "rb") as f:
                    self.bm25_retriever = pickle.load(f)
                with open(docstore_path, "rb") as f:
                    self.docstore.store = pickle.load(f)
                logger.info("Loaded BM25 and DocStore from disk.")
            except Exception as e:
                logger.error(f"Error loading local state: {e}")

    def _save_bm25(self, folder_path: str):
        """Saves BM25 and DocStore states to disk."""
        bm25_path = os.path.join(folder_path, "bm25_retriever.pkl")
        docstore_path = os.path.join(folder_path, "docstore.pkl")
        
        with open(bm25_path, "wb") as f:
            pickle.dump(self.bm25_retriever, f)
        with open(docstore_path, "wb") as f:
            pickle.dump(self.docstore.store, f)
        logger.info("Saved BM25 and DocStore to disk.")

    async def ingest_documents(self, folder_path: Optional[str] = None) -> dict:
        """Load, chunk, embed, and store documents from a folder using ParentDocumentRetriever.

        Args:
            folder_path: Path to folder containing PDF files.

        Returns:
            Summary dict
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

        # For ParentDocument and BM25, since they rely on LocalStore/In-Memory state which is lost on restart,
        # we try fetching state from disk. If we need to ingest, we recreate the collection.
        # Check if we have vectors
        need_ingest = True
        try:
            info = self._qdrant_client.get_collection(settings.qdrant_collection)
            if info.points_count > 0:
                self._load_or_init_bm25(folder_path)
                if self.bm25_retriever and len(self.docstore.store) > 0:
                    need_ingest = False
        except Exception:
            pass # Collection might not exist yet

        if not need_ingest:
            logger.info("Documents already ingested and states loaded.")
            return {
                "documents_processed": len(pdf_files),
                "status": "already_ingested"
            }

        logger.info(f"Ingesting {len(pdf_files)} PDF files...")

        # Create/Recreate collection
        try:
            self._qdrant_client.recreate_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
            )
        except Exception as e:
            logger.error(f"Failed to recreate Qdrant collection: {e}")

        self.vector_store = self._ensure_vector_store()
        
        # Setup ParentDocumentRetriever
        parent_retriever = ParentDocumentRetriever(
            vectorstore=self.vector_store,
            docstore=self.docstore,
            child_splitter=self.child_splitter,
            parent_splitter=self.parent_splitter,
        )

        all_docs: list[Document] = []
        for pdf_path in pdf_files:
            logger.info(f"Loading: {os.path.basename(pdf_path)}")
            loader = PyMuPDFLoader(pdf_path)
            documents = loader.load()

            # Add source metadata & fix 0-indexed pages
            for doc in documents:
                doc.metadata["source_file"] = os.path.basename(pdf_path)
                if "page" in doc.metadata:
                    doc.metadata["page"] += 1

            all_docs.extend(documents)
            
        logger.info(f"Total pages loaded: {len(all_docs)}")

        # 1. Add to Parent Retriever (Vector Store + DocStore)
        parent_retriever.add_documents(all_docs)
        
        # 2. Add to BM25
        self.bm25_retriever = BM25Retriever.from_documents(all_docs)
        
        # Persist states
        self._save_bm25(folder_path)

        summary = {
            "documents_processed": len(pdf_files),
            "collection": settings.qdrant_collection,
            "status": "ingested"
        }
        logger.info(f"Ingestion complete: {summary}")
        return summary

    async def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        use_reranking: bool = True,
    ) -> list[Document]:
        """Retrieve relevant parent document chunks using Ensemble Retriever.

        Args:
            question: The user's question.
            top_k: Number of initial results to retrieve.
            use_reranking: Whether to apply Cohere reranking.

        Returns:
            List of relevant Document chunks, ordered by relevance.
        """
        top_k = top_k or settings.rag_top_k
        self.vector_store = self._ensure_vector_store()
        
        # Make sure BM25/DocStore is loaded
        if not self.bm25_retriever or not self.docstore.store:
            self._load_or_init_bm25(settings.documents_path)
            
        parent_retriever = ParentDocumentRetriever(
            vectorstore=self.vector_store,
            docstore=self.docstore,
            child_splitter=self.child_splitter,
            parent_splitter=self.parent_splitter,
            search_kwargs={"k": top_k}
        )

        # Ensemble
        if self.bm25_retriever:
            self.bm25_retriever.k = top_k
            ensemble_retriever = EnsembleRetriever(
                retrievers=[self.bm25_retriever, parent_retriever],
                weights=[0.3, 0.7] # Emphasize dense but keep sparse for exact hits
            )
        else:
            logger.warning("BM25 not loaded, falling back to pure Vector search.")
            ensemble_retriever = parent_retriever

        if use_reranking:
            retriever = ContextualCompressionRetriever(
                base_compressor=self.reranker,
                base_retriever=ensemble_retriever,
            )
            results = await retriever.ainvoke(question)
        else:
            results = await ensemble_retriever.ainvoke(question)

        logger.info(
            f"Query: '{question[:50]}...' → {len(results)} results "
        )
        return results

    async def get_context_for_prompt(
        self,
        question: str,
        use_reranking: bool = True,
    ) -> str:
        """Retrieve and format context for inclusion in an LLM prompt."""
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
        """Get information about the current Qdrant collection."""
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
        print(f"\nFound {len(context.split('---'))} contexts")

    asyncio.run(test())
