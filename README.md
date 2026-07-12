# Faculty AI Dashboard

A Flask-based web app for academic faculty profile generation, document upload analysis, and AI-powered assistant interactions.

This project provides a clean dashboard experience for:
- uploading academic documents (PDF, DOCX, TXT)
- extracting career highlights and research strengths
- generating a faculty profile summary
- viewing analytics-style research metrics
- chatting with an AI assistant that can answer questions about uploaded documents

## Features

- Dashboard overview with publication, project, citation, and profile generation metrics
- Document upload form for CVs, resumes, research summaries, and academic profiles
- Automatic text extraction from PDF and DOCX files when `PyPDF2` and `python-docx` are installed
- Profile generation flow with extracted text preview, detected strengths, and downloadable summary
- AI assistant page that responds to questions using the last uploaded document content
- Analytics page with sample publication trends, citation insights, H-index, and research focus visuals
- History controls to clear uploads, generated summaries, and timeline events

## Tech Stack

- Python 3
- Flask
- Jinja2 templates
- HTML/CSS/JavaScript
- `python-dotenv` for environment configuration support
- Optional document parsers: `PyPDF2`, `python-docx`

## Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd "final project"
   ```

2. Create and activate a Python environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open a browser and visit:
   ```
   http://127.0.0.1:5000
   ```

## Usage

1. Open the app in your browser.
2. Use the sidebar to navigate between Dashboard, AI Assistant, Profile upload, and Analytics.
3. Go to the Profile page and upload a document (`.pdf`, `.docx`, or `.txt`).
4. Generate a faculty profile to see extracted text, strengths, and a downloadable summary.
5. Ask the AI assistant questions about the uploaded document on the Chat page.
6. View research metrics and insights on the Analytics page.

## Project Structure

- `app.py` — Flask application and backend logic
- `requirements.txt` — Python dependencies
- `templates/` — Jinja2 HTML templates for the UI
  - `base.html`, `index.html`, `chat.html`, `profile.html`, `analysis.html`
- `static/` — client-side assets
  - `style.css` — styling for the app
  - `script.js` — optional custom JavaScript support

## Notes

- The app uses a simple text extraction pipeline and a heuristic document assistant.
- If `PyPDF2` or `python-docx` are missing, the app still accepts text uploads and falls back to plain text extraction.
- `langchain-ibm` and `ibm-watson-machine-learning` are included in `requirements.txt` but not required for the core local app to run.
- Add a `.env` file if you extend the app with IBM or other API credentials in the future.
- Keep `.env` local and never push it to GitHub. Use `.env.example` with placeholder values in the repository instead.

## Customization

- Update the dashboard state in `app.py` to reflect real faculty metrics and data.
- Enhance the AI assistant by integrating a real LLM backend or a knowledge retrieval system.
- Add support for additional file formats or richer profile export types.

## License

This project does not include a license file by default. Add `LICENSE` if you want to publish it with an open source license.
