import requests

def query_model(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "[No response text found]")
        else:
            return f"[Error {response.status_code}] {response.text}"
    except Exception as e:
        return f"[LLaMA Error] {str(e)}"