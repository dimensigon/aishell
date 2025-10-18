# How-To: Use Cognitive Shell Memory (CogShell)

## What is Cognitive Memory?

Cognitive Shell Memory (CogShell) is an intelligent memory system that learns from every command you run. It remembers successful patterns, learns from failures, and helps you work more efficiently by suggesting commands based on your history and context.

## Quick Start

### Enable Cognitive Memory

```bash
# Memory is enabled by default, but you can configure it
aishell --enable-cognitive-memory
```

### Basic Usage

#### 1. Recall Similar Commands

Find commands you've run before that are similar to what you're looking for:

```bash
# Find all git-related commands
aishell memory recall "git commit"

# Find Docker commands
aishell memory recall "docker" --limit 10

# Find commands with high similarity
aishell memory recall "deploy" --threshold 0.8
```

**Example Output:**
```
┌─────────────────────────────────────────────────────────────┐
│ Memories matching: git commit                               │
├──────────────────────────────┬─────────┬────────┬──────────┤
│ Command                      │ Success │ Import │ Freq     │
├──────────────────────────────┼─────────┼────────┼──────────┤
│ git commit -m "feat: add..."│    ✓    │  0.85  │    15    │
│ git commit --amend          │    ✓    │  0.72  │     8    │
│ git commit -a -m "fix: ..." │    ✗    │  0.45  │     2    │
└──────────────────────────────┴─────────┴────────┴──────────┘
```

#### 2. Get Insights from Your Command History

Analyze your command patterns and see what you use most:

```bash
# View comprehensive insights
aishell memory insights

# Get JSON output for scripting
aishell memory insights --json-output
```

**Example Output:**
```
┌─────────────────────────────────────┐
│ Most Used Commands                  │
├─────────────────────┬───────────────┤
│ Command             │ Usage Count   │
├─────────────────────┼───────────────┤
│ git status          │     127       │
│ ls -la              │      98       │
│ cd projects         │      76       │
└─────────────────────┴───────────────┘

Overall Statistics:
  • Success Rate: 94.5%
  • Total Memories: 1,247
  • Avg Importance: 0.63
  • Avg Sentiment: 0.45
```

#### 3. Get Smart Command Suggestions

Let CogShell suggest commands based on your context:

```bash
# Get suggestions for current context
aishell memory suggest

# Provide specific context
aishell memory suggest -c '{"cwd": "/project", "last_command": "git add ."}'
```

**Example Output:**
```
Command Suggestions:
  1. git commit -m "update" (confidence: 0.89)
  2. git push origin main (confidence: 0.76)
  3. npm test (confidence: 0.62)
```

## Advanced Usage

### Export and Share Knowledge

Share your command knowledge with your team:

```bash
# Export your knowledge base
aishell memory export team-knowledge.json

# Team member imports it
aishell memory import team-knowledge.json
```

### Integration with Other Tools

#### Use with Scripts

```bash
# Get most relevant command for a task
SUGGESTION=$(aishell memory recall "backup database" --limit 1 --json-output | jq -r '.[0].command')
echo "Suggested: $SUGGESTION"
```

#### Create Aliases from Memory

```bash
# Find your most used complex commands
aishell memory insights --json-output | jq '.most_used_commands[] | select((.command | length) > 20)'

# Create aliases for them
alias deploy="docker-compose -f prod.yml up -d"
```

## Use Cases

### 1. Learning New Technologies

When learning a new framework, CogShell remembers what worked:

```bash
# First time using kubectl
kubectl get pods --all-namespaces

# Later, just ask
aishell memory recall "kubectl pods"
# Shows you the exact command you used before
```

### 2. Troubleshooting

Find how you fixed similar issues before:

```bash
# Remember how you fixed Docker issues
aishell memory recall "docker error"

# See all failed commands for a service
aishell memory recall "nginx" --threshold 0.0 | grep "✗"
```

### 3. Team Onboarding

Export senior developer's knowledge for new team members:

```bash
# Senior dev exports knowledge
aishell memory export senior-dev-knowledge.json

# New dev imports
aishell memory import senior-dev-knowledge.json

# Now new dev can recall expert patterns
aishell memory recall "deploy to production"
```

### 4. Documentation Generation

Use memory to document your processes:

```bash
# Extract deployment workflow
aishell memory recall "deploy" --json-output > deploy-commands.json

# Convert to documentation
python scripts/memory-to-docs.py deploy-commands.json > DEPLOYMENT.md
```

## Understanding Memory Features

### Pattern Recognition

CogShell automatically recognizes patterns:

- **Git Workflow**: commit, push, pull sequences
- **File Operations**: cp, mv, rm patterns
- **Docker Operations**: build, run, deploy patterns
- **Debugging**: strace, gdb, profiling patterns
- **Network**: curl, wget, netcat patterns

### Importance Scoring

Commands are scored by importance (0-1):

- **0.8-1.0**: Critical operations, complex commands, errors
- **0.5-0.7**: Common workflows, successful operations
- **0.0-0.4**: Simple commands, low-impact operations

### Memory Decay

Older, unused memories gradually decrease in importance (forgetting factor: 0.95/day):

```python
# After 1 day: importance * 0.95
# After 7 days: importance * (0.95^7) ≈ 0.70
# After 30 days: importance * (0.95^30) ≈ 0.21
```

### Sentiment Analysis

Commands are assigned sentiment scores (-1 to 1):

- **Positive (0.5-1.0)**: Successful operations, completed tasks
- **Neutral (0)**: Regular operations
- **Negative (-1.0 to -0.5)**: Errors, failures, denied operations

## Configuration

### Memory Settings

Create `~/.aishell/memory_config.yaml`:

```yaml
cognitive_memory:
  # Storage
  memory_dir: "~/.aishell/memory"
  max_memories: 100000

  # Vector search
  vector_dim: 384
  similarity_threshold: 0.7

  # Learning
  learning_rate: 0.1
  forgetting_factor: 0.95

  # Performance
  cache_size: 1000
  enable_embeddings: true

  # Privacy
  anonymize_sensitive: true
  exclude_patterns:
    - "password"
    - "token"
    - "secret"
```

### Integration with AI-Shell

Memory automatically integrates with all AI-Shell features:

```bash
# AI queries use memory for context
aishell ai "what was that docker command I used yesterday?"
# CogShell provides context to LLM

# Agent tasks learn from memory
aishell agent "deploy like last time"
# Agent recalls successful deployment pattern
```

## Tips and Tricks

### 1. Quick Command Lookup

Create shell function for fast lookup:

```bash
# Add to ~/.bashrc
recall() {
    aishell memory recall "$@" --limit 1 | grep -E '│.*│' | head -2 | tail -1
}

# Usage
recall "git push"
```

### 2. Auto-suggest on Tab

Integrate with shell completion:

```bash
# Add to ~/.bashrc
_aishell_suggest() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    if [ ${#cur} -gt 2 ]; then
        COMPREPLY=($(aishell memory suggest -c "{\"cwd\": \"$PWD\"}" 2>/dev/null | grep -E '^\s+[0-9]' | cut -d'.' -f2 | awk '{$1=$1};1'))
    fi
}
complete -F _aishell_suggest aishell
```

### 3. Memory-Based Aliases

Generate aliases from most-used commands:

```bash
# Generate aliases
aishell memory insights --json-output | jq -r '.most_used_commands[] | "alias cmd\(.command | @sh | split(" ")[0])='\(.command)'"'
```

### 4. Learning from Errors

Review and learn from failures:

```bash
# Find all errors
aishell memory insights | grep "Common Errors"

# Get detailed error info
aishell memory recall "error" --threshold 0.0 --json-output | jq '.[] | select(.success == false)'
```

## Troubleshooting

### Memory Not Working

```bash
# Check if memory is initialized
ls ~/.aishell/memory/

# Reinitialize if needed
rm -rf ~/.aishell/memory/
aishell --init-memory
```

### Slow Recall

```bash
# Reduce vector dimension for speed
# Edit ~/.aishell/memory_config.yaml
vector_dim: 128  # Faster but less accurate

# Or limit history
max_memories: 10000  # Keep only recent 10k
```

### Privacy Concerns

```bash
# Enable anonymization
# Edit config
anonymize_sensitive: true

# Or export without sensitive data
aishell memory export clean-knowledge.json --filter-sensitive
```

## Best Practices

1. **Regular Exports**: Backup your knowledge monthly
2. **Team Sharing**: Share knowledge bases for common tasks
3. **Clean Imports**: Review imported knowledge before accepting
4. **Feedback Loop**: Use insights to improve your workflow
5. **Privacy First**: Never export memory containing secrets

## Next Steps

- **Advanced**: Learn about [Anomaly Detection](ANOMALY_DETECTION.md)
- **Integration**: Set up [Autonomous DevOps](AUTONOMOUS_DEVOPS.md)
- **API**: Read the [Memory API Documentation](../API.md#cognitive-memory-api)

## Examples

### Example 1: Development Workflow

```bash
# Morning routine
$ cd ~/projects/myapp
$ aishell memory suggest
# Suggests: git pull, npm install, npm start

# During development
$ git commit -m "feat: add feature"
$ aishell memory recall "git push"
# Shows: git push origin feature-branch

# End of day
$ aishell memory insights
# See what you accomplished
```

### Example 2: Production Debugging

```bash
# Issue occurs
$ aishell memory recall "nginx error"
# Find how you fixed it before

# Apply the fix
$ sudo systemctl restart nginx

# Check logs
$ aishell memory suggest -c '{"last_command": "restart nginx"}'
# Suggests: tail -f /var/log/nginx/error.log
```

### Example 3: Learning New Tool

```bash
# First time using tool
$ kubectl get pods --all-namespaces
$ kubectl describe pod my-pod

# Week later
$ aishell memory recall "kubectl"
# Shows your complete kubectl usage history

# Extract learning path
$ aishell memory recall "kubectl" --json-output | jq -r '.[] | .command' | sort -u
# See your kubectl progression
```

---

**Version**: 1.0.0
**Last Updated**: 2025-01-17
**Related**: [Anomaly Detection](ANOMALY_DETECTION.md) | [ADA](AUTONOMOUS_DEVOPS.md)