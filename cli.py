import click
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

@click.group()
def cli():
    """FredFix CLI for terminal use."""
    pass

@cli.command()
@click.argument("message", nargs=-1)
def chat(message):
    """Chat with FredFix, with streaming response."""
    full_message = " ".join(message)
    if not full_message:
        print("Please provide a message to send.")
        return

    try:
        response = requests.post(
            f"{BASE_URL}/chat-stream",
            json={
                "messages": [{"role": "user", "content": full_message}],
                "source": "cli"
            },
            stream=True
        )
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                print(chunk.decode('utf-8'), end='', flush=True)
        print() # for a newline at the end

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


@cli.command()
@click.argument("folder")
def analyze(folder):
    """Analyze a folder with FredFix."""
    try:
        response = requests.post(f"{BASE_URL}/analyze-folder", data={"folder_path": folder})
        response.raise_for_status()
        print(response.json().get("summary", "No summary returned."))
    except requests.exceptions.RequestException as e:
        print(f"Error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

@cli.command()
def ping():
    """Check if FredFix backend is running."""
    try:
        response = requests.get(f"{BASE_URL}/ping")
        response.raise_for_status()
        print("FredFix backend is up:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Ping failed: {e}")

if __name__ == "__main__":
    cli()
