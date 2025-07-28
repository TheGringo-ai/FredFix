from flask import Flask, render_template, request, jsonify, send_from_directory
import os

# Import your FredFix logic
from fredfixos.tools.llama_agent import run_llama_agent
from fredfixos.core.refactor import refactor_code

app = Flask(__name__, static_folder="static", template_folder="templates")

# ---------------------------
# FRONTEND ROUTES
# ---------------------------
@app.route("/")
def home():
    """Serve the main index page."""
    return render_template("index.html")

@app.route("/static/<path:path>")
def send_static(path):
    """Serve static files."""
    return send_from_directory("static", path)

# ---------------------------
# API ROUTES
# ---------------------------
@app.route("/chat", methods=["POST"])
def chat():
    """Chat endpoint connected to llama agent."""
    data = request.get_json()
    user_message = data.get("message", "")

    if not user_message.strip():
        return jsonify({"response": "No message provided."})

    try:
        # Call your llama agent
        bot_response = run_llama_agent(user_message)
    except Exception as e:
        bot_response = f"Error running agent: {str(e)}"

    return jsonify({"response": bot_response})

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    upload_path = os.path.join("uploads", file.filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(upload_path)
    
    return jsonify({"message": f"File {file.filename} uploaded successfully."})

@app.route("/reset", methods=["POST"])
def reset():
    """Reset application state."""
    # If your llama agent has session/state, clear it here
    return jsonify({"message": "Session reset successfully."})

# ---------------------------
# RUN APP
# ---------------------------
if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True)