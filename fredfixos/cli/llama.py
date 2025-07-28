import click
from fredfixos.core.refactor import refactor_file

@click.command()
@click.argument("file")
def cli(file):
    """Use the local LLaMA model to refactor the code in the given file."""
    result = refactor_file(file_path=file, model="llama")
    click.echo(result)
