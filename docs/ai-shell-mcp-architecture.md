# AI-Shell MCP Architecture & Implementation Plan

## Executive Summary

AI-Shell represents a paradigm shift in CLI-based system administration, leveraging Model Context Protocol (MCP) clients, local LLMs, and asynchronous processing to create an intelligent, context-aware terminal experience. The architecture prioritizes security, performance, and user experience through modular design patterns and reactive UI components.

## Core Architecture Components

### 1. Foundation Layer

```python
# Core application structure using prompt-toolkit
from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app
import asyncio
from threading import Thread, Lock
from queue import Queue
import click

class AIShellCore:
    """
    Central orchestrator managing module lifecycle, MCP clients, and UI state.
    """
    def __init__(self):
        self.modules = {}
        self.mcp_clients = {}
        self.llm_manager = LocalLLMManager()
        self.ui_manager = UIManager()
        self.event_bus = AsyncEventBus()
        self.vector_store = VectorDatabase()
        
    async def initialize(self):
        """Matrix-style initialization with system checks"""
        await self.llm_manager.check_models()
        await self.initialize_mcp_clients()
        await self.vector_store.load_system_objects()
```

### 2. MCP Client Architecture

```python
# MCP Client Base Pattern
from typing import Protocol, Dict, Any
import cx_Oracle
import psycopg2
from psycopg2.extras import RealDictCursor

class MCPClient(Protocol):
    """Protocol definition for MCP database clients"""
    
    async def connect(self, credentials: Dict[str, Any]) -> None:
        """Establish database connection using thin client"""
        ...
    
    async def query_user_objects(self) -> Dict[str, Any]:
        """Retrieve user-defined database objects"""
        ...
    
    async def execute_statement(self, sql: str, params: tuple = None) -> Any:
        """Execute SQL with parameter binding"""
        ...

class OracleMCPClient:
    """Oracle MCP implementation using cx_Oracle thin mode"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    async def connect(self, credentials: Dict[str, Any]) -> None:
        # Use thin mode - no Oracle client required
        cx_Oracle.init_oracle_client(lib_dir=None)
        dsn = cx_Oracle.makedsn(
            credentials['host'], 
            credentials['port'], 
            service_name=credentials['service']
        )
        self.connection = await asyncio.get_event_loop().run_in_executor(
            None, 
            cx_Oracle.connect,
            credentials['user'],
            credentials['password'],
            dsn
        )

class PostgreSQLMCPClient:
    """PostgreSQL MCP implementation using psycopg2"""
    
    async def connect(self, credentials: Dict[str, Any]) -> None:
        self.connection = await asyncio.get_event_loop().run_in_executor(
            None,
            psycopg2.connect,
            dbname=credentials['database'],
            user=credentials['user'],
            password=credentials['password'],
            host=credentials['host'],
            port=credentials['port'],
            cursor_factory=RealDictCursor
        )
```

## Phase 1: Core Infrastructure & Local LLM Integration

### Technical Implementation

#### 1.1 Local LLM Manager

```python
import ollama
from transformers import pipeline
import torch
from sentence_transformers import SentenceTransformer

class LocalLLMManager:
    """
    Manages local LLM instances for intent analysis and pseudo-anonymization
    """
    def __init__(self):
        self.models = {
            'intent': None,      # Lightweight model for intent classification
            'completion': None,  # Code/command completion model
            'anonymizer': None   # Data sanitization model
        }
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.anonymization_map = {}
        
    async def analyze_intent(self, user_input: str, context: Dict) -> Dict:
        """
        Asynchronously analyze user intent for module panel enrichment
        """
        embeddings = self.embedding_model.encode(user_input)
        
        # Vector similarity search for command patterns
        similar_commands = await self.vector_store.search(embeddings, k=5)
        
        intent_result = await self._run_inference(
            self.models['intent'],
            prompt=self._build_intent_prompt(user_input, context, similar_commands)
        )
        
        return {
            'primary_intent': intent_result['intent'],
            'confidence': intent_result['confidence'],
            'suggested_commands': similar_commands,
            'context_enrichment': intent_result['context']
        }
    
    def pseudo_anonymize(self, text: str) -> tuple[str, Dict]:
        """
        Replace sensitive data with tokens, maintaining mapping for response translation
        """
        import re
        
        patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'ip': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'username': r'(?:user|username|login)[:=]\s*([^\s,]+)',
            'server': r'(?:server|host)[:=]\s*([^\s,]+)',
        }
        
        anonymized = text
        mapping = {}
        
        for data_type, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                token = f"<{data_type.upper()}_{len(mapping)}>"
                mapping[token] = match.group(0)
                anonymized = anonymized.replace(match.group(0), token)
                
        return anonymized, mapping
```

#### 1.2 Dynamic Panel System

```python
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout import ConditionalContainer, Window
from prompt_toolkit.filters import Condition

class DynamicPanelManager:
    """
    Manages flexible panel sizing with content-aware priority
    """
    def __init__(self):
        self.panel_weights = {
            'output': 0.5,
            'module': 0.3,
            'prompt': 0.2
        }
        self.active_typing = False
        self.content_sizes = {}
        
    def calculate_dimensions(self, terminal_height: int) -> Dict[str, Dimension]:
        """
        Dynamically calculate panel dimensions based on content and user activity
        """
        if self.active_typing:
            # Prioritize prompt when user is typing
            prompt_lines = self._calculate_prompt_lines()
            prompt_height = min(prompt_lines + 2, terminal_height // 2)
            
            remaining = terminal_height - prompt_height
            output_height = int(remaining * 0.7)
            module_height = remaining - output_height
        else:
            # Balance based on content
            output_content = self.content_sizes.get('output', 10)
            module_content = self.content_sizes.get('module', 5)
            
            total_content = output_content + module_content + 3  # +3 for prompt
            
            if total_content <= terminal_height:
                # All content fits
                return {
                    'output': Dimension(min=output_content),
                    'module': Dimension(min=module_content),
                    'prompt': Dimension(min=3)
                }
            else:
                # Apply weighted distribution
                output_height = int(terminal_height * self.panel_weights['output'])
                module_height = int(terminal_height * self.panel_weights['module'])
                prompt_height = terminal_height - output_height - module_height
                
        return {
            'output': Dimension(min=output_height, max=output_height),
            'module': Dimension(min=module_height, max=module_height),
            'prompt': Dimension(min=prompt_height)
        }
```

## Phase 2: MCP Integration & Asynchronous Processing

### Technical Implementation

#### 2.1 Asynchronous Module Panel Enrichment

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator

class ModulePanelEnricher:
    """
    Asynchronously enriches module panel with contextual information
    """
    def __init__(self, llm_manager: LocalLLMManager):
        self.llm_manager = llm_manager
        self.update_queue = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def enrich_continuously(self):
        """
        Background task continuously processing enrichment requests
        """
        while True:
            try:
                context = await self.update_queue.get()
                
                # Analyze intent asynchronously
                intent_analysis = await self.llm_manager.analyze_intent(
                    context['user_input'],
                    context['system_state']
                )
                
                # Gather system information via MCP
                system_info = await self._gather_system_context(intent_analysis)
                
                # Update module panel without blocking prompt
                await self._update_panel(system_info, intent_analysis)
                
            except Exception as e:
                logger.error(f"Enrichment error: {e}")
                
    async def _gather_system_context(self, intent: Dict) -> Dict:
        """
        Use MCP shell commands to gather relevant system information
        """
        commands = self._determine_relevant_commands(intent)
        results = {}
        
        for cmd in commands:
            if cmd.requires_sudo:
                result = await self._execute_sudo_command(cmd)
            else:
                result = await self._execute_command(cmd)
            results[cmd.name] = result
            
        return results
```

#### 2.2 Vector Database for System Objects

```python
import faiss
import numpy as np
import pickle
from pathlib import Path

class VectorDatabase:
    """
    FAISS-based vector store for system objects and command patterns
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []
        self.system_objects_loaded = False
        
    async def load_system_objects(self):
        """
        Pre-load system database objects for instant access
        """
        system_catalogs = {
            'oracle': [
                'SELECT object_name, object_type FROM all_objects WHERE owner = "SYS"',
                'SELECT table_name, column_name FROM all_tab_columns WHERE owner = "SYS"'
            ],
            'postgresql': [
                'SELECT * FROM information_schema.tables WHERE table_schema = "pg_catalog"',
                'SELECT * FROM information_schema.columns WHERE table_schema = "pg_catalog"'
            ]
        }
        
        for db_type, queries in system_catalogs.items():
            objects = await self._fetch_catalog_objects(db_type, queries)
            embeddings = self._generate_embeddings(objects)
            
            self.index.add(embeddings)
            self.metadata.extend(objects)
            
        self.system_objects_loaded = True
        
    async def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """
        Semantic search for similar commands or objects
        """
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1), 
            k
        )
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.metadata):
                results.append({
                    'object': self.metadata[idx],
                    'similarity': 1 / (1 + distance)
                })
                
        return results
```

## Phase 3: Advanced Features & Security

### Technical Implementation

#### 3.1 Command Auto-completion with Data Dictionary

```python
from prompt_toolkit.completion import Completer, Completion
from typing import Iterable

class IntelligentCompleter(Completer):
    """
    Context-aware auto-completion using local LLM and data dictionary
    """
    def __init__(self, vector_db: VectorDatabase, llm_manager: LocalLLMManager):
        self.vector_db = vector_db
        self.llm_manager = llm_manager
        self.data_dictionary = {}
        self.command_cache = LRUCache(maxsize=1000)
        
    def get_completions(self, document, complete_event) -> Iterable[Completion]:
        """
        Generate intelligent completions based on context
        """
        text_before_cursor = document.text_before_cursor
        
        # Check if in SQL context
        if self._is_sql_context(text_before_cursor):
            yield from self._sql_completions(text_before_cursor)
        
        # Check if accessing vault
        elif '$vault.' in text_before_cursor:
            yield from self._vault_completions(text_before_cursor)
        
        # Standard command completion
        else:
            # Use LLM for intent prediction
            context = asyncio.run(
                self.llm_manager.analyze_intent(
                    text_before_cursor,
                    self._get_current_context()
                )
            )
            
            # Vector search for similar commands
            embeddings = self.llm_manager.embedding_model.encode(text_before_cursor)
            similar = asyncio.run(self.vector_db.search(embeddings, k=10))
            
            for item in similar:
                yield Completion(
                    item['object']['name'],
                    start_position=-len(text_before_cursor.split()[-1]),
                    display_meta=item['object'].get('description', '')
                )
```

#### 3.2 Secure Credential Management

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import keyring
import json

class SecureVault:
    """
    Encrypted credential storage with automatic redaction
    """
    def __init__(self):
        self.cipher = self._initialize_cipher()
        self.credentials = {}
        self.redaction_patterns = []
        
    def store_credential(self, name: str, value: Any, type: str = 'standard'):
        """
        Store encrypted credential with type metadata
        """
        if type == 'database':
            self._validate_database_credential(value)
            
        encrypted = self.cipher.encrypt(json.dumps(value).encode())
        self.credentials[name] = {
            'data': encrypted,
            'type': type,
            'created': datetime.now().isoformat()
        }
        
        # Add to redaction patterns
        self._update_redaction_patterns(name, value)
        
    def retrieve_credential(self, name: str, anonymize: bool = False) -> Any:
        """
        Retrieve credential with optional anonymization for AI calls
        """
        if name not in self.credentials:
            raise KeyError(f"Credential {name} not found")
            
        encrypted = self.credentials[name]['data']
        decrypted = json.loads(self.cipher.decrypt(encrypted))
        
        if anonymize:
            # For external AI calls
            return self._create_anonymized_token(name)
        
        return decrypted
        
    def auto_redact(self, text: str) -> str:
        """
        Automatically redact sensitive data from logs and history
        """
        redacted = text
        for pattern in self.redaction_patterns:
            redacted = redacted.replace(pattern['value'], f"***{pattern['name']}***")
            
        return redacted
```

## Phase 4: Database Module Integration

### Technical Implementation

#### 4.1 Unified Database Interface

```python
class DatabaseModule:
    """
    Unified interface for multiple database engines via MCP
    """
    def __init__(self):
        self.connections = {}
        self.risk_analyzer = SQLRiskAnalyzer()
        self.performance_monitor = PerformanceMonitor()
        
    async def execute_sql(self, sql: str, connection_name: str = 'default'):
        """
        Execute SQL with comprehensive analysis and monitoring
        """
        # Risk assessment
        risk_level = await self.risk_analyzer.analyze(sql)
        
        if risk_level > RiskLevel.MEDIUM:
            # Get AI recommendation
            recommendation = await self._get_ai_recommendation(sql, risk_level)
            
            # Update module panel with warning
            await self.update_module_panel({
                'risk': risk_level,
                'recommendation': recommendation,
                'affected_rows_estimate': self._estimate_impact(sql)
            })
            
            # Require confirmation
            if not await self._get_user_confirmation(risk_level):
                return None
                
        # Execute with monitoring
        start_time = time.perf_counter()
        
        try:
            result = await self.connections[connection_name].execute_statement(sql)
            execution_time = time.perf_counter() - start_time
            
            # Log to SQL history
            await self._log_execution(sql, result, execution_time, risk_level)
            
            # Update performance metrics
            self.performance_monitor.record(sql, execution_time, result.rowcount)
            
            return result
            
        except Exception as e:
            # AI-powered error analysis
            error_analysis = await self._analyze_error(sql, str(e))
            await self.update_module_panel({'error': error_analysis})
            raise
```

#### 4.2 Natural Language to SQL

```python
class NLPToSQL:
    """
    Convert natural language to SQL using local LLM and schema awareness
    """
    def __init__(self, schema_manager: SchemaManager):
        self.schema_manager = schema_manager
        self.llm = None  # Local LLM instance
        
    async def translate(self, natural_query: str, database_type: str) -> str:
        """
        Translate natural language to optimized SQL
        """
        # Get relevant schema context
        schema_context = await self.schema_manager.get_relevant_tables(natural_query)
        
        # Build prompt with schema awareness
        prompt = self._build_translation_prompt(
            natural_query,
            schema_context,
            database_type
        )
        
        # Generate SQL
        sql = await self.llm.generate(prompt)
        
        # Validate and optimize
        validated_sql = await self._validate_sql(sql, schema_context)
        optimized_sql = await self._optimize_sql(validated_sql, database_type)
        
        return optimized_sql
```

## Phase 5: Production Deployment

### Performance Optimization

```python
# Asynchronous event processing
class AsyncEventBus:
    """
    High-performance event bus for module communication
    """
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.event_queue = asyncio.Queue()
        self.processing = True
        
    async def process_events(self):
        """
        Continuous event processing with backpressure handling
        """
        while self.processing:
            event = await self.event_queue.get()
            
            # Process in parallel
            tasks = [
                subscriber(event) 
                for subscriber in self.subscribers[event.type]
            ]
            
            # Fire and forget for non-critical events
            if not event.critical:
                asyncio.create_task(asyncio.gather(*tasks))
            else:
                await asyncio.gather(*tasks)
```

### Monitoring & Health Checks

```python
class SystemMonitor:
    """
    Comprehensive system health monitoring
    """
    def __init__(self):
        self.metrics = {
            'llm_latency': [],
            'db_query_time': [],
            'ui_responsiveness': [],
            'memory_usage': []
        }
        
    async def health_check(self) -> Dict:
        """
        Perform comprehensive health check
        """
        checks = {
            'llm_models': await self._check_llm_availability(),
            'mcp_clients': await self._check_mcp_connections(),
            'vector_db': self._check_vector_db_status(),
            'memory': self._check_memory_usage(),
            'response_time': self._check_response_times()
        }
        
        return {
            'status': 'healthy' if all(checks.values()) else 'degraded',
            'checks': checks,
            'metrics': self._calculate_metrics()
        }
```

## Implementation Timeline

| Phase | Duration | Key Deliverables |
|-------|----------|-----------------|
| **Phase 1** | 3 weeks | Core CLI with prompt-toolkit, Local LLM integration, Dynamic panel system |
| **Phase 2** | 2 weeks | MCP Oracle/PostgreSQL clients, Asynchronous enrichment, Vector database |
| **Phase 3** | 2 weeks | Intelligent auto-completion, Secure vault, Pseudo-anonymization |
| **Phase 4** | 3 weeks | Unified database interface, NLP to SQL, Risk analysis |
| **Phase 5** | 2 weeks | Performance optimization, Production hardening, Monitoring |

## Critical Technical Decisions

### 1. Database Connectivity
- **cx_Oracle in thin mode**: Eliminates Oracle client dependency
- **psycopg2 with async wrapper**: Pure Python PostgreSQL access
- **Connection pooling**: Maintain persistent connections for performance

### 2. Local LLM Strategy
- **Ollama for flexibility**: Supports multiple model formats
- **Specialized models**: Separate models for intent, completion, anonymization
- **FAISS for vector search**: Efficient similarity matching

### 3. UI Architecture
- **Textual as primary framework**: Modern, async-native TUI library
- **prompt-toolkit for input handling**: Superior completion and key binding support
- **Click for CLI arguments**: Industry-standard command-line parsing

### 4. Security Considerations
- **Keyring integration**: OS-level credential protection
- **Automatic redaction**: Pattern-based sensitive data removal
- **Local LLM for sensitive operations**: No external API exposure

### 5. Performance Optimization
- **Async-first design**: Non-blocking operations throughout
- **Worker thread pools**: CPU-bound operations isolated
- **LRU caching**: Frequently accessed data in memory
- **Lazy loading**: Deferred initialization for faster startup

## Testing Strategy

```python
# Comprehensive test coverage
class AIShellTestSuite:
    """
    End-to-end testing framework
    """
    async def test_mcp_connection_resilience(self):
        """Test MCP client reconnection and failover"""
        pass
        
    async def test_llm_anonymization_accuracy(self):
        """Verify pseudo-anonymization maintains data integrity"""
        pass
        
    async def test_panel_responsiveness(self):
        """Ensure UI remains responsive under load"""
        pass
        
    async def test_sql_risk_assessment(self):
        """Validate risk analyzer accuracy"""
        pass
```

## Deployment Configuration

```yaml
# ai-shell-config.yaml
system:
  startup_animation: true
  matrix_style: enhanced
  
llm:
  models:
    intent: "llama2:7b"
    completion: "codellama:13b"
    anonymizer: "mistral:7b"
  ollama_host: "localhost:11434"
  
mcp:
  oracle:
    thin_mode: true
    connection_pool_size: 5
  postgresql:
    connection_pool_size: 5
    
ui:
  framework: "textual"
  theme: "cyberpunk"
  panel_priority:
    typing: "prompt"
    idle: "balanced"
    
security:
  vault_backend: "keyring"
  auto_redaction: true
  sensitive_commands_require_confirmation: true
  
performance:
  async_workers: 4
  cache_size: 1000
  vector_db_dimension: 384
```

This architecture provides a robust foundation for AI-Shell with MCP integration, local LLM support, and intelligent asynchronous processing while maintaining security and performance standards suitable for production deployment.
