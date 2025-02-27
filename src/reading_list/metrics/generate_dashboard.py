from reading_list.analytics.visualizations import ReadingVisualizer

def main():
    visualizer = ReadingVisualizer()
    visualizer.generate_dashboard("reports/reading_dashboard.html")

if __name__ == "__main__":
    main()