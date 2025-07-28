#
# FastAPI app for web frontend and chat endpoint
#
from fastapi import FastAPI, Request, Form
from fastapi import UploadFile
from typing import List
from tempfile import NamedTemporaryFile
import diskcache
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
from llama_cpp import Llama

app = FastAPI()

CONFIG_DIR = Path.home() / ".fredfix"
CONFIG_DIR.mkdir(exist_ok=True)

chat_history = diskcache.Cache(str(CONFIG_DIR / "chat_cache"))

frontend_path = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")
templates = Jinja2Templates(directory=str(frontend_path))

model_path = str(Path.home() / "models/CodeLLaMA/codellama-7b-instruct.Q4_K_M.gguf")
llm = Llama(model_path=model_path)

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return FileResponse(frontend_path / "index.html")

@app.post("/chat")
async def chat_handler(message: str = Form(...)):
    history = chat_history.get("thread", [])
    prompt = "\n".join(f"{i+1}. {msg}" for i, msg in enumerate(history[-5])) + f"\n{len(history)+1}. {message}"
    output = llm(prompt=prompt, max_tokens=1024, temperature=0.7, stop=["</s>"])
    response = output["choices"][0]["text"]
    history.append(message)
    history.append(response)
    chat_history["thread"] = history
    return {"response": response}


# Upload route for code analysis
@app.post("/upload")
async def upload_files(files: List[UploadFile]):
    responses = []
    for file in files:
        contents = await file.read()
        lang = file.filename.split('.')[-1]
        prompt = f"Analyze this {lang} file and provide a summary:\n\n{contents.decode()}"
        output = llm(prompt=prompt, max_tokens=1024, temperature=0.7, stop=["</s>"])
        responses.append({"filename": file.filename, "analysis": output["choices"][0]["text"]})
    return {"results": responses}


# Route to clear chat history
@app.post("/reset")
async def reset_chat():
    chat_history["thread"] = []
    return {"status": "Chat history cleared."}
#!/usr/bin/env python3
import click
import os
import json
from pathlib import Path
from datetime import datetime
import subprocess
import shutil

CONFIG_DIR = Path.home() / ".fredfix"
CONFIG_DIR.mkdir(exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"
LOG_DIR = CONFIG_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Load or create default config
def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    else:
        default = {
            "model": "llama",
            "log_enabled": True,
            "name": "Fred",
            "role": "Owner",
            "company": "Parati.chat",
            "theme": "dark",
            "branding": {
                "color": "green"
            },
            "onboarded": True
        }
        with open(CONFIG_PATH, 'w') as f:
            json.dump(default, f)
        return default

config = load_config()

@click.group()
@click.option('--god', is_flag=True, help="Enable God Mode")
@click.option('--log', is_flag=True, help="Enable output logging")
@click.option('--set-openai-key', is_flag=True, help="Set OpenAI API key")
@click.pass_context
def cli(ctx, god, log, set_openai_key):
    ctx.ensure_object(dict)
    ctx.obj['god'] = god
    ctx.obj['log'] = log or config.get("log_enabled", True)
    if set_openai_key:
        import getpass
        key = getpass.getpass("Enter OpenAI API key: ")
        os.environ['OPENAI_API_KEY'] = key
        print("API key set for current session.")
    # Detect and warn if llama model isn't set up
    model_path = Path.home() / "models/CodeLLaMA/codellama-7b-instruct.Q4_K_M.gguf"
    if config.get("model") == "llama" and not model_path.exists():
        print(f"⚠️  LLaMA model not found at {model_path}. Use --model openai or fix model path in ~/.fredfix/config.json")

def log_output(data):
    if config.get("log_enabled", True):
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        with open(LOG_DIR / f"log-{ts}.txt", 'w') as f:
            f.write(data)

# Add LLaMA refactor command
@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.pass_context
def llama(ctx, path):
    """Refactor a Python file or all Python files in a directory using LLaMA."""
    from llama_cpp import Llama
    model_path = str(Path.home() / "models/CodeLLaMA/codellama-7b-instruct.Q4_K_M.gguf")
    llm = Llama(model_path=model_path)
    
    files = []
    # Extended list of file extensions
    exts = [
        ".py", ".cpp", ".c", ".java", ".txt",
        ".yaml", ".yml", ".json", ".md",
        ".html", ".css", ".js", ".ts", ".tsx",
        ".sh", ".bash", ".zsh",
        ".go", ".rs", ".swift", ".kt"
    ]
    # Mapping extensions to language labels
    lang_map = {
        ".py": "Python", ".cpp": "C++", ".c": "C", ".java": "Java", ".txt": "text",
        ".yaml": "YAML", ".yml": "YAML", ".json": "JSON", ".md": "Markdown",
        ".html": "HTML", ".css": "CSS", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
        ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
        ".go": "Go", ".rs": "Rust", ".swift": "Swift", ".kt": "Kotlin"
    }
    def detect_language(file_path):
        return lang_map.get(file_path.suffix.lower(), "code")

    p = Path(path)
    if p.is_dir():
        files = [f for f in p.rglob("*") if f.suffix in exts]
    elif p.is_file():
        files = [p]
    else:
        print("❌ Invalid path")
        return

    for file in files:
        with open(file, 'r') as f:
            content = f.read()
        lang = detect_language(file)
        prompt = f"Refactor this {lang} code:\n\n{content}\n\nImproved version:"
        response = llm(prompt=prompt, max_tokens=1024, temperature=0.7, stop=["</s>"])
        print(f"[Refactored output of {file}]:\n{response['choices'][0]['text']}")

# Add utility commands dynamically
@cli.command()
@click.argument('query')
@click.pass_context
def chat(ctx, query):
    """Talk to the agent."""
    model = config.get("model")
    if model == "llama":
        from llama_cpp import Llama
        model_path = str(Path.home() / "models/CodeLLaMA/codellama-7b-instruct.Q4_K_M.gguf")
        llm = Llama(model_path=model_path)
        response = llm(prompt=query, max_tokens=1024, temperature=0.7, stop=["</s>"])
        print(response["choices"][0]["text"])
    else:
        print(f"[OpenAI responding to]: {query}")
        subprocess.run(["echo", f"TODO: call OpenAI API with: {query}"])

@cli.command()
@click.pass_context
def dedupe(ctx):
    """Find and remove duplicate files from ~/Downloads."""
    from hashlib import md5
    seen = {}
    dupes = []
    base = Path.home() / "Downloads"
    for path in base.rglob("*"):
        if path.is_file():
            h = md5(path.read_bytes()).hexdigest()
            if h in seen:
                dupes.append(path)
            else:
                seen[h] = path
    for f in dupes:
        print(f"🗑 Deleting duplicate: {f}")
        f.unlink()

@cli.command()
@click.pass_context
def clean_tmp(ctx):
    """Delete all temporary files in /tmp."""
    tmp = Path("/tmp")
    for f in tmp.rglob("*"):
        try:
            if f.is_file():
                f.unlink()
        except Exception:
            pass
    print("🧹 /tmp cleaned.")

@cli.command()
@click.pass_context
def sort_files(ctx):
    """Move files from ~/Downloads into folders by type."""
    base = Path.home() / "Downloads"
    types = {
        ".png": "Images", ".jpg": "Images", ".jpeg": "Images",
        ".pdf": "PDFs", ".txt": "Text", ".py": "Code"
    }
    for file in base.glob("*"):
        if file.suffix.lower() in types:
            dest = base / types[file.suffix.lower()]
            dest.mkdir(exist_ok=True)
            shutil.move(str(file), str(dest / file.name))
    print("📁 Files sorted by type.")


if __name__ == "__main__":
    cli()
