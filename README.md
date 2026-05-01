# 🧠 RAG AI Chatbot

A production-ready **Retrieval-Augmented Generation (RAG)** chatbot that lets you upload PDF documents and ask questions about their content using semantic search.

**Tech Stack:**
- 🐍 **Backend**: FastAPI · sentence-transformers · FAISS · scikit-learn · PyPDF
- ⚛️ **Frontend**: React · Vite · Tailwind CSS
- 🔍 **Retrieval**: Hybrid FAISS semantic search + sklearn TF-IDF re-ranking

---

## 📁 Project Structure

```
RAG_LLM/
├── backend/
│   ├── api.py           # FastAPI app + endpoints
│   ├── embedding.py     # sentence-transformers (all-MiniLM-L6-v2)
│   ├── vector_store.py  # FAISS index with persistence
│   └── retrieval.py     # Hybrid retrieval (FAISS + sklearn TF-IDF)
├── frontend/
│   └── src/
│       ├── components/  # React UI components
│       ├── hooks/       # useChat, useDocuments
│       └── services/    # API layer
├── data/
│   ├── uploads/         # Uploaded PDFs (auto-created)
│   └── index/           # FAISS index files (auto-created)
├── .env                 # Config (chunk size, top_k, etc.)
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Clone / open the project

```bash
cd D:\coding\Projects_All\RAG_LLM
```

### 2. Create Python virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Note**: `faiss-cpu` requires `pip` — if you have a GPU, replace with `faiss-gpu`.  
> The sentence-transformers model (~90 MB) is downloaded automatically on first run.

---

## 🚀 Running the Backend

```bash
cd backend
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: **http://localhost:8000**

API docs (Swagger UI): **http://localhost:8000/docs**

---

## 🚀 Running the Frontend

```bash
cd frontend
npm install      # first time only
npm run dev
```

Frontend will be available at: **http://localhost:5173**

---

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Health check + index stats |
| `POST` | `/upload` | Upload PDF files (multipart) |
| `POST` | `/query`  | Query documents → RAG response |
| `GET`  | `/documents` | List all indexed documents |
| `DELETE` | `/documents/{doc_id}` | Remove a document |

### Query Response Format

```json
{
  "answer": "...",
  "sources": ["document.pdf"],
  "confidence": 0.87,
  "matched_chunks": [
    {
      "text": "...",
      "source": "document.pdf",
      "page": 3,
      "confidence": 0.87,
      "doc_id": "uuid"
    }
  ],
  "low_confidence": false,
  "retrieval_method": "Hybrid (FAISS semantic + sklearn TF-IDF)"
}
```

---

## 🧠 How It Works

```
PDF Upload
    ↓
PyPDF text extraction (page by page)
    ↓
Overlapping chunk splitting (500 chars, 50 overlap)
    ↓
sentence-transformers embedding (all-MiniLM-L6-v2, 384-d)
    ↓
FAISS IndexFlatL2 storage + pickle metadata
    ↓ (on query)
FAISS semantic search (top-K×2 candidates)
    ↓
sklearn TF-IDF re-ranking (TfidfVectorizer + cosine_similarity)
    ↓
Hybrid score fusion: 0.7×semantic + 0.3×keyword
    ↓
Confidence assessment → structured JSON response
```

---

## 🛠️ Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K` | `5` | Retrieved chunks per query |
| `CONFIDENCE_THRESHOLD` | `0.25` | Below this = low-confidence warning |
| `UPLOAD_DIR` | `./data/uploads` | PDF storage path |
| `INDEX_DIR` | `./data/index` | FAISS index storage path |

---

## ✨ Features

- 📤 **Multi-PDF upload** with drag-and-drop
- 🔍 **Hybrid retrieval**: semantic (FAISS) + keyword (TF-IDF)
- 📊 **Confidence score** shown as color-coded progress bar
- 📄 **Source attribution** — which PDF each answer came from
- 🧠 **Sources panel** — view exact matched chunks per answer
- ⏳ **Typing animation** — word-by-word reveal like ChatGPT
- 💾 **Persistent index** — no re-embedding on server restart
- 📱 **Responsive** — works on mobile and desktop

---

## 📦 Tech Highlights (AI/ML Resume)

| Library | Usage |
|---|---|
| `sentence-transformers` | Dense vector embeddings (all-MiniLM-L6-v2) |
| `faiss-cpu` | Approximate nearest-neighbour vector search |
| `scikit-learn` | TF-IDF vectorisation + cosine similarity re-ranking |
| `pypdf` | PDF text extraction |
| `fastapi` | Async REST API |
| `numpy` | Embedding array operations |
