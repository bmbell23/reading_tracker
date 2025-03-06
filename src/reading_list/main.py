from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

# Initialize paths
templates_dir = Path(__file__).parent / "templates"
reports_dir = Path(__file__).parent.parent.parent / "reports"
assets_path = Path(__file__).parent.parent.parent / "assets"

# Initialize templates
templates = Jinja2Templates(directory=str(templates_dir))

# Mount the reports directory as static files
app.mount("/reports", StaticFiles(directory=str(reports_dir)), name="reports")
app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

def datetime_filter(timestamp):
    """Convert timestamp to human readable date"""
    try:
        date = datetime.fromtimestamp(float(timestamp))
        return date.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return "Unknown date"

# Register the filter with Jinja2
templates.env.filters["datetime"] = datetime_filter

@app.get("/", response_class=HTMLResponse)
async def reports_index(request: Request):
    """Display an index of all available reports."""
    reports = []

    # Define report types to look for
    report_types = ['yearly', 'monthly', 'tbr']

    try:
        # Create reports directory if it doesn't exist
        reports_dir.mkdir(parents=True, exist_ok=True)

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
    except Exception as e:
        print(f"Error in reports_index: {str(e)}")
        raise

@app.get("/reports/{report_type}/{report_name}")
async def serve_report(report_type: str, report_name: str):
    """Serve a specific report file."""
    report_path = reports_dir / report_type / report_name
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(str(report_path))

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle internal server errors"""
    print(f"Internal Server Error: {exc}")
    return HTMLResponse(
        content="<h1>Internal Server Error</h1><p>The server encountered an error. Please check the logs for details.</p>",
        status_code=500
    )

@app.get("/tbr", response_class=HTMLResponse)
async def tbr_manager(request: Request):
    """Display the TBR manager interface."""
    try:
        # Initialize the ReadingChainService
        chain_service = ReadingChainService()
        
        # Get all chains with their books
        all_chains = chain_service.get_all_chains_with_books()
        
        # Reformat the data structure to match template expectations
        chains = {
            chain['media'].lower(): {
                'total_books': chain['total_books'],
                'total_pages': chain['total_pages'],
                'completion_rate': chain['completion_rate'],
                'books': chain['books']
            }
            for chain in all_chains
        }
        
        return templates.TemplateResponse(
            "tbr/tbr_manager.html",
            {
                "request": request,
                "chains": chains,
                "title": "TBR Manager"
            }
        )
    except Exception as e:
        print(f"Error in tbr_manager: {str(e)}")
        raise
