import time
import random
from datetime import datetime

# Try to import embedding dependencies with better error handling
EMBEDDINGS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    EMBEDDINGS_AVAILABLE = True
    print("Embeddings functionality available")
except (ImportError, ValueError) as e:
    print(f"Warning: Cannot use semantic embeddings: {e}")
    print("Running without semantic memory search capabilities.")


class MemorySystem:
    def __init__(self, embedding_model_name="all-MiniLM-L6-v2"):
        """Initialize the memory system with an embedding model for semantic search"""
        self.memories = []
        self.consolidated_memories = []
        self.insights = []
        self.memory_id_counter = 0
        self.embedding_model = None
        self.embeddings_enabled = False

        # Try to load embedding model if dependencies are available
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(embedding_model_name)
                print(f"Loaded embedding model: {embedding_model_name}")
                self.embeddings_enabled = True
            except Exception as e:
                print(f"Could not load embedding model: {e}")
                print("Running without semantic memory search")

    def add_memory(self, text, source="conversation", importance=None, metadata=None):
        """Add a regular memory to the system

        Args:
            text: The memory text content
            source: Source of the memory (conversation, dream, etc.)
            importance: Importance score (0-1). If None, it will be calculated.
            metadata: Additional metadata for the memory

        Returns:
            dict: The created memory object
        """
        # Create embedding for semantic search
        embedding = None
        if self.embeddings_enabled:
            try:
                embedding = self.embedding_model.encode(text)
            except Exception as e:
                print(f"Error creating embedding: {e}")

        # If importance not provided, calculate it
        if importance is None:
            importance = self._calculate_importance(text, source)

        # Generate a unique ID
        self.memory_id_counter += 1
        memory_id = self.memory_id_counter

        # Create memory entry
        memory = {
            "id": memory_id,
            "text": text,
            "source": source,
            "embedding": embedding,
            "timestamp": time.time(),
            "formatted_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "importance": importance,
            "metadata": metadata or {},
            "recall_count": 0,
            "processed": False  # Flag for dream processing
        }

        # Store in memories collection
        self.memories.append(memory)

        # Keep memory size manageable
        if len(self.memories) > 100:
            # Sort by recency and recall count (keep frequently accessed)
            self.memories.sort(key=lambda x: x["timestamp"] + (x["recall_count"] * 86400))
            # Keep most recent/important
            self.memories = self.memories[-100:]

        return memory

    def add_consolidated_memory(self, text, importance=0.7, metadata=None):
        """Add a consolidated memory created during dreaming

        Args:
            text: The consolidated memory text
            importance: Importance score (0-1)
            metadata: Additional metadata including original memory IDs

        Returns:
            dict: The created consolidated memory object
        """
        # Generate a unique ID
        self.memory_id_counter += 1
        memory_id = self.memory_id_counter

        # Create consolidated memory entry
        memory = {
            "id": memory_id,
            "text": text,
            "source": "consolidated",
            "timestamp": time.time(),
            "formatted_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "importance": importance,
            "metadata": metadata or {},
            "recall_count": 0
        }

        # Store in consolidated memories collection
        self.consolidated_memories.append(memory)

        # Keep memory size manageable
        if len(self.consolidated_memories) > 50:
            # Sort by importance (keep most important)
            self.consolidated_memories.sort(key=lambda x: x["importance"], reverse=True)
            # Keep most important
            self.consolidated_memories = self.consolidated_memories[-50:]

        return memory

    def add_insight(self, text, importance=0.8, metadata=None):
        """Add an insight generated during dreaming

        Args:
            text: The insight text
            importance: Importance/value score (0-1)
            metadata: Additional metadata

        Returns:
            dict: The created insight object
        """
        # Generate a unique ID
        self.memory_id_counter += 1
        memory_id = self.memory_id_counter

        # Create insight entry
        insight = {
            "id": memory_id,
            "text": text,
            "source": "insight",
            "timestamp": time.time(),
            "formatted_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "importance": importance,
            "metadata": metadata or {},
            "recall_count": 0
        }

        # Store in insights collection
        self.insights.append(insight)

        # Keep insights size manageable
        if len(self.insights) > 30:
            # Sort by importance (keep most important)
            self.insights.sort(key=lambda x: x["importance"], reverse=True)
            # Keep most important
            self.insights = self.insights[-30:]

        return insight

    def _calculate_importance(self, text, source):
        """Calculate the importance of a memory

        Args:
            text: Memory text
            source: Memory source

        Returns:
            float: Importance score (0-1)
        """
        # Simple heuristics for importance:
        # 1. Length - longer memories might contain more information
        # 2. Source - different sources have different baseline importance
        # 3. Similarity to existing important memories

        # Length factor (normalize between 0.2-0.5)
        length = len(text)
        length_factor = min(0.5, max(0.2, length / 500))

        # Source factor
        source_weights = {
            "conversation": 0.5,
            "insight": 0.8,
            "consolidated": 0.6,
            "generated": 0.4,
            "encounter": 0.4,
            "observation": 0.4,
            "conversation": 0.5,
            "learning": 0.6,
            "routine": 0.3
        }
        source_factor = source_weights.get(source, 0.4)

        # Similarity factor (if embeddings enabled)
        similarity_factor = 0.0
        if self.embeddings_enabled and self.memories:
            try:
                # Get embedding for this text
                new_embedding = self.embedding_model.encode(text)

                # Find similarity to most important existing memories
                important_memories = sorted(self.memories, key=lambda x: x.get("importance", 0), reverse=True)[:5]
                for memory in important_memories:
                    if memory.get("embedding") is not None:
                        similarity = cosine_similarity(
                            [new_embedding],
                            [memory["embedding"]]
                        )[0][0]
                        similarity_factor = max(similarity_factor, similarity * 0.3)
            except Exception as e:
                print(f"Error calculating memory similarity: {e}")

        # Combine factors with some randomness
        importance = (length_factor * 0.3 +
                      source_factor * 0.5 +
                      similarity_factor * 0.2 +
                      random.uniform(-0.1, 0.1))  # Add some randomness

        # Ensure it's in the 0-1 range
        return max(0.1, min(0.95, importance))

    def find_related_memories(self, text, threshold=0.6, max_results=3):
        """Find memories semantically related to the given text

        Args:
            text: Query text
            threshold: Minimum similarity threshold
            max_results: Maximum number of results to return

        Returns:
            list: Matching memories with similarity scores
        """
        if not self.embeddings_enabled or not self.memories:
            # Fall back to keyword matching if embeddings not available
            return self._find_related_by_keywords(text, max_results)

        # Create query embedding
        try:
            query_embedding = self.embedding_model.encode(text)

            # Compare with stored memories
            results = []
            for memory in self.memories:
                if memory["embedding"] is not None:
                    similarity = cosine_similarity(
                        [query_embedding],
                        [memory["embedding"]]
                    )[0][0]

                    if similarity >= threshold:
                        results.append((memory, similarity))

            # Sort by similarity
            results.sort(key=lambda x: x[1], reverse=True)

            # Update recall count for retrieved memories
            for memory, _ in results[:max_results]:
                memory["recall_count"] += 1

            return results[:max_results]

        except Exception as e:
            print(f"Error finding related memories: {e}")
            # Fall back to keyword matching if embeddings fail
            return self._find_related_by_keywords(text, max_results)

    def _find_related_by_keywords(self, text, max_results=3):
        """Simple keyword-based memory retrieval as fallback

        Args:
            text: Query text
            max_results: Maximum number of results to return

        Returns:
            list: Matching memories with similarity scores
        """
        if not self.memories:
            return []

        # Simple keyword matching as fallback
        words = set(text.lower().split())
        results = []

        for memory in self.memories:
            memory_words = set(memory["text"].lower().split())
            common_words = words.intersection(memory_words)

            if common_words:
                # Calculate a simple similarity based on word overlap
                similarity = len(common_words) / max(len(words), len(memory_words))
                if similarity > 0.1:  # Minimum threshold
                    results.append((memory, similarity))

        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)

        # Update recall count for retrieved memories
        for memory, _ in results[:max_results]:
            memory["recall_count"] += 1

        return results[:max_results]

    def find_similar_memories(self, similarity_threshold=0.65):
        """Find groups of similar memories for consolidation

        Returns:
            list: Lists of similar memories grouped together
        """
        if not self.memories or len(self.memories) < 2:
            return []

        # Method 1: Use embeddings if available
        if self.embeddings_enabled:
            try:
                # Extract embeddings for all memories
                memory_embeddings = []
                valid_memories = []

                for memory in self.memories:
                    if memory["embedding"] is not None and not memory.get("processed", False):
                        memory_embeddings.append(memory["embedding"])
                        valid_memories.append(memory)

                if not valid_memories:
                    return []

                # Calculate similarity matrix
                similarity_matrix = cosine_similarity(memory_embeddings)

                # Find groups of similar memories
                similar_groups = []
                processed_indices = set()

                for i in range(len(valid_memories)):
                    if i in processed_indices:
                        continue

                    group = [valid_memories[i]]
                    processed_indices.add(i)

                    for j in range(i + 1, len(valid_memories)):
                        if j in processed_indices:
                            continue

                        if similarity_matrix[i][j] >= similarity_threshold:
                            group.append(valid_memories[j])
                            processed_indices.add(j)

                    if len(group) > 1:
                        similar_groups.append(group)

                return similar_groups

            except Exception as e:
                print(f"Error finding similar memories with embeddings: {e}")
                # Fall back to metadata-based similarity

        # Method 2: Check metadata for similar_to relationships
        similar_groups = []
        processed_ids = set()

        for memory in self.memories:
            if memory.get("id") in processed_ids or memory.get("processed", False):
                continue

            metadata = memory.get("metadata", {})
            if "similar_to" in metadata:
                similar_to = metadata["similar_to"]

                # Find all memories with the same similar_to value
                group = [memory]
                processed_ids.add(memory.get("id"))

                for other_memory in self.memories:
                    if other_memory.get("id") in processed_ids or other_memory.get("processed", False):
                        continue

                    other_metadata = other_memory.get("metadata", {})
                    if "similar_to" in other_metadata and other_metadata["similar_to"] == similar_to:
                        group.append(other_memory)
                        processed_ids.add(other_memory.get("id"))

                if len(group) > 1:
                    similar_groups.append(group)

        # Method 3: Check for same event_type in metadata
        event_type_groups = {}

        for memory in self.memories:
            if memory.get("id") in processed_ids or memory.get("processed", False):
                continue

            metadata = memory.get("metadata", {})
            if "event_type" in metadata:
                event_type = metadata["event_type"]

                if event_type not in event_type_groups:
                    event_type_groups[event_type] = []

                event_type_groups[event_type].append(memory)
                processed_ids.add(memory.get("id"))

        # Add groups with more than one memory
        for event_type, group in event_type_groups.items():
            if len(group) > 1:
                similar_groups.append(group)

        return similar_groups

    def get_memories_by_importance(self, min_importance=None, max_importance=None, min_count=1, max_count=None):
        """Get memories filtered by importance

        Args:
            min_importance: Minimum importance (inclusive)
            max_importance: Maximum importance (inclusive)
            min_count: Minimum number of memories to return
            max_count: Maximum number of memories to return

        Returns:
            list: Filtered memories
        """
        filtered = []

        for memory in self.memories:
            importance = memory.get("importance", 0)

            if ((min_importance is None or importance >= min_importance) and
                    (max_importance is None or importance <= max_importance)):
                filtered.append(memory)

        # Sort by importance (highest first)
        filtered.sort(key=lambda x: x.get("importance", 0), reverse=True)

        # Apply count limits
        if max_count and len(filtered) > max_count:
            filtered = filtered[:max_count]

        # If we don't have enough memories, relax the importance criteria
        if min_count and len(filtered) < min_count:
            needed = min_count - len(filtered)
            remaining = [m for m in self.memories if m not in filtered]
            remaining.sort(key=lambda x: x.get("importance", 0), reverse=True)
            filtered.extend(remaining[:needed])

        return filtered

    def get_unprocessed_memories(self):
        """Get memories that haven't been processed by the dream system

        Returns:
            list: Unprocessed memories
        """
        return [m for m in self.memories if not m.get("processed", False)]

    def mark_memories_processed(self, memory_ids):
        """Mark memories as processed by the dream system

        Args:
            memory_ids: List of memory IDs to mark as processed
        """
        for memory in self.memories:
            if memory.get("id") in memory_ids:
                memory["processed"] = True

    def get_recent_memories(self, max_count=10):
        """Get the most recent memories

        Args:
            max_count: Maximum number of memories to return

        Returns:
            list: Recent memories
        """
        # Sort all memories by timestamp
        sorted_memories = sorted(self.memories, key=lambda x: x.get("timestamp", 0), reverse=True)

        # Return the requested number
        return sorted_memories[:max_count]

    def get_consolidated_memories(self, max_count=None):
        """Get consolidated memories

        Args:
            max_count: Maximum number of memories to return

        Returns:
            list: Consolidated memories
        """
        if max_count:
            return self.consolidated_memories[:max_count]
        return self.consolidated_memories

    def get_insights(self, max_count=None):
        """Get insights generated during dreaming

        Args:
            max_count: Maximum number of insights to return

        Returns:
            list: Insights
        """
        if max_count:
            return self.insights[:max_count]
        return self.insights

    def reset(self):
        """Reset the memory system"""
        self.memories = []
        self.consolidated_memories = []
        self.insights = []
        self.memory_id_counter = 0