# claude-rag-agent

Production Document Q&A chatbot — upload a PDF or DOCX, ask questions in plain English, get answers with cited sources (`[Page X, Chunk Y]`).

Built with Claude API (prompt caching), FastAPI, and ChromaDB.

---

## Features

- **PDF & DOCX upload** — drag and drop, up to 50 MB
- **Semantic chunking** — 1000-char chunks with 200-char overlap, smart sentence-boundary splitting
- **Vector search** — ChromaDB + `all-MiniLM-L6-v2` embeddings, top-5 relevant chunks retrieved per query
- **Cited answers** — every claim sourced with `[Page X, Chunk Y]` inline citations
- **Prompt caching** — system prompt cached via Claude API (`cache_control: ephemeral`), cache hit/miss shown in UI
- **Multi-document** — upload and query multiple documents independently

---

## Tech Stack

| Layer | Tech |
|-------|------|
| LLM | Claude (`claude-sonnet-4-6`) with prompt caching |
| Vector DB | ChromaDB (persistent) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Backend | FastAPI + Python |
| Frontend | Vanilla HTML + Tailwind CSS |

---

## Quick Start

```bash
git clone https://github.com/DevanshKalra-ai/claude-rag-agent.git
cd claude-rag-agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...   # Windows: $env:ANTHROPIC_API_KEY="sk-..."
uvicorn main:app --reload --port 8000
```

Open `http://localhost:8000`

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload PDF or DOCX, returns `doc_id` |
| POST | `/query` | Ask a question, returns answer + citations + token usage |
| GET | `/documents` | List uploaded documents |
| DELETE | `/documents/{doc_id}` | Remove a document |
| GET | `/health` | Health check |

### Query example

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "abc-123", "question": "What are the main findings?"}'
```

```json
{
  "answer": "The study found three main outcomes [Page 4, Chunk 12]...",
  "chunks_used": [{"page": 4, "chunk_index": 12, "relevance_score": 0.91}],
  "usage": {"input_tokens": 1820, "cache_read_tokens": 312, "output_tokens": 245}
}
```

---

## Project Structure

```
claude-rag-agent/
├── main.py               # FastAPI app — upload, query, document management
├── document_processor.py # PDF (PyMuPDF) + DOCX chunking pipeline
├── rag.py                # ChromaDB store/retrieve
├── claude_client.py      # Claude API with prompt caching
├── requirements.txt
└── static/
    └── index.html        # Drag-and-drop UI
```
