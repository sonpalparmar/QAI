from fastapi import APIRouter, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel
from app.file_upload.utils import generate_embedding
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from starlette.responses import StreamingResponse
import os
import asyncio
import logging

load_dotenv()
YOUR_API_KEY = os.getenv('YOUR_API_KEY')

qdrant_host = "localhost"
qdrant_port = 6333
client = QdrantClient(host=qdrant_host, port=qdrant_port)

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str
    session_id: str

# Store for conversation memories
conversation_store = {}

def get_or_create_memory(session_id: str) -> ConversationBufferMemory:
    if session_id not in conversation_store:
        conversation_store[session_id] = ConversationBufferMemory(return_messages=True)
    return conversation_store[session_id]

llm = ChatGoogleGenerativeAI(
    google_api_key=YOUR_API_KEY,
    model="gemini-1.5-pro",
    temperature=0,
)

class QueryResponseIterator:
    def __init__(self, query: str, session_id: str):
        self.query = query
        self.session_id = session_id
        self.limit = 5

    async def __aiter__(self):
        try:
            query_embedding = generate_embedding(self.query)

            search_results = client.search(
                collection_name="document_collection",
                query_vector=query_embedding,
                limit=self.limit
            )
            
            context = "\n".join([result.payload.get('content', '') for result in search_results])

            
            memory = get_or_create_memory(self.session_id)

          
            history = memory.load_memory_variables({})
            history_messages = history.get("history", [])

            
            system_message = f"""You are an AI assistant designed to answer questions based on the provided context and previous conversation history. Your goal is to provide accurate, relevant, and concise responses.

            Guidelines:
            1. Use the given context to inform your answers when possible.
            2. If the context doesn't provide enough information, use your general knowledge to supplement the answer.
            3. Consider the conversation history when formulating your response to maintain continuity.
            4. Organize your answers with clear structure, using bullet points or numbered lists when appropriate.
            5. If you're uncertain about any part of your answer, clearly communicate that uncertainty.
            6. Avoid repeating the question in your answer.
            7. If asked about previous questions or context, refer to the conversation history provided.

            Context: {context}
            """

            messages = [
                HumanMessage(content=system_message)
            ] + history_messages + [HumanMessage(content=self.query)]

            for attempt in range(3):  # Retry up to 3 times
                try:
                    response = await llm.agenerate([messages])
                    ai_message = response.generations[0][0].text

                    # Add the new query and response to the memory
                    memory.save_context({"input": self.query}, {"output": ai_message})

                    for chunk in ai_message.split():
                        yield chunk + " "
                        await asyncio.sleep(0.05)
                    
                    break  # If successful, exit the retry loop
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == 2:  # If it's the last attempt
                        yield "I apologize, but I'm having trouble processing your request at the moment. Please try again later."
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        except Exception as e:
            logger.error(f"An error occurred during query processing: {str(e)}")
            yield "I apologize, but I encountered an error while processing your query. Please try again later."

@router.post("/query", response_class=StreamingResponse)
async def query(query: QueryRequest):
    return StreamingResponse(QueryResponseIterator(query.query, query.session_id), media_type="text/plain")