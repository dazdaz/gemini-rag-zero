# Gemini File Search (RAG) – Python Demo

Google released a **fully managed RAG system** built directly into the Gemini API (Nov 6, 2024).

No vector DB. No embedding costs. No chunking code. Just upload files → ask questions with perfect citations.

## What is this?

A minimal Python demo showing Google's new File Search capability for Gemini. This RAG system is:
- **Fully managed** – no infrastructure to maintain
- **Free storage and embeddings** – you only pay for Gemini tokens
- **Built-in citations** – answers include source references
- **Simple API** – ~50 lines of code to get started

## Features

This demo shows how to:
- ✅ Create a persistent File Search Store
- ✅ Upload multiple PDFs concurrently with metadata
- ✅ Ask questions and get grounded answers with inline citations
- ✅ Search the index directly (without generation)
- ✅ Delete and cleanup resources

**Note on Persistence:**
- File Search Stores and their indexed data persist indefinitely in Gemini's cloud
- This demo **deletes the store at the end** for cleanup
- To keep your data persistent, simply comment out the deletion step in the script
- Raw PDF files uploaded via File API expire after 48 hours, but the indexed/embedded data in the store remains until you delete it

## Setup

1. **Get your API key**: https://aistudio.google.com/app/apikey

2. **Enable the Generative Language API**:
   ```bash
   # Option 1 (Fastest - CLI):
   gcloud services enable generativelanguage.googleapis.com
   
   # Option 2 (Web Console):
   # Visit: https://console.developers.google.com/apis/api/generativelanguage.googleapis.com
   # Click 'Enable API'
   ```

3. **Set up your environment**:
   ```bash
   # Copy the example env file
   cp .env.example .env
   # Edit .env and add your API key: GEMINI_API_KEY=your-actual-key
   ```

4. **Install dependencies** (with uv - recommended):
   ```bash
   # Install uv if you don't have it
   brew install uv  # or: curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create venv and install dependencies (fast!)
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

   <details>
   <summary>Or use traditional pip (slower)</summary>

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   </details>

5. **Run the demo**:
   ```bash
   python3 gemini-rag-zero.py
   ```

**Note**: The script requires sample PDF files in a `samples/` directory. You'll need to add your own documents or update the file paths in the script.

## How It Works: Automatic RAG Indexing

**Everything is automatic!** When you upload a file to a File Search Store:

1. ✅ **Upload** → File is sent to Google Cloud
2. ✅ **Chunking** → Automatically split into chunks (500 tokens by default)
3. ✅ **Embedding** → Each chunk is embedded (FREE - no cost!)
4. ✅ **Indexing** → Vectors stored in managed vector database (FREE - no cost!)
5. ✅ **Ready** → Immediately queryable (no waiting!)

**You don't need to:**
- ❌ Manually chunk documents
- ❌ Generate embeddings yourself
- ❌ Manage a vector database
- ❌ Trigger indexing
- ❌ Rebuild indexes

**When you upload a file, it's instantly indexed and ready to query.** The entire RAG pipeline is fully managed by Google—just upload and start asking questions!

**What you do pay for:**
- 💰 Indexing embeddings: $0.15 per 1M tokens (one-time at upload)
- 💰 Query tokens: Standard Gemini pricing

**What's FREE:**
- 🆓 Storage (up to 1 GB)
- 🆓 Query-time embeddings
- 🆓 Vector database management

## Managing & Querying Your Stores

Use the comprehensive **`manage-filestore.py`** utility for all operations:

### 📊 View & Analyze

```bash
# List all stores
python3 manage-filestore.py list

# List documents in a specific store
python3 manage-filestore.py list fileSearchStores/abc123

# Show global storage statistics
python3 manage-filestore.py stats

# Show stats for a specific store
python3 manage-filestore.py stats fileSearchStores/abc123
```

### 🎯 Query & Search

```bash
# Query with RAG (returns answers with citations)
python3 manage-filestore.py query fileSearchStores/abc123 "What are the main topics?"

# Interactive query mode - ask multiple questions
python3 manage-filestore.py query fileSearchStores/abc123

# Fast vector search (find matching documents)
python3 manage-filestore.py search fileSearchStores/abc123 "revenue forecast"
```

### 📤 Upload & Modify

```bash
# Upload new files to existing store
python3 manage-filestore.py upload fileSearchStores/abc123 doc1.pdf doc2.pdf

# Rename a store
python3 manage-filestore.py rename fileSearchStores/abc123 "Q4 Documents"
```

### 💾 Export & Delete

```bash
# Export all stores to JSON (for backup/documentation)
python3 manage-filestore.py export > backup.json

# Export specific store with documents
python3 manage-filestore.py export fileSearchStores/abc123

# Delete entire store (with confirmation)
python3 manage-filestore.py delete fileSearchStores/abc123

# Remove a specific document (with confirmation)
python3 manage-filestore.py remove fileSearchStores/abc123/documents/xyz789
```

### Complete Feature Set

- 📚 **List** - View all stores and documents
- 📊 **Stats** - Monitor storage usage (Free tier: 1 GB)
- 🎯 **Query** - Ask questions with RAG and citations
- 🔍 **Search** - Fast vector search for matching docs
- 📤 **Upload** - Add files to existing stores
- ✏️ **Rename** - Update store display names
- 💾 **Export** - Backup store information (JSON)
- 🗑️ **Delete/Remove** - Manage stores and documents
- ✅ **Safety** - Confirmations before destructive operations
- ⚡ **Fast** - Uses gemini-2.5-flash for queries

**Example outputs:**

```bash
# List all stores
$ ./manage-filestore.py list
📚 Your File Search Stores:

1. Company Knowledge Base - Demo
   Name: fileSearchStores/company-knowledge-base-demo-kj90trspe5wo
   Created: 2025-11-08 00:22:25.719967+00:00
   Documents: 3
```

```bash
# Check storage statistics
$ ./manage-filestore.py stats fileSearchStores/company-knowledge-base-demo-kj90trspe5wo
📊 Statistics for store: fileSearchStores/company-knowledge-base-demo-kj90trspe5wo

Documents: 3
Total Size: ~4.23 MB
Estimated Storage (with embeddings): ~12.69 MB
```

```bash
# Query your documents
$ ./manage-filestore.py query fileSearchStores/company-knowledge-base-demo-kj90trspe5wo "what is this about?"
🔍 Querying store: fileSearchStores/company-knowledge-base-demo-kj90trspe5wo

Q: what is this about?

A: I found information about three different topics in the documents:

1. **The Gettysburg Address**: This is a famous speech delivered by Abraham Lincoln 
   on November 19, 1863, during the American Civil War. It was given at the dedication 
   of the National Cemetery in Gettysburg, Pennsylvania.

2. **Alice's Adventures in Wonderland**: This is a classic novel by Lewis Carroll, 
   featuring illustrations by John Tenniel. The story begins with Alice feeling bored 
   and then following a White Rabbit down a rabbit-hole.

3. **Hamlet**: This refers to William Shakespeare's tragedy, "Hamlet". The provided 
   text includes scenes from Act I, introducing characters like Francisco, Bernardo, 
   Horatio, and Marcellus.

📌 Sources:
   • The Gettysburg Address
   • Alice's Adventures in Wonderland
   • Hamlet
```

## Supported Models

The following Gemini models support File Search:
- **gemini-2.5-pro** - Most capable, best for complex reasoning
- **gemini-2.5-flash** - Faster and more cost-effective (used in this demo)

## Limits & Pricing

**File Size Limits:**
- Maximum file size: **100 MB per document**
- Recommended file search store size: **Under 20 GB** (for optimal retrieval speed)

**Storage Limits:**
- **Free tier**: Up to **1 GB** free (includes input data + embeddings, typically ~3x your input size)
- **Paid tiers**: 10 GB (Tier 1), 100 GB (Tier 2), 1 TB (Tier 3)

**Pricing:**
- **Storage**: FREE
- **Embeddings at query time**: FREE
- **Indexing embeddings**: $0.15 per 1M tokens (one-time at upload)
- **Gemini tokens**: Standard pricing (input/output tokens only)

## How RAG Works

**RAG** = Retrieval-Augmented Generation

Traditional AI models only know what they learned during training. With RAG, you provide your own documents and the system:

1. Automatically chunks and embeds your files
2. Stores them in a searchable vector index
3. Finds relevant content when you ask questions
4. Grounds answers in your actual data (reduces hallucinations)

**What Google eliminated**: Before this, you needed to manually parse files, manage chunking strategies, generate embeddings, run vector databases (Pinecone, Weaviate, etc.), and write retrieval code. Now it's all handled by the API.

## Learn More

- 📝 [Phil's JavaScript Tutorial](https://www.philschmid.de/gemini-file-search-javascript) – Comprehensive hands-on guide
- 📢 [Google's Official Announcement](https://blog.google/technology/developers/file-search-gemini-api/)
- 📚 [Official Documentation](https://ai.google.dev/gemini-api/docs/file-search)

## Why This Matters

Google's File Search competes directly with OpenAI's Assistants API file search, but with:
- Simpler implementation
- Often lower costs (free storage + embeddings)
- Works with Gemini 2.5 Pro/Flash (huge context windows)
- Production-ready for enterprise use

Perfect for building AI assistants that need to answer questions about your documents, contracts, reports, knowledge bases, etc.
