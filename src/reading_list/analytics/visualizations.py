import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .core import ReadingAnalytics, AuthorAnalytics, SeriesAnalytics, TimeAnalytics

class ReadingVisualizer:
    """Generate visualizations for reading statistics"""
    
    def __init__(self):
        self.reading_analytics = ReadingAnalytics()
        self.author_analytics = AuthorAnalytics()
        self.series_analytics = SeriesAnalytics()
        self.time_analytics = TimeAnalytics()

    def create_reading_trends_chart(self):
        """Create a combination chart showing reading trends over time"""
        df = self.reading_analytics.get_reading_trends()
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Books read line
        fig.add_trace(
            go.Scatter(x=df['month'], y=df['books_read'], name="Books Read"),
            secondary_y=False,
        )
        
        # Words read line
        fig.add_trace(
            go.Scatter(x=df['month'], y=df['words_read'], name="Words Read"),
            secondary_y=True,
        )
        
        fig.update_layout(
            title="Reading Trends Over Time",
            xaxis_title="Month",
            yaxis_title="Books Read",
            yaxis2_title="Words Read",
            height=500,  # Fixed height for consistency
            margin=dict(t=30, b=30, l=30, r=30)  # Reduced margins
        )
        
        return fig

    def create_author_distribution_chart(self):
        """Create a chart showing distribution of books by top authors"""
        df = self.author_analytics.get_top_authors()
        
        fig = px.bar(
            df,
            x='author',
            y=['books_read', 'total_words'],
            title="Top Authors by Books and Words",
            barmode='group',
            height=500,  # Fixed height for consistency
        )
        
        fig.update_layout(
            margin=dict(t=30, b=30, l=30, r=30)  # Reduced margins
        )
        
        return fig

    def create_series_progress_chart(self):
        """Create a chart showing progress in different series"""
        df = self.series_analytics.get_series_completion()
        
        fig = px.bar(
            df,
            x='series',
            y=['books_read', 'total_books'],
            title="Series Completion Progress",
            barmode='overlay',
            height=500,  # Fixed height for consistency
        )
        
        fig.update_layout(
            margin=dict(t=30, b=30, l=30, r=30)  # Reduced margins
        )
        
        return fig

    def create_reading_velocity_chart(self):
        """Create a chart showing reading velocity over time"""
        df = self.time_analytics.get_reading_velocity()
        
        fig = px.line(
            df,
            x='period',
            y=['books_per_day', 'words_per_day'],
            title="Reading Velocity Over Time"
        )
        
        return fig

    def generate_dashboard(self, output_path: str):
        """Generate a complete HTML dashboard with all charts"""
        from dash import Dash, html, dcc
        
        app = Dash(__name__)
        
        app.layout = html.Div([
            html.H1("Reading Analytics Dashboard"),
            
            # Wrap charts in a flex container
            html.Div([
                # Each chart in a flex item with width set to 33%
                html.Div([
                    dcc.Graph(figure=self.create_reading_trends_chart())
                ], style={'width': '33%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(figure=self.create_author_distribution_chart())
                ], style={'width': '33%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(figure=self.create_series_progress_chart())
                ], style={'width': '33%', 'display': 'inline-block'})
            ], style={
                'display': 'flex',
                'flexDirection': 'row',
                'justifyContent': 'space-between',
                'gap': '20px',
                'marginTop': '20px'
            })
        ], style={
            'padding': '20px',
            'maxWidth': '1800px',  # Increased to accommodate horizontal layout
            'margin': '0 auto'
        })
        
        app.write_html(output_path)
