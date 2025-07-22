"""This module provides the RP To-Do CLI."""
# rptodo/cli.py

from typing import Optional

import typer
import os


from ddgen import __app_name__, __version__, dbc2sldd, slddgen

app = typer.Typer()

def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    return

@app.command()
def delete(
    username: str,
    force: bool = typer.Option(
        ...,
        prompt="Are you sure you want to delete the user?",
        help="Force deletion without confirmation.",
    ),
):
    """
    Delete a user with USERNAME.

    If --force is not used, will ask for confirmation.
    """
    if force:
        print(f"Deleting user: {username}")
    else:
        print("Operation cancelled")
        
@app.command()
def dbc(
    dbcpath: str,
    # force: bool = typer.Option(
    #     ...,
    #     prompt=f"Are you sure you want to generate sldd?",
    #     help="Generate sldd from dbc file without confirmation.",
    # ),
):
    """
    Generate a Simulink Data Dictionary from a DBC file.

    If --force is not used, will ask for confirmation.
    """
    dbcname = os.path.basename(dbcpath)
    # if force:
    print(f"Generating sldd for: {dbcname}")
    dbc2sldd.dbc2sldd_gen(dbcpath)
    # else:
    #     print("Operation cancelled")