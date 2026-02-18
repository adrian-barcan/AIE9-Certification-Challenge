"""Document management API endpoints.

Handles document ingestion into the RAG pipeline and listing indexed documents.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas import IngestResponse, DocumentInfo
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents() -> IngestResponse:
    """Trigger RAG pipeline to ingest documents from the /documents folder.

    Loads PDFs, chunks them, generates embeddings, and stores in Qdrant.

    Returns:
        Summary of ingested documents and chunk counts.
    """
    try:
        result = await rag_service.ingest_documents()
        return IngestResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/", response_model=list[DocumentInfo])
async def list_documents() -> list[DocumentInfo]:
    """List indexed documents with collection info.

    Returns:
        List with collection status info.
    """
    try:
        info = await rag_service.get_collection_info()
        return [
            DocumentInfo(
                filename=f"Collection: {info['collection']}",
                chunk_count=info["points_count"],
            )
        ]
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
