from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .utils.paths import get_project_paths


app = FastAPI(title="Reading Tracker Reports")

# Initialize templates
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Get project paths
project_paths = get_project_paths()
reports_dir = project_paths['workspace'] / 'reports'
assets_dir = project_paths['workspace'] / 'assets'

# Ensure directories exist
reports_dir.mkdir(parents=True, exist_ok=True)
assets_dir.mkdir(parents=True, exist_ok=True)

# Mount static directories
app.mount("/reports", StaticFiles(directory=str(reports_dir), html=True), name="reports")
app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# Import and include routers
try:
    from .api.routes import router as api_router
    app.include_router(api_router)
except ImportError:
    pass

@app.get("/", response_class=HTMLResponse)
async def reports_index(request: Request):
    """Display an index of all available reports."""
    reports = []
    
    # Define report types to look for
    report_types = ['yearly', 'monthly', 'tbr']
    
    # Collect all HTML reports
    for report_type in report_types:
        type_dir = reports_dir / report_type
        if type_dir.exists():
            for report in type_dir.glob('*.html'):
                reports.append({
                    'name': report.stem.replace('_', ' ').title(),
                    'type': report_type,
                    'url': f"/reports/{report_type}/{report.name}",
                    'date_modified': report.stat().st_mtime
                })
    
    # Sort reports by modification date, newest first
    reports.sort(key=lambda x: x['date_modified'], reverse=True)
    
    return templates.TemplateResponse(
        "reports_index.html",
        {
            "request": request,
            "reports": reports,
            "title": "Reading Tracker Reports"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle internal server errors"""
    print(f"Internal Server Error: {exc}")
    return HTMLResponse(
        content="<h1>Internal Server Error</h1><p>The server encountered an error. Please check the logs for details.</p>",
        status_code=500
    )
