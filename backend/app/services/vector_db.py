import chromadb
from chromadb.utils import embedding_functions
import os
from pathlib import Path
from app.config import get_settings
import openai
from typing import List


class CustomOpenAIEmbeddingFunction:
    """Custom embedding function compatible with OpenAI 1.12.0+"""
    
    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """Generate embeddings for input texts"""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=input
        )
        return [item.embedding for item in response.data]


class PolicyVectorStore:
    """ChromaDB vector store for insurance policy RAG"""
    
    def __init__(self):
        settings = get_settings()
        self.client = chromadb.Client()
        # Use custom OpenAI embeddings compatible with OpenAI 1.12.0+
        # Initialize with API key but don't create client until needed
        self.embedding_fn = CustomOpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name="text-embedding-3-small"
        )
        self.collection = self.client.create_collection(
            name="payer_policies",
            embedding_function=self.embedding_fn
        )
        self._loaded = False
    
    async def load_policies(self, policy_dir: str):
        """Load and chunk policy documents into vector store"""
        if self._loaded:
            return
            
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        documents = []
        metadatas = []
        ids = []
        
        policy_path = Path(policy_dir)
        for i, filepath in enumerate(policy_path.glob("*.txt")):
            content = filepath.read_text()
            chunks = splitter.split_text(content)
            payer_name = filepath.stem
            
            for j, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({"payer": payer_name, "chunk_id": j})
                ids.append(f"{payer_name}_{j}")
        
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        
        self._loaded = True
        print(f"Loaded {len(documents)} policy chunks into vector store")
    
    async def query(self, query: str, top_k: int = 5, payer: str = None) -> str:
        """Query for relevant policy sections"""
        where_filter = {"payer": payer} if payer else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter
        )
        
        if not results["documents"][0]:
            return "No relevant policy sections found."
        
        context_parts = []
        for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
            context_parts.append(f"[{metadata['payer']}]: {doc}")
        
        return "\n\n---\n\n".join(context_parts)
