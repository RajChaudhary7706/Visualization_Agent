from fastapi import FastAPI
from app.routes.analyze import router

app = FastAPI()

app.include_router(router)

@app.get("/")
def home():
    return {"message": "AI Architecture Agent Running 🚀"}