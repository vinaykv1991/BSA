from fastapi import FastAPI
from app.database import engine
from app.models import models
from app.api.endpoints import router as api_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Financial Planner API")

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Financial Planner API"}
