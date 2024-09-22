from fastapi import APIRouter, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from app.file_upload.utils import generate_embedding
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

qdrant_host = "localhost"
qdrant_port = 6333
client = QdrantClient(host=qdrant_host, port=qdrant_port)

YOUR_API_KEY = "AIzaSyBbn-o5unmTL_aZ86OPWoqPuvMlDTJ-WDc"

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    chunk_id: int
    document_id: str
    title: str
    content: str
    score: float


@router.post("/query")
def query(query: QueryRequest):
    try:
        limit = 5
        # Generate embedding for the query
        query_embedding = generate_embedding(query.query)

        # Search in Qdrant
        search_results = client.search(
            collection_name="document_collection",
            query_vector=query_embedding,
            limit=limit
        )

        # Process and format the results
        responses = []
        for result in search_results:
            payload = result.payload
            responses.append(payload.get('content', ''))

        # Initialize the Google Generative AI client
        llm = ChatGoogleGenerativeAI(
            google_api_key=YOUR_API_KEY,
            model="gemini-1.5-pro",
            temperature=0,
        )

        # Construct the user prompt with query and retrieved results
        USER_PROMPT = f"Query: {query.query}\n\nResults:\n" + "\n".join(responses)

        SYSTEM_PROMPT = """
        You are a question answering system that is constantly learning and improving.
        You can process and comprehend vast amounts of text and utilize this knowledge to provide grounded, accurate, and as concise as possible answers to diverse queries.
        Your answer should be well-organized, featuring appropriate headers, subheaders, bullet points, lists, tables to enhance readability.
        You always clearly communicate ANY UNCERTAINTY in your answer. DO NOT echo any given command in your answer.
        """

        messages = [
            ("system", SYSTEM_PROMPT),
            ("human", USER_PROMPT),
        ]

        # Invoke the LLM
        res = llm.invoke(messages)

        return {"response": res}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during the search: {str(e)}")
