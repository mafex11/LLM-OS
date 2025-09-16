"""
Memory management system for storing and retrieving successful task solutions
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
import re

@dataclass
class TaskMemory:
    """Represents a stored task solution"""
    query_pattern: str  # Pattern to match similar queries
    solution_steps: List[Dict[str, Any]]  # List of actions that solved the task
    success_count: int = 1  # Number of times this solution worked
    last_used: str = None  # Last time this solution was used
    created_at: str = None  # When this memory was created
    tags: List[str] = None  # Tags for categorization
    
    def __post_init__(self):
        if self.last_used is None:
            self.last_used = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []

class MemoryManager:
    """Manages persistent task memories"""
    
    def __init__(self, memory_file: str = "agent_memories.json"):
        self.memory_file = Path(memory_file)
        self.memories: Dict[str, TaskMemory] = {}
        self.load_memories()
    
    def load_memories(self):
        """Load memories from file"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, memory_data in data.items():
                        self.memories[key] = TaskMemory(**memory_data)
            except Exception as e:
                print(f"Error loading memories: {e}")
                self.memories = {}
    
    def save_memories(self):
        """Save memories to file"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                data = {key: asdict(memory) for key, memory in self.memories.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving memories: {e}")
    
    def generate_key(self, query: str) -> str:
        """Generate a unique key for a query"""
        # Normalize query: lowercase, remove extra spaces, remove punctuation
        normalized = re.sub(r'[^\w\s]', '', query.lower().strip())
        normalized = re.sub(r'\s+', ' ', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def find_similar_memory(self, query: str) -> Optional[TaskMemory]:
        """Find a similar memory for the given query"""
        query_lower = query.lower()
        
        # First try exact key match
        key = self.generate_key(query)
        if key in self.memories:
            return self.memories[key]
        
        # Then try pattern matching
        for memory in self.memories.values():
            if self._is_similar_query(query_lower, memory.query_pattern.lower()):
                return memory
        
        return None
    
    def _is_similar_query(self, query: str, pattern: str) -> bool:
        """Check if query is similar to pattern"""
        # Extract key words from both
        query_words = set(re.findall(r'\b\w+\b', query))
        pattern_words = set(re.findall(r'\b\w+\b', pattern))
        
        # Calculate similarity based on common words
        if not query_words or not pattern_words:
            return False
        
        common_words = query_words.intersection(pattern_words)
        similarity = len(common_words) / max(len(query_words), len(pattern_words))
        
        # Consider similar if more than 60% of words match
        return similarity > 0.6
    
    def add_memory(self, query: str, solution_steps: List[Dict[str, Any]], tags: List[str] = None) -> str:
        """Add a new memory or update existing one"""
        key = self.generate_key(query)
        
        if key in self.memories:
            # Update existing memory
            memory = self.memories[key]
            memory.success_count += 1
            memory.last_used = datetime.now().isoformat()
            # Update solution steps if they're different
            if solution_steps != memory.solution_steps:
                memory.solution_steps = solution_steps
        else:
            # Create new memory
            memory = TaskMemory(
                query_pattern=query,
                solution_steps=solution_steps,
                tags=tags or []
            )
            self.memories[key] = memory
        
        self.save_memories()
        return key
    
    def get_memory_solution(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get solution steps for a query"""
        memory = self.find_similar_memory(query)
        if memory:
            memory.last_used = datetime.now().isoformat()
            self.save_memories()
            return memory.solution_steps
        return None
    
    def list_memories(self) -> List[Dict[str, Any]]:
        """List all memories"""
        return [
            {
                'key': key,
                'query': memory.query_pattern,
                'success_count': memory.success_count,
                'last_used': memory.last_used,
                'created_at': memory.created_at,
                'tags': memory.tags
            }
            for key, memory in self.memories.items()
        ]
    
    def delete_memory(self, key: str) -> bool:
        """Delete a memory by key"""
        if key in self.memories:
            del self.memories[key]
            self.save_memories()
            return True
        return False
    
    def clear_memories(self):
        """Clear all memories"""
        self.memories.clear()
        self.save_memories()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        if not self.memories:
            return {'total_memories': 0, 'total_successes': 0}
        
        total_successes = sum(memory.success_count for memory in self.memories.values())
        return {
            'total_memories': len(self.memories),
            'total_successes': total_successes,
            'average_successes': total_successes / len(self.memories)
        }
