import uvicorn
import os
from pathlib import Path

# Add debug print
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {os.environ.get('PYTHONPATH')}")

def main():
    """Run the reports server."""
    uvicorn.run(
        "reading_list.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        workers=2,
        log_level="debug"  # Add debug logging
    )

if __name__ == "__main__":
    main()
