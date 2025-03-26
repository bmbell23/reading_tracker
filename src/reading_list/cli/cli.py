import click
from .reading_stats import reading_stats
from .media_stats import media_stats
# ... other imports ...

@click.group()
def cli():
    """Reading List CLI"""
    pass

# Add the new reading-stats command
cli.add_command(reading_stats)

# ... other commands ...

if __name__ == '__main__':
    cli()