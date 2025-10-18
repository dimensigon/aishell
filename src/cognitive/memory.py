"""
Cognitive Shell Memory (CogShell)
A persistent, searchable memory system that learns from every interaction
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
import numpy as np
import sqlite3
import pickle
import logging

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from ..llm.manager import LocalLLMManager
from ..vector.store import VectorDatabase

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry in the cognitive system"""
    id: str
    command: str
    output: str
    error: Optional[str]
    context: Dict[str, Any]
    timestamp: float
    success: bool
    duration: float
    tags: List[str] = field(default_factory=list)
    learned_patterns: List[str] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None
    frequency: int = 1
    last_accessed: float = field(default_factory=time.time)
    sentiment: float = 0.0  # -1 (negative) to 1 (positive)
    importance: float = 0.5  # 0 (low) to 1 (high)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        if self.embedding is not None:
            data['embedding'] = self.embedding.tolist()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary"""
        if 'embedding' in data and data['embedding']:
            data['embedding'] = np.array(data['embedding'])
        return cls(**data)


class PatternExtractor:
    """Extract patterns from command interactions"""

    def __init__(self):
        self.patterns = {
            'git_workflow': [
                r'git (add|commit|push|pull)',
                r'git (checkout|branch|merge)',
                r'git (status|log|diff)'
            ],
            'file_operations': [
                r'(ls|ll|dir)',
                r'(cp|mv|rm)',
                r'(find|grep|awk|sed)'
            ],
            'docker_operations': [
                r'docker (run|exec|ps)',
                r'docker (build|push|pull)',
                r'docker-compose'
            ],
            'debugging': [
                r'(gdb|lldb|pdb)',
                r'(strace|ltrace)',
                r'(top|htop|ps aux)'
            ],
            'network': [
                r'(ping|traceroute|nslookup)',
                r'(netstat|ss|lsof)',
                r'(curl|wget|nc)'
            ]
        }

    def extract(self, command: str, output: str) -> List[str]:
        """Extract learned patterns from command and output"""
        patterns = []

        # Check command patterns
        import re
        for category, regex_list in self.patterns.items():
            for regex in regex_list:
                if re.search(regex, command, re.IGNORECASE):
                    patterns.append(f"pattern:{category}")
                    break

        # Extract success/failure patterns
        if "error" in output.lower() or "failed" in output.lower():
            patterns.append("outcome:error")
        elif "success" in output.lower() or "complete" in output.lower():
            patterns.append("outcome:success")

        # Extract time patterns
        hour = datetime.now().hour
        if 0 <= hour < 6:
            patterns.append("time:late_night")
        elif 6 <= hour < 12:
            patterns.append("time:morning")
        elif 12 <= hour < 18:
            patterns.append("time:afternoon")
        else:
            patterns.append("time:evening")

        # Extract frequency patterns
        if len(command.split()) > 10:
            patterns.append("complexity:high")
        elif len(command.split()) > 5:
            patterns.append("complexity:medium")
        else:
            patterns.append("complexity:low")

        return patterns


class CognitiveMemory:
    """
    Cognitive Memory System for AI-Shell

    Features:
    - Semantic search across all command history
    - Automatic pattern recognition
    - Cross-session learning
    - Team knowledge base integration
    - Adaptive learning from user feedback
    """

    def __init__(self,
                 memory_dir: str = "~/.aishell/memory",
                 vector_dim: int = 384,
                 max_memories: int = 100000):

        self.memory_dir = Path(memory_dir).expanduser()
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.vector_dim = vector_dim
        self.max_memories = max_memories

        # Initialize components
        self.pattern_extractor = PatternExtractor()
        self.vector_store = VectorDatabase(dimension=vector_dim)
        self.llm_provider = None

        # Memory storage
        self.db_path = self.memory_dir / "cognitive_memory.db"
        self._init_database()

        # In-memory cache
        self.memory_cache: Dict[str, MemoryEntry] = {}
        self.pattern_stats: Dict[str, int] = {}

        # Learning parameters
        self.learning_rate = 0.1
        self.forgetting_factor = 0.95  # Memory decay over time

        # Load existing memories
        asyncio.create_task(self._load_memories())

    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                command TEXT NOT NULL,
                output TEXT,
                error TEXT,
                context TEXT,
                timestamp REAL,
                success INTEGER,
                duration REAL,
                tags TEXT,
                learned_patterns TEXT,
                embedding BLOB,
                frequency INTEGER DEFAULT 1,
                last_accessed REAL,
                sentiment REAL DEFAULT 0.0,
                importance REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp);
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_command ON memories(command);
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance);
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_stats (
                pattern TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                last_seen REAL,
                success_rate REAL DEFAULT 0.5
            )
        """)

        conn.commit()
        conn.close()

    async def _load_memories(self):
        """Load memories from database into vector store"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            # Load recent high-importance memories
            cursor.execute("""
                SELECT * FROM memories
                WHERE importance > 0.3
                ORDER BY timestamp DESC
                LIMIT 10000
            """)

            rows = cursor.fetchall()

            for row in rows:
                memory_dict = {
                    'id': row[0],
                    'command': row[1],
                    'output': row[2],
                    'error': row[3],
                    'context': json.loads(row[4]) if row[4] else {},
                    'timestamp': row[5],
                    'success': bool(row[6]),
                    'duration': row[7],
                    'tags': json.loads(row[8]) if row[8] else [],
                    'learned_patterns': json.loads(row[9]) if row[9] else [],
                    'embedding': pickle.loads(row[10]) if row[10] else None,
                    'frequency': row[11],
                    'last_accessed': row[12],
                    'sentiment': row[13],
                    'importance': row[14]
                }

                memory = MemoryEntry.from_dict(memory_dict)
                self.memory_cache[memory.id] = memory

                # Add to vector store
                if memory.embedding is not None:
                    await self.vector_store.add(
                        vector=memory.embedding,
                        metadata={'id': memory.id}
                    )

            logger.info(f"Loaded {len(rows)} memories into cognitive system")

        except Exception as e:
            logger.error(f"Error loading memories: {e}")
        finally:
            conn.close()

    async def remember(self,
                      command: str,
                      output: str,
                      error: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None,
                      duration: float = 0.0) -> MemoryEntry:
        """
        Store a new memory with semantic embedding and pattern extraction
        """

        # Generate unique ID
        memory_id = hashlib.md5(
            f"{command}{time.time()}".encode()
        ).hexdigest()

        # Extract patterns
        patterns = self.pattern_extractor.extract(command, output)

        # Calculate importance
        importance = self._calculate_importance(command, output, error, patterns)

        # Calculate sentiment
        sentiment = await self._analyze_sentiment(command, output, error)

        # Create embedding
        embedding = await self._create_embedding(command, output, context)

        # Create memory entry
        memory = MemoryEntry(
            id=memory_id,
            command=command,
            output=output[:5000],  # Truncate long outputs
            error=error,
            context=context or {},
            timestamp=time.time(),
            success=error is None,
            duration=duration,
            tags=self._extract_tags(command),
            learned_patterns=patterns,
            embedding=embedding,
            sentiment=sentiment,
            importance=importance
        )

        # Store in cache
        self.memory_cache[memory_id] = memory

        # Store in vector store
        if embedding is not None:
            await self.vector_store.add(
                vector=embedding,
                metadata={'id': memory_id}
            )

        # Persist to database
        await self._persist_memory(memory)

        # Update pattern statistics
        await self._update_pattern_stats(patterns, error is None)

        # Trigger learning if needed
        if len(self.memory_cache) % 100 == 0:
            asyncio.create_task(self._consolidate_learning())

        logger.debug(f"Remembered: {command[:50]}... (importance: {importance:.2f})")

        return memory

    async def recall(self,
                    query: str,
                    k: int = 5,
                    threshold: float = 0.7) -> List[MemoryEntry]:
        """
        Recall similar memories using semantic search
        """

        # Create query embedding
        query_embedding = await self._create_embedding(query, "", {})

        if query_embedding is None:
            # Fallback to text search
            return await self._text_search(query, k)

        # Search vector store
        results = await self.vector_store.search(
            query=query_embedding,
            k=k * 2,  # Get more candidates
            threshold=threshold
        )

        memories = []
        for result in results:
            memory_id = result['metadata']['id']

            if memory_id in self.memory_cache:
                memory = self.memory_cache[memory_id]
            else:
                # Load from database
                memory = await self._load_memory(memory_id)
                if memory:
                    self.memory_cache[memory_id] = memory

            if memory:
                # Update access statistics
                memory.last_accessed = time.time()
                memory.frequency += 1

                # Apply forgetting factor
                age = time.time() - memory.timestamp
                memory.importance *= self.forgetting_factor ** (age / 86400)  # Daily decay

                memories.append(memory)

        # Sort by relevance and importance
        memories.sort(key=lambda m: m.importance, reverse=True)

        return memories[:k]

    async def recall_by_pattern(self, pattern: str, k: int = 5) -> List[MemoryEntry]:
        """Recall memories that match a specific pattern"""

        matching_memories = []

        for memory in self.memory_cache.values():
            if pattern in memory.learned_patterns:
                matching_memories.append(memory)

        # Sort by recency and importance
        matching_memories.sort(
            key=lambda m: (m.importance, m.timestamp),
            reverse=True
        )

        return matching_memories[:k]

    async def get_command_suggestions(self,
                                     context: Dict[str, Any],
                                     k: int = 3) -> List[Tuple[str, float]]:
        """
        Get command suggestions based on current context and past patterns
        """

        suggestions = []

        # Get time-based patterns
        hour = datetime.now().hour
        time_pattern = "time:morning" if 6 <= hour < 12 else \
                      "time:afternoon" if 12 <= hour < 18 else \
                      "time:evening" if 18 <= hour < 24 else \
                      "time:late_night"

        # Find memories with similar time patterns
        time_memories = await self.recall_by_pattern(time_pattern, k=10)

        # Get current directory context
        if 'cwd' in context:
            cwd = context['cwd']
            # Find memories from same directory
            for memory in self.memory_cache.values():
                if memory.context.get('cwd') == cwd and memory.success:
                    score = memory.importance * memory.frequency / 100
                    suggestions.append((memory.command, score))

        # Get workflow patterns
        if 'last_command' in context:
            last_cmd = context['last_command']
            # Find commands that frequently follow
            following_commands = await self._find_following_commands(last_cmd)
            suggestions.extend(following_commands)

        # Sort by score and deduplicate
        seen = set()
        unique_suggestions = []
        for cmd, score in sorted(suggestions, key=lambda x: x[1], reverse=True):
            if cmd not in seen:
                seen.add(cmd)
                unique_suggestions.append((cmd, score))

        return unique_suggestions[:k]

    async def learn_from_feedback(self,
                                 memory_id: str,
                                 positive: bool,
                                 feedback: Optional[str] = None):
        """
        Update memory importance based on user feedback
        """

        if memory_id not in self.memory_cache:
            memory = await self._load_memory(memory_id)
            if not memory:
                return
        else:
            memory = self.memory_cache[memory_id]

        # Update importance
        if positive:
            memory.importance = min(1.0, memory.importance * (1 + self.learning_rate))
            memory.sentiment = min(1.0, memory.sentiment + 0.1)
        else:
            memory.importance = max(0.0, memory.importance * (1 - self.learning_rate))
            memory.sentiment = max(-1.0, memory.sentiment - 0.1)

        # Store feedback
        if feedback:
            if 'feedback' not in memory.context:
                memory.context['feedback'] = []
            memory.context['feedback'].append({
                'text': feedback,
                'positive': positive,
                'timestamp': time.time()
            })

        # Update patterns success rate
        for pattern in memory.learned_patterns:
            await self._update_pattern_success(pattern, positive)

        # Persist changes
        await self._persist_memory(memory)

        logger.info(f"Learned from feedback on {memory.command[:50]}...")

    async def get_insights(self) -> Dict[str, Any]:
        """
        Generate insights from memory patterns
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        insights = {}

        try:
            # Most used commands
            cursor.execute("""
                SELECT command, SUM(frequency) as total
                FROM memories
                GROUP BY command
                ORDER BY total DESC
                LIMIT 10
            """)
            insights['most_used_commands'] = cursor.fetchall()

            # Error patterns
            cursor.execute("""
                SELECT command, COUNT(*) as errors
                FROM memories
                WHERE success = 0
                GROUP BY command
                ORDER BY errors DESC
                LIMIT 5
            """)
            insights['common_errors'] = cursor.fetchall()

            # Time patterns
            cursor.execute("""
                SELECT
                    CAST(timestamp / 3600 AS INTEGER) % 24 as hour,
                    COUNT(*) as count
                FROM memories
                GROUP BY hour
                ORDER BY hour
            """)
            insights['hourly_activity'] = cursor.fetchall()

            # Success rate
            cursor.execute("""
                SELECT
                    COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*) as success_rate
                FROM memories
            """)
            insights['overall_success_rate'] = cursor.fetchone()[0]

            # Pattern statistics
            cursor.execute("""
                SELECT pattern, count, success_rate
                FROM pattern_stats
                ORDER BY count DESC
                LIMIT 10
            """)
            insights['top_patterns'] = cursor.fetchall()

        finally:
            conn.close()

        # Memory statistics
        insights['total_memories'] = len(self.memory_cache)
        insights['avg_importance'] = np.mean([m.importance for m in self.memory_cache.values()])
        insights['avg_sentiment'] = np.mean([m.sentiment for m in self.memory_cache.values()])

        return insights

    async def export_knowledge(self, output_path: str):
        """Export knowledge base for sharing or backup"""

        knowledge = {
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'memories': [],
            'patterns': {},
            'insights': await self.get_insights()
        }

        # Export high-importance memories
        for memory in self.memory_cache.values():
            if memory.importance > 0.5:
                knowledge['memories'].append(memory.to_dict())

        # Export pattern statistics
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pattern_stats")
        knowledge['patterns'] = cursor.fetchall()
        conn.close()

        # Save to file
        output = Path(output_path)
        output.write_text(json.dumps(knowledge, indent=2, default=str))

        logger.info(f"Exported knowledge to {output_path}")

    async def import_knowledge(self, input_path: str):
        """Import knowledge from another instance"""

        knowledge = json.loads(Path(input_path).read_text())

        imported_count = 0
        for memory_dict in knowledge['memories']:
            memory = MemoryEntry.from_dict(memory_dict)

            # Check if not duplicate
            if memory.id not in self.memory_cache:
                self.memory_cache[memory.id] = memory
                await self._persist_memory(memory)

                if memory.embedding is not None:
                    await self.vector_store.add(
                        vector=memory.embedding,
                        metadata={'id': memory.id}
                    )

                imported_count += 1

        logger.info(f"Imported {imported_count} memories from {input_path}")

    # Helper methods

    async def _create_embedding(self, text: str, output: str, context: Dict) -> Optional[np.ndarray]:
        """Create semantic embedding for memory"""

        if not self.llm_provider:
            try:
                self.llm_provider = LocalLLMManager()
                self.llm_provider.initialize(provider_type='ollama', model_name='llama2')
            except:
                return None

        try:
            combined_text = f"{text}\n{output[:500]}\n{json.dumps(context, default=str)[:200]}"

            # Get embedding from LLM (if provider supports it)
            if hasattr(self.llm_provider.provider, 'get_embedding'):
                response = await self.llm_provider.provider.get_embedding(combined_text)
            else:
                # Fallback to hash-based embedding
                return None

            if response and len(response) == self.vector_dim:
                return np.array(response, dtype=np.float32)

        except Exception as e:
            logger.debug(f"Failed to create embedding: {e}")

        # Fallback to simple hash-based embedding
        return self._create_hash_embedding(text)

    def _create_hash_embedding(self, text: str) -> np.ndarray:
        """Create a simple hash-based embedding"""

        # Simple but deterministic embedding
        hash_val = hashlib.md5(text.encode()).hexdigest()

        # Convert to vector
        embedding = np.zeros(self.vector_dim, dtype=np.float32)
        for i, char in enumerate(hash_val):
            if i >= self.vector_dim:
                break
            embedding[i] = ord(char) / 255.0

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding /= norm

        return embedding

    def _calculate_importance(self, command: str, output: str, error: Optional[str], patterns: List[str]) -> float:
        """Calculate memory importance score"""

        importance = 0.5  # Base importance

        # Error commands are important to remember
        if error:
            importance += 0.2

        # Complex commands are more important
        if len(command.split()) > 5:
            importance += 0.1

        # Commands with many patterns are important
        importance += len(patterns) * 0.05

        # Long outputs might be important
        if len(output) > 1000:
            importance += 0.1

        return min(1.0, importance)

    async def _analyze_sentiment(self, command: str, output: str, error: Optional[str]) -> float:
        """Analyze sentiment of the interaction"""

        if error:
            return -0.5  # Errors are negative

        # Success indicators
        positive_words = ['success', 'complete', 'done', 'created', 'updated']
        negative_words = ['error', 'failed', 'denied', 'invalid', 'missing']

        output_lower = output.lower()

        positive_count = sum(1 for word in positive_words if word in output_lower)
        negative_count = sum(1 for word in negative_words if word in output_lower)

        if positive_count > negative_count:
            return min(1.0, positive_count * 0.2)
        elif negative_count > positive_count:
            return max(-1.0, -negative_count * 0.2)

        return 0.0

    def _extract_tags(self, command: str) -> List[str]:
        """Extract tags from command"""

        tags = []

        # Extract command name
        parts = command.split()
        if parts:
            tags.append(f"cmd:{parts[0]}")

        # Extract file extensions
        import re
        extensions = re.findall(r'\.\w+', command)
        for ext in extensions:
            tags.append(f"ext:{ext}")

        # Extract flags
        flags = re.findall(r'-\w+', command)
        for flag in flags[:5]:  # Limit flags
            tags.append(f"flag:{flag}")

        return tags

    async def _persist_memory(self, memory: MemoryEntry):
        """Persist memory to database"""

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO memories (
                    id, command, output, error, context, timestamp,
                    success, duration, tags, learned_patterns, embedding,
                    frequency, last_accessed, sentiment, importance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.command,
                memory.output,
                memory.error,
                json.dumps(memory.context),
                memory.timestamp,
                int(memory.success),
                memory.duration,
                json.dumps(memory.tags),
                json.dumps(memory.learned_patterns),
                pickle.dumps(memory.embedding) if memory.embedding is not None else None,
                memory.frequency,
                memory.last_accessed,
                memory.sentiment,
                memory.importance
            ))

            conn.commit()

        except Exception as e:
            logger.error(f"Error persisting memory: {e}")
        finally:
            conn.close()

    async def _load_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Load memory from database"""

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()

            if row:
                memory_dict = {
                    'id': row[0],
                    'command': row[1],
                    'output': row[2],
                    'error': row[3],
                    'context': json.loads(row[4]) if row[4] else {},
                    'timestamp': row[5],
                    'success': bool(row[6]),
                    'duration': row[7],
                    'tags': json.loads(row[8]) if row[8] else [],
                    'learned_patterns': json.loads(row[9]) if row[9] else [],
                    'embedding': pickle.loads(row[10]) if row[10] else None,
                    'frequency': row[11],
                    'last_accessed': row[12],
                    'sentiment': row[13],
                    'importance': row[14]
                }

                return MemoryEntry.from_dict(memory_dict)

        except Exception as e:
            logger.error(f"Error loading memory: {e}")
        finally:
            conn.close()

        return None

    async def _text_search(self, query: str, k: int) -> List[MemoryEntry]:
        """Fallback text search when embeddings not available"""

        results = []
        query_lower = query.lower()

        for memory in self.memory_cache.values():
            if query_lower in memory.command.lower():
                results.append(memory)

        results.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)

        return results[:k]

    async def _update_pattern_stats(self, patterns: List[str], success: bool):
        """Update pattern statistics"""

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            for pattern in patterns:
                cursor.execute("""
                    INSERT INTO pattern_stats (pattern, count, last_seen, success_rate)
                    VALUES (?, 1, ?, ?)
                    ON CONFLICT(pattern) DO UPDATE SET
                        count = count + 1,
                        last_seen = ?,
                        success_rate = (success_rate * count + ?) / (count + 1)
                """, (pattern, time.time(), 1.0 if success else 0.0, time.time(), 1.0 if success else 0.0))

            conn.commit()

        except Exception as e:
            logger.error(f"Error updating pattern stats: {e}")
        finally:
            conn.close()

    async def _update_pattern_success(self, pattern: str, success: bool):
        """Update pattern success rate"""

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE pattern_stats
                SET success_rate = (success_rate * count + ?) / (count + 1)
                WHERE pattern = ?
            """, (1.0 if success else 0.0, pattern))

            conn.commit()

        except Exception as e:
            logger.error(f"Error updating pattern success: {e}")
        finally:
            conn.close()

    async def _find_following_commands(self, command: str, k: int = 3) -> List[Tuple[str, float]]:
        """Find commands that frequently follow the given command"""

        following = []

        # Find memories with this command
        for memory in self.memory_cache.values():
            if memory.command == command:
                # Look for next command in same session
                next_memories = [
                    m for m in self.memory_cache.values()
                    if m.timestamp > memory.timestamp
                    and m.timestamp < memory.timestamp + 300  # Within 5 minutes
                    and m.context.get('session') == memory.context.get('session')
                ]

                for next_mem in next_memories:
                    score = next_mem.importance * (1.0 if next_mem.success else 0.5)
                    following.append((next_mem.command, score))

        # Aggregate and sort
        command_scores = {}
        for cmd, score in following:
            if cmd not in command_scores:
                command_scores[cmd] = []
            command_scores[cmd].append(score)

        results = [
            (cmd, np.mean(scores))
            for cmd, scores in command_scores.items()
        ]

        results.sort(key=lambda x: x[1], reverse=True)

        return results[:k]

    async def _consolidate_learning(self):
        """Consolidate learning from recent memories"""

        logger.info("Consolidating learning from memories...")

        # Prune old, low-importance memories
        if len(self.memory_cache) > self.max_memories:
            sorted_memories = sorted(
                self.memory_cache.values(),
                key=lambda m: (m.importance, m.timestamp)
            )

            to_remove = sorted_memories[:len(self.memory_cache) - self.max_memories]

            for memory in to_remove:
                if memory.importance < 0.3:  # Only remove low importance
                    del self.memory_cache[memory.id]

        # Update pattern relationships
        # This could involve more sophisticated ML in the future

        logger.info(f"Consolidated to {len(self.memory_cache)} memories")