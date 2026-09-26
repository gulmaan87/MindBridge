# MindBridge API (`apps/api`)

Backend application service for the AI-Powered Cognitive Engagement & Memory Assistance Platform.

Built with **Python**, **FastAPI**, **Pydantic v2**, and **SQLAlchemy 2.x**.

## Running Locally

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies in editable mode with dev tools
pip install -e ".[dev]"

# Run tests
pytest

# Start development server
uvicorn app.main:app --reload --port 8000
```
