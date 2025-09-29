# 🤖 AI Powered HR Assistant

An intelligent HR assistant that analyzes resume authenticity and matches candidates with job descriptions using advanced document processing and natural language analysis.

## ✨ Features

- **📊 Resume Authenticity Scanner**: Multi-criteria analysis including:
  - Font consistency detection across documents
  - Grammar and language quality assessment
  - Formatting consistency validation
  - Suspicious pattern detection (templates, placeholders)
  - Document structure analysis
  
- **📋 Document Processing**: 
  - Support for PDF, DOC, and DOCX formats
  - Automatic text extraction with fallback methods
  - Font metadata extraction (no OCR needed for fonts)
  - Structure and layout analysis

- **🌐 Web Interface**: 
  - Beautiful, responsive UI built with Bootstrap
  - Single and batch resume upload
  - Real-time analysis with progress indicators
  - Detailed scoring breakdown with visual feedback

- **🔍 JD-Resume Matching** (Coming Soon): 
  - Skill matching algorithms
  - Experience relevance scoring
  - Education qualification matching

## 🚀 Quick Start

### Prerequisites

- **Python 3.10 or higher** (Python 3.10, 3.11, or 3.12 recommended)
- **Git** (for cloning the repository)
- **UV Package Manager** (recommended) or pip

### Installation

#### Option 1: Using UV (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/anandvijay96/kp-ai-hr-recruitement-assistant.git
cd kp-ai-hr-recruitement-assistant
```

2. **Install UV** (if not already installed):
```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. **Install dependencies:**
```bash
uv sync
```

4. **Run the application:**
```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

5. **Open your browser:**
```
http://localhost:8000
```

#### Option 2: Using Traditional Virtual Environment

1. **Clone the repository:**
```bash
git clone https://github.com/anandvijay96/kp-ai-hr-recruitement-assistant.git
cd kp-ai-hr-recruitement-assistant
```

2. **Create virtual environment:**
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Download NLTK data** (required for grammar analysis):
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

5. **Run the application:**
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

6. **Open your browser:**
```
http://localhost:8000
```

## 🧪 Running Tests

### Using UV:
```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_main.py -v

# Run with coverage
uv run python -m pytest tests/ --cov=. --cov-report=html
```

### Using pip:
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_main.py -v
```

## 📁 Project Structure

```
ai-hr-assistant/
├── core/               # Core configuration and settings
├── models/             # Pydantic models and schemas
├── services/           # Business logic services
│   ├── document_processor.py    # Document text extraction
│   └── resume_analyzer.py       # Authenticity analysis
├── templates/          # HTML templates (Jinja2)
├── static/            # Static files (CSS, JS, images)
├── tests/             # Test suite
├── uploads/           # Uploaded resume files (gitignored)
├── temp/              # Temporary files (gitignored)
├── results/           # Analysis results (gitignored)
├── main.py            # FastAPI application entry point
├── requirements.txt   # Python dependencies
└── pyproject.toml     # Project configuration (UV)
```

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, FastAPI
- **Document Processing**: PyMuPDF (fitz), pdfplumber, python-docx
- **NLP**: NLTK (grammar analysis)
- **Web Framework**: FastAPI with Jinja2 templates
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Package Manager**: UV (recommended) or pip
- **Testing**: pytest, pytest-asyncio

## 📊 How It Works

### Resume Authenticity Analysis

The system uses a **multi-criteria weighted scoring algorithm**:

1. **Font Consistency (25%)**: Analyzes font usage patterns across the document
   - Extracts font metadata from PDFs using PyMuPDF
   - Analyzes DOCX font properties using python-docx
   - Scores based on number of unique fonts (fewer = better)

2. **Grammar Quality (25%)**: Evaluates language patterns
   - Sentence structure analysis using NLTK
   - Detects excessive capitalization and punctuation
   - Identifies fragmented or poorly constructed text

3. **Formatting Consistency (20%)**: Checks document structure
   - Page count analysis
   - Layout consistency across pages
   - Font usage patterns

4. **Content Pattern Analysis (15%)**: Detects suspicious patterns
   - Template-like repeated phrases
   - Placeholder text detection
   - Generic job title patterns
   - Inconsistent date formats

5. **Structure Consistency (15%)**: Validates overall structure
   - Text length consistency across pages
   - Document organization patterns

**Overall Score** = Weighted average of all criteria

### Scoring Interpretation

- **90-100%**: Excellent - Professional, authentic resume
- **80-89%**: Good - Minor inconsistencies, likely authentic
- **70-79%**: Fair - Some concerns, review recommended
- **60-69%**: Poor - Multiple red flags detected
- **Below 60%**: Critical - High likelihood of template/fake resume

## 🔧 Configuration

Edit `core/config.py` to customize:

```python
class Settings(BaseSettings):
    app_name: str = "AI Powered HR Assistant"
    host: str = "127.0.0.1"
    port: int = 8000
    upload_dir: str = "uploads"
    results_dir: str = "results"
    temp_dir: str = "temp"
    allowed_extensions: List[str] = [".pdf", ".doc", ".docx"]
    max_file_size: int = 10 * 1024 * 1024  # 10MB
```

## 🐛 Troubleshooting

### Port Already in Use (Windows)

If you get a port binding error:

```bash
# Try a different port
uvicorn main:app --host 127.0.0.1 --port 8080

# Or find and kill the process using the port
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Import Errors

Make sure all dependencies are installed:

```bash
# Using UV
uv sync

# Using pip
pip install -r requirements.txt
```

### NLTK Data Missing

Download required NLTK data:

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Anand Vijay** - [GitHub](https://github.com/anandvijay96)

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- PyMuPDF for PDF processing capabilities
- NLTK for natural language processing tools
- Bootstrap for the responsive UI components

## 📧 Contact

For questions or support, please open an issue on GitHub or contact the maintainers.

---

**Built with ❤️ for better recruitment processes**
