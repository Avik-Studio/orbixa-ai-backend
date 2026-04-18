"""
Knowledge base configuration for Medical Bot Agent OS.
Sets up Qdrant vector database and Knowledge instance with helper functions for PDF operations.
"""
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from qdrant_client import QdrantClient
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader

from config.database import get_qdrant, get_mongodb


# Constants for PDF ingestion
CHUNK_SIZE = 1000
EMBEDDING_MODEL = "default"


def create_knowledge_base() -> Knowledge:
    """Create and configure the Medical Knowledge Base with Qdrant."""
    vector_db = get_qdrant()
    
    return Knowledge(
        name="Medical Knowledge Base",
        description="Comprehensive medical textbooks and documentation for healthcare professionals",
        vector_db=vector_db,
    )


async def ingest_pdf_file(file_path: Path, original_filename: str) -> Dict[str, Any]:
    """
    Directly ingest a single PDF file - Agno v2 style.
    Supports formats: bookname.pdf or bookname_Part17.pdf
    
    Args:
        file_path: Path to the PDF file on disk
        original_filename: Original filename of the uploaded file
        
    Returns:
        Dict containing ingestion result
    """
    try:
        # Validate PDF
        if not file_path.suffix.lower() == '.pdf':
            return {
                "success": False,
                "error": "File is not a PDF",
                "error_type": "invalid_file"
            }
        
        # Extract part information from filename - expected format: "bookname_Part17.pdf"
        filename = file_path.stem  # e.g., "bookname_Part17" (without .pdf extension)
        
        # Initialize variables
        part_info = None  # Will be like "Part_17"
        book_name_for_metadata = filename  # Will be like "bookname.pdf"
        
        # Pattern to match "_Part" followed by numbers at the end
        part_pattern = r'_Part(\d+)$'
        match = re.search(part_pattern, filename, re.IGNORECASE)
        
        if match:
            # Extract the part number
            part_number = match.group(1)
            part_info = f"Part_{part_number}"  # Format as "Part_1", "Part_17", etc.
            
            # Get the base book name (everything before "_Part17")
            base_book_name = filename[:match.start()]
            
            # Add .pdf extension to create the book_name metadata
            book_name_for_metadata = f"{base_book_name}.pdf"
        else:
            # No part detected - treat as single file
            part_info = None
            # If filename doesn't end with .pdf, add it for book_name metadata
            if not filename.endswith('.pdf'):
                book_name_for_metadata = f"{filename}.pdf"
            else:
                book_name_for_metadata = filename
        
        # Create metadata matching your structure
        metadata = {
            "book_name": book_name_for_metadata,  # e.g., "bookname.pdf"
            "original_filename": original_filename,
            "upload_date": datetime.now(timezone.utc).isoformat(),
            "processing_date": datetime.now(timezone.utc).isoformat(),
            "part": part_info,
            "file_size": file_path.stat().st_size,
            "source": "api_ingestion",
            "chunk_size": CHUNK_SIZE,
            "embedding_model": EMBEDDING_MODEL,
        }
        
        # Initialize knowledge base for processing
        kb = Knowledge(
            vector_db=get_qdrant(),
            contents_db=get_mongodb()  # Track content in MongoDB
        )
        
        # Create custom reader with specific settings
        reader = PDFReader(
            chunk_size=CHUNK_SIZE
        )
        
        # Use add_content_async for Agno v2
        # The name parameter will automatically become the payload 'name' field
        await kb.add_content_async(
            name=filename,  # This becomes the payload 'name' field automatically
            path=str(file_path),
            metadata=metadata,
            reader=reader,
            skip_if_exists=True  # Skip files already uploaded (checks content_hash)
        )
        
        return {
            "success": True,
            "message": f"Successfully ingested {original_filename}",
            "filename": original_filename,
            "book_name": book_name_for_metadata,
            "part_info": part_info,
            "metadata": metadata,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except FileNotFoundError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "file_not_found"
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "invalid_file"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "processing_error",
            "message": f"Error loading document: {str(e)}"
        }


async def delete_book_by_name(book_name: str) -> Dict[str, Any]:
    """
    Delete all chunks of a specific book from the Qdrant collection.
    Uses the same logic as the provided delete_book method.
    
    Args:
        book_name: Name of the book to delete
        
    Returns:
        Dict containing deletion result
    """
    try:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "medical_knowledge_base")
        
        # Create a direct Qdrant client
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        
        # Find all point IDs that match the book name
        points_to_delete = []
        offset = None
        
        while True:
            points, next_page_offset = client.scroll(
                collection_name=collection_name,
                with_payload=True,
                with_vectors=False,
                limit=1000,
                offset=offset
            )
            
            if not points:
                break
            
            for point in points:
                if point.payload:
                    # Extract book name using the same logic as your fetch function
                    found_book_name = None
                    
                    # Method 1: Check meta_data field
                    if 'meta_data' in point.payload:
                        meta_data = point.payload['meta_data']
                        if isinstance(meta_data, dict):
                            for field in ['book_name', 'book_title', 'original_filename', 'title']:
                                if field in meta_data:
                                    found_book_name = meta_data[field]
                                    break
                    
                    # Method 2: Check direct payload fields
                    if not found_book_name:
                        for field in ['book_name', 'book_title', 'original_filename', 'title']:
                            if field in point.payload:
                                found_book_name = point.payload[field]
                                break
                    
                    # Method 3: Check the 'name' field
                    if not found_book_name and 'name' in point.payload:
                        name = point.payload['name']
                        if name and not name.startswith('tmp') and name.endswith('.pdf'):
                            found_book_name = name
                    
                    # Clean up the book name
                    if found_book_name:
                        if found_book_name.endswith('.pdf'):
                            found_book_name = found_book_name.replace('.pdf', '')
                    
                    # Check if this matches the book to delete
                    if found_book_name and found_book_name.lower() == book_name.lower():
                        points_to_delete.append(point.id)
            
            if not next_page_offset:
                break
            offset = next_page_offset
        
        # Delete the points
        if points_to_delete:
            # Delete points in batches (Qdrant recommends batch operations)
            batch_size = 100
            deleted_count = 0
            
            for i in range(0, len(points_to_delete), batch_size):
                batch = points_to_delete[i:i + batch_size]
                
                client.delete(
                    collection_name=collection_name,
                    points_selector=batch
                )
                
                deleted_count += len(batch)
            
            return {
                "success": True,
                "message": f"Successfully deleted '{book_name}' ({deleted_count} chunks)",
                "deleted_chunks": deleted_count
            }
        else:
            # Get available books for reference
            available_books = await get_all_books()
            
            return {
                "success": False,
                "message": f"Book '{book_name}' not found in the collection",
                "available_books": list(available_books.get("books", {}).keys())
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to delete book '{book_name}'"
        }


async def get_all_books() -> Dict[str, Any]:
    """
    Get list of ingested book names from Qdrant metadata.
    Returns book names with chunk counts and parts information.
    
    Returns:
        Dict containing books information
    """
    try:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "medical_knowledge_base")
        
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        
        books = {}
        offset = None
        
        while True:
            points, next_page_offset = client.scroll(
                collection_name=collection_name,
                with_payload=True,
                with_vectors=False,
                limit=1000,
                offset=offset
            )
            
            if not points:
                break
            
            for point in points:
                if point.payload:
                    book_name = None
                    part_info = None
                    
                    # Extract book name from meta_data or direct payload
                    if 'meta_data' in point.payload and isinstance(point.payload['meta_data'], dict):
                        meta_data = point.payload['meta_data']
                        for field in ['book_name', 'book_title']:
                            if field in meta_data:
                                book_name = meta_data[field]
                                break
                        part_info = meta_data.get('part')
                    
                    if not book_name:
                        for field in ['book_name', 'book_title', 'name']:
                            if field in point.payload:
                                book_name = point.payload[field]
                                break
                        part_info = point.payload.get('part')
                    
                    if book_name:
                        book_name = book_name.replace('.pdf', '')
                        if book_name not in books:
                            books[book_name] = {"chunks": 0, "parts": set()}
                        books[book_name]["chunks"] += 1
                        if part_info:
                            books[book_name]["parts"].add(part_info)
            
            if not next_page_offset:
                break
            offset = next_page_offset
        
        # Convert sets to lists for JSON serialization
        books_details = {}
        for book_name, info in books.items():
            books_details[book_name] = {
                "chunks": info["chunks"],
                "parts": sorted(list(info["parts"])) if info["parts"] else []
            }
        
        return {
            "success": True,
            "books": books_details,
            "total_books": len(books_details),
            "source": "qdrant_metadata"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }