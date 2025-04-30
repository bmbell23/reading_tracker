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

    try:
        reports_dir.mkdir(parents=True, exist_ok=True)

        for report in reports_dir.rglob('*.html'):
            report_type = report.parent.name if report.parent != reports_dir else 'general'
            url_path = report.relative_to(reports_dir)

            # Parse the filename to determine the appropriate display name
            name = report.stem
            if name.endswith('_reading_journey'):
                year = name.split('_')[0]
                display_name = f"{year} Reading Journey"
            elif name.endswith('_reading_goals'):
                year = name.split('_')[0]
                display_name = f"{year} Reading Goals"
            else:
                display_name = name.replace('_', ' ').title()

            reports.append({
                'name': display_name,
                'type': report_type,
                'url': f"/reports/{url_path}",
                'date_modified': report.stat().st_mtime
            })

        return templates.TemplateResponse(
            "reports_index.html",
            {
                "request": request,
                "reports": reports,
                "title": "GreatReads"
            }
        )
    except Exception as e:
        # Log the error and return a simple error response
        print(f"Error generating reports index: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "Failed to generate reports index",
                "title": "Error - GreatReads"
            },
            status_code=500
        )
