from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "Hello from Metra Backend!",
        "port": os.getenv("PORT", "No PORT env var"),
        "env": os.getenv("RAILWAY_ENVIRONMENT", "No RAILWAY_ENVIRONMENT")
    }

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 