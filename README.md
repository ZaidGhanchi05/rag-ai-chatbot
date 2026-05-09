# 🧠 RAG AI Chatbot

A production-ready **Retrieval-Augmented Generation (RAG)** chatbot that lets you upload PDF documents and ask questions about their content. Uses hybrid semantic search + Groq LLM to generate real, streamed answers.

**Tech Stack:**
- 🐍 **Backend**: FastAPI · sentence-transformers · FAISS · scikit-learn · PyPDF · Groq SDK
- ⚛️ **Frontend**: React · Vite · Tailwind CSS
- 🔍 **Retrieval**: Hybrid FAISS semantic search + sklearn TF-IDF re-ranking
- 🤖 **LLM**: Groq `llama-3.1-8b-instant` (free tier, token streaming)

---

## 📁 Project Structure

```
RAG_LLM/
├── backend/
│   ├── api.py           # FastAPI app + endpoints (incl. /query/stream SSE)
│   ├── embedding.py     # sentence-transformers (all-MiniLM-L6-v2)
│   ├── vector_store.py  # FAISS index with persistence
│   ├── retrieval.py     # Hybrid retrieval (FAISS + sklearn TF-IDF)
│   └── llm.py           # Groq LLM integration (sync + streaming)
├── frontend/
│   └── src/
│       ├── components/  # React UI components
│       ├── hooks/       # useChat (real SSE streaming), useDocuments
│       └── services/    # API layer (streamQuery + sendQuery)
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
| `POST` | `/query`  | Query documents → RAG response (sync) |
| `POST` | `/query/stream` | Same but streams tokens via SSE |
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
Confidence assessment
    ↓
Groq LLM (llama-3.1-8b-instant) synthesizes answer from chunks
    ↓
Streamed token-by-token to frontend via SSE
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
| `GROQ_API_KEY` | *(empty)* | Get free at [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Groq model to use |

---

## ✨ Features

- 📤 **Multi-PDF upload** with drag-and-drop
- 🔍 **Hybrid retrieval**: semantic (FAISS) + keyword (TF-IDF)
- 🤖 **Groq LLM**: synthesizes coherent answers from retrieved chunks
- 🌊 **Real token streaming**: answers appear word-by-word via SSE (like ChatGPT)
- 📊 **Confidence score** shown as color-coded progress bar
- 📄 **Source attribution** — which PDF each answer came from
- 🧠 **Sources panel** — view exact matched chunks per answer
- 💾 **Persistent index** — no re-embedding on server restart
- 📱 **Responsive** — works on mobile and desktop
- 🔄 **Graceful fallback** — works without Groq key (shows raw chunks)

---

## 📦 Tech Highlights (AI/ML Resume)

| Library | Usage |
|---|---|
| `sentence-transformers` | Dense vector embeddings (all-MiniLM-L6-v2) |
| `faiss-cpu` | Approximate nearest-neighbour vector search |
| `scikit-learn` | TF-IDF vectorisation + cosine similarity re-ranking |
| `groq` | LLM answer generation with token streaming |
| `pypdf` | PDF text extraction |
| `fastapi` | Async REST API with SSE streaming |
| `numpy` | Embedding array operations |

---

## ☁️ Deployment

### Backend → Render.com (free)
1. Push repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service → connect your repo
3. Render auto-detects `render.yaml` and configures everything
4. In Render dashboard → **Environment** tab → add `GROQ_API_KEY` manually

### Frontend → Vercel (free)
1. Go to [vercel.com](https://vercel.com) → New Project → import your GitHub repo
2. Set root directory to `frontend`
3. Add environment variable: `VITE_API_URL` = your Render backend URL
4. Deploy!

### Full stack → Docker
```bash
docker-compose up --build
```
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
