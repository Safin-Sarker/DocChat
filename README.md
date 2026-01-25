<p align="center">
  <img src="https://img.icons8.com/fluency/96/chat.png" alt="DocChat Logo" width="80"/>
</p>

<h1 align="center">DocChat Advanced RAG</h1>

<p align="center">
  <strong>Multimodal Document Intelligence Platform with Knowledge Graph Visualization</strong>
</p>

<p align="center">
  <a href="#features"><img src="https://img.shields.io/badge/Features-10+-blue" alt="Features"></a>
  <a href="#tech-stack"><img src="https://img.shields.io/badge/Python-3.11+-green" alt="Python"></a>
  <a href="#tech-stack"><img src="https://img.shields.io/badge/React-19.x-61DAFB" alt="React"></a>
  <a href="#tech-stack"><img src="https://img.shields.io/badge/FastAPI-0.110+-009688" alt="FastAPI"></a>
  <a href="#license"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License"></a>
</p>

<p align="center">
  An advanced Retrieval-Augmented Generation (RAG) system that combines multimodal document processing, hybrid search retrieval, and interactive knowledge graph visualization for intelligent document question-answering.
</p>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
  - [4. Database Setup](#4-database-setup)
  - [5. Environment Configuration](#5-environment-configuration)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Configuration Options](#configuration-options)
- [Contributing](#contributing)
- [License](#license)
- [Contact Information](#contact-information)

---

## Overview

**DocChat Advanced RAG** is a sophisticated document intelligence platform that enables users to upload documents (PDFs, images, text files) and interact with them through natural language queries. The system leverages state-of-the-art AI technologies to provide accurate, context-aware responses while visualizing document relationships through an interactive knowledge graph.

### Why DocChat?

Traditional document search systems rely on keyword matching, often missing the semantic meaning behind queries. DocChat solves this by:

- **Understanding Context**: Uses embeddings to capture semantic meaning
- **Hybrid Retrieval**: Combines BM25, semantic search, and graph traversal
- **Visual Insights**: Displays entity relationships in an interactive knowledge graph
- **Multimodal Support**: Processes text, tables, and images from documents

---

## Features

| Feature                            | Description                                                                     |
| ---------------------------------- | ------------------------------------------------------------------------------- |
| **Multimodal Document Processing** | Extract and process text, tables, and images from PDFs and documents            |
| **Hybrid RAG Pipeline**            | Combines semantic search, BM25, and graph-based retrieval for superior accuracy |
| **Knowledge Graph Visualization**  | Interactive vis-network graph showing entity relationships                      |
| **Real-time Chat Interface**       | Stream-like chat experience with source citations                               |
| **Entity Extraction**              | Automatic extraction of people, organizations, concepts from documents          |
| **Hierarchical Chunking**          | Parent-child chunking strategy for better context preservation                  |
| **OpenAI Reranking**               | GPT-powered reranking for optimal result ordering                               |
| **Persistent Sessions**            | Chat history and document context preserved across sessions                     |
| **Docker Support**                 | One-command infrastructure setup with Docker Compose                            |
| **RESTful API**                    | Well-documented API with Swagger UI                                             |

---

## Tech Stack

### Backend

| Technology                | Purpose                                      |
| ------------------------- | -------------------------------------------- |
| **Python 3.11+**          | Core programming language                    |
| **FastAPI**               | High-performance async web framework         |
| **LangChain**             | LLM orchestration and chain management       |
| **LlamaIndex**            | Document indexing and retrieval              |
| **OpenAI GPT-4**          | Language model for generation and embeddings |
| **Pinecone**              | Vector database for semantic search          |
| **Neo4j**                 | Graph database for entity relationships      |
| **Sentence Transformers** | Local embedding generation                   |
| **Pydantic**              | Data validation and settings management      |
| **Uvicorn**               | ASGI server                                  |

### Frontend

| Technology         | Purpose                          |
| ------------------ | -------------------------------- |
| **React 19**       | UI component library             |
| **TypeScript**     | Type-safe JavaScript             |
| **Vite**           | Next-generation frontend tooling |
| **TailwindCSS**    | Utility-first CSS framework      |
| **shadcn/ui**      | Accessible component library     |
| **vis-network**    | Interactive graph visualization  |
| **TanStack Query** | Async state management           |
| **Zustand**        | Lightweight state management     |
| **Axios**          | HTTP client                      |

### Infrastructure

| Technology         | Purpose                       |
| ------------------ | ----------------------------- |
| **Docker**         | Containerization              |
| **Docker Compose** | Multi-container orchestration |
| **Neo4j 5.16**     | Graph database container      |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────┐  │
│  │   Document  │  │    Chat     │  │      Knowledge Graph            │  │
│  │   Upload    │  │  Interface  │  │      Visualization              │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────────┬─────────────────┘  │
│         │                │                         │                     │
│         └────────────────┼─────────────────────────┘                     │
│                          │                                               │
│                    React + TypeScript + Vite                             │
└──────────────────────────┼───────────────────────────────────────────────┘
                           │ HTTP/REST
┌──────────────────────────┼───────────────────────────────────────────────┐
│                          ▼                                               │
│                    ┌───────────┐                                         │
│                    │  FastAPI  │                                         │
│                    │  Server   │                                         │
│                    └─────┬─────┘                                         │
│                          │                                               │
│         ┌────────────────┼────────────────┐                              │
│         ▼                ▼                ▼                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                       │
│  │  Document   │  │   Hybrid    │  │  Response   │                       │
│  │  Processor  │  │  Retrieval  │  │  Generator  │                       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                       │
│         │                │                │                              │
│         │         ┌──────┴──────┐         │                              │
│         │         ▼             ▼         │                              │
│         │    ┌────────┐   ┌────────┐      │                              │
│         │    │Semantic│   │ Graph  │      │                              │
│         │    │ Search │   │Traverse│      │                              │
│         │    └───┬────┘   └───┬────┘      │                              │
│         │        │            │           │                              │
│                       BACKEND (Python)                                   │
└─────────┼────────┼────────────┼───────────┼──────────────────────────────┘
          │        │            │           │
          ▼        ▼            ▼           ▼
     ┌─────────────────┐   ┌─────────┐  ┌─────────┐
     │    Pinecone     │   │  Neo4j  │  │ OpenAI  │
     │ (Vector Store)  │   │ (Graph) │  │  (LLM)  │
     └─────────────────┘   └─────────┘  └─────────┘
```

---

## Prerequisites

Before you begin, ensure you have the following installed:

| Requirement        | Version | Installation                                                |
| ------------------ | ------- | ----------------------------------------------------------- |
| **Python**         | 3.11+   | [Download](https://www.python.org/downloads/)               |
| **Node.js**        | 18+     | [Download](https://nodejs.org/)                             |
| **Docker Desktop** | Latest  | [Download](https://www.docker.com/products/docker-desktop/) |
| **Git**            | Latest  | [Download](https://git-scm.com/)                            |

### Required API Keys

| Service      | Purpose          | Get Key                                                 |
| ------------ | ---------------- | ------------------------------------------------------- |
| **OpenAI**   | LLM & Embeddings | [OpenAI Platform](https://platform.openai.com/api-keys) |
| **Pinecone** | Vector Database  | [Pinecone Console](https://www.pinecone.io/)            |

---

## Installation

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/DocChat.git

# Navigate to project directory
cd DocChat
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install
```

### 4. Database Setup

Start the Neo4j database using Docker:

```bash
# From project root directory
docker-compose up -d

# Verify Neo4j is running
docker ps
```

Neo4j will be available at:

- **Browser UI**: http://localhost:7474
- **Bolt Connection**: bolt://localhost:7687
- **Credentials**: neo4j / password123

### 5. Environment Configuration

Create a `.env` file in the **project root** directory:

```bash
# Copy the example file (if available)
cp backend/.env.example .env
```

Edit the `.env` file with your credentials:

```env
# ===========================================
# OpenAI Configuration (Required)
# ===========================================
OPENAI_API_KEY=sk-your-openai-api-key-here

# ===========================================
# Pinecone Configuration (Required)
# ===========================================
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=docgraph-multimodal

# ===========================================
# Neo4j Configuration
# ===========================================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# ===========================================
# AWS S3 Configuration (Optional)
# ===========================================
# Leave as default for local storage
AWS_ACCESS_KEY_ID=not_required
AWS_SECRET_ACCESS_KEY=not_required
AWS_BUCKET_NAME=local_storage
AWS_REGION=us-east-1
USE_LOCAL_STORAGE=True
```

---

## Running the Application

### Option 1: Run All Services Manually

Open **three terminal windows**:

**Terminal 1 - Start Neo4j:**

```bash
docker-compose up
```

**Terminal 2 - Start Backend:**

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 3 - Start Frontend:**

```bash
cd frontend
npm run dev
```

### Option 2: Quick Start Script (Windows)

Create a `start.bat` file in the project root:

```batch
@echo off
echo Starting DocChat Advanced RAG...
echo.
echo Starting Neo4j database...
start cmd /k "docker-compose up"
echo Waiting for Neo4j to initialize...
timeout /t 15 /nobreak
echo.
echo Starting Backend API server...
start cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 5 /nobreak
echo.
echo Starting Frontend development server...
start cmd /k "cd frontend && npm run dev"
echo.
echo All services started!
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8001
echo Neo4j:    http://localhost:7474
```

### Access the Application

| Service                         | URL                            |
| ------------------------------- | ------------------------------ |
| **Frontend Application**        | http://localhost:5173          |
| **Backend API**                 | http://localhost:8001          |
| **API Documentation (Swagger)** | http://localhost:8001/api/docs |
| **Neo4j Browser**               | http://localhost:7474          |

---

## Project Structure

```
DocChat/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── documents.py    # Document upload endpoints
│   │   │       │   ├── query.py        # RAG query endpoints
│   │   │       │   └── graph.py        # Graph query endpoints
│   │   │       └── api.py              # API router
│   │   ├── core/
│   │   │   └── config.py               # Application settings
│   │   ├── models/
│   │   │   └── graph_store.py          # Neo4j operations
│   │   ├── schemas/
│   │   │   ├── documents.py            # Document schemas
│   │   │   ├── query.py                # Query schemas
│   │   │   └── graph.py                # Graph schemas
│   │   ├── services/
│   │   │   ├── advanced_rag.py         # Main RAG pipeline
│   │   │   ├── document_processor.py   # Document processing
│   │   │   ├── entity_extractor.py     # Entity extraction
│   │   │   ├── hybrid_retrieval.py     # Hybrid search
│   │   │   ├── reranker.py             # Result reranking
│   │   │   └── response_generator.py   # LLM response generation
│   │   └── main.py                     # FastAPI application entry
│   ├── requirements.txt                # Python dependencies
│   └── .env.example                    # Environment template
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts               # API client
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx       # Chat UI component
│   │   │   ├── DocumentUpload.tsx      # Upload component
│   │   │   ├── GraphVisualization.tsx  # Knowledge graph
│   │   │   ├── Message.tsx             # Chat message component
│   │   │   └── ui/                     # shadcn/ui components
│   │   ├── hooks/
│   │   │   ├── useGraph.ts             # Graph data hook
│   │   │   └── useQuery.ts             # RAG query hook
│   │   ├── stores/
│   │   │   └── chatStore.ts            # Zustand state store
│   │   ├── types/
│   │   │   └── api.ts                  # TypeScript types
│   │   ├── App.tsx                     # Main application
│   │   └── main.tsx                    # Entry point
│   ├── package.json                    # Node dependencies
│   ├── vite.config.ts                  # Vite configuration
│   ├── tailwind.config.js              # Tailwind configuration
│   └── tsconfig.json                   # TypeScript configuration
│
├── docker-compose.yml                  # Docker services (Neo4j)
├── .env                                # Environment variables
├── .gitignore                          # Git ignore rules
└── README.md                           # This file
```

---

## Configuration Options

### Backend Configuration

| Variable            | Default                  | Description                   |
| ------------------- | ------------------------ | ----------------------------- |
| `DEBUG`             | `False`                  | Enable debug mode             |
| `EMBEDDING_MODEL`   | `text-embedding-ada-002` | OpenAI embedding model        |
| `LLM_MODEL`         | `gpt-4`                  | OpenAI chat model             |
| `VISION_MODEL`      | `gpt-4-vision-preview`   | Model for image analysis      |
| `TEMPERATURE`       | `0.7`                    | LLM response temperature      |
| `PARENT_CHUNK_SIZE` | `1500`                   | Parent chunk token size       |
| `CHILD_CHUNK_SIZE`  | `300`                    | Child chunk token size        |
| `SEMANTIC_TOP_K`    | `10`                     | Semantic search results count |
| `RERANK_TOP_K`      | `5`                      | Final reranked results count  |
| `MAX_UPLOAD_SIZE`   | `52428800`               | Max upload file size (50MB)   |

### Frontend Configuration

Create `frontend/.env` (optional):

```env
VITE_API_URL=http://localhost:8001
VITE_API_TIMEOUT=30000
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit** your changes
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push** to the branch
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open** a Pull Request

### Development Guidelines

- Follow **PEP 8** for Python code
- Use **TypeScript strict mode** for frontend
- Write **meaningful commit messages**
- Add **tests** for new features
- Update **documentation** as needed

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Contact Information

|               |                                                                                     |
| ------------- | ----------------------------------------------------------------------------------- |
| **Name**      | MD Safin Sarker                                                                     |
| **Email**     | [safinsarker1122@gmail.com](mailto:safinsarker1122@gmail.com)                       |
| **LinkedIn**  | [linkedin.com/in/safin-sarker](https://www.linkedin.com/in/safin-sarker/)           |
| **Portfolio** | [safin-portfolio-website.netlify.app](https://safin-portfolio-website.netlify.app/) |

---

<p align="center">
  <strong>Built with passion for intelligent document interaction</strong>
</p>

<p align="center">
  <a href="#table-of-contents">Back to Top</a>
</p>
