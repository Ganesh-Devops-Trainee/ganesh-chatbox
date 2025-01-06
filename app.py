import os
import google.generativeai as genai
from flask import Flask, render_template, request, session, jsonify
from flask_session import Session
import markdown
from datetime import datetime

# Flask app configuration
app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "secret_key_for_sessions"  # Change this in production
Session(app)


# Configure the Gemini model
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")



@app.route("/")
def index():
    if "history" not in session:
        session["history"] = []
    return render_template("index.html", history=session["history"])


@app.route("/predict", methods=["POST"])
def predict():
    history = session.get("history", [])
    uploaded_file = request.files.get("file")
    prompt = request.form.get("prompt", "").strip()  # Ensure prompt is not None and trim whitespace

    try:
        if prompt:
            # Only a prompt is provided
            response_text = model.generate_content(prompt).text
        else:
            return jsonify({"error": "No valid prompt provided."}), 400

        # Format response
        output_html = markdown.markdown(response_text)
        now = datetime.now()
        formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        history.append({
            "prompt": prompt,
            "response_raw": response_text,
            "response_html": output_html,
            "created_at": formatted_datetime
        })
        session["history"] = history

        return jsonify({"prompt": prompt, "response_html": output_html})

    except Exception as e:
        return jsonify({"error": f"Error: {e}"}), 500



@app.route("/view-history/<int:index>", methods=["GET"])
def view_history(index):
    history = session.get("history", [])
    if 0 <= index < len(history):
        return jsonify(history[index])
    return jsonify({"error": "Invalid index."}), 400


@app.route("/edit-history/<int:index>", methods=["POST"])
def edit_history(index):
    history = session.get("history", [])
    if 0 <= index < len(history):
        data = request.json
        new_prompt = data.get("prompt")

        if new_prompt:
            try:
                response_text = model.generate_content(new_prompt).text
                output_html = markdown.markdown(response_text)
                now = datetime.now()
                formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S")

                history[index] = {
                    "prompt": new_prompt,
                    "response_raw": response_text,
                    "response_html": output_html,
                    "created_at": formatted_datetime
                }
                session["history"] = history
                return jsonify({"success": True, "prompt": new_prompt, "response_html": output_html})
            except Exception as e:
                return jsonify({"error": f"Error while regenerating response: {e}"})
    return jsonify({"error": "Invalid index or missing prompt."}), 400


@app.route("/delete-history/<int:index>", methods=["POST"])
def delete_history(index):
    history = session.get("history", [])
    if 0 <= index < len(history):
        history.pop(index)
        session["history"] = history
        return jsonify({"success": True})
    return jsonify({"error": "Invalid index."}), 400


if __name__ == "__main__":
    app.run()
