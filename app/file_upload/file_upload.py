from fastapi import APIRouter, HTTPException, UploadFile, File
from app.model import DocumentIngestionRequest
from app.file_upload.utils import generate_embedding, chunk_document, create_metadata
from app.file_upload.file_processing import process_uploaded_file
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

router = APIRouter(prefix="/manage")

qdrant_host = "localhost"
qdrant_port = 6333

# Create a QdrantClient instance
client = QdrantClient(host=qdrant_host, port=qdrant_port)

def ensure_collection_exists(collection_name: str, vector_size: int):
    collections = client.get_collections().collections
    if not any(collection.name == collection_name for collection in collections):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

def insert_vectors(collection_name: str, chunk: str, metadata: dict, chunk_id: int, embeddings: list):
    client.upsert(
        collection_name=collection_name,
        points=[
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings,
                payload={
                    "document_id": metadata["document_id"],
                    "chunk_id": chunk_id,
                    "title": metadata.get("title", ""),
                    "content": chunk,
                    "metadata": metadata,
                }
            )
        ]
    )

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await process_uploaded_file(file)

        source_type = file.filename.split(".")[-1].lower()
        title = file.filename

        # Create metadata
        metadata = create_metadata(
            document_title=title,
            source_type=source_type,
            doc_updated_at=None,
            primary_owners=[],
            secondary_owners=[],
            metadata_list=[],
            access_control_list={},
            document_sets={},
        )

        # Chunk the document content
        chunks = chunk_document(content)

        # Ensure the collection exists
        vector_size = len(generate_embedding("Sample text"))
        collection_name = "document_collection"
        ensure_collection_exists(collection_name, vector_size)

        # Ingest each chunk
        for chunk_id, chunk in enumerate(chunks):
            content_embedding = generate_embedding(chunk)
            insert_vectors(collection_name, chunk, metadata, chunk_id, content_embedding)

        return {
            "status": "Document ingested successfully",
            "document_id": metadata["document_id"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")