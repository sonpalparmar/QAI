from fastapi import APIRouter, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from app.file_upload.utils import generate_embedding
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from starlette.responses import StreamingResponse
import os

load_dotenv()
YOUR_API_KEY = os.getenv('YOUR_API_KEY')

qdrant_host = "localhost"
qdrant_port = 6333
client = QdrantClient(host=qdrant_host, port=qdrant_port)

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

class QueryResponseIterator:
    def __init__(self, query: str):
        self.query = query
        self.limit = 5
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=YOUR_API_KEY,
            model="gemini-1.5-pro",
            temperature=0,
        )

    async def __aiter__(self):
        try:
            query_embedding = generate_embedding(self.query)

            search_results = client.search(
                collection_name="document_collection",
                query_vector=query_embedding,
                limit=self.limit
            )

            # print(search_results)
            
            responses = []
            for result in search_results:
                payload = result.payload
                responses.append(payload.get('content', ''))

            USER_PROMPT = f"Query: {self.query}\n\nResults:\n" + "\n".join(responses)

            SYSTEM_PROMPT = """
            You are a question answering system that is constantly learning and improving.
            if you are not able to give answer from given context then you utilize your knowledge and give answer, answer should be well-organized.
            You can process and comprehend vast amounts of text and utilize this knowledge to provide grounded, accurate, and as concise as possible answers to diverse queries.
            Your answer should be well-organized, featuring appropriate headers, subheaders, bullet points, lists, tables to enhance readability.
            You always clearly communicate ANY UNCERTAINTY in your answer. DO NOT echo any given command in your answer.
            """

            messages = [
                ("system", SYSTEM_PROMPT),
                ("human", USER_PROMPT),
            ]

           
            async for chunk in self.llm.astream(messages):
                yield chunk.content  

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred during the search: {str(e)}")

@router.post("/query", response_class=StreamingResponse)
async def query(query: QueryRequest):
    return StreamingResponse(QueryResponseIterator(query.query), media_type="text/plain")
