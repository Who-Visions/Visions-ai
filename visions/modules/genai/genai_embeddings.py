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
        model_name: str = Config.EMBEDDING_MODEL,
        task_type: str = "RETRIEVAL_DOCUMENT",
        output_dimensionality: int = 768,
        batch_size: int = 1, # Reduced for stability
        requests_per_minute: int = 1500, # Default free tier for Flash/Embedding
        project: Optional[str] = None,
        location: Optional[str] = None
    ):
        self.model_name = model_name
        self.task_type = task_type
        self.output_dimensionality = output_dimensionality
        self.batch_size = batch_size
        self.requests_per_minute = requests_per_minute
        
        # Determine Project/Location with fallbacks
        self.project = project or Config.VERTEX_PROJECT_ID
        self.location = location or Config.VERTEX_LOCATION

        if not self.project or not self.location:
             # If still missing, try to get from common environment variables as last resort
             self.project = self.project or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
             self.location = self.location or "us-central1"

        # Init GenAI Client (Vertex AI mode)
        self.client = genai.Client(
            vertexai=True, 
            project=self.project,
            location=self.location
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
                
                # Rate limiting strategy
                if len(texts) > self.batch_size and self.requests_per_minute > 0:
                    delay = 60.0 / self.requests_per_minute
                    time.sleep(delay)
                    
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
        """Embed a single query with RETRIEVAL_QUERY optimization.
           Normalizes embedding for 768 dim as per docs.
        """
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
            
            vals = result.embeddings[0].values
            
            # Normalize if dimension is not default (3072)
            # The docs say: "For other dimensions, including 768... you need to normalize"
            # Although the values come as list, we'll manually normalize if we can't depend on numpy being present
            # But let's check for numpy or implement simple norm
            
            try:
                import numpy as np
                arr = np.array(vals)
                norm = np.linalg.norm(arr)
                if norm > 0:
                    vals = (arr / norm).tolist()
            except ImportError:
                # Fallback manual normalization
                sq_sum = sum(x*x for x in vals)
                norm = sq_sum ** 0.5
                if norm > 0:
                    vals = [x/norm for x in vals]

            return vals
            
        except Exception as e:
            print(f"❌ Error during query embedding: {e}")
            raise e
