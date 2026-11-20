"""WSGI app for local development; use the CLI for a running server."""
from .server import create_app

app = create_app()


if __name__ == "__main__":
    from .cli import main
    main()
