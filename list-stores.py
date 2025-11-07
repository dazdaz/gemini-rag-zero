#!/usr/bin/env python3
"""
Utility script to list and manage File Search Stores in Gemini
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def list_all_stores():
    """List all File Search Stores"""
    print("📚 Your File Search Stores:\n")
    stores = list(client.file_search_stores.list())
    
    if not stores:
        print("   No stores found. Create one by running gemini-rag-zero.py with persistence enabled.")
        return
    
    for i, store in enumerate(stores, 1):
        print(f"{i}. {store.display_name}")
        print(f"   ID: {store.name}")
        print(f"   Created: {store.create_time}")
        print()

def list_documents_in_store(store_name):
    """List all documents in a specific File Search Store"""
    print(f"\n📄 Documents in store: {store_name}\n")
    
    try:
        # List documents in the store
        documents = list(client.file_search_stores.list_documents(file_search_store_name=store_name))
        
        if not documents:
            print("   No documents found in this store.")
            return
        
        total_size = 0
        for i, doc in enumerate(documents, 1):
            # Get document details
            size_mb = getattr(doc, 'size_bytes', 0) / (1024 * 1024) if hasattr(doc, 'size_bytes') else 0
            total_size += size_mb
            
            print(f"{i}. {doc.display_name}")
            print(f"   ID: {doc.name}")
            if size_mb > 0:
                print(f"   Size: {size_mb:.2f} MB")
            if hasattr(doc, 'create_time'):
                print(f"   Uploaded: {doc.create_time}")
            if hasattr(doc, 'metadata') and doc.metadata:
                print(f"   Metadata: {doc.metadata}")
            print()
        
        print(f"Total: {len(documents)} document(s), ~{total_size:.2f} MB")
        
    except Exception as e:
        print(f"   Error listing documents: {e}")

def main():
    print("🚀 Gemini File Search Store Manager\n")
    
    # List all stores
    list_all_stores()
    
    # Ask user which store to inspect
    stores = list(client.file_search_stores.list())
    if not stores:
        return
    
    if len(stores) == 1:
        print(f"Inspecting the only available store...")
        list_documents_in_store(stores[0].name)
    else:
        print("\nEnter store number to view documents (or press Enter to skip): ", end='')
        choice = input().strip()
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(stores):
                list_documents_in_store(stores[idx].name)
            else:
                print("Invalid store number.")

if __name__ == "__main__":
    main()
