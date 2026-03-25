from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import predict_router, analytics_router

app = FastAPI(title="Real Estate ML API", version="1.0.0")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router, prefix="/api/predict", tags=["prediction"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Real Estate ML API is running"}
