# 🚀 AI-Shell Quick Start Guide

## 📦 Installation Complete!

Your AI-Shell is installed at: `/home/claude/AIShell-Local/`

---

## 🎯 Quick Launch (Easiest Method)

```bash
cd /home/claude/AIShell-Local
./launch.sh
```

That's it! The launch script handles everything automatically.

---

## 📋 Manual Launch (Step by Step)

### 1. Navigate to the directory
```bash
cd /home/claude/AIShell-Local
```

### 2. Activate virtual environment
```bash
source venv/bin/activate
```

### 3. Run AI-Shell
```bash
python aishell.py
```

### 4. Exit virtual environment (when done)
```bash
deactivate
```

---

## 🎮 Basic Commands

Once AI-Shell is running, try these commands:

| Command | Description |
|---------|-------------|
| `help` | Show all available commands |
| `status` | Check system status |
| `ai help` | Get AI assistance |
| `db list` | List database connections |
| `exit` or `Ctrl+D` | Exit AI-Shell |

---

## ⚙️ Configuration

### 1. Environment Variables
Create a `.env` file in `/home/claude/AIShell-Local/`:

```bash
# LLM Configuration
OLLAMA_HOST=http://localhost:11434
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Database Connections
POSTGRES_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
```

### 2. AI Model Selection
Set your preferred AI model:
```bash
export AI_MODEL=ollama/llama2  # For local Ollama
export AI_MODEL=gpt-4          # For OpenAI
export AI_MODEL=claude-3        # For Anthropic
```

---

## 🔧 Troubleshooting

### Issue: "Command not found"
**Solution:** Make sure you're in the right directory and virtual environment is activated:
```bash
cd /home/claude/AIShell-Local
source venv/bin/activate
```

### Issue: "Module not found"
**Solution:** Install missing dependencies:
```bash
pip install -r requirements-minimal.txt
```

### Issue: "TypeScript build failed"
**Solution:** Install Node dependencies and rebuild:
```bash
npm install
npm run build
```

### Issue: "Connection refused" for AI models
**Solution:** Start your AI service:
```bash
# For Ollama
ollama serve

# For other services, check their documentation
```

---

## 🚀 Advanced Usage

### Running with specific configuration
```bash
./launch.sh --config production.yaml
```

### Enable debug mode
```bash
./launch.sh --debug
```

### Use different AI model
```bash
AI_MODEL=ollama/mistral ./launch.sh
```

### Connect to remote database
```bash
DB_URL=postgresql://remote-host/db ./launch.sh
```

---

## 📚 Features

### ✅ Available Features
- ✅ Interactive CLI with auto-completion
- ✅ AI-powered command suggestions
- ✅ Database management (PostgreSQL, Redis)
- ✅ Async command processing
- ✅ Command history with search
- ✅ Multi-model LLM support
- ✅ MCP protocol integration

### 🔄 Coming Soon
- 🔄 Vector database integration
- 🔄 Web UI interface
- 🔄 Plugin system
- 🔄 Cloud sync

---

## 📖 Documentation

- **Full Documentation**: See `README.md`
- **API Reference**: See `docs/api.md`
- **Configuration Guide**: See `docs/configuration.md`
- **Developer Guide**: See `docs/development.md`

---

## 🆘 Getting Help

1. **In AI-Shell**: Type `help` or `ai help <topic>`
2. **Documentation**: Check the `docs/` folder
3. **Issues**: Report at GitHub (when repository is public)

---

## 🎉 Ready to Go!

Your AI-Shell is ready to use. Start with:

```bash
./launch.sh
```

Then try:
- `help` - See all commands
- `ai suggest` - Get AI suggestions
- `status` - Check system health

Enjoy your intelligent shell experience! 🚀