"""
Entry point for `python -m scenografia` command.

Enables CLI invocation via: python -m scenografia generate --prompt "..." --mode standard --orientation landscape
"""

from scenografia.main import app

if __name__ == "__main__":
    app()
