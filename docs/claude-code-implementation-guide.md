# Claude Code Implementation Guidelines for AI-Shell

## Priority Implementation Order

### Phase 0: Project Initialization (Day 1)

```bash
# Initialize project structure
mkdir -p ai-shell/{core,modules,mcp_clients,ui,tests,config}
cd ai-shell

# Create virtual environment with Python 3.11+
python3.11 -m venv venv
source venv/bin/activate

# Core dependencies
pip install textual click prompt-toolkit cx-oracle psycopg2-binary
pip install ollama faiss-cpu sentence-transformers
pip install cryptography keyring asyncio aiofiles
pip install pyyaml rich pytest pytest-asyncio
```

### Phase 1: Core UI with Textual (Week 1)

```python
# core/ui_manager.py - Start with this file
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Input, TextArea
from textual.reactive import reactive
import asyncio

class AIShellApp(App):
    """Main application using Textual for modern TUI"""
    
    CSS = """
    #output {
        height: 60%;
        border: solid green;
    }
    
    #module {
        height: 30%;
        border: solid cyan;
        overflow-y: auto;
    }
    
    #prompt {
        height: 10%;
        border: solid white;
        dock: bottom;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield TextArea(id="output", read_only=True)
            yield Static("Module Info", id="module")
            yield Input(placeholder="AI$ >", id="prompt")
    
    async def on_input_submitted(self, event):
        """Handle command submission"""
        command = event.value
        
        # Async intent analysis
        asyncio.create_task(self.analyze_intent(command))
        
        # Process command
        await self.process_command(command)
```

### Phase 2: MCP Client Implementation (Week 2)

```python
# mcp_clients/oracle_thin.py - Critical: No Oracle client needed
import cx_Oracle
import asyncio
from typing import Dict, Any

class OracleThinMCPClient:
    """
    CRITICAL: Use thin mode to avoid Oracle client installation
    """
    def __init__(self):
        # Enable thin mode - no Oracle Instant Client required
        cx_Oracle.init_oracle_client(lib_dir=None)  # This is the key
        self.pool = None
        
    async def connect(self, config: Dict[str, Any]):
        """Establish connection pool using thin mode"""
        dsn = cx_Oracle.makedsn(
            host=config['host'],
            port=config['port'],
            service_name=config.get('service_name', 'ORCL')
        )
        
        # Create async connection pool
        loop = asyncio.get_event_loop()
        self.pool = await loop.run_in_executor(
            None,
            cx_Oracle.create_pool,
            config['user'],
            config['password'],
            dsn,
            min=2,
            max=10,
            increment=1
        )
        
    async def query_user_objects(self) -> list:
        """Query user-defined database objects"""
        async with self.acquire() as connection:
            cursor = connection.cursor()
            
            # Get user tables, views, procedures
            query = """
            SELECT object_name, object_type, status 
            FROM user_objects 
            WHERE object_type IN ('TABLE', 'VIEW', 'PROCEDURE', 'FUNCTION', 'PACKAGE')
            ORDER BY object_type, object_name
            """
            
            result = await self._execute_async(cursor, query)
            return result
```

```python
# mcp_clients/postgresql_pure.py - Pure Python, no psql needed
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio

class PostgreSQLPureMCPClient:
    """
    Pure Python PostgreSQL client - no psql binary required
    """
    def __init__(self):
        self.connection_pool = []
        
    async def connect(self, config: Dict[str, Any]):
        """Create connection using pure Python psycopg2"""
        conn_params = {
            'dbname': config['database'],
            'user': config['user'],
            'password': config['password'],
            'host': config['host'],
            'port': config.get('port', 5432),
            'cursor_factory': RealDictCursor
        }
        
        # Create connection pool
        for _ in range(5):
            conn = await asyncio.get_event_loop().run_in_executor(
                None, 
                psycopg2.connect, 
                **conn_params
            )
            self.connection_pool.append(conn)
```

### Phase 3: Local LLM Integration (Week 3)

```python
# core/llm_manager.py - Local LLM with Ollama
import ollama
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, Tuple

class LocalLLMIntentAnalyzer:
    """
    CRITICAL: Use local LLM for privacy and speed
    """
    def __init__(self):
        # Small, fast model for intent classification
        self.intent_model = "llama2:7b"
        
        # Embedding model for semantic search
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Pre-computed command embeddings
        self.command_embeddings = None
        self.command_metadata = []
        
    async def analyze_intent_async(self, user_input: str, context: Dict) -> Dict:
        """
        Asynchronously analyze user intent for module panel enrichment
        """
        # Generate embedding
        input_embedding = self.embedder.encode(user_input)
        
        # Find similar commands
        similarities = self._find_similar_commands(input_embedding)
        
        # Prepare prompt for local LLM
        prompt = f"""
        Analyze the intent of this command and suggest helpful information:
        Command: {user_input}
        Current directory: {context.get('cwd', '/')}
        Previous command: {context.get('last_command', 'none')}
        
        Respond with JSON:
        {{
            "intent": "file_operation|database_query|system_admin|navigation",
            "risk_level": "low|medium|high",
            "suggestions": ["suggestion1", "suggestion2"],
            "relevant_info": "brief helpful context"
        }}
        """
        
        # Call local LLM
        response = await self._ollama_async(prompt)
        
        return {
            'analysis': response,
            'similar_commands': similarities[:5]
        }
        
    def pseudo_anonymize(self, text: str) -> Tuple[str, Dict]:
        """
        Replace sensitive data before external API calls
        """
        import re
        
        anonymization_map = {}
        anonymized = text
        
        # Patterns for sensitive data
        patterns = {
            'ip': (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', 'IP_ADDR'),
            'email': (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-Z]{2,}', 'EMAIL'),
            'username': (r'(?:user|username)[:=]\s*([^\s,]+)', 'USERNAME'),
            'password': (r'(?:password|pwd)[:=]\s*([^\s,]+)', 'PASSWORD'),
            'server': (r'(?:server|host)[:=]\s*([^\s,]+)', 'SERVER'),
            'path': (r'/home/[^/\s]+', 'USER_PATH')
        }
        
        counter = 0
        for pattern_name, (regex, prefix) in patterns.items():
            for match in re.finditer(regex, text, re.IGNORECASE):
                token = f"<{prefix}_{counter}>"
                anonymization_map[token] = match.group(0)
                anonymized = anonymized.replace(match.group(0), token)
                counter += 1
                
        return anonymized, anonymization_map
```

### Phase 4: Asynchronous Module Panel (Week 4)

```python
# modules/panel_enricher.py - Critical async architecture
import asyncio
from typing import Dict, Any
from asyncio import Queue
import time

class AsyncPanelEnricher:
    """
    CRITICAL: Non-blocking panel updates while user types
    """
    def __init__(self, ui_app, llm_manager, mcp_clients):
        self.ui_app = ui_app
        self.llm_manager = llm_manager
        self.mcp_clients = mcp_clients
        
        # Priority queue for updates
        self.update_queue = asyncio.PriorityQueue()
        self.running = True
        
    async def start_enrichment_loop(self):
        """
        Main loop - runs continuously in background
        """
        while self.running:
            try:
                # Get next update request
                priority, timestamp, context = await self.update_queue.get()
                
                # Skip if too old (user typed something new)
                if time.time() - timestamp > 1.0:
                    continue
                    
                # Analyze intent with local LLM
                intent = await self.llm_manager.analyze_intent_async(
                    context['input'],
                    context['state']
                )
                
                # Gather relevant info based on intent
                enrichment = await self._gather_contextual_info(intent)
                
                # Update module panel without blocking
                await self._update_panel_async(enrichment)
                
            except Exception as e:
                # Log but don't crash
                print(f"Enrichment error: {e}")
                
    async def _gather_contextual_info(self, intent: Dict) -> Dict:
        """
        Use MCP clients to gather database/system info
        """
        info = {}
        
        if intent.get('intent') == 'database_query':
            # Check active database connections
            for name, client in self.mcp_clients.items():
                if client.is_connected():
                    info[name] = {
                        'tables': await client.get_table_count(),
                        'active_queries': await client.get_active_queries()
                    }
                    
        elif intent.get('intent') == 'file_operation':
            # Use MCP shell commands
            info['disk_usage'] = await self._run_shell_command('df -h')
            info['current_files'] = await self._run_shell_command('ls -la')
            
        return info
```

### Phase 5: Vector Database for Auto-completion (Week 5)

```python
# core/vector_store.py - FAISS for fast similarity search
import faiss
import pickle
import numpy as np
from pathlib import Path

class CommandVectorStore:
    """
    Pre-computed embeddings for instant auto-completion
    """
    def __init__(self, dimension=384):
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        self.dimension = dimension
        
        # Metadata storage
        self.commands = []
        self.system_objects = {}
        
    async def initialize_system_objects(self):
        """
        Pre-load database system objects for auto-completion
        """
        # Oracle system tables
        oracle_objects = [
            ('ALL_TABLES', 'View of all accessible tables'),
            ('ALL_TAB_COLUMNS', 'Columns of all accessible tables'),
            ('USER_CONSTRAINTS', 'User constraint definitions'),
            ('DBA_USERS', 'Database user accounts'),
            ('V$SESSION', 'Current database sessions'),
            ('V$SQL', 'SQL statements in shared pool')
        ]
        
        # PostgreSQL system catalogs
        pg_objects = [
            ('pg_catalog.pg_tables', 'System table catalog'),
            ('information_schema.tables', 'Standard table information'),
            ('pg_stat_activity', 'Current database activity'),
            ('pg_indexes', 'Index definitions')
        ]
        
        # Generate embeddings
        all_objects = oracle_objects + pg_objects
        embeddings = []
        
        for obj_name, description in all_objects:
            # Create embedding from name + description
            text = f"{obj_name} {description}"
            embedding = await self._generate_embedding(text)
            embeddings.append(embedding)
            
            self.system_objects[obj_name] = {
                'description': description,
                'type': 'system_object'
            }
            
        # Add to FAISS index
        embeddings_array = np.array(embeddings).astype('float32')
        self.index.add(embeddings_array)
        
    async def search_similar(self, query: str, k: int = 5) -> list:
        """
        Find similar commands/objects for auto-completion
        """
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        
        # Search in FAISS
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1),
            k
        )
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.system_objects):
                obj_name = list(self.system_objects.keys())[idx]
                results.append({
                    'name': obj_name,
                    'info': self.system_objects[obj_name],
                    'similarity': float(1 / (1 + distance))
                })
                
        return results
```

## Critical Implementation Notes for Claude Code

### 1. Dependency Order
```bash
# Install in this exact order to avoid conflicts
pip install prompt-toolkit==3.0.43  # Stable version
pip install textual==0.47.1         # Latest stable
pip install cx-Oracle==8.3.0        # Supports thin mode
pip install psycopg2-binary==2.9.9  # Pure Python
pip install ollama==0.1.7           # Local LLM client
pip install faiss-cpu==1.7.4        # No GPU required
```

### 2. Startup Sequence
```python
# main.py - Application entry point
async def main():
    # 1. Initialize vector store (background)
    vector_task = asyncio.create_task(vector_store.initialize())
    
    # 2. Check local LLM availability
    llm_status = await llm_manager.check_models()
    
    # 3. Start UI (immediate)
    app = AIShellApp()
    
    # 4. Initialize MCP clients (background)
    asyncio.create_task(initialize_mcp_clients())
    
    # 5. Start enrichment loop (background)
    asyncio.create_task(panel_enricher.start_enrichment_loop())
    
    # 6. Run application
    await app.run_async()
```

### 3. Panel Priority Logic
```python
def calculate_panel_sizes(self, terminal_height: int, user_typing: bool):
    """Dynamic panel sizing based on activity"""
    
    if user_typing:
        # User actively typing - prioritize prompt
        prompt_height = min(
            self.prompt_lines_needed() + 2,
            terminal_height // 3
        )
        module_height = terminal_height // 4
        output_height = terminal_height - prompt_height - module_height
    else:
        # Idle - show more module info
        output_height = terminal_height * 0.5
        module_height = terminal_height * 0.35
        prompt_height = terminal_height * 0.15
        
    return {
        'output': int(output_height),
        'module': int(module_height),
        'prompt': int(prompt_height)
    }
```

### 4. MCP Shell Integration
```python
# Use MCP for system commands with sudo support
async def execute_system_command(cmd: str, sudo: bool = False):
    """Execute via MCP shell client"""
    if sudo:
        # Request sudo through MCP
        result = await mcp_shell.sudo_execute(cmd)
    else:
        result = await mcp_shell.execute(cmd)
    
    # Auto-redact sensitive info
    result = vault.auto_redact(result)
    return result
```

### 5. Testing Priority
```python
# tests/test_core.py - Start with these tests
@pytest.mark.asyncio
async def test_thin_oracle_connection():
    """Verify Oracle thin mode works without client"""
    client = OracleThinMCPClient()
    # Should not raise "Oracle Client not found"
    await client.connect(test_config)
    
@pytest.mark.asyncio  
async def test_panel_async_update():
    """Verify panel updates don't block input"""
    # Simulate typing while panel updates
    pass
    
@pytest.mark.asyncio
async def test_llm_anonymization():
    """Verify sensitive data is anonymized"""
    pass
```

## Development Workflow for Claude Code

1. **Start with UI skeleton** - Get Textual app running first
2. **Add MCP clients** - Test thin connections work
3. **Integrate local LLM** - Verify Ollama connectivity
4. **Build async enrichment** - Non-blocking panel updates
5. **Add vector search** - Auto-completion system
6. **Security layer** - Vault and redaction
7. **Performance tuning** - Profile and optimize

This architecture ensures no external database client dependencies while maintaining full functionality through pure Python libraries and MCP integration.
