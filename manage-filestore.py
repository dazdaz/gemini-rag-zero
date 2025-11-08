#!/usr/bin/env python3
"""
Gemini File Search Store Management Utility

Usage:
    python3 manage-store.py create "store name"               # Create a new store
    python3 manage-store.py list                              # List all stores
    python3 manage-store.py list <store-name>                 # List documents in a store
    python3 manage-store.py info <store-name>                 # Show detailed store info
    python3 manage-store.py stats                             # Show storage statistics
    python3 manage-store.py stats <store-name>                # Show stats for specific store
    python3 manage-store.py query <store-name> "question"     # Query a store
    python3 manage-store.py search <store-name> "query"       # Vector search (no generation)
    python3 manage-store.py upload <store-name> <file>...     # Upload files to store
    python3 manage-store.py import <store-name> <file-id>...  # Import files from File API
    python3 manage-store.py operation <operation-id>          # Check operation status
    python3 manage-store.py rename <store-name> "new name"    # Rename a store
    python3 manage-store.py export [store-name]               # Export store info
    python3 manage-store.py delete <store-name>               # Delete entire store
    python3 manage-store.py remove <doc-id>                   # Remove a document
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def create_store(display_name):
    """Create a new File Search Store"""
    print(f"📦 Creating new File Search Store...\n")
    
    try:
        store = client.file_search_stores.create(
            config={'display_name': display_name}
        )
        
        print(f"✅ Store created successfully!\n")
        print(f"Display Name: {store.display_name}")
        print(f"Store Name: {store.name}")
        print(f"Created: {store.create_time}")
        print(f"\nYou can now upload files to this store:")
        print(f"  python3 manage-filestore.py upload {store.name} file1.pdf file2.pdf")
        
    except Exception as e:
        print(f"❌ Error creating store: {e}")

def list_stores():
    """List all File Search Stores"""
    print("📚 Your File Search Stores:\n")
    stores = list(client.file_search_stores.list())
    
    if not stores:
        print("   No stores found.")
        print("   Create one by running: python3 gemini-rag-zero.py")
        print("   (Make sure to comment out the deletion line to keep it persistent)")
        return []
    
    for i, store in enumerate(stores, 1):
        print(f"{i}. {store.display_name}")
        print(f"   Name: {store.name}")
        print(f"   Created: {store.create_time}")
        
        # Show document count
        try:
            docs = list(client.file_search_stores.documents.list(parent=store.name))
            print(f"   Documents: {len(docs)}")
        except:
            pass
        print()
    
    return stores

def list_documents(store_name):
    """List all documents in a specific File Search Store"""
    print(f"\n📄 Documents in store:\n")
    
    try:
        # Try the correct API method - documents() instead of list_documents()
        documents = list(client.file_search_stores.documents.list(parent=store_name))
        
        if not documents:
            print("   No documents found in this store.")
            return []
        
        total_size = 0
        for i, doc in enumerate(documents, 1):
            size_mb = getattr(doc, 'size_bytes', 0) / (1024 * 1024) if hasattr(doc, 'size_bytes') else 0
            total_size += size_mb
            
            print(f"{i}. {doc.display_name}")
            print(f"   ID: {doc.name}")
            if size_mb > 0:
                print(f"   Size: {size_mb:.2f} MB")
            if hasattr(doc, 'create_time'):
                print(f"   Created: {doc.create_time}")
            if hasattr(doc, 'metadata') and doc.metadata:
                print(f"   Metadata: {doc.metadata}")
            print()
        
        print(f"Total: {len(documents)} document(s), ~{total_size:.2f} MB")
        return documents
        
    except AttributeError:
        print("   ℹ️  Document listing not available in current API version.")
        print("   Note: Documents are indexed and queryable, but listing is not yet supported.")
        return []
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def show_stats(store_name=None):
    """Show storage statistics"""
    if store_name:
        # Stats for specific store
        print(f"📊 Statistics for store: {store_name}\n")
        try:
            docs = list(client.file_search_stores.documents.list(parent=store_name))
            total_size = sum(getattr(doc, 'size_bytes', 0) for doc in docs) / (1024 * 1024)
            
            print(f"Documents: {len(docs)}")
            print(f"Total Size: ~{total_size:.2f} MB")
            print(f"Estimated Storage (with embeddings): ~{total_size * 3:.2f} MB")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        # Global stats
        print("📊 Global Storage Statistics\n")
        stores = list(client.file_search_stores.list())
        
        if not stores:
            print("No stores found.")
            return
        
        total_docs = 0
        total_size_mb = 0
        
        for store in stores:
            try:
                docs = list(client.file_search_stores.documents.list(parent=store.name))
                store_size = sum(getattr(doc, 'size_bytes', 0) for doc in docs) / (1024 * 1024)
                total_docs += len(docs)
                total_size_mb += store_size
            except:
                pass
        
        estimated_storage_mb = total_size_mb * 3  # Approximation with embeddings
        
        print(f"Total Stores: {len(stores)}")
        print(f"Total Documents: {total_docs}")
        print(f"Total Input Size: ~{total_size_mb:.2f} MB")
        print(f"Estimated Storage Used: ~{estimated_storage_mb:.2f} MB (~{estimated_storage_mb/1024:.2f} GB)")
        print(f"\nFree Tier Limit: 1 GB")
        if estimated_storage_mb < 1024:
            remaining = 1024 - estimated_storage_mb
            print(f"Remaining: ~{remaining:.2f} MB ({remaining/1024*100:.1f}% free)")
        else:
            print(f"⚠️  Exceeds free tier by ~{(estimated_storage_mb-1024):.2f} MB")

def upload_files(store_name, file_paths):
    """Upload files to an existing File Search Store"""
    print(f"📤 Uploading files to store: {store_name}\n")
    
    uploaded = 0
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"   ⚠️  File not found: {file_path}")
            continue
        
        try:
            print(f"   Uploading {file_path}...")
            operation = client.file_search_stores.upload_to_file_search_store(
                file=file_path,
                parent=store_name,
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
            
            print(f"   ✅ Uploaded successfully")
            uploaded += 1
            
        except Exception as e:
            print(f"   ❌ Error uploading {file_path}: {e}")
    
    print(f"\n✅ Uploaded {uploaded}/{len(file_paths)} files")

def vector_search(store_name, query, top_k=5):
    """Perform vector search without generation"""
    print(f"🔍 Searching store: {store_name}\n")
    print(f"Query: {query}\n")
    
    try:
        # Note: Direct search API might not be available in all versions
        # This is a placeholder for when the API supports it
        print("ℹ️  Direct vector search API coming soon.")
        print("   Using query with generation for now...\n")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
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
        
        if response.candidates[0].grounding_metadata:
            print("📄 Matching Documents:\n")
            for i, chunk in enumerate(response.candidates[0].grounding_metadata.grounding_chunks, 1):
                if hasattr(chunk, 'file_search'):
                    doc = chunk.file_search.document
                    print(f"{i}. {doc.display_name}")
                    if hasattr(chunk.file_search, 'page_range'):
                        pages = chunk.file_search.page_range
                        print(f"   Pages: {pages.start_page_index}-{pages.end_page_index}")
                    print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def rename_store(store_name, new_display_name):
    """Rename a File Search Store"""
    try:
        print(f"✏️  Renaming store: {store_name}")
        print(f"   New name: {new_display_name}\n")
        
        # Update the store
        updated_store = client.file_search_stores.update(
            name=store_name,
            config={'display_name': new_display_name}
        )
        
        print(f"✅ Store renamed successfully")
        print(f"   {updated_store.display_name}")
        
    except Exception as e:
        print(f"❌ Error renaming store: {e}")

def export_stores(store_name=None, format='json'):
    """Export store information"""
    if store_name:
        # Export specific store
        try:
            docs = list(client.file_search_stores.documents.list(parent=store_name))
            
            export_data = {
                'store_name': store_name,
                'documents': [
                    {
                        'display_name': doc.display_name,
                        'name': doc.name,
                        'size_bytes': getattr(doc, 'size_bytes', None),
                        'create_time': str(getattr(doc, 'create_time', None)),
                        'metadata': dict(doc.metadata) if hasattr(doc, 'metadata') and doc.metadata else {}
                    }
                    for doc in docs
                ]
            }
            
            print(json.dumps(export_data, indent=2))
            
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        # Export all stores
        stores = list(client.file_search_stores.list())
        export_data = []
        
        for store in stores:
            try:
                docs = list(client.file_search_stores.documents.list(parent=store.name))
                export_data.append({
                    'display_name': store.display_name,
                    'name': store.name,
                    'create_time': str(store.create_time),
                    'document_count': len(docs)
                })
            except:
                pass
        
        print(json.dumps(export_data, indent=2))

def delete_store(store_name):
    """Delete an entire File Search Store"""
    try:
        print(f"⚠️  Deleting store: {store_name}")
        print("   This will remove the store and all its documents.")
        confirm = input("   Type 'yes' to confirm: ")
        
        if confirm.lower() == 'yes':
            client.file_search_stores.delete(name=store_name, config={'force': True})
            print("   ✅ Store deleted successfully!")
        else:
            print("   ❌ Deletion cancelled.")
    except Exception as e:
        print(f"   ❌ Error deleting store: {e}")

def remove_document(doc_id):
    """Remove a specific document from a store"""
    try:
        print(f"⚠️  Removing document: {doc_id}")
        confirm = input("   Type 'yes' to confirm: ")
        
        if confirm.lower() == 'yes':
            client.file_search_stores.delete_document(name=doc_id)
            print("   ✅ Document removed successfully!")
        else:
            print("   ❌ Removal cancelled.")
    except Exception as e:
        print(f"   ❌ Error removing document: {e}")

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

def interactive_query(store_name):
    """Interactive query mode - ask multiple questions"""
    print(f"\n✅ Querying store: {store_name}\n")
    print("Enter questions (or 'quit' to exit)\n")
    
    while True:
        print("Question: ", end='')
        question = input().strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
        
        if question:
            print()
            query_store(store_name, question)
            print()

def get_store_info(store_name):
    """Get detailed information about a specific File Search Store"""
    print(f"ℹ️  File Search Store Information\n")
    
    try:
        store = client.file_search_stores.get(name=store_name)
        
        print(f"Name: {store.name}")
        print(f"Display Name: {store.display_name}")
        print(f"Created: {store.create_time}")
        print(f"Updated: {store.update_time}")
        print(f"\n📊 Document Statistics:")
        
        # Handle None values for counts
        active_count = int(store.active_documents_count) if store.active_documents_count is not None else 0
        pending_count = int(store.pending_documents_count) if store.pending_documents_count is not None else 0
        failed_count = int(store.failed_documents_count) if store.failed_documents_count is not None else 0
        
        print(f"   Active Documents: {active_count}")
        print(f"   Pending Documents: {pending_count}")
        print(f"   Failed Documents: {failed_count}")
        
        # Handle None for size_bytes
        size_mb = int(store.size_bytes) / (1024 * 1024) if store.size_bytes is not None and store.size_bytes else 0
        print(f"\n💾 Storage:")
        print(f"   Raw Size: {size_mb:.2f} MB")
        print(f"   Estimated with Embeddings: ~{size_mb * 3:.2f} MB")
        
        if failed_count > 0:
            print(f"\n⚠️  Warning: {failed_count} document(s) failed processing")
        
    except Exception as e:
        print(f"❌ Error getting store info: {e}")

def import_files(store_name, file_ids, custom_metadata=None):
    """Import files from File API to a File Search Store"""
    print(f"📥 Importing files to store: {store_name}\n")
    
    imported = 0
    for file_id in file_ids:
        try:
            print(f"   Importing {file_id}...")
            
            config = {}
            if custom_metadata:
                config['custom_metadata'] = custom_metadata
            
            operation = client.file_search_stores.import_file(
                file_search_store_name=store_name,
                file_name=file_id,
                config=config
            )
            
            # Wait for import to complete
            while not operation.done:
                time.sleep(2)
                operation = client.operations.get(operation)
            
            if hasattr(operation, 'error') and operation.error:
                print(f"   ❌ Failed: {operation.error}")
            else:
                print(f"   ✅ Imported successfully")
                imported += 1
            
        except Exception as e:
            print(f"   ❌ Error importing {file_id}: {e}")
    
    print(f"\n✅ Imported {imported}/{len(file_ids)} files")

def check_operation(operation_id):
    """Check the status of a long-running operation"""
    print(f"🔄 Operation Status\n")
    
    try:
        operation = client.operations.get(name=operation_id)
        
        print(f"Operation: {operation.name}")
        print(f"Done: {operation.done}")
        
        if operation.metadata:
            print(f"\nMetadata:")
            for key, value in operation.metadata.items():
                print(f"   {key}: {value}")
        
        if operation.done:
            if hasattr(operation, 'error') and operation.error:
                print(f"\n❌ Error: {operation.error}")
            elif hasattr(operation, 'response') and operation.response:
                print(f"\n✅ Success!")
                if operation.response:
                    print(f"Response:")
                    for key, value in operation.response.items():
                        print(f"   {key}: {value}")
        else:
            print(f"\n⏳ Operation in progress...")
            
    except Exception as e:
        print(f"❌ Error checking operation: {e}")

def list_stores_paginated(page_size=10):
    """List all File Search Stores with pagination"""
    print("📚 Your File Search Stores:\n")
    
    page_token = None
    page_num = 1
    total_stores = 0
    
    while True:
        try:
            if page_token:
                result = client.file_search_stores.list(page_size=page_size, page_token=page_token)
            else:
                result = client.file_search_stores.list(page_size=page_size)
            
            stores = list(result.file_search_stores) if hasattr(result, 'file_search_stores') else []
            
            if not stores and page_num == 1:
                print("   No stores found.")
                return
            
            print(f"Page {page_num}:")
            for i, store in enumerate(stores, 1 + total_stores):
                print(f"{i}. {store.display_name}")
                print(f"   Name: {store.name}")
                print(f"   Created: {store.create_time}")
                print(f"   Active Documents: {store.active_documents_count}")
                print()
            
            total_stores += len(stores)
            
            # Check if there are more pages
            if hasattr(result, 'next_page_token') and result.next_page_token:
                page_token = result.next_page_token
                page_num += 1
                
                response = input(f"\nShow next page? (y/n): ")
                if response.lower() != 'y':
                    break
            else:
                break
                
        except Exception as e:
            print(f"❌ Error listing stores: {e}")
            break
    
    print(f"\nTotal stores: {total_stores}")

def upload_with_metadata(store_name, file_paths, custom_metadata=None):
    """Upload files with custom metadata"""
    print(f"📤 Uploading files to store: {store_name}\n")
    
    if custom_metadata:
        print(f"Custom metadata: {custom_metadata}\n")
    
    uploaded = 0
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"   ⚠️  File not found: {file_path}")
            continue
        
        try:
            print(f"   Uploading {file_path}...")
            
            config = {
                'display_name': os.path.basename(file_path),
                'chunking_config': {
                    'white_space_config': {
                        'max_tokens_per_chunk': 500,
                        'max_overlap_tokens': 50
                    }
                }
            }
            
            if custom_metadata:
                config['custom_metadata'] = custom_metadata
            
            operation = client.file_search_stores.upload_to_file_search_store(
                file=file_path,
                parent=store_name,
                config=config
            )
            
            # Show progress
            print(f"   ⏳ Processing...")
            while not operation.done:
                time.sleep(2)
                operation = client.operations.get(operation)
            
            print(f"   ✅ Uploaded successfully")
            uploaded += 1
            
        except Exception as e:
            print(f"   ❌ Error uploading {file_path}: {e}")
    
    print(f"\n✅ Uploaded {uploaded}/{len(file_paths)} files")

def show_usage():
    """Show usage information"""
    print("""
🔧 Gemini File Search Store Manager

Usage:
    python3 manage-store.py create "name"                   # Create a new store
    python3 manage-store.py list                            # List all stores
    python3 manage-store.py list <store-name>               # List documents in a store
    python3 manage-store.py info <store-name>               # Show detailed store info
    python3 manage-store.py stats                           # Show global storage stats
    python3 manage-store.py stats <store-name>              # Show stats for specific store
    python3 manage-store.py query <store-name> "question"   # Query a store
    python3 manage-store.py search <store-name> "query"     # Vector search (fast)
    python3 manage-store.py upload <store-name> <files>...  # Upload files to store
    python3 manage-store.py import <store-name> <file-ids>  # Import from File API
    python3 manage-store.py operation <operation-id>        # Check operation status
    python3 manage-store.py rename <store-name> "new name"  # Rename store
    python3 manage-store.py export                          # Export all stores to JSON
    python3 manage-store.py export <store-name>             # Export specific store
    python3 manage-store.py delete <store-name>             # Delete entire store
    python3 manage-store.py remove <doc-id>                 # Remove a document

New Features:
    create    - Create a new File Search Store from scratch
    info      - Get detailed metadata (active/pending/failed docs, storage size)
    import    - Import files already uploaded to File API (reuse across stores)
    operation - Check status of long-running operations (uploads, imports)

Examples:
    # Create a new store
    python3 manage-store.py create "My Knowledge Base"
    
    # View detailed store info with metadata
    python3 manage-store.py info fileSearchStores/abc123
    
    # View storage usage
    python3 manage-store.py stats
    
    # Upload new documents
    python3 manage-store.py upload fileSearchStores/abc123 doc1.pdf doc2.pdf
    
    # Import already-uploaded files from File API
    python3 manage-store.py import fileSearchStores/abc123 files/xyz789
    
    # Check operation status
    python3 manage-store.py operation fileSearchStores/abc123/operations/op123
    
    # Search without generation (faster)
    python3 manage-store.py search fileSearchStores/abc123 "revenue forecast"
    
    # Rename a store
    python3 manage-store.py rename fileSearchStores/abc123 "Q4 Documents"
    
    # Export for backup
    python3 manage-store.py export > backup.json

Interactive Mode:
    python3 manage-store.py                                 # Browse stores
""")

def main():
    if len(sys.argv) < 2:
        # Interactive mode
        print("🚀 Gemini File Search Store Manager\n")
        stores = list_stores()
        
        if stores:
            print("\nEnter store number to view documents (or 'q' to quit): ", end='')
            choice = input().strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(stores):
                    list_documents(stores[idx].name)
        return
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        if len(sys.argv) == 3:
            create_store(sys.argv[2])
        else:
            print("❌ Error: Missing display name")
            print("Usage: python3 manage-store.py create \"My Store Name\"")
    
    elif command == 'info':
        if len(sys.argv) == 3:
            get_store_info(sys.argv[2])
        else:
            print("❌ Error: Missing store name")
            print("Usage: python3 manage-store.py info <store-name>")
    
    elif command == 'import':
        if len(sys.argv) >= 4:
            store_name = sys.argv[2]
            file_ids = sys.argv[3:]
            import_files(store_name, file_ids)
        else:
            print("❌ Error: Missing arguments")
            print("Usage: python3 manage-store.py import <store-name> <file-id1> [file-id2] ...")
    
    elif command == 'operation':
        if len(sys.argv) == 3:
            check_operation(sys.argv[2])
        else:
            print("❌ Error: Missing operation ID")
            print("Usage: python3 manage-store.py operation <operation-id>")
    
    elif command == 'list':
        if len(sys.argv) == 2:
            list_stores()
        elif len(sys.argv) == 3:
            list_documents(sys.argv[2])
        else:
            show_usage()
    
    elif command == 'stats':
        if len(sys.argv) == 2:
            show_stats()
        elif len(sys.argv) == 3:
            show_stats(sys.argv[2])
        else:
            show_usage()
    
    elif command == 'upload':
        if len(sys.argv) >= 4:
            store_name = sys.argv[2]
            file_paths = sys.argv[3:]
            upload_files(store_name, file_paths)
        else:
            print("❌ Error: Missing arguments")
            print("Usage: python3 manage-store.py upload <store-name> <file1> [file2] ...")
    
    elif command == 'search':
        if len(sys.argv) == 4:
            store_name = sys.argv[2]
            query = sys.argv[3]
            vector_search(store_name, query)
        else:
            print("❌ Error: Missing arguments")
            print("Usage: python3 manage-store.py search <store-name> \"query\"")
    
    elif command == 'rename':
        if len(sys.argv) == 4:
            store_name = sys.argv[2]
            new_name = sys.argv[3]
            rename_store(store_name, new_name)
        else:
            print("❌ Error: Missing arguments")
            print("Usage: python3 manage-store.py rename <store-name> \"New Display Name\"")
    
    elif command == 'export':
        if len(sys.argv) == 2:
            export_stores()
        elif len(sys.argv) == 3:
            export_stores(sys.argv[2])
        else:
            show_usage()
    
    elif command == 'delete':
        if len(sys.argv) == 3:
            delete_store(sys.argv[2])
        else:
            print("❌ Error: Missing store name")
            print("Usage: python3 manage-store.py delete <store-name>")
    
    elif command == 'remove':
        if len(sys.argv) == 3:
            remove_document(sys.argv[2])
        else:
            print("❌ Error: Missing document ID")
            print("Usage: python3 manage-store.py remove <document-id>")
    
    elif command == 'query':
        if len(sys.argv) == 3:
            interactive_query(sys.argv[2])
        elif len(sys.argv) == 4:
            query_store(sys.argv[2], sys.argv[3])
        else:
            print("❌ Error: Missing arguments")
            print("Usage: python3 manage-store.py query <store-name> [\"question\"]")
    
    elif command in ['help', '-h', '--help']:
        show_usage()
    
    else:
        print(f"❌ Unknown command: {command}")
        show_usage()

if __name__ == "__main__":
    main()
