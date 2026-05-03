import uuid
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from claude_client import answer_question
from document_processor import extract_chunks
from rag import delete_document, list_chunks_count, store_chunks, query_chunks

app = FastAPI(title="claude-rag-agent")

# In-memory document registry — maps doc_id → metadata
_documents: Dict[str, Dict] = {}


# ── Static frontend ──────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return FileResponse("static/index.html")


# ── Models ────────────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    doc_id: str
    question: str
    n_results: int = 5


class QueryResponse(BaseModel):
    answer: str
    chunks_used: List[Dict]
    usage: Dict


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "document"
    lower = filename.lower()
    if not (lower.endswith(".pdf") or lower.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB guard
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit.")

    try:
        chunks = extract_chunks(content, filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse document: {e}")

    if not chunks:
        raise HTTPException(status_code=422, detail="No text content found in document.")

    doc_id = str(uuid.uuid4())
    store_chunks(doc_id, filename, chunks)

    _documents[doc_id] = {
        "doc_id": doc_id,
        "filename": filename,
        "chunk_count": len(chunks),
        "page_count": chunks[-1]["page"] if chunks else 0,
    }

    return {
        "doc_id": doc_id,
        "filename": filename,
        "chunk_count": len(chunks),
        "page_count": _documents[doc_id]["page_count"],
        "message": "Document uploaded and indexed successfully.",
    }


@app.post("/query", response_model=QueryResponse)
def query_document(req: QueryRequest):
    if req.doc_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found. Please upload it first.")
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    chunks = query_chunks(req.doc_id, req.question, n_results=req.n_results)
    result = answer_question(req.question, chunks)
    return result


@app.get("/documents")
def list_documents():
    return {"documents": list(_documents.values())}


@app.delete("/documents/{doc_id}")
def remove_document(doc_id: str):
    if doc_id not in _documents:
        raise HTTPException(status_code=404, detail="Document not found.")
    delete_document(doc_id)
    del _documents[doc_id]
    return {"message": "Document deleted."}


@app.get("/health")
def health():
    return {"status": "ok"}
