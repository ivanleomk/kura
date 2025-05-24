import typer
import uvicorn
from kura.cli.server import api
from rich import print
import os

app = typer.Typer()


@app.command()
def start_app(
    dir: str = typer.Option(
        "./checkpoints",
        help="Directory to use for checkpoints, relative to the current directory",
    ),
):
    """Start the FastAPI server"""
    os.environ["KURA_CHECKPOINT_DIR"] = dir
    print(
        "\n[bold green]🚀 Access website at[/bold green] [bold blue][http://localhost:8000](http://localhost:8000)[/bold blue]\n"
    )
    uvicorn.run(api, host="0.0.0.0", port=8000)


@app.command()
def explore(
    checkpoint_dir: str = typer.Argument(
        ...,
        help="Directory containing checkpoint files to explore",
    ),
    port: int = typer.Option(
        8001,
        help="Port to run the explorer API on",
    ),
):
    """Start the Kura Explorer API for checkpoint data exploration"""
    os.environ["KURA_CHECKPOINT_DIR"] = checkpoint_dir
    
    # Import here to avoid circular dependencies
    from kura.explorer.backend.main import app as explorer_app
    
    print(
        f"\n[bold green]🔍 Starting Kura Explorer[/bold green]\n"
        f"[bold blue]API docs at: http://localhost:{port}/docs[/bold blue]\n"
        f"[dim]Loading checkpoint data from: {checkpoint_dir}[/dim]\n"
    )
    
    uvicorn.run(explorer_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    app()
