"""Semantic matching service using sentence-transformers/all-MiniLM-L6-v2.

Design Highlights:
1. Model Loaded Once at Startup: The transformer model and tokenizer are initialized as a singleton
   module-level instance upon module import (and in FastAPI lifespan), never reloaded per-request.
2. Batch Embeddings: Vectorizes candidate skill lists in a single tensor operation.
3. In-Memory LRU Cache: Caches computed embeddings for repeated queries/skills to avoid redundant GPU/CPU passes.
"""

from typing import List, Dict, Union, Optional
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from app.core.config import settings


class SemanticMatcher:
    """Computes semantic similarity embeddings using sentence-transformers/all-MiniLM-L6-v2."""

    _instance: Optional["SemanticMatcher"] = None

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.SEMANTIC_MODEL_NAME or "sentence-transformers/all-MiniLM-L6-v2"
        # Ensure model is identified properly if short name provided
        if not ("/" in self.model_name or "\\" in self.model_name):
            self.model_identifier = f"sentence-transformers/{self.model_name}"
        else:
            self.model_identifier = self.model_name

        print(f"Loading semantic transformer model once at process startup: {self.model_identifier}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_identifier)
        self.model = AutoModel.from_pretrained(self.model_identifier)
        self.model.eval()

        # In-memory embedding cache for strings to avoid re-encoding common skill names
        self._embedding_cache: Dict[str, torch.Tensor] = {}

    @classmethod
    def get_instance(cls) -> "SemanticMatcher":
        """Singleton accessor ensuring the model is loaded once across process lifespan."""
        if cls._instance is None:
            cls._instance = SemanticMatcher()
        return cls._instance

    def _mean_pooling(self, model_output, attention_mask: torch.Tensor) -> torch.Tensor:
        """Apply mean pooling to extract sentence-level embedding vector (all-MiniLM-L6-v2 standard)."""
        token_embeddings = model_output[0]  # First element contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> torch.Tensor:
        """Batch encode list of texts into normalized embedding vectors with caching."""
        if isinstance(texts, str):
            text_list = [texts]
        else:
            text_list = texts

        if not text_list:
            return torch.empty((0, 384))

        # Check cache for any already-computed vectors
        uncached_texts = []
        uncached_indices = []
        cached_results: Dict[int, torch.Tensor] = {}

        for i, text in enumerate(text_list):
            clean = text.strip()
            if clean in self._embedding_cache:
                cached_results[i] = self._embedding_cache[clean]
            else:
                uncached_texts.append(clean)
                uncached_indices.append(i)

        # Batch encode uncached texts
        if uncached_texts:
            all_new_embeddings = []
            for start in range(0, len(uncached_texts), batch_size):
                batch = uncached_texts[start : start + batch_size]
                encoded_input = self.tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=128,
                    return_tensors="pt",
                )

                with torch.no_grad():
                    model_output = self.model(**encoded_input)

                sentence_embeddings = self._mean_pooling(
                    model_output, encoded_input["attention_mask"]
                )
                # Normalize embeddings for direct cosine similarity via dot product
                normalized = F.normalize(sentence_embeddings, p=2, dim=1)
                all_new_embeddings.append(normalized)

            concatenated_new = torch.cat(all_new_embeddings, dim=0)

            # Store in cache
            for idx_in_new, orig_idx in enumerate(uncached_indices):
                vec = concatenated_new[idx_in_new : idx_in_new + 1]
                self._embedding_cache[uncached_texts[idx_in_new]] = vec
                cached_results[orig_idx] = vec

        # Reconstruct in original order
        ordered_tensors = [cached_results[i] for i in range(len(text_list))]
        return torch.cat(ordered_tensors, dim=0)

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two individual text strings."""
        emb_a = self.encode(text_a)
        emb_b = self.encode(text_b)
        cosine_sim = torch.sum(emb_a * emb_b, dim=-1).item()
        return round(float(cosine_sim), 4)

    def batch_compare(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
    ) -> torch.Tensor:
        """Batch comparison matrix between candidate skills (rows) and required skills (cols).
        
        Returns a 2D tensor of shape [len(candidate_skills), len(required_skills)]
        containing cosine similarity scores between each pair.
        """
        if not candidate_skills or not required_skills:
            return torch.empty((len(candidate_skills), len(required_skills)))

        # Batch encode both sets
        cand_embeddings = self.encode(candidate_skills)  # [N, 384]
        req_embeddings = self.encode(required_skills)    # [M, 384]

        # Cosine similarity matrix via matrix multiplication of L2-normalized vectors
        similarity_matrix = torch.matmul(cand_embeddings, req_embeddings.T)  # [N, M]
        return similarity_matrix


# Singleton instance loaded once at process startup
semantic_matcher = SemanticMatcher.get_instance()
