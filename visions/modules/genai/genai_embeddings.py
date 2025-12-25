import time
from typing import List, Optional
from langchain_core.embeddings import Embeddings
from google import genai
from google.genai import types
from visions.core.config import Config

class GenAIEmbeddings(Embeddings):
    """
    Custom LangChain Embeddings wrapper using the native google-genai SDK.
    Optimized for Gemini 3 and gemini-embedding-001.
    """
    
    def __init__(
        self, 
        model_name: str = "gemini-embedding-001",
        task_type: str = "RETRIEVAL_DOCUMENT",
        output_dimensionality: int = 768,
        batch_size: int = 5,
        requests_per_minute: int = 1500 # Default free tier for Flash/Embedding
    ):
        self.model_name = model_name
        self.task_type = task_type
        self.output_dimensionality = output_dimensionality
        self.batch_size = batch_size
        
        # Init GenAI Client (Vertex AI mode)
        self.client = genai.Client(
            vertexai=True, 
            project=Config.VERTEX_PROJECT_ID,
            location=Config.VERTEX_LOCATION
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents with batching and rate limiting."""
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                # Use types.EmbedContentConfig for task-specific optimization
                config = types.EmbedContentConfig(
                    task_type=self.task_type,
                    output_dimensionality=self.output_dimensionality
                )
                
                result = self.client.models.embed_content(
                    model=self.model_name,
                    contents=batch,
                    config=config
                )
                
                # extract values
                batch_embeddings = [e.values for e in result.embeddings]
                all_embeddings.extend(batch_embeddings)
                
                # Small sleep to be safe with quotas (User: "take a break")
                if len(texts) > self.batch_size:
                    time.sleep(2.0)
                    
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    backoff = 10
                    max_backoff = 120
                    while backoff <= max_backoff:
                        print(f"⚠️ Rate limited. Exponential backoff: Waiting {backoff}s...")
                        time.sleep(backoff)
                        try:
                            result = self.client.models.embed_content(
                                model=self.model_name,
                                contents=batch,
                                config=config
                            )
                            batch_embeddings = [e.values for e in result.embeddings]
                            all_embeddings.extend(batch_embeddings)
                            break # Success!
                        except Exception as retry_e:
                            if "429" in str(retry_e) or "RESOURCE_EXHAUSTED" in str(retry_e):
                                backoff *= 2 # Double the wait
                            else:
                                raise retry_e
                    else:
                        print(f"❌ Max backoff reached for batch.")
                        raise e
                else:
                    print(f"❌ Error during document embedding: {e}")
                    raise e
                    
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query with RETRIEVAL_QUERY optimization."""
        try:
            # For queries, always use RETRIEVAL_QUERY task type
            config = types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self.output_dimensionality
            )
            
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=text,
                config=config
            )
            
            return result.embeddings[0].values
        except Exception as e:
            print(f"❌ Error during query embedding: {e}")
            raise e
