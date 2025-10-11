# AI-Shell Quick Start - Video Tutorial Script (5 minutes)

**Target Duration**: 5:00
**Audience**: First-time users, developers
**Prerequisites**: Python 3.8+, basic command line knowledge

---

## Scene 1: Introduction (0:00 - 0:30)

### Screen: Title Card
**Voice Over**:
> "Welcome to AI-Shell - the intelligent command-line interface that combines the power of AI with database management. In just 5 minutes, you'll have AI-Shell up and running on your system."

### Screen Capture Notes:
- Show AI-Shell logo
- Display tagline: "AI-Powered Shell with Enterprise Database Features"
- Quick feature highlights animation

---

## Scene 2: Installation (0:30 - 1:45)

### Screen: Terminal Window
**Voice Over**:
> "Installation is simple. We support three methods: pip, pipx, or from source."

### Demo Code (Type on screen):
```bash
# Method 1: Using pip (Recommended)
pip install ai-shell

# Method 2: Using pipx (Isolated environment)
pipx install ai-shell

# Method 3: From source
git clone https://github.com/yourusername/ai-shell.git
cd ai-shell
pip install -e .
```

**Voice Over**:
> "We'll use pip for this demo. Just run 'pip install ai-shell' and you're ready to go."

### Screen Capture Notes:
- Show pip installation progress bar
- Highlight successful installation message
- Show installed version: `ai-shell --version`

**Timestamp**: 0:30 - 1:45

---

## Scene 3: First Launch (1:45 - 2:30)

### Screen: Terminal Window
**Voice Over**:
> "Launch AI-Shell by typing 'ai-shell'. On first run, you'll see a welcome screen and configuration wizard."

### Demo Code:
```bash
ai-shell
```

### Expected Output:
```
╔══════════════════════════════════════╗
║     Welcome to AI-Shell v1.0.0       ║
║  AI-Powered Shell & Database Tool    ║
╚══════════════════════════════════════╝

First run detected! Let's configure your environment.

? Select your preferred LLM provider:
  > OpenAI (GPT-4)
    Anthropic (Claude)
    Local LLM (Ollama)
    Azure OpenAI
```

**Voice Over**:
> "Choose your AI provider. I'll select OpenAI for this demo."

### Screen Capture Notes:
- Show interactive menu navigation
- Highlight provider selection
- Show API key input (masked)

**Timestamp**: 1:45 - 2:30

---

## Scene 4: Basic Commands (2:30 - 3:45)

### Screen: AI-Shell Interface
**Voice Over**:
> "Now let's explore basic commands. AI-Shell understands natural language."

### Demo Commands (Type sequentially):

```bash
# Natural language command
ai> what files are in this directory?

# AI translates to: ls -la
[AI] I'll list the files in the current directory:
total 48
drwxr-xr-x  12 user  staff   384 Oct 11 10:00 .
drwxr-xr-x   8 user  staff   256 Oct 11 09:30 ..
-rw-r--r--   1 user  staff  1234 Oct 11 10:00 README.md
-rw-r--r--   1 user  staff   567 Oct 11 09:45 config.yaml
```

**Voice Over**:
> "Notice how AI-Shell understood our question and executed the appropriate command."

### Demo Commands (Continue):
```bash
# Database connection
ai> connect to postgres database localhost:5432/mydb

[AI] Connecting to PostgreSQL database...
✓ Connected to mydb@localhost:5432
Database: PostgreSQL 14.5

# Natural language query
ai> show me all users created in the last 7 days

[AI] I'll query the users table for recent entries:
SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '7 days';

┌────┬──────────┬─────────────────────┬────────────────────┐
│ id │ username │ email               │ created_at         │
├────┼──────────┼─────────────────────┼────────────────────┤
│ 42 │ alice    │ alice@example.com   │ 2025-10-05 14:23   │
│ 43 │ bob      │ bob@example.com     │ 2025-10-08 09:15   │
└────┴──────────┴─────────────────────┴────────────────────┘
```

**Voice Over**:
> "AI-Shell can connect to databases and translate your questions into SQL queries automatically."

### Screen Capture Notes:
- Show syntax highlighting
- Highlight AI interpretation in brackets
- Show formatted table output
- Demonstrate tab completion

**Timestamp**: 2:30 - 3:45

---

## Scene 5: Help and Next Steps (3:45 - 5:00)

### Screen: AI-Shell Help Menu
**Voice Over**:
> "Need help? Just type 'help' or ask AI-Shell directly."

### Demo Commands:
```bash
ai> help

Available Commands:
  help              - Show this help message
  connect <uri>     - Connect to database
  disconnect        - Disconnect from current database
  query <sql>       - Execute SQL query
  ai <question>     - Ask AI for help
  config            - Configure AI-Shell
  exit              - Exit AI-Shell

Type 'help <command>' for detailed information.

# Ask AI for help
ai> how do I export query results to CSV?

[AI] You can export query results using the --export flag:
query "SELECT * FROM users" --export=csv --output=users.csv

Or use natural language:
"export all users to users.csv"
```

**Voice Over**:
> "You can also export results, schedule queries, and much more."

### Screen: Next Steps Card
**Voice Over**:
> "You're all set! Check out our database setup tutorial next, or explore our AI features guide. Visit our documentation at docs.ai-shell.io. Thanks for watching!"

### Screen Capture Notes:
- Show help menu with syntax highlighting
- Display AI response with example
- Show closing card with links:
  - Next: Database Setup (Tutorial 02)
  - Documentation: docs.ai-shell.io
  - GitHub: github.com/yourusername/ai-shell
  - Discord: discord.gg/ai-shell

**Timestamp**: 3:45 - 5:00

---

## Production Notes

### Visual Style:
- Terminal theme: Dark background with syntax highlighting
- Font: Fira Code or JetBrains Mono
- Window size: 1920x1080, terminal at 80% width
- Show cursor movements and typing (medium speed)

### Audio:
- Background music: Subtle tech/ambient
- Voice: Clear, professional, friendly tone
- Sound effects: Subtle for successful operations

### Graphics:
- Overlay AI-Shell logo (top-right corner)
- Timestamp counter (bottom-right)
- Highlight important commands with subtle box
- Use arrows/circles to point out key features

### Accessibility:
- Include captions for all voice-over
- Ensure high contrast for text
- Provide audio descriptions for visual elements

### Call-to-Action:
- Subscribe button animation at end
- Links to next tutorials
- GitHub star reminder
- Community Discord invite

---

## Key Learning Outcomes

By the end of this tutorial, viewers will:
1. ✓ Install AI-Shell using their preferred method
2. ✓ Complete initial configuration
3. ✓ Execute basic natural language commands
4. ✓ Connect to a database
5. ✓ Use AI assistance for queries
6. ✓ Know where to find help and next steps

---

## Resources Mentioned

- **Documentation**: https://docs.ai-shell.io
- **GitHub**: https://github.com/yourusername/ai-shell
- **Discord Community**: https://discord.gg/ai-shell
- **Next Tutorial**: 02-database-setup-script.md

---

## Video Metadata

**Title**: AI-Shell Quick Start - Install and Run in 5 Minutes
**Description**: Learn how to install and use AI-Shell, the intelligent command-line interface with AI-powered database management. This tutorial covers installation, first launch, basic commands, and natural language queries.

**Tags**: ai-shell, cli, artificial intelligence, database, tutorial, quick start, python, postgresql, natural language processing

**Thumbnail**: Terminal window showing AI-Shell with highlighted features
