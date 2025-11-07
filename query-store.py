#!/usr/bin/env python3
"""
Query any File Search Store with questions

Usage:
    python3 query-store.py                                      # Interactive mode - select store
    python3 query-store.py <store-name> "Your question here"    # Query specific store
    python3 query-store.py list                                 # List available stores
"""

import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def list_stores():
    """List all available File Search Stores"""
    print("📚 Available File Search Stores:\n")
    stores = list(client.file_search_stores.list())
    
    if not stores:
        print("   No stores found.")
        print("   Create one by running: python3 gemini-rag-zero.py")
        print("   (Comment out the deletion line to keep it persistent)")
        return []
    
    for i, store in enumerate(stores, 1):
        print(f"{i}. {store.display_name}")
        print(f"   ID: {store.name}")
        print(f"   Created: {store.create_time}")
        
        # Show document count
        try:
            docs = list(client.file_search_stores.list_documents(file_search_store_name=store.name))
            print(f"   Documents: {len(docs)}")
        except:
            pass
        print()
    
    return stores

def query_store(store_name, question, model="gemini-2.5-flash"):
    """Query a File Search Store with a question"""
    print(f"🔍 Querying store: {store_name}\n")
    print(f"Q: {question}\n")
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=question,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[store_name]
                        )
                    )
                ]
            )
        )
        
        print(f"A: {response.text}\n")
        
        # Show citations if available
        if response.candidates[0].grounding_metadata:
            print("📌 Sources:")
            for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                if hasattr(chunk, 'file_search'):
                    doc = chunk.file_search.document
                    print(f"   • {doc.display_name}")
                    if hasattr(chunk.file_search, 'page_range'):
                        pages = chunk.file_search.page_range
                        print(f"     Pages: {pages.start_page_index}-{pages.end_page_index}")
        else:
            print("(No sources cited)")
            
    except Exception as e:
        print(f"❌ Error querying store: {e}")

def interactive_mode():
    """Interactive mode - select store and ask questions"""
    print("🤖 Gemini File Search Query Tool\n")
    
    stores = list_stores()
    if not stores:
        return
    
    print("Enter store number to query: ", end='')
    choice = input().strip()
    
    if not choice.isdigit():
        print("Invalid selection")
        return
    
    idx = int(choice) - 1
    if not (0 <= idx < len(stores)):
        print("Invalid store number")
        return
    
    store = stores[idx]
    print(f"\n✅ Selected: {store.display_name}\n")
    
    # Ask questions in a loop
    while True:
        print("Enter your question (or 'quit' to exit): ", end='')
        question = input().strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if question:
            print()
            query_store(store.name, question)
            print()

def show_usage():
    """Show usage information"""
    print("""
🤖 Gemini File Search Query Tool

Usage:
    python3 query-store.py                                    # Interactive mode
    python3 query-store.py list                               # List all stores
    python3 query-store.py <store-id> "question"             # Query specific store

Examples:
    # Interactive mode
    python3 query-store.py
    
    # List available stores
    python3 query-store.py list
    
    # Query a specific store
    python3 query-store.py fileSearchStores/abc123 "What are the key findings?"
    
    # Query with gemini-2.5-pro (more capable, slower)
    # Set MODEL=gemini-2.5-pro environment variable or modify the script

Note: 
- Store IDs can be found using: python3 manage-store.py list
- You can query ANY persistent store, not just the demo one
- Stores persist indefinitely until you delete them
""")

def main():
    if len(sys.argv) == 1:
        # No arguments - interactive mode
        interactive_mode()
        return
    
    command = sys.argv[1].lower()
    
    if command in ['list', 'ls']:
        list_stores()
    elif command in ['help', '-h', '--help']:
        show_usage()
    elif len(sys.argv) == 3:
        # Query mode: <store-name> "question"
        store_name = sys.argv[1]
        question = sys.argv[2]
        query_store(store_name, question)
    else:
        print("❌ Invalid arguments")
        show_usage()

if __name__ == "__main__":
    main()
