from flask import Flask, render_template, request
from classradar_core import process_pdf_and_generate_output
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

TODOIST_TOKEN = "your_token_here"  # Replace with your actual Todoist token

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["syllabus"]
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            tasks = process_pdf_and_generate_output(filepath, TODOIST_TOKEN)
            return render_template("results.html", tasks=tasks)
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
