#!/usr/bin/env python3

import click
from fredfixos.cli import llama

@click.command(name="openai")
@click.option("--file", "file_path", required=True, help="Path to the file to refactor.")
@click.option("--api-key", "api_key", required=False, help="API key for OpenAI.")
def openai(file_path, api_key):
    """Use OpenAI model to refactor the code in the given file."""
    if not api_key:
        click.echo("No API key provided. Falling back to LLaMA model.")
        llama_command(file_path)
    else:
        result = f"[OpenAI Placeholder] Refactored output of {file_path} using API key {api_key}"
        click.echo(result)

@click.command(name="llama")
@click.option("--file", "file_path", required=True, help="Path to the file to refactor.")
def llama_command(file_path):
    """Use the local LLaMA model to refactor the code in the given file."""
    result = llama.refactor_file(file_path)
    click.echo(result)

@click.group()
def cli():
    pass

cli.add_command(openai)
cli.add_command(llama_command)

if __name__ == "__main__":
    cli()