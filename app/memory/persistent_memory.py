import numpy as np
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from app.utils.config import settings
from app.utils.logger import get_logger


class PersistentMemory:
    def __init__(self):
        self.logger = get_logger(__name__)
        # self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._model = None
        if not settings.memory_api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables")
        pc = Pinecone(api_key=settings.memory_api_key)
        self.index = pc.Index("knowthyself")

    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model
    
    def store(self, user_id, track, session_no, memory_type, content):
        if not content or not content.strip():
            return
        unique_id = f"{user_id}_{track}_{session_no}_{memory_type}"
        embeddings = self.model.encode(content).tolist()
        metadata = {
            "user_id": user_id,
            "track": track,
            "session_no": session_no,
            "memory_type": memory_type,
            "content": content
        }
        self.index.upsert(
            vectors=[
                ({"id": unique_id, "values": embeddings, "metadata": metadata})
            ]
        )
        self.logger.info("Memory Stored.")

    def retrieve(self, user_id, track, query, top_k=3):
        embeddings = self.model.encode(query).tolist()
        self.logger.info("Query Embedded.")

        results = self.index.query(
            vector=embeddings,
            top_k=top_k * 2,
            include_metadata=True,
            filter={
                "user_id": {"$eq": user_id},
                "track": {"$eq": track}                
            }
        )
        if not results.matches:
            return []
        max_session = max(match.metadata["session_no"] for match in results.matches)
        scored_matches = []
        for i, match in enumerate(results.matches):
            final_score = match.score + (match.metadata["session_no"] / max_session) * 0.1
            if final_score >= 0.4:
                scored_matches.append((final_score, match))
        
        sorted_matches = sorted(scored_matches, key=lambda x: x[0], reverse=True)
        top_matches = [match for score, match in sorted_matches[:top_k]]

        self.logger.info(f"{len(top_matches)} results received.")

        return top_matches

    def get_session_history(self, user_id, track):
        self.logger.info(f"{user_id} on {track} track.")
        # Use a neutral query instead of zero vector
        vector = self.model.encode("session summary progress").tolist()
        results = self.index.query(
            vector=vector,
            top_k=100,
            include_metadata=True,
            filter={
                "user_id": {"$eq": user_id},
                "track": {"$eq": track}
            }
        )
        self.logger.info(f"get_session_history: {len(results.matches)} matches for {user_id}/{track}")
        return results
