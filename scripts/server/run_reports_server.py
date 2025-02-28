import uvicorn
from reading_list.main import app

def main():
    """Run the reports server."""
    uvicorn.run(
        "reading_list.main:app",
        host="0.0.0.0",
        port=8001,  # Changed from 8000 to 8001
        reload=False,
        workers=2
    )

if __name__ == "__main__":
    main()
