"""
Minimal FastAPI app for Render deployment testing
Tests basic HTTP connectivity without complex dependencies
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Octa Minimal Test")

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})

@app.get("/")
async def root():
    return JSONResponse({"message": "Octa API - Minimal Version"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
