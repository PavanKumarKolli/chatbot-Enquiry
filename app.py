import os
from flask import Flask, render_template, request, jsonify
from chatbot import StudentChatbot

# Initialize Flask application with explicit template and static folder configurations
# Reloaded to update dataset configurations
app = Flask(__name__, template_folder="templates", static_folder="static")

# Initialize Chatbot
chatbot = StudentChatbot(dataset_path=os.path.join(os.path.dirname(__file__), "dataset.json"))

@app.route("/")
def home():
    """
    Renders the student chatbot interface.
    """
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    API endpoint for handling student queries.
    Expects JSON payload with 'message' field.
    Returns JSON with 'response', 'category', and 'is_exit' flags.
    """
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({
            "response": "Invalid request. Please provide a message.",
            "category": "error",
            "is_exit": False
        }), 400

    user_message = data["message"]
    response, category, is_exit = chatbot.get_response(user_message)
    
    return jsonify({
        "response": response,
        "category": category,
        "is_exit": is_exit
    })

if __name__ == "__main__":
    print("=========================================")
    print(" EduAssist AI Student Chatbot Server     ")
    print(" Running at http://127.0.0.1:5000/      ")
    print("=========================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
