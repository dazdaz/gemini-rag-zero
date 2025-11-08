#!/usr/bin/env python3

import os
import sys
import time
import argparse
import warnings
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Suppress Python version warning
warnings.filterwarnings('ignore', category=FutureWarning, module='google.api_core._python_version_support')

load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found!")
    print("   Please create a .env file with: GEMINI_API_KEY=your-api-key-here")
    print("   Or export GEMINI_API_KEY=your-api-key-here")
    exit(1)

# Initialize the client
client = genai.Client(api_key=api_key)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Gemini RAG Demo - Create and query a File Search Store',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default model and questions
  python3 gemini-rag-zero.py
  
  # Use Pro model for better reasoning
  python3 gemini-rag-zero.py --model gemini-2.5-pro
  python3 gemini-rag-zero.py -m gemini-2.5-pro
  
  # Ask a custom question
  python3 gemini-rag-zero.py --query "What are the main conclusions?"
  python3 gemini-rag-zero.py -q "Explain the key findings"
  
  # Combine model and query options
  python3 gemini-rag-zero.py -m gemini-2.5-pro -q "Summarize in detail"
        """
    )
    parser.add_argument(
        '-m', '--model',
        choices=['gemini-2.5-flash', 'gemini-2.5-pro'],
        default='gemini-2.5-flash',
        help='Gemini model to use for queries (default: gemini-2.5-flash)'
    )
    parser.add_argument(
        '-q', '--query',
        type=str,
        help='Ask a specific question instead of default questions'
    )
    args = parser.parse_args()
    
    model_name = args.model
    model_display = "Flash (fast & cost-effective)" if model_name == "gemini-2.5-flash" else "Pro (most capable)"
    
    print(f"🚀 Creating File Search Store in Gemini using {model_name} ({model_display})...")
    try:
        file_search_store = client.file_search_stores.create(
            config={'display_name': 'Company Knowledge Base - Demo'}
        )
    except Exception as e:
        error_str = str(e)
        if 'PERMISSION_DENIED' in error_str or 'SERVICE_DISABLED' in error_str:
            # Extract project ID from error message
            import re
            project_match = re.search(r'project[s]?[/:](\d+)', error_str)
            project_id = project_match.group(1) if project_match else 'YOUR_PROJECT_ID'
            
            print("\n❌ Error: Generative Language API is not enabled!")
            print("\n📝 To fix this (choose one):")
            print("\n   Option 1 (Fastest - CLI):")
            print(f"   gcloud services enable generativelanguage.googleapis.com --project={project_id}")
            print("\n   Option 2 (Web Console):")
            print("   1. Visit: https://console.developers.google.com/apis/api/generativelanguage.googleapis.com")
            print("   2. Click 'Enable API'")
            print("   3. Wait a few minutes for changes to propagate")
            print("\n   Then run the script again")
            exit(1)
        elif 'API_KEY_INVALID' in error_str:
            print("\n❌ Error: Invalid API key!")
            print("\n📝 To fix this:")
            print("   1. Get a valid API key from: https://aistudio.google.com/apikey")
            print("   2. Update your .env file with: GEMINI_API_KEY=your-actual-key")
            exit(1)
        else:
            # Re-raise unexpected errors
            raise
    
    print(f"   Store created: {file_search_store.name}")

    print("\n📂 Uploading sample documents...")
    print("   Note: This demo expects PDF files in the 'samples/' directory.")
    print("   Add your own PDFs there, or modify the file paths below.")
    
    # FILE SIZE LIMITS:
    # - Maximum: 100 MB per document
    # - Free tier total storage: 1 GB (includes input + embeddings, typically ~3x your input size)
    # - Recommended store size: Under 20 GB for optimal retrieval speed
    # - Indexing cost: $0.15 per 1M tokens (one-time at upload)
    
    # Upload files from the samples directory
    sample_files = [
        "samples/sample1.pdf",
        "samples/sample2.pdf",
        "samples/sample3.pdf",
    ]
    
    uploaded_count = 0
    for file_path in sample_files:
        if os.path.exists(file_path):
            print(f"   Uploading {file_path}...")
            operation = client.file_search_stores.upload_to_file_search_store(
                file=file_path,
                file_search_store_name=file_search_store.name,
                config={
                    'display_name': os.path.basename(file_path),
                    'chunking_config': {
                        'white_space_config': {
                            'max_tokens_per_chunk': 500,
                            'max_overlap_tokens': 50
                        }
                    }
                }
            )
            
            # Wait for upload to complete
            while not operation.done:
                time.sleep(2)
                operation = client.operations.get(operation)
            
            uploaded_count += 1
        else:
            print(f"   ⚠️  File not found: {file_path}")
    
    if uploaded_count == 0:
        print("\n   ❌ No files were uploaded. Please add PDF files to the 'samples/' directory.")
        print("   Cleaning up and exiting...")
        client.file_search_stores.delete(name=file_search_store.name, config={'force': True})
        return
    
    print(f"   ✅ Uploaded {uploaded_count} file(s)")

    print("\n🤖 Asking questions with RAG enabled...")
    
    # Use custom query if provided, otherwise use default questions
    if args.query:
        questions = [args.query]
    else:
        questions = [
            "Summarize the main topics covered in the documents.",
            "What are the key findings or recommendations?",
            "List any important dates or deadlines mentioned."
        ]

    for q in questions:
        print(f"\nQ: {q}")
        response = client.models.generate_content(
            model=model_name,
            contents=q,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[file_search_store.name]
                        )
                    )
                ]
            )
        )
        print(f"A: {response.text}")
        
        # Show citations if available
        if response.candidates[0].grounding_metadata:
            print("   📌 Sources:")
            for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                if hasattr(chunk, 'file_search'):
                    print(f"   • {chunk.file_search.document.display_name}")

    print("\n🧹 Cleaning up...")
    # NOTE: Comment out the line below to keep your File Search Store persistent
    # The store and indexed data will remain in Gemini's cloud until you manually delete it
    client.file_search_stores.delete(name=file_search_store.name, config={'force': True})
    print("   Store deleted. All done! 🎉")

if __name__ == "__main__":
    main()
