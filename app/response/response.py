from fastapi import APIRouter, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from app.file_upload.utils import generate_embedding
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os


load_dotenv()
YOUR_API_KEY = os.getenv('YOUR_API_KEY')

qdrant_host = "localhost"
qdrant_port = 6333
client = QdrantClient(host=qdrant_host, port=qdrant_port)



router = APIRouter()

class QueryRequest(BaseModel):
    query: str


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

        responses = []
        for result in search_results:
            payload = result.payload
            responses.append(payload.get('content', ''))

        llm = ChatGoogleGenerativeAI(
            google_api_key=YOUR_API_KEY,
            model="gemini-1.5-pro",
            temperature=0,
        )


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

      
        res = llm.invoke(messages)

        return {"response": res}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during the search: {str(e)}")
