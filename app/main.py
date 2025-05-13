# app/main.py

from fastapi import FastAPI
from app.routers import router

app = FastAPI(title="FastAPI AWS S3 Service")

# Include S3 routes at the `/s3` prefix.
app.include_router(router, prefix="/s3", tags=["S3 File Service"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI AWS S3 Service"}
