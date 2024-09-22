from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.file_upload.utils import generate_embedding
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

router = APIRouter(prefix="/query")

qdrant_host = "localhost"
qdrant_port = 6333
client = QdrantClient(host=qdrant_host, port=qdrant_port)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class QueryResponse(BaseModel):
    chunk_id: int
    document_id: str
    title: str
    content: str
    score: float

@router.post("/search", response_model=List[QueryResponse])
async def search_documents(query_request: QueryRequest):
    try:
        
        query_embedding = generate_embedding(query_request.query)

        
        search_results = client.search(
            collection_name="document_collection",
            query_vector=query_embedding,
            limit=query_request.top_k
        )

        responses = []
        for result in search_results:
            payload = result.payload
            responses.append(QueryResponse(
                chunk_id=payload.get('chunk_id'),
                document_id=payload.get('document_id'),
                title=payload.get('title', ''),
                content=payload.get('content', ''),
                score=result.score
            ))

        return responses

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during the search: {str(e)}")

class FilteredQueryRequest(QueryRequest):
    source_type: str = None

@router.post("/filtered_search", response_model=List[QueryResponse])
async def filtered_search_documents(query_request: FilteredQueryRequest):
    try:
        query_embedding = generate_embedding(query_request.query)      
        search_filter = None
        if query_request.source_type:
            search_filter = Filter(
                must=[FieldCondition(key="metadata.source_type", match=MatchValue(value=query_request.source_type))]
            )

        search_results = client.search(
            collection_name="document_collection",
            query_vector=query_embedding,
            limit=query_request.top_k,
            query_filter=search_filter
        )

        responses = []
        for result in search_results:
            payload = result.payload
            responses.append(QueryResponse(
                chunk_id=payload.get('chunk_id'),
                document_id=payload.get('document_id'),
                title=payload.get('title', ''),
                content=payload.get('content', ''),
                score=result.score
            ))

        return responses

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during the filtered search: {str(e)}")