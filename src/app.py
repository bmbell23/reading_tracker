from fastapi import FastAPI
from reading_list.routes.api import router as api_router  # Updated import path

app = FastAPI(title="Reading List API")

# Register routes
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
