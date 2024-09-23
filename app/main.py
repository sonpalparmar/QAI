from fastapi import FastAPI
from app.file_upload.file_upload import router as upload_router
# from app.file_upload.search import router as search_router
from app.response.response import router as query_router
app = FastAPI()

app.include_router(upload_router)
# app.include_router(search_router) 
app.include_router(query_router)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
