
import math
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from LLM.settings import settings

logger = logging.getLogger(__name__)

class GeminiEmbeddingFunction:
    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        model_name = settings.gemini_embedding_model.replace("models/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:embedContent?key={settings.gemini_api_key}"
        
        for i, text in enumerate(input):
            print(f" ⏳ Đang xử lý tài liệu số {i+1}/{len(input)}...")
            payload = {
                "model": f"models/{model_name}",
                "content": {"parts": [{"text": text}]}
            }
            try:
                response = requests.post(url, json=payload)
                if response.status_code == 200:
                    embeddings.append(response.json()["embedding"]["values"])
                else:
                    print(f" ❌ Lỗi từ Google: {response.text}")
                    embeddings.append([0.0] * 768)
            except Exception as e:
                print(f" ❌ Lỗi mạng: {e}")
                embeddings.append([0.0] * 768)
                
            time.sleep(1) #Tránh việc gọi API bị quá tải
        print("thành công")
        return embeddings

class VectorStore:
    def __init__(self, collection_name: str = "chro_hr"): 
        self.documents = []  
        self.embeddings = [] 
        self.embedding_fn = GeminiEmbeddingFunction()
        
    def ingest_documents(self, documents: List[Dict[str, Any]]) -> int:
        if not documents: return 0
        texts = [doc["text"] for doc in documents]
        vectors = self.embedding_fn(texts) 

        self.documents.extend(documents)
        self.embeddings.extend(vectors)
        logger.info(f"{len(documents)}")
        return len(documents)

    def search(self, query: str, top_k: Optional[int] = None, filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        k = top_k or settings.rag_top_k
        print(f"\n[Debug] Đang nhúng câu hỏi: '{query}'...")
        
        query_vector = self.embedding_fn([query])[0]
        
        results = []
        for idx, doc_vec in enumerate(self.embeddings):
            dot_product = sum(x * y for x, y in zip(query_vector, doc_vec))
            mag1 = math.sqrt(sum(x * x for x in query_vector))
            mag2 = math.sqrt(sum(x * x for x in doc_vec))
            
            if mag1 == 0 or mag2 == 0:
                sim = 0.0
            else:
                sim = dot_product / (mag1 * mag2)
            
            doc = self.documents[idx]
            
            if filter_metadata:
                match = all(doc["metadata"].get(mk) == mv for mk, mv in filter_metadata.items())
                if not match: continue
                    
            if sim >= settings.rag_similarity_threshold:
                results.append({
                    "id": doc["id"],
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "similarity": round(sim, 4),
                    "rank": 0 
                })
                
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:k]
        
        for i, r in enumerate(results): 
            r["rank"] = i + 1
            
        logger.info(f"RAG search trả về {len(results)} kết quả.")
        return results

    def format_context(self, search_results: List[Dict]) -> str:
        if not search_results: return ""
        context_parts = ["KNOWLEDGE:\n" + "─" * 40]
        for r in search_results:
            source = r["metadata"].get("source", "HR Knowledge Base")
            category = r["metadata"].get("category", "general")
            context_parts.append(f"[{r['rank']}] [{category.upper()}] {source}\n{r['text']}\n")
        return "\n".join(context_parts) + "\n" + "─" * 40

    def get_stats(self) -> Dict:
        return {"total_documents": len(self.documents)}

    def reset(self):
        self.documents = []
        self.embeddings = []