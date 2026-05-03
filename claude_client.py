import anthropic
from typing import List, Dict

SYSTEM_PROMPT = """You are a precise document Q&A assistant. Your job is to answer questions \
using ONLY the context chunks provided. Rules:

1. Cite every claim with [Page X, Chunk Y] immediately after the relevant sentence.
2. If the answer spans multiple chunks, cite each one.
3. If the answer is not present in the provided context, respond with:
   "I could not find an answer to this question in the uploaded document."
4. Never fabricate information or draw on outside knowledge.
5. Keep answers concise and well-structured. Use bullet points when listing multiple items."""

_client = anthropic.Anthropic()


def answer_question(question: str, chunks: List[Dict]) -> Dict:
    if not chunks:
        return {
            "answer": "No relevant chunks were found in the document for your question.",
            "chunks_used": [],
            "usage": {},
        }

    context_blocks = []
    for c in chunks:
        header = f"[Page {c['page']}, Chunk {c['chunk_index']}] (Source: {c['doc_name']}, Relevance: {c['relevance_score']})"
        context_blocks.append(f"{header}\n{c['text']}")
    context = "\n\n---\n\n".join(context_blocks)

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Context from the document:\n\n{context}\n\nQuestion: {question}",
            }
        ],
    )

    usage = response.usage
    return {
        "answer": response.content[0].text,
        "chunks_used": [
            {"page": c["page"], "chunk_index": c["chunk_index"], "relevance_score": c["relevance_score"]}
            for c in chunks
        ],
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0),
            "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0),
        },
    }
