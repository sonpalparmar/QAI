from fastapi import APIRouter, UploadFile, File, HTTPException
from io import StringIO
import pandas as pd
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Distance
from qdrant_client.http import models as rest
from starlette.responses import StreamingResponse
from langchain_google_genai import ChatGoogleGenerativeAI
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
from typing import List, AsyncGenerator
import json

load_dotenv()
YOUR_API_KEY = os.getenv('YOUR_API_KEY')

# Qdrant setup
qdrant_client = QdrantClient(host="localhost", port=6333)
collection_name = "csv_collection"
embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

router = APIRouter()

def create_qdrant_collection():
    try:
        collections = qdrant_client.get_collections()
        if collection_name not in [col.name for col in collections.collections]:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=rest.VectorParams(
                    size=embedding_model.get_sentence_embedding_dimension(),
                    distance=Distance.COSINE
                )
            )
            print(f"Collection '{collection_name}' created successfully.")
        else:
            print(f"Collection '{collection_name}' already exists.")
    except Exception as e:
        print(f"Error creating collection: {str(e)}")
        raise

class CSVToolAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=YOUR_API_KEY,
            model="gemini-1.5-pro",
            temperature=0,
        )

    async def handle_query(self, query: str) -> AsyncGenerator[str, None]:
        if "graph" in query.lower() or "chart" in query.lower():
            async for chunk in self.generate_graph_code(query):
                yield chunk
        else:
            async for chunk in self.query_qdrant_for_csv(query):
                yield chunk

    async def generate_graph_code(self, query: str) -> AsyncGenerator[str, None]:
        prompt = f"""
        You are a code generation tool. The user has uploaded a CSV file.
        The user query is:
        "{query}"
        
        Create Python code using Matplotlib or Seaborn to generate the graph 
        requested in the query. Respond only with the code.
        """
        
        messages = [
            ("system", prompt),
            ("human", query),
        ]
        
        async for chunk in self.llm.astream(messages):
            yield chunk.content

    async def query_qdrant_for_csv(self, query: str) -> AsyncGenerator[str, None]:
        query_embedding = embedding_model.encode(query).tolist()

        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=5
        )

        responses = [result.payload.get('content', '') for result in search_results]

        USER_PROMPT = f"Query: {query}\n\nResults:\n" + "\n".join(responses)

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

        async for chunk in self.llm.astream(messages):
            yield chunk.content

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

@router.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode('utf-8')))

        create_qdrant_collection()
        
        points = []
        for idx, row in df.iterrows():
            text_data = ','.join([str(val) for val in row.values])
            embedding = embedding_model.encode(text_data).tolist()

            points.append(
                PointStruct(
                    id=idx,
                    vector=embedding,
                    payload={'content': text_data}
                )
            )
        
        qdrant_client.upsert(collection_name=collection_name, points=points)

        # Convert DataFrame to JSON-safe format
        df_json = json.loads(df.head().to_json(orient='split'))

        return {"message": "CSV uploaded and stored successfully", "data_preview": df_json}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error uploading CSV: {str(e)}")

@router.post("/query_csv")
async def query_csv(query: str):
    csv_agent = CSVToolAgent()
    
    async def generate():
        async for chunk in csv_agent.handle_query(query):
            yield chunk.encode('utf-8')
    
    return StreamingResponse(generate(), media_type="text/plain")