# Document Management and Query System

This project is a FastAPI-based application that allows users to upload documents, process them, store their content in a vector database (Qdrant), and perform semantic searches on the uploaded documents.

## Features

- Document upload support for PDF, DOCX, and TXT files
- Automatic text extraction from uploaded documents
- Document chunking for efficient processing and storage
- Semantic embedding generation using the 'thenlper/gte-small' model
- Vector storage and retrieval using Qdrant
- Semantic search functionality with optional filtering

## Prerequisites

- Python 3.7+
- FastAPI
- Qdrant
- PyPDF2
- python-docx
- transformers
- llama-index

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/sonpalparmar/QAI.git
   cd document-management-system
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install fastapi uvicorn pydantic python-multipart PyPDF2 python-docx transformers torch llama-index qdrant-client
   ```

4. Install and run Qdrant. You can use Docker for this:
   ```
   docker pull qdrant/qdrant
   docker run -p 6333:6333 qdrant/qdrant
   ```

## Project Structure

```
document-management-system/
├── app/
│   ├── file_upload/
│   │   ├── __init__.py
│   │   ├── file_upload.py
│   │   ├── file_processing.py
│   │   ├── utils.py
│   │   └── query.py
│   ├── __init__.py
│   └── model.py
├── main.py
└── README.md
```

## Usage

1. Start the FastAPI server:
   ```
   uvicorn main:app --reload
   ```

2. The API will be available at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.

3. Use the `/manage/upload` endpoint to upload documents. You can use curl or any API client:
   ```
   curl -X POST "http://localhost:8000/manage/upload" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@path/to/your/document.pdf"
   ```

4. Use the `/query/search` endpoint to search for information in the uploaded documents:
   ```
   curl -X POST "http://localhost:8000/query/search" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query": "Your search query here", "top_k": 5}'
   ```

5. Use the `/query/filtered_search` endpoint to perform a filtered search:
   ```
   curl -X POST "http://localhost:8000/query/filtered_search" -H "accept: application/json" -H "Content-Type: application/json" -d '{"query": "Your search query here", "top_k": 5, "source_type": "pdf"}'
   ```

## API Endpoints

### Document Upload

- **URL**: `/manage/upload`
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Parameters**: 
  - `file`: The document file to upload (PDF, DOCX, or TXT)
- **Response**:  JSON object with upload status and document ID

### Search

- **URL**: `/query/search`
- **Method**: POST
- **Content-Type**: application/json
- **Request Body**:
  ```json
  {
    "query": "Your search query",
    "top_k": 5
  }
  ```
- **Response**: List of relevant document chunks with metadata and relevance scores

### Filtered Search

- **URL**: `/query/filtered_search`
- **Method**: POST
- **Content-Type**: application/json
- **Request Body**:
  ```json
  {
    "query": "Your search query",
    "top_k": 5,
    "source_type": "pdf"
  }
  ```
- **Response**: List of relevant document chunks with metadata and relevance scores, filtered by source type

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
