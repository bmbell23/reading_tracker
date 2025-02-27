from fastapi import FastAPI
from reading_list.api.routes import router as api_router

app = FastAPI(title="Reading List API")
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)