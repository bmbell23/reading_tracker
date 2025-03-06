from reading_list.analytics.visualizations import ReadingVisualizer
from reading_list.reports.chain_report import generate_chain_report
from reading_list.utils.paths import get_project_paths
from rich.console import Console
from pathlib import Path

console = Console()

def main():
    console.print("[blue]Starting dashboard generation...[/blue]")
    
    # Get project paths
    paths = get_project_paths()
    reports_dir = paths['reports']
    
    # Ensure reports directory exists
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # First generate the chain report
    console.print("[blue]Generating chain report...[/blue]")
    generate_chain_report()
    
    # Then generate the dashboard
    console.print("[blue]Generating dashboard visualizations...[/blue]")
    visualizer = ReadingVisualizer()
    dashboard_path = reports_dir / "reading_dashboard.html"
    visualizer.generate_dashboard(str(dashboard_path))
    
    console.print(f"[green]Dashboard generated successfully at: {dashboard_path}[/green]")

if __name__ == "__main__":
    main()
