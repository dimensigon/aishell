# LLM Models and CLI Modes in AI-Shell

**Date**: November 18, 2025
**Version**: AI-Shell v2.0.0

---

## Executive Summary

AI-Shell uses **3 distinct LLM models** (intent, completion, anonymizer) across **two primary CLI modes**:

1. **Interactive/REPL Mode** - Uses all 3 models
2. **Natural Language Query Mode** - Uses intent + completion models

---

## The Three Models

### 1. Intent Model (`intent`)

**Purpose**: Understanding and classifying user queries and commands

**Function**: `analyze_intent(query: str) -> Dict[str, Any]`

**Classification Types**:
- `QUERY` - SELECT, read operations
- `MUTATION` - INSERT, UPDATE, DELETE operations
- `SCHEMA` - DDL, structure changes
- `PERFORMANCE` - Optimization queries

**Example**:
```python
# Classifies: "SELECT * FROM users WHERE active = true"
result = manager.analyze_intent(query)
# Returns: {'intent': 'QUERY', 'confidence': 0.95}
```

**Default Model**: `llama2:7b` (self-hosted)
**Alternative**: OpenAI GPT-3.5 (fast, accurate)

---

### 2. Completion Model (`completion`)

**Purpose**: Generating SQL code, explanations, and suggestions

**Function**: `explain_query(query: str) -> str`

**Operations**:
- SQL generation from natural language
- Query explanation in plain English
- Code completion and suggestions
- Optimization recommendations

**Example**:
```python
# Generates explanation for SQL query
explanation = manager.explain_query("SELECT COUNT(*) FROM orders WHERE date > '2024-01-01'")
# Returns: "This query counts all orders placed after January 1st, 2024..."
```

**Default Model**: `codellama:13b` (self-hosted, code-specialized)
**Alternative**: OpenAI GPT-4 (best quality)

---

### 3. Anonymizer Model (`anonymizer`)

**Purpose**: Pseudo-anonymizing sensitive data in queries

**Function**: `anonymize_query(query: str) -> Tuple[str, Dict]`

**Detects & Anonymizes**:
- Email addresses → `USER_EMAIL_001`
- SSNs → `USER_SSN_001`
- Phone numbers → `USER_PHONE_001`
- Names → `USER_NAME_001`
- Credit cards → `USER_CC_001`

**Example**:
```python
# Anonymizes sensitive data
query = "SELECT * FROM users WHERE email = 'john@example.com' AND ssn = '123-45-6789'"
anonymized, mapping = manager.anonymize_query(query)
# Returns:
# anonymized = "SELECT * FROM users WHERE email = 'USER_EMAIL_001' AND ssn = 'USER_SSN_001'"
# mapping = {'john@example.com': 'USER_EMAIL_001', '123-45-6789': 'USER_SSN_001'}
```

**Default Model**: `mistral:7b` (self-hosted)
**Alternative**: DeepSeek (cost-effective)

---

## CLI Modes

### Mode 1: Interactive/REPL Mode ✅ (All 3 Models)

**Invocation**:
```bash
# Start interactive mode
ai-shell

# Or explicitly
python src/main.py
```

**Entry Point**: `src/main.py::interactive_mode()`

**Available Commands**:
```
ai-shell> query <sql>          # Uses: Intent + Completion
ai-shell> ask <question>        # Uses: Intent + Completion
ai-shell> agent <task>          # Uses: Intent
ai-shell> llm generate <prompt> # Uses: Completion
ai-shell> suggest               # Uses: Intent + Completion
ai-shell> help
ai-shell> history
ai-shell> health
ai-shell> metrics
ai-shell> exit
```

**How Models Are Used**:

#### Command: `query <sql>`
```python
# Step 1: Analyze intent
intent = llm_manager.analyze_intent(sql_query)
# Uses: INTENT MODEL (llama2:7b or OpenAI GPT-3.5)

# Step 2: Check for sensitive data
anonymized_query, mapping = llm_manager.anonymize_query(sql_query)
# Uses: ANONYMIZER MODEL (mistral:7b or DeepSeek)

# Step 3: Execute and explain
explanation = llm_manager.explain_query(sql_query)
# Uses: COMPLETION MODEL (codellama:13b or OpenAI GPT-4)
```

#### Command: `ask <question>`
```python
# Step 1: Analyze what user is asking
intent = nlp_processor.analyze_intent(question)
# Uses: INTENT MODEL

# Step 2: Generate response
response = llm_manager.provider.generate(question)
# Uses: COMPLETION MODEL
```

#### Command: `llm generate <prompt>`
```python
# Direct LLM generation
response = llm_manager.provider.generate(prompt, max_tokens=200)
# Uses: COMPLETION MODEL
```

**Example Session**:
```bash
$ ai-shell
AI-Shell Interactive Mode
==================================================
Commands:
  query <sql>    - Execute SQL query
  ask <question> - Ask AI assistant
  ...
==================================================

ai-shell> query SELECT * FROM users WHERE email = 'test@example.com'

[INTENT MODEL]: Classifying query...
  Intent: QUERY (confidence: 0.95)

[ANONYMIZER MODEL]: Checking for sensitive data...
  Found: email address 'test@example.com'
  Anonymized to: USER_EMAIL_001

[Executing query...]

[COMPLETION MODEL]: Generating explanation...
  This query retrieves all columns from the users table where
  the email matches 'test@example.com'. This is a simple SELECT
  query with a single equality condition.

Results: 1 row returned
```

---

### Mode 2: Natural Language Query Mode ⚡ (Intent + Completion)

**Invocation**:
```bash
# Using TypeScript CLI
ai-shell query "show me all active users"

# With options
ai-shell query "show revenue by product" --format json --limit 100
```

**Entry Point**: `src/cli/nl-admin.ts::NLAdminCLI`

**How Models Are Used**:

#### Command: `ai-shell query "<natural language>"`
```typescript
// Step 1: Analyze intent of natural language
const intent = await translator.analyzeIntent(nlQuery);
// Uses: INTENT MODEL

// Step 2: Translate to SQL
const sqlQuery = await translator.translateToSQL(nlQuery, schema);
// Uses: COMPLETION MODEL

// Step 3: Execute query
const results = await executor.execute(sqlQuery);

// Step 4: Explain results
const explanation = await translator.explainQuery(sqlQuery);
// Uses: COMPLETION MODEL
```

**Example**:
```bash
$ ai-shell query "show me the top 10 customers by revenue last month"

[INTENT MODEL]: Analyzing natural language...
  Intent: QUERY (complex aggregation)
  Entities: [time_period: "last month", metric: "revenue", limit: 10]

[COMPLETION MODEL]: Generating SQL...
  SELECT
    c.customer_id,
    c.customer_name,
    SUM(o.total_amount) as revenue
  FROM customers c
  JOIN orders o ON c.customer_id = o.customer_id
  WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
  GROUP BY c.customer_id, c.customer_name
  ORDER BY revenue DESC
  LIMIT 10

[Executing...]

[COMPLETION MODEL]: Explaining results...
  This query finds the 10 customers who generated the most revenue
  in the past month by summing their order totals and sorting by
  highest revenue first.

Results: 10 rows (formatted as table)
```

**Note**: This mode typically does NOT use the anonymizer model unless explicitly enabled with `--anonymize` flag.

---

### Mode 3: Non-Interactive/Script Mode (No LLM)

**Invocation**:
```bash
# Execute specific command without LLM
ai-shell --no-interactive --execute "health"
```

**Entry Point**: `src/main.py` (non-interactive branch)

**LLM Usage**: ❌ None - Direct command execution only

---

## Configuration

### Default Configuration (Self-Hosted)

```yaml
# config/ai-shell-config.yaml
llm:
  models:
    intent: "llama2:7b"         # Pattern recognition, classification
    completion: "codellama:13b" # SQL generation, explanations
    anonymizer: "mistral:7b"    # Sensitive data detection

  ollama_host: "localhost:11434"
  model_path: "/data0/models"
```

### Hybrid Configuration (Recommended)

```yaml
llm:
  function_providers:
    intent:
      provider: "openai"           # Fast intent classification
      model: "gpt-3.5-turbo"
      api_key_env: "OPENAI_API_KEY"

    completion:
      provider: "ollama"           # Keep code local for privacy
      model: "codellama:13b"

    anonymizer:
      provider: "deepseek"         # Cost-effective anonymization
      model: "deepseek-chat"
      api_key_env: "DEEPSEEK_API_KEY"
```

### Python Code Configuration

```python
from src.llm.manager import LocalLLMManager, FunctionProviderConfig

manager = LocalLLMManager()

# Configure different providers for each function
manager.initialize_function_providers(
    intent_config=FunctionProviderConfig(
        provider_type="openai",
        model_name="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY")
    ),
    completion_config=FunctionProviderConfig(
        provider_type="ollama",
        model_name="codellama:13b"
    ),
    anonymizer_config=FunctionProviderConfig(
        provider_type="deepseek",
        model_name="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )
)
```

---

## Model Usage Breakdown by CLI Mode

| CLI Mode | Intent Model | Completion Model | Anonymizer Model |
|----------|--------------|------------------|------------------|
| **Interactive/REPL** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Natural Language Query** | ✅ Yes | ✅ Yes | ⚠️ Optional |
| **Non-Interactive** | ❌ No | ❌ No | ❌ No |

---

## Implementation Details

### Source Files

#### Intent Model Usage
- `src/llm/manager.py::analyze_intent()`
- `src/ai/nlp_processor.py::analyze_intent()`
- Used in: Interactive mode, NL query mode

#### Completion Model Usage
- `src/llm/manager.py::explain_query()`
- `src/ai/query_assistant.py` (SQL generation)
- `src/cli/nl-query-translator.ts` (TypeScript)
- Used in: Interactive mode, NL query mode

#### Anonymizer Model Usage
- `src/llm/manager.py::anonymize_query()`
- `src/security/pii.py` (PII detection)
- Used in: Interactive mode (automatic), NL mode (optional)

### Initialization (main.py)

```python
# Line 106-111
model_path = self.config.get('llm.model_path', '/data0/models')
self.llm_manager = LocalLLMManager(model_path=model_path)
provider_type = self.config.get('llm.provider', 'ollama')
model_name = self.config.get('llm.models.intent', 'llama2')
self.llm_manager.initialize(provider_type=provider_type, model_name=model_name)
```

**Note**: Basic initialization only loads intent model. Full dual-mode requires calling `initialize_function_providers()`.

---

## Workflow Examples

### Workflow 1: Interactive Query with All 3 Models

```
User Input: "query SELECT * FROM users WHERE ssn = '123-45-6789'"
     ↓
[1. INTENT MODEL]
  - Input: "SELECT * FROM users WHERE ssn = '123-45-6789'"
  - Output: {intent: "QUERY", confidence: 0.95}
     ↓
[2. ANONYMIZER MODEL]
  - Input: "SELECT * FROM users WHERE ssn = '123-45-6789'"
  - Output: {
      anonymized: "SELECT * FROM users WHERE ssn = 'USER_SSN_001'",
      mapping: {'123-45-6789': 'USER_SSN_001'}
    }
     ↓
[3. Execute Query]
  - Runs: SELECT * FROM users WHERE ssn = 'USER_SSN_001'
  - Returns: [results]
     ↓
[4. COMPLETION MODEL]
  - Input: "Explain: SELECT * FROM users WHERE ssn = '123-45-6789'"
  - Output: "This query retrieves all user records matching the provided
             Social Security Number. The query has been anonymized for
             security purposes."
     ↓
Display Results + Explanation
```

### Workflow 2: Natural Language to SQL

```
User Input: ai-shell query "show me users who signed up last week"
     ↓
[1. INTENT MODEL]
  - Input: "show me users who signed up last week"
  - Output: {
      intent: "QUERY",
      entities: [
        {type: "table", value: "users"},
        {type: "time_filter", value: "last week"}
      ]
    }
     ↓
[2. COMPLETION MODEL - SQL Generation]
  - Input: Natural language + schema context
  - Output: "SELECT * FROM users
             WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
     ↓
[3. Execute Generated SQL]
  - Returns: [results]
     ↓
[4. COMPLETION MODEL - Explanation]
  - Input: Generated SQL
  - Output: "This query selects all users who registered within
             the last 7 days by comparing their creation date
             to one week ago."
     ↓
Display Results + SQL + Explanation
```

---

## Summary

### Which Mode Uses All 3 Models?

**✅ Interactive/REPL Mode** is the primary mode that uses all three models:
- **Intent Model**: Classifies every query/command
- **Completion Model**: Generates explanations and responses
- **Anonymizer Model**: Automatically detects and anonymizes sensitive data

### Quick Reference

**To use all 3 models**:
```bash
ai-shell  # Start interactive mode
```

**To use intent + completion only**:
```bash
ai-shell query "natural language question"
```

**To skip LLM entirely**:
```bash
ai-shell --no-interactive --execute "health"
```

---

## Documentation References

- [Public LLM Providers Guide](./PUBLIC_LLM_PROVIDERS.md)
- [Functionality Report](./reports/PUBLIC_LLM_FUNCTIONALITY_REPORT.md)
- [LLM Manager Source](../src/llm/manager.py)
- [Main Entry Point](../src/main.py)
- [NL Query Translator](../src/cli/nl-query-translator.ts)
