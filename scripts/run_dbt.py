"""Lance dbt avec l'interpréteur verrouillé, sans lanceur Windows intermédiaire."""

from dbt.cli.main import cli


if __name__ == "__main__":
    cli()
