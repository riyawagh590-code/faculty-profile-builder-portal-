from flask import Flask, render_template, request, jsonify, make_response
import io
import os
import re
from dotenv import load_dotenv

load_dotenv()

try:
    import docx
except ImportError:
    docx = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

app = Flask(__name__)

dashboard_state = {
    'stats': {
        'publications': 34,
        'projects': 12,
        'citations': 560,
        'profiles_generated': 18,
    },
    'recent_uploads': [
        {'name': 'Dr_Sharma_CV.pdf', 'date': 'Today'},
        {'name': 'Prof_Arora_Resume.docx', 'date': 'Yesterday'},
        {'name': 'Dr_Khan_Profile.txt', 'date': '2 days ago'},
    ],
    'generated_profiles': [
        {'name': 'Faculty Summary - Sharma', 'status': 'Ready'},
        {'name': 'Faculty Summary - Arora', 'status': 'Review'},
    ],
    'timeline': [
        {'title': 'Generated profile for Sharma', 'detail': 'AI summary completed successfully.', 'time': 'Today • 11:20 AM'},
        {'title': 'Uploaded Prof_Arora_Resume.docx', 'detail': 'Processing started automatically.', 'time': 'Yesterday • 4:15 PM'},
        {'title': 'New chat session initiated', 'detail': 'Assistant engaged for research support.', 'time': '2 days ago'},
    ],
    'last_doc_text': '',
    'last_doc_name': '',
    'analytics': {
        'total_publications': 142,
        'active_patents': 8,
        'h_index': 27,
        'collaboration_score': 74,
        'publication_trend': 12,
        'citation_trend': 18,
        'recent_trend_points': [68, 70, 72, 74, 78, 82, 85],
        'publications_sparkline': [40, 48, 52, 56, 64, 72, 84],
        'citations_sparkline': [42, 50, 58, 67, 75, 84, 100],
        'top_paper_title': 'Advances in Hybrid AI Systems for Education',
        'top_paper_journal': 'International Journal of AI & Learning',
        'top_paper_year': 2024,
        'top_paper_citations': 268,
        'monthly_progress': [
            {'period': 'Mar', 'value': 82, 'label': 'Publication momentum'},
            {'period': 'Apr', 'value': 85, 'label': 'Citation growth'},
            {'period': 'May', 'value': 88, 'label': 'Collaboration surge'},
            {'period': 'Jun', 'value': 91, 'label': 'Conference activity'},
            {'period': 'Jul', 'value': 94, 'label': 'Mentorship outreach'},
        ],
        'recommended_actions': [
            'Publish a conference paper in your top research area this quarter.',
            'Increase interdisciplinary collaborations through joint grant proposals.',
            'Mentor two new PhD candidates and highlight student outcomes.',
            'Join a workshop or panel to strengthen academic outreach visibility.',
        ],
        'benchmark': [
            {'label': 'Publications', 'you': 142, 'peer': 118},
            {'label': 'Citations', 'you': 560, 'peer': 492},
            {'label': 'H-index', 'you': 27, 'peer': 23},
            {'label': 'Collaboration', 'you': 74, 'peer': 65},
        ],
        'research_focus': [
            {
                'label': 'AI & Machine Learning',
                'value': 40,
                'color': '#3b82f6',
                'description': 'Leading AI and ML research with strong publication impact and cross-domain innovation.',
            },
            {
                'label': 'Interdisciplinary Studies',
                'value': 28,
                'color': '#2563eb',
                'description': 'Bridges multiple academic disciplines through collaborative research and partnerships.',
            },
            {
                'label': 'Education & Mentorship',
                'value': 20,
                'color': '#10b981',
                'description': 'Prioritizes teaching excellence, student mentorship, and curriculum development.',
            },
            {
                'label': 'Service & Outreach',
                'value': 12,
                'color': '#f59e0b',
                'description': 'Supports community engagement, academic service, and outreach initiatives.',
            },
        ],
    },
}


def build_research_pie_style(focus_list):
    if not focus_list:
        return ''

    stops = []
    current = 0
    for item in focus_list:
        start = current
        end = current + item['value']
        stops.append(f"{item['color']} {start}% {end}%")
        current = end

    return f"background: conic-gradient({', '.join(stops)});"


def extract_document_highlights(text):
    if not text:
        return [
            'No text available from this document yet. Please upload a supported file type for extraction.',
        ]

    content = text.lower()
    highlights = []

    if any(keyword in content for keyword in ['publication', 'published', 'journal', 'conference']):
        highlights.append('Strong research record with publications and academic dissemination.')
    if any(keyword in content for keyword in ['research', 'lab', 'study', 'project']):
        highlights.append('Research-focused achievements and project leadership are clearly highlighted.')
    if any(keyword in content for keyword in ['teach', 'mentorship', 'student', 'curriculum', 'lecture']):
        highlights.append('Demonstrated teaching excellence and student mentorship responsibilities.')
    if any(keyword in content for keyword in ['award', 'grant', 'fellowship', 'honor', 'recognit']):
        highlights.append('Recognized through awards, grants, or professional honors.')
    if any(keyword in content for keyword in ['conference', 'workshop', 'seminar', 'committee', 'panel']):
        highlights.append('Active academic engagement through conferences, workshops, or service roles.')
    if any(keyword in content for keyword in ['collaborat', 'partnership', 'interdisciplin']):
        highlights.append('Interdisciplinary collaborations and partnership accomplishments are noted.')

    if not highlights:
        highlights.append('Core strengths are present but require a fuller document extract to identify key achievements.')

    return highlights[:5]


def sanitize_text(text: str) -> str:
    """Remove control/binary characters and normalize whitespace."""
    if not text:
        return ''
    # Replace C0 control characters (except common whitespace) with space
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", ' ', text)
    # Normalize whitespace runs
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def is_probably_text(text: str, threshold: float = 0.7) -> bool:
    """Simple heuristic: fraction of printable ASCII characters.

    Returns True when the proportion of common printable characters
    is above `threshold`.
    """
    if not text:
        return False
    printable = 0
    total = len(text)
    for ch in text:
        o = ord(ch)
        # allow common whitespace
        if 32 <= o <= 126 or ch in '\n\r\t':
            printable += 1
    return (printable / total) >= threshold


def tokenize_text(text):
    return re.findall(r"\w+", text.lower())


def rank_chunks(query, text, max_chunks=4):
    query_terms = set(tokenize_text(query))
    if not query_terms:
        return []

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 30]
    scored = []
    for sentence in sentences:
        sentence_terms = set(tokenize_text(sentence))
        overlap = len(query_terms.intersection(sentence_terms))
        scored.append((overlap, len(sentence_terms), sentence))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [sentence for score, _, sentence in scored if score > 0][:max_chunks] or sentences[:max_chunks]


def build_rag_chat_response(question, document_text):
    question_lower = question.lower()
    relevant_chunks = rank_chunks(question, document_text, max_chunks=4)
    if not relevant_chunks:
        relevant_chunks = [document_text[:400].strip() + '...'] if document_text else []

    highlights = extract_document_highlights(document_text)
    summary = ''

    if 'summary' in question_lower or 'overview' in question_lower or 'profile' in question_lower:
        summary = (
            'Based on the uploaded document, the faculty profile shows a strong mix of research, teaching, and academic service. '
            'Key strengths include leadership in academic publications, mentorship activities, and interdisciplinary collaborations.'
        )
        return (
            f"{summary}\n\nHighlights from the document:\n" +
            '\n'.join(f'- {item}' for item in highlights)
        )

    if 'research' in question_lower or 'publication' in question_lower or 'papers' in question_lower or 'journal' in question_lower:
        return (
            'Here are the most relevant document excerpts related to your research query:\n\n' +
            '\n\n'.join(relevant_chunks)
        )

    if 'teach' in question_lower or 'mentor' in question_lower or 'student' in question_lower:
        return (
            'The uploaded document highlights teaching and mentorship contributions. ' 
            'Relevant passages from the document are below:\n\n' +
            '\n\n'.join(relevant_chunks)
        )

    return (
        'I found these relevant passages in the uploaded document based on your question:\n\n' +
        '\n\n'.join(relevant_chunks) +
        '\n\nSummary highlights:\n' +
        '\n'.join(f'- {item}' for item in highlights)
    )

# --- Existing Routes ---
@app.route('/')
def home():
    return render_template(
        'index.html',
        stats=dashboard_state['stats'],
        recent_uploads=dashboard_state['recent_uploads'],
        generated_profiles=dashboard_state['generated_profiles'],
        timeline=dashboard_state['timeline'],
    )

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

# --- NEW ROUTES ---
@app.route('/analytics')
def analytics():
    analytics = dashboard_state['analytics'].copy()
    analytics['research_pie_style'] = build_research_pie_style(analytics['research_focus'])
    return render_template('analysis.html', analytics=analytics)

@app.route('/documents')
def documents():
    return render_template('documents.html')


@app.route('/upload', methods=['POST'])
@app.route('/generate-profile', methods=['POST'])
def generate_profile():
    faculty_doc = request.files.get('faculty_doc')
    if not faculty_doc or faculty_doc.filename == '':
        return render_template(
            'index.html',
            error='Please choose a faculty document before generating a profile.',
            stats=dashboard_state['stats'],
            recent_uploads=dashboard_state['recent_uploads'],
            generated_profiles=dashboard_state['generated_profiles'],
            timeline=dashboard_state['timeline'],
        )

    filename = faculty_doc.filename
    file_content = ''
    text_sample = ''
    file_ext = os.path.splitext(filename)[1].lower()
    parser_note = ''

    try:
        if file_ext in ['.docx'] and docx is not None:
            document = docx.Document(io.BytesIO(faculty_doc.read()))
            file_content = '\n'.join(p.text for p in document.paragraphs if p.text)
        elif file_ext in ['.pdf'] and PdfReader is not None:
            reader = PdfReader(io.BytesIO(faculty_doc.read()))
            paragraphs = []
            for page in reader.pages:
                text = page.extract_text() or ''
                paragraphs.append(text)
            file_content = '\n'.join(paragraphs).strip()
        else:
            raw_bytes = faculty_doc.read(200000)
            file_content = raw_bytes.decode('utf-8', errors='ignore').strip()

        # Short sample for preview
        text_sample = file_content[:750].strip()
        if len(file_content) > 750:
            text_sample += '...'
    except Exception:
        file_content = ''
        text_sample = ''

    # sanitize extracted content and detect binary/gibberish results
    file_content = sanitize_text(file_content)
    if file_content and not is_probably_text(file_content):
        # mark as unreadable and don't store binary blobs for chat
        parser_note = (
            'The uploaded document appears to contain binary or non-text data. '
            'For best results upload a PDF/DOCX/TXT and ensure PyPDF2/python-docx are installed.'
        )
        file_content = ''
        text_sample = ''

    if not text_sample:
        if file_ext == '.pdf' and PdfReader is None:
            parser_note = 'PDF parsing is not available because the PyPDF2 package is not installed.'
        elif file_ext == '.docx' and docx is None:
            parser_note = 'DOCX parsing is not available because the python-docx package is not installed.'
        else:
            parser_note = 'The uploaded document could not be extracted for preview.'

    detected_strengths = extract_document_highlights(file_content)
    preview_text = text_sample or parser_note
    # only store cleaned, textual document content for RAG
    dashboard_state['last_doc_text'] = file_content if file_content and is_probably_text(file_content) else ''
    dashboard_state['last_doc_name'] = filename

    profile_data = (
        f"Faculty AI Profile for {filename}\n\n"
        "Summary:\n"
        "This faculty member demonstrates strong academic leadership, research excellence, and teaching innovation.\n\n"
        "Key strengths:\n"
        "- Research focus on interdisciplinary collaborations and student mentorship.\n"
        "- Consistent publication record and strong academic contributions.\n"
        "- Experienced in curriculum development, workshops, and advising.\n\n"
        "Recommended next steps:\n"
        "- Highlight your most recent publications and teaching achievements.\n"
        "- Add measurable outcomes for curriculum and student success.\n"
    )

    # update dashboard state
    dashboard_state['stats']['profiles_generated'] += 1
    dashboard_state['recent_uploads'].insert(0, {'name': filename, 'date': 'Just now'})
    if len(dashboard_state['recent_uploads']) > 5:
        dashboard_state['recent_uploads'].pop()

    generated_name = f'Faculty Summary - {os.path.splitext(filename)[0]}'
    dashboard_state['generated_profiles'].insert(0, {'name': generated_name, 'status': 'Ready'})
    if len(dashboard_state['generated_profiles']) > 5:
        dashboard_state['generated_profiles'].pop()

    dashboard_state['timeline'].insert(0, {
        'title': f'Generated profile for {os.path.splitext(filename)[0]}',
        'detail': 'AI summary completed successfully.',
        'time': 'Just now',
    })
    if len(dashboard_state['timeline']) > 6:
        dashboard_state['timeline'].pop()

    return render_template(
        'index.html',
        profile_data=profile_data,
        file_name=filename,
        extracted_snippet=preview_text,
        detected_strengths=detected_strengths,
        stats=dashboard_state['stats'],
        recent_uploads=dashboard_state['recent_uploads'],
        generated_profiles=dashboard_state['generated_profiles'],
        timeline=dashboard_state['timeline'],
    )


@app.route('/clear-history', methods=['POST'])
def clear_history():
    dashboard_state['recent_uploads'] = []
    dashboard_state['generated_profiles'] = []
    dashboard_state['timeline'] = []
    dashboard_state['stats']['profiles_generated'] = 0
    return render_template(
        'index.html',
        stats=dashboard_state['stats'],
        recent_uploads=dashboard_state['recent_uploads'],
        generated_profiles=dashboard_state['generated_profiles'],
        timeline=dashboard_state['timeline'],
        message='Dashboard history cleared successfully.',
    )


@app.route('/download-profile', methods=['POST'])
def download_profile():
    profile_text = request.form.get('profile_text', '').strip()
    filename = request.form.get('file_name', 'faculty-profile').strip()
    if not profile_text:
        return render_template('index.html', error='No profile available to download.')

    safe_name = filename.rsplit('.', 1)[0]
    response = make_response(profile_text)
    response.headers['Content-Disposition'] = f'attachment; filename={safe_name}_profile.txt'
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response


# --- API Route (Keep your existing API logic here) ---
@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        payload = request.get_json(silent=True) or {}
        user_message = (payload.get('message') or '').strip()

        if not user_message:
            reply = "Hello! I can help summarize uploaded documents, answer questions, or guide you through the portal."
        else:
            document_text = dashboard_state.get('last_doc_text', '')
            if document_text:
                reply = build_rag_chat_response(user_message, document_text)
            else:
                message_lower = user_message.lower()
                if 'analytics' in message_lower:
                    reply = "I can help you review analytics, interpret trends, and summarize performance insights."
                elif 'document' in message_lower or 'file' in message_lower:
                    reply = "Upload a document first and I can summarize it, extract research highlights, or explain your profile."
                elif 'profile' in message_lower:
                    reply = "Upload an academic document and I can generate a faculty profile summary from it."
                else:
                    reply = f"Thanks for asking: {user_message}. I can help you explore the platform, review content, or answer questions about your faculty work."

        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"response": f"An infrastructure error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
 