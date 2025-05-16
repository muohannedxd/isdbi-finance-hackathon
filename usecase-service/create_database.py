import os
import shutil
import argparse
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma  # Updated import
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CHROMA_PATH = "chroma"
DEFAULT_DATA_PATH = "data"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2" 

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Create vector database from documents.")
    parser.add_argument("--data_dir", type=str, default=DEFAULT_DATA_PATH, 
                      help=f"Directory containing documents (default: {DEFAULT_DATA_PATH})")
    parser.add_argument("--embedding_model", type=str, default=DEFAULT_EMBEDDING_MODEL,
                      help=f"HuggingFace model to use for embeddings (default: {DEFAULT_EMBEDDING_MODEL})")
    
    args = parser.parse_args()
    print(f"Using data directory: {args.data_dir}")
    print(f"Using embedding model: {args.embedding_model}")
    
    generate_data_store(data_path=args.data_dir, embedding_model=args.embedding_model)

def generate_data_store(data_path, embedding_model):
    print("Starting database creation...")
    documents = load_documents(data_path)
    if not documents:
        print("No documents were loaded. Please check your data directory.")
        return
        
    print("Splitting documents into chunks...")
    chunks = split_text(documents)
    if not chunks:
        print("No text chunks were created. Documents might be empty.")
        return
        
    print("Saving chunks to Chroma database...")
    save_to_chroma(chunks, embedding_model)
    print("Database creation completed successfully!")

def load_documents(data_path):
    print(f"Scanning directory: {data_path}")
    # Make sure directory exists
    if not os.path.exists(data_path):
        os.makedirs(data_path, exist_ok=True)
        print(f"Created directory {data_path} - please add your document files there")
        return []
    
    # Recursively find all PDF and DOCX files
    pdf_files = []
    docx_files = []
    subdirectories = set()
    
    for root, dirs, files in os.walk(data_path):
        if root != data_path:  # This is a subdirectory
            rel_path = os.path.relpath(root, data_path)
            subdirectories.add(rel_path)
            
        for file in files:
            full_path = os.path.join(root, file)
            if file.lower().endswith('.pdf'):
                pdf_files.append(full_path)
            elif file.lower().endswith('.docx'):
                docx_files.append(full_path)
    
    total_files = len(pdf_files) + len(docx_files)
    if total_files == 0:
        print(f"No PDF or DOCX files found in {data_path} or its subdirectories.")
        return []
    
    # Report on directory structure    
    print(f"Found {len(subdirectories)} subdirectories")
    for subdir in sorted(subdirectories):
        print(f"  - {subdir}")
    print(f"Found {len(pdf_files)} PDF files and {len(docx_files)} DOCX files")
    
    # Load document files one by one
    documents = []
    
    # Function to enhance metadata with folder information
    def enhance_metadata(doc, file_path):
        rel_path = os.path.relpath(os.path.dirname(file_path), data_path)
        if rel_path == ".":  # File is directly in data_path
            rel_path = "root"
        doc.metadata["folder"] = rel_path
        doc.metadata["source"] = file_path
        doc.metadata["filename"] = os.path.basename(file_path)
        return doc
    
    # Load PDF files
    for pdf_path in pdf_files:
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            # Add folder information to metadata
            docs = [enhance_metadata(doc, pdf_path) for doc in docs]
            if docs:
                documents.extend(docs)
                rel_path = os.path.relpath(os.path.dirname(pdf_path), data_path)
                print(f"Loaded {len(docs)} pages from PDF: {os.path.basename(pdf_path)} in {rel_path}")
            else:
                print(f"Warning: No content extracted from PDF: {os.path.basename(pdf_path)}")
        except Exception as e:
            print(f"Error loading PDF {pdf_path}: {str(e)}")
    
    # Load DOCX files with similar metadata enhancement
    for docx_path in docx_files:
        try:
            loader = Docx2txtLoader(docx_path)
            docs = loader.load()
            # Add folder information to metadata
            docs = [enhance_metadata(doc, docx_path) for doc in docs]
            if docs:
                documents.extend(docs)
                rel_path = os.path.relpath(os.path.dirname(docx_path), data_path)
                print(f"Loaded document: {os.path.basename(docx_path)} in {rel_path}")
            else:
                print(f"Warning: No content extracted from DOCX: {os.path.basename(docx_path)}")
        except Exception as e:
            print(f"Error loading DOCX {docx_path}: {str(e)}")
    
    print(f"Loaded {len(documents)} total documents/pages")
    
    # Verify documents have content
    empty_docs = [i for i, doc in enumerate(documents) if not doc.page_content.strip()]
    if empty_docs:
        print(f"Warning: {len(empty_docs)} documents have empty content")
        documents = [doc for doc in documents if doc.page_content.strip()]
        print(f"Proceeding with {len(documents)} non-empty documents")
    
    return documents

def split_text(documents: list[Document]):
    # If there are no documents, return empty list
    if not documents:
        return []
        
    # Chunk documents
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=50,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks")
    
    return chunks

def save_to_chroma(chunks: list[Document], embedding_model):
    print(f"Starting save_to_chroma with {len(chunks)} chunks using model {embedding_model}")
    
    # Always clear out the database first to avoid corruption
    if os.path.exists(CHROMA_PATH):
        print(f"Removing existing database at {CHROMA_PATH}")
        shutil.rmtree(CHROMA_PATH)
    
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            cache_folder="./models/"  # Cache the model locally
        )
        
        # Test embedding to validate
        test_text = "This is a test"
        test_embedding = embeddings.embed_query(test_text)
        print(f"Test embedding dimension: {len(test_embedding)}")
        
        # Create a new DB from the documents
        # When a persist_directory is provided, it automatically persists
        db = Chroma.from_documents(
            chunks, embeddings, persist_directory=CHROMA_PATH
        )
        # No need to call persist() - it's already done when using persist_directory
        print(f"Successfully saved {len(chunks)} chunks to {CHROMA_PATH}")
    except Exception as e:
        print(f"Error in save_to_chroma: {str(e)}")
        if chunks:
            print(f"First chunk content: {chunks[0].page_content[:100]}...")
        raise

if __name__ == "__main__":
    main()
