from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PATH = "chroma"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def inspect_database():
    embedding_function = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        cache_folder="./models/"
    )
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Retrieve all documents in the database
    documents = db.similarity_search("test", k=100)
    print(f"Total documents in database: {len(documents)}")
    for doc in documents[:5]:  # Print the first 5 documents
        print(f"Document: {doc.page_content[:100]}...")  # Print the first 100 characters
        print(f"Metadata: {doc.metadata}")

if __name__ == "__main__":
    inspect_database()