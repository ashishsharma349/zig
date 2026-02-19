import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

INDEX_PATH = "knowledge_base/index"
RAW_PATH = "knowledge_base/raw"

# Use a lightweight local embedding model — no internet needed after first download
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.llm = None  # We handle LLM separately via Ollama

def load_or_build_index():
    if os.path.exists(INDEX_PATH) and os.listdir(INDEX_PATH):
        print("Loading existing index...")
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_PATH)
        index = load_index_from_storage(storage_context)
    else:
        print("Building index from knowledge base...")
        documents = SimpleDirectoryReader(RAW_PATH).load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=INDEX_PATH)
    return index

def get_context(query: str, index) -> str:
    retriever = index.as_retriever(similarity_top_k=2)
    results = retriever.retrieve(query)
    if not results:
        return ""
    return "\n\n".join([r.text for r in results])