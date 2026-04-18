#!/usr/bin/env python3
"""
Qdrant Metadata Update Script: Remove _PartN from book names and add separate part field
"""

import os
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import certifi
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Set SSL certificate file
os.environ['SSL_CERT_FILE'] = certifi.where()
load_dotenv()

class QdrantMetadataUpdater:
    def __init__(self):
        """Initialize Qdrant client and setup"""
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=60
        )
        self.collection_name = "medical_knowledge_base"
        self.batch_size = 100  # Process in batches to avoid memory issues
        self.updated_count = 0
        self.error_count = 0
        self.skipped_count = 0
        
    def create_upload_date_index(self):
        """Create an index for the upload_date field to enable efficient filtering"""
        try:
            print("🔧 Creating index for meta_data.upload_date...")
            
            # Create the index for upload_date field
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="meta_data.upload_date",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            print("✅ Successfully created index for meta_data.upload_date")
            return True
            
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️ Index for meta_data.upload_date already exists")
                return True
            else:
                print(f"❌ Error creating index: {e}")
                return False
        
    def extract_part_info(self, book_name: str) -> Tuple[str, Optional[str]]:
        """
        Extract part information from book name
        
        Args:
            book_name: Original book name like "CALLEN_S ULTRASOUND OBG 6th edition_Part14.pdf"
            
        Returns:
            Tuple of (cleaned_book_name, part_number)
            Example: ("CALLEN_S ULTRASOUND OBG 6th edition.pdf", "Part_14")
        """
        # Pattern to match _PartN at the end (before .pdf extension if present)
        pattern = r'_Part(\d+)(?=\.pdf$|$)'
        
        match = re.search(pattern, book_name)
        if match:
            part_number = match.group(1)
            # Remove the _PartN portion
            cleaned_name = re.sub(pattern, '', book_name)
            
            # Fix double .pdf extensions (e.g., "file.pdf_Part4.pdf" -> "file.pdf.pdf" -> "file.pdf")
            if cleaned_name.endswith('.pdf.pdf'):
                cleaned_name = cleaned_name[:-4]  # Remove the extra .pdf
            
            return cleaned_name, f"Part_{part_number}"
        
        # If no part pattern found, return original name and None
        return book_name, None
    
    def get_total_points_count(self) -> int:
        """Get total number of points in the collection"""
        try:
            count_result = self.client.count(collection_name=self.collection_name, exact=True)
            return count_result.count
        except Exception as e:
            print(f"❌ Error getting total count: {e}")
            return 0
    
    def scroll_all_points(self, limit: Optional[int] = None):
        """
        Generator to scroll through all points in the collection
        
        Args:
            limit: If specified, only process this many points (for testing)
        """
        offset = None
        processed = 0
        
        print(f"🔄 Starting to scroll through collection points...")
        
        while True:
            try:
                # Scroll through points in batches
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    offset=offset,
                    limit=self.batch_size,
                    with_payload=True,
                    with_vectors=False  # We don't need vectors for metadata updates
                )
                
                points, next_offset = result
                
                if not points:
                    break
                
                for point in points:
                    yield point
                    processed += 1
                    
                    # Stop if we've hit the limit
                    if limit and processed >= limit:
                        return
                
                offset = next_offset
                if not offset:
                    break
                    
            except Exception as e:
                print(f"❌ Error during scroll: {e}")
                break
    
    def update_point_metadata(self, point_id: str, new_payload: Dict) -> bool:
        """
        Update a single point's metadata
        
        Args:
            point_id: The point ID to update
            new_payload: The new payload data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=new_payload,
                points=[point_id]
            )
            return True
        except Exception as e:
            print(f"❌ Error updating point {point_id}: {e}")
            return False
    
    def process_single_point(self, point) -> bool:
        """
        Process a single point and update its metadata if needed
        
        Args:
            point: The point object from Qdrant
            
        Returns:
            True if point was updated, False if skipped or error
        """
        try:
            # Check if point has the expected metadata structure
            if not point.payload or 'meta_data' not in point.payload:
                self.skipped_count += 1
                return False
            
            meta_data = point.payload['meta_data']
            
            # Check if book_name exists
            if 'book_name' not in meta_data:
                self.skipped_count += 1
                return False
            
            original_book_name = meta_data['book_name']
            
            # Check for double PDF extension from previous run and fix it
            needs_pdf_fix = original_book_name.endswith('.pdf.pdf')
            
            # Extract part information
            cleaned_book_name, part_number = self.extract_part_info(original_book_name)
            
            # If no part number found but needs PDF fix, handle that
            if part_number is None and needs_pdf_fix:
                # Fix the double PDF extension
                fixed_name = original_book_name[:-4]  # Remove extra .pdf
                
                # Create updated metadata with fixed name
                updated_meta_data = meta_data.copy()
                updated_meta_data['book_name'] = fixed_name
                
                # Create new payload
                new_payload = point.payload.copy()
                new_payload['meta_data'] = updated_meta_data
                
                # Update the point
                success = self.update_point_metadata(point.id, new_payload)
                
                if success:
                    self.updated_count += 1
                    print(f"🔧 Fixed double PDF extension for point {point.id}:")
                    print(f"   Original: {original_book_name}")
                    print(f"   Fixed:    {fixed_name}")
                    return True
                else:
                    self.error_count += 1
                    return False
            
            # If no part number found and no PDF fix needed, skip this point
            if part_number is None:
                self.skipped_count += 1
                return False
            
            # Create updated metadata
            updated_meta_data = meta_data.copy()
            updated_meta_data['book_name'] = cleaned_book_name
            updated_meta_data['part'] = part_number
            
            # Create new payload
            new_payload = point.payload.copy()
            new_payload['meta_data'] = updated_meta_data
            
            # Update the point
            success = self.update_point_metadata(point.id, new_payload)
            
            if success:
                self.updated_count += 1
                print(f"✅ Updated point {point.id}:")
                print(f"   Original: {original_book_name}")
                print(f"   Cleaned:  {cleaned_book_name}")
                print(f"   Part:     {part_number}")
                return True
            else:
                self.error_count += 1
                return False
                
        except Exception as e:
            print(f"❌ Error processing point {point.id}: {e}")
            self.error_count += 1
            return False
    
    def run_update(self, test_mode: bool = True, test_limit: int = 10):
        """
        Main method to run the metadata update
        
        Args:
            test_mode: If True, only process a small number of points for testing
            test_limit: Number of points to process in test mode
        """
        start_time = time.time()
        
        print("🚀 Starting Qdrant Metadata Update")
        print("=" * 60)
        
        # Check collection exists
        if not self.client.collection_exists(self.collection_name):
            print(f"❌ Collection '{self.collection_name}' does not exist!")
            return
        
        # Get total count
        total_points = self.get_total_points_count()
        print(f"📊 Total points in collection: {total_points:,}")
        
        if test_mode:
            print(f"🧪 Running in TEST MODE - processing only {test_limit} points")
            limit = test_limit
        else:
            print(f"🔥 Running in PRODUCTION MODE - processing ALL points")
            limit = None
        
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # Process points
        processed = 0
        for point in self.scroll_all_points(limit=limit):
            processed += 1
            
            # Process the point
            self.process_single_point(point)
            
            # Progress update every 50 points
            if processed % 50 == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                print(f"📈 Progress: {processed:,} processed | {self.updated_count:,} updated | {rate:.1f} points/sec")
        
        # Final summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 60)
        print("📋 FINAL SUMMARY")
        print("=" * 60)
        print(f"⏰ Duration: {duration:.2f} seconds")
        print(f"📊 Points processed: {processed:,}")
        print(f"✅ Points updated: {self.updated_count:,}")
        print(f"⏭️ Points skipped: {self.skipped_count:,}")
        print(f"❌ Errors: {self.error_count:,}")
        
        if processed > 0:
            success_rate = (self.updated_count / processed) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        # Show some examples of the changes
        if self.updated_count > 0:
            print(f"\n🎯 Metadata changes applied:")
            print(f"   • Removed '_PartN' suffix from book names")
            print(f"   • Added 'part' field with 'Part_N' format")
            print(f"   • Example: 'BOOK_Part14.pdf' → 'BOOK.pdf' + part='Part_14'")
    
    def find_books_by_upload_date(self, target_date: str) -> Dict[str, Dict]:
        """
        Find all books with a specific upload date and check their indexing status
        
        Args:
            target_date: Upload date to search for (e.g., "2025-10-05T21:42:31.475167")
            
        Returns:
            Dictionary with book names as keys and indexing info as values
        """
        print(f"🔍 Searching for books with upload date: {target_date}")
        print("=" * 60)
        
        try:
            # Use filter to efficiently find points with the target upload date
            date_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="meta_data.upload_date",
                        match=models.MatchValue(value=target_date)
                    )
                ]
            )
            
            # First, get count of matching points
            count_result = self.client.count(
                collection_name=self.collection_name,
                count_filter=date_filter,
                exact=True
            )
            
            total_matches = count_result.count
            print(f"📊 Total points with upload date {target_date}: {total_matches:,}")
            
            if total_matches == 0:
                print(f"❌ No books found with upload date: {target_date}")
                return {}
            
            # Scroll through all matching points
            books_found = {}
            processed = 0
            
            offset = None
            while True:
                # Get points with the filter
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=date_filter,
                    limit=100,  # Process in batches
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                points, next_offset = result
                
                if not points:
                    break
                
                for point in points:
                    processed += 1
                    
                    try:
                        meta_data = point.payload.get('meta_data', {})
                        book_name = meta_data.get('book_name', 'Unknown')
                        part = meta_data.get('part', 'No Part')
                        
                        # Initialize book entry if not exists
                        if book_name not in books_found:
                            books_found[book_name] = {
                                'total_parts': 0,
                                'parts_list': [],
                                'indexed_fields': set(),
                                'sample_point_id': None,
                                'book_size_estimate': 0
                            }
                        
                        # Add part info
                        books_found[book_name]['total_parts'] += 1
                        books_found[book_name]['parts_list'].append({
                            'part': part,
                            'point_id': point.id,
                            'chunk_index': meta_data.get('chunk_index', 'Unknown'),
                            'page_number': meta_data.get('page_number', 'Unknown')
                        })
                        
                        # Check what fields are indexed (present in metadata)
                        for field in meta_data.keys():
                            books_found[book_name]['indexed_fields'].add(field)
                        
                        # Store a sample point ID for testing
                        if not books_found[book_name]['sample_point_id']:
                            books_found[book_name]['sample_point_id'] = point.id
                            
                        # Estimate book size by content length
                        content = point.payload.get('page_content', '')
                        books_found[book_name]['book_size_estimate'] += len(content)
                        
                    except Exception as e:
                        print(f"❌ Error processing point {point.id}: {e}")
                
                offset = next_offset
                if not offset:
                    break
                    
                # Progress update
                print(f"📈 Processed: {processed}/{total_matches} points...")
            
            # Display results with indexing analysis
            print("=" * 60)
            print(f"📊 INDEXING ANALYSIS RESULTS")
            print("=" * 60)
            print(f"Total matching points: {total_matches:,}")
            print(f"Unique books found: {len(books_found)}")
            
            if books_found:
                print(f"\n📚 BOOKS WITH UPLOAD DATE {target_date}:")
                print("=" * 80)
                
                for book_name, info in books_found.items():
                    print(f"\n📖 BOOK: {book_name}")
                    print("-" * 60)
                    print(f"   📊 Total parts/chunks: {info['total_parts']:,}")
                    print(f"   📏 Estimated size: {info['book_size_estimate']:,} characters")
                    print(f"   🆔 Sample Point ID: {info['sample_point_id']}")
                    
                    # Check indexing completeness
                    expected_fields = {'book_name', 'upload_date', 'file_name', 'part', 'chunk_index', 'page_number'}
                    indexed_fields = info['indexed_fields']
                    
                    print(f"   🏗️ INDEXING STATUS:")
                    print(f"      • Indexed fields: {len(indexed_fields)}")
                    print(f"      • Fields present: {', '.join(sorted(indexed_fields))}")
                    
                    missing_fields = expected_fields - indexed_fields
                    if missing_fields:
                        print(f"      ⚠️ Missing fields: {', '.join(sorted(missing_fields))}")
                        print(f"      📊 Indexing completeness: {((len(indexed_fields) - len(missing_fields)) / len(expected_fields)) * 100:.1f}%")
                    else:
                        print(f"      ✅ All expected fields are indexed")
                        print(f"      📊 Indexing completeness: 100%")
                    
                    # Show part distribution
                    parts_by_name = {}
                    for part_info in info['parts_list']:
                        part_name = part_info['part']
                        if part_name not in parts_by_name:
                            parts_by_name[part_name] = 0
                        parts_by_name[part_name] += 1
                    
                    print(f"   📋 Part distribution:")
                    for part_name, count in sorted(parts_by_name.items()):
                        print(f"      • {part_name}: {count} chunks")
                
                # Test search functionality for each book
                print(f"\n🔍 SEARCH FUNCTIONALITY TEST:")
                print("=" * 60)
                
                for book_name, info in books_found.items():
                    print(f"\n📖 Testing search for: {book_name[:50]}...")
                    
                    try:
                        # Test book name filter
                        book_filter = models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="meta_data.book_name",
                                    match=models.MatchValue(value=book_name)
                                )
                            ]
                        )
                        
                        book_count = self.client.count(
                            collection_name=self.collection_name,
                            count_filter=book_filter,
                            exact=True
                        )
                        
                        print(f"   ✅ Book filter works: {book_count.count:,} total chunks found")
                        
                        # Test if we can search within this book
                        sample_search = self.client.scroll(
                            collection_name=self.collection_name,
                            scroll_filter=book_filter,
                            limit=1,
                            with_payload=True,
                            with_vectors=False
                        )
                        
                        if sample_search[0]:
                            print(f"   ✅ Content retrieval works")
                            
                            # Check if vector search is available
                            try:
                                vector_search_test = self.client.search(
                                    collection_name=self.collection_name,
                                    query_text="medical",
                                    query_filter=book_filter,
                                    limit=1
                                )
                                print(f"   ✅ Vector search works: Found {len(vector_search_test)} results")
                            except Exception as e:
                                print(f"   ⚠️ Vector search issue: {str(e)[:50]}...")
                        else:
                            print(f"   ❌ Content retrieval failed")
                            
                    except Exception as e:
                        print(f"   ❌ Search test failed: {e}")
            
            return books_found
            
        except Exception as e:
            print(f"❌ Error searching for books by upload date: {e}")
            return {}
    
    def query_book_content(self, book_name: str, query_text: str = "medical diagnosis", limit: int = 5):
        """
        Query content from a specific book
        
        Args:
            book_name: Name of the book to query
            query_text: Text to search for
            limit: Maximum number of results to return
        """
        print(f"\n🔍 Querying book: {book_name}")
        print(f"Query: '{query_text}'")
        print("-" * 60)
        
        try:
            # Search for content in the specific book
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_text=query_text,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="meta_data.book_name",
                            match=models.MatchValue(value=book_name)
                        )
                    ]
                ),
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            if search_result:
                print(f"✅ Found {len(search_result)} relevant results:")
                
                for i, result in enumerate(search_result, 1):
                    meta = result.payload.get('meta_data', {})
                    content = result.payload.get('page_content', '')
                    
                    print(f"\n🔍 Result {i} (Score: {result.score:.3f})")
                    print(f"Part: {meta.get('part', 'Unknown')}")
                    print(f"Page: {meta.get('page_number', 'Unknown')}")
                    print(f"Chunk: {meta.get('chunk_index', 'Unknown')}")
                    print(f"Content preview: {content[:200]}...")
                    print("-" * 40)
            else:
                print("❌ No results found for this query")
                
        except Exception as e:
            print(f"❌ Error querying book content: {e}")
    
    def find_book_by_name(self, book_name: str):
        """Find and analyze a specific book by name"""
        try:
            print(f"🔍 Searching for book: '{book_name}'")
            print("=" * 60)
            
            # Use scroll to find all points with this book name
            offset = None
            total_found = 0
            unique_pages = set()
            sample_content = []
            
            while True:
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="meta_data.book_name",
                                match=models.MatchValue(value=book_name)
                            )
                        ]
                    ),
                    limit=100,
                    offset=offset,
                    with_payload=True
                )
                
                points, next_offset = result
                
                if not points:
                    break
                
                for point in points:
                    total_found += 1
                    payload = point.payload
                    metadata = payload.get('meta_data', {})
                    
                    # Collect page numbers
                    if 'page_number' in metadata:
                        unique_pages.add(metadata['page_number'])
                    
                    # Collect sample content (first 5 entries)
                    if len(sample_content) < 5:
                        sample_content.append({
                            'page': metadata.get('page_number', 'Unknown'),
                            'content': payload.get('page_content', '')[:300] + "..." if len(payload.get('page_content', '')) > 300 else payload.get('page_content', ''),
                            'upload_date': metadata.get('upload_date', 'Unknown'),
                            'part': metadata.get('part', 'Unknown')
                        })
                
                if next_offset is None:
                    break
                    
                offset = next_offset
            
            # Display results
            if total_found > 0:
                print(f"📊 BOOK ANALYSIS RESULTS")
                print(f"📚 Book Name: {book_name}")
                print(f"📄 Total Chunks Found: {total_found}")
                print(f"📖 Unique Pages: {len(unique_pages)} pages")
                if unique_pages:
                    sorted_pages = sorted(list(unique_pages))
                    print(f"📋 Page Range: {min(sorted_pages)} - {max(sorted_pages)}")
                
                # Show metadata from first sample
                if sample_content:
                    first_sample = sample_content[0]
                    print(f"📅 Upload Date: {first_sample['upload_date']}")
                    print(f"🧩 Part Info: {first_sample['part']}")
                
                print(f"\n📝 SAMPLE CONTENT (First 5 chunks):")
                print("=" * 50)
                
                for i, sample in enumerate(sample_content, 1):
                    print(f"{i}. Page {sample['page']}:")
                    print(f"   {sample['content']}")
                    print("-" * 40)
                
                return {
                    'total_chunks': total_found,
                    'unique_pages': len(unique_pages),
                    'page_range': f"{min(sorted_pages)} - {max(sorted_pages)}" if unique_pages else "Unknown",
                    'upload_date': sample_content[0]['upload_date'] if sample_content else 'Unknown',
                    'part_info': sample_content[0]['part'] if sample_content else 'Unknown',
                    'indexed': True
                }
            else:
                print(f"❌ No chunks found for book: '{book_name}'")
                print("📋 This could mean:")
                print("   • Book name doesn't match exactly")
                print("   • Book is not indexed in the database")
                print("   • Book was uploaded with a different name")
                return None
                
        except Exception as e:
            print(f"❌ Error searching for book: {e}")
            return None
    
    def test_extraction_logic(self):
        """Test the part extraction logic with sample data"""
        test_cases = [
            "CALLEN_S ULTRASOUND OBG 6th edition_Part14.pdf",
            "Medical Textbook_Part1.pdf", 
            "Surgery Guide_Part22.pdf",
            "Regular Book.pdf",  # No part number
            "Book_Part5",  # No .pdf extension
            "Complex_Name_With_Underscores_Part99.pdf"
        ]
        
        print("🧪 Testing Part Extraction Logic")
        print("=" * 50)
        
        for test_case in test_cases:
            cleaned, part = self.extract_part_info(test_case)
            print(f"Original: {test_case}")
            print(f"Cleaned:  {cleaned}")
            print(f"Part:     {part}")
            print("-" * 30)

def find_books_by_date():
    """Function to find and query books by upload date"""
    updater = QdrantMetadataUpdater()
    
    # Target upload date
    target_date = "2025-10-05T21:42:31.475167"
    
    # Find books with this upload date
    books_found = updater.find_books_by_upload_date(target_date)
    
    if books_found:
        print(f"\n🎯 DETAILED ANALYSIS OF FOUND BOOKS")
        print("=" * 60)
        
        for book_name, parts in books_found.items():
            print(f"\n📖 BOOK: {book_name}")
            print(f"📊 Total parts found: {len(parts)}")
            
            # Show all parts for this book
            parts.sort(key=lambda x: x['part'])
            print(f"📋 Parts list:")
            for part in parts:
                print(f"   • {part['part']}: Chunk {part['chunk_index']}, Page {part['page_number']} (ID: {part['point_id']})")
            
            # Query this book for some sample content
            print(f"\n🔍 Sample queries for '{book_name}':")
            
            # Try different queries
            sample_queries = [
                "medical diagnosis",
                "treatment",
                "patient care",
                "clinical",
                "therapy"
            ]
            
            for query in sample_queries:
                updater.query_book_content(book_name, query, limit=3)
                print()
    
    else:
        print(f"❌ No books found with upload date: {target_date}")

def search_williams_obstetrics():
    """Search for Williams Obstetrics book specifically"""
    updater = QdrantMetadataUpdater()
    book_name = "Williams obstetrics 26 edition, 2022 (1)"
    
    result = updater.find_book_by_name(book_name)
    return result

def interactive_menu():
    """Interactive menu for different operations"""
    updater = QdrantMetadataUpdater()
    
    while True:
        print("\n🔧 Qdrant Management Tool")
        print("=" * 40)
        print("1. Update metadata (remove _PartN from book names)")
        print("2. Find books by upload date (2025-10-05T21:42:31.475167)")
        print("3. Search for Williams Obstetrics book")
        print("4. Exit")
        print("=" * 40)
        
        choice = input("Choose an option (1-4): ").strip()
        
        if choice == "1":
            # Original metadata update functionality
            updater.test_extraction_logic()
            print("\n" + "=" * 60)
            input("Press Enter to continue with the actual update (or Ctrl+C to cancel)...")
            
            print("\n🧪 RUNNING TEST MODE FIRST (10 points)")
            updater.run_update(test_mode=True, test_limit=10)
            
            print("\n" + "=" * 60)
            response = input("Test completed. Do you want to run the FULL update? (yes/no): ").strip().lower()
            
            if response in ['yes', 'y']:
                updater.updated_count = 0
                updater.error_count = 0
                updater.skipped_count = 0
                
                print("\n🔥 RUNNING FULL UPDATE")
                updater.run_update(test_mode=False)
            else:
                print("✅ Update cancelled. Test results are available above.")
                
        elif choice == "2":
            find_books_by_date()
            
        elif choice == "3":
            search_williams_obstetrics()
            
        elif choice == "4":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-4.")

def main():
    """Main function"""
    interactive_menu()

if __name__ == "__main__":
    main()
