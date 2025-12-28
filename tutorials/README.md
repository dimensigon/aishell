# 📚 AI-Shell Tutorials

**Comprehensive hands-on guides to master AI-Shell's advanced features**

---

## 🎯 Quick Navigation

| Tutorial | Topic | Level | Time | Prerequisites |
|----------|-------|-------|------|---------------|
| [01](./01-health-checks-tutorial.md) | Health Check System | Beginner | 30 min | Basic Python, async/await |
| [02](./02-building-custom-agents.md) | Building Custom Agents | Intermediate | 60 min | Tutorial 01, 03 |
| [03](./03-tool-registry-guide.md) | Tool Registry System | Intermediate | 45 min | Tutorial 01 |
| [04](./04-safety-and-approvals.md) | Safety & Approvals | Advanced | 40 min | Tutorial 02, 03 |

**Total Learning Time**: ~3 hours

---

## 📖 Tutorial Descriptions

### 1. Health Check System
**[01-health-checks-tutorial.md](./01-health-checks-tutorial.md)**

Master the art of system health monitoring with async health checks.

**What You'll Learn:**
- Implement parallel health checks for LLM, database, and system resources
- Configure timeout protection and async-first design patterns
- Create custom health checks for application-specific needs
- Monitor system status with real-time diagnostics
- Troubleshoot common health check issues

**Key Concepts:**
- Async/await patterns
- Timeout management
- Parallel execution
- Health status reporting

**Hands-On Projects:**
- Build a custom API health check
- Create a database connection monitor
- Implement filesystem capacity checks
- Design a complete health monitoring dashboard

---

### 2. Building Custom AI Agents
**[02-building-custom-agents.md](./02-building-custom-agents.md)**

Create autonomous AI agents with multi-step workflows and intelligent planning.

**What You'll Learn:**
- Design agent architectures with planning and execution logic
- Integrate LLM reasoning for task decomposition
- Implement state persistence and checkpointing
- Handle error recovery and rollback scenarios
- Build production-ready autonomous agents

**Key Concepts:**
- Agent planning algorithms
- Tool-based execution
- State management
- Safety validation
- Error recovery patterns

**Hands-On Projects:**
- Build a DatabaseMaintenanceAgent
- Create a FileProcessingAgent
- Implement a DataMigrationAgent
- Design multi-agent orchestration

**Complete Example**: Full DatabaseMaintenanceAgent with backup, optimization, and cleanup capabilities.

---

### 3. Tool Registry System
**[03-tool-registry-guide.md](./03-tool-registry-guide.md)**

Master centralized tool management, validation, and execution for agent workflows.

**What You'll Learn:**
- Register tools with parameter validation using JSON schemas
- Implement five-level risk classification (SAFE → CRITICAL)
- Configure capability-based access control
- Generate LLM-friendly tool descriptions
- Set up rate limiting and execution logging
- Create audit trails for compliance

**Key Concepts:**
- Tool registration and discovery
- JSON Schema validation
- Risk assessment frameworks
- Capability matching
- Rate limiting strategies

**Hands-On Projects:**
- Create validated database backup tools
- Build file processing tools with safety checks
- Implement API integration tools
- Design a complete tool ecosystem

**Real-World Examples**: Database operations, file management, API integrations, and system administration tools.

---

### 4. Safety & Approval System
**[04-safety-and-approvals.md](./04-safety-and-approvals.md)**

Implement multi-layer protection with risk assessment and approval workflows.

**What You'll Learn:**
- Configure automatic risk assessment for operations
- Design approval workflows with human-in-the-loop
- Implement SQL analysis for dangerous patterns
- Set up audit logging for compliance
- Create custom safety constraints
- Test safety logic in development environments

**Key Concepts:**
- Risk level classification
- Approval callback patterns
- SQL injection detection
- Destructive operation prevention
- Audit trail management

**Hands-On Projects:**
- Build a SQL risk analyzer
- Create interactive approval workflows
- Implement custom safety validators
- Design audit logging systems

**Production Deployment**: Best practices for deploying safety systems in production environments.

---

## 🎓 Learning Paths

### Path 1: Foundation (Beginner)
**Goal**: Understand core AI-Shell concepts

1. **Start Here**: [Health Check System](./01-health-checks-tutorial.md) (30 min)
   - Learn async patterns
   - Understand system monitoring
   - Build your first health check

2. **Next**: Explore the main [README.md](../README.md)
   - Review architecture
   - Study module system
   - Try basic commands

**Time Investment**: 1 hour
**Outcome**: Comfortable with AI-Shell basics

---

### Path 2: Agent Development (Intermediate)
**Goal**: Build autonomous AI agents

1. **Prerequisites**: Complete Path 1

2. **Tool Registry**: [Tool Registry Guide](./03-tool-registry-guide.md) (45 min)
   - Register validated tools
   - Implement safety checks
   - Create tool categories

3. **Agent Building**: [Building Custom Agents](./02-building-custom-agents.md) (60 min)
   - Design agent logic
   - Implement planning
   - Handle state persistence

**Time Investment**: 2 hours
**Outcome**: Can build production-ready agents

---

### Path 3: Production Deployment (Advanced)
**Goal**: Deploy safe, reliable autonomous systems

1. **Prerequisites**: Complete Path 1 & 2

2. **Safety Systems**: [Safety & Approvals](./04-safety-and-approvals.md) (40 min)
   - Risk assessment
   - Approval workflows
   - Audit logging

3. **Integration**: Apply all concepts
   - Build complete workflows
   - Deploy to production
   - Monitor and maintain

**Time Investment**: 1.5 hours
**Outcome**: Production-ready autonomous systems

---

## 🛠️ Prerequisites Matrix

| Tutorial | Python | Async/Await | LLM Basics | Database | AI-Shell |
|----------|--------|-------------|------------|----------|----------|
| 01 - Health Checks | ✅ Basic | ✅ Required | ⚪ Optional | ⚪ Optional | ⚪ None |
| 02 - Custom Agents | ✅ Intermediate | ✅ Required | ✅ Required | ⚪ Optional | ✅ Tutorial 01 |
| 03 - Tool Registry | ✅ Intermediate | ✅ Required | ⚪ Optional | ⚪ Optional | ✅ Tutorial 01 |
| 04 - Safety & Approvals | ✅ Advanced | ✅ Required | ⚪ Optional | ✅ Recommended | ✅ Tutorial 02, 03 |

**Legend:**
- ✅ Required
- ⚪ Optional but helpful

---

## 💡 Tutorial Features

### Every Tutorial Includes:

✅ **Clear Learning Objectives**: Know what you'll master
✅ **Hands-On Examples**: Copy-paste code that works
✅ **Real-World Projects**: Build actual applications
✅ **Troubleshooting Guides**: Fix common issues
✅ **Best Practices**: Production-ready patterns
✅ **Performance Tips**: Optimize your implementations
✅ **Testing Strategies**: Validate your code

---

## 🚀 Quick Start Guide

**Never used AI-Shell? Start here:**

1. **Install AI-Shell** (see main [README.md](../README.md))
2. **Complete Tutorial 01** - Health Checks (30 min)
3. **Try examples** from the tutorial
4. **Explore advanced features** based on your needs

**Need help?** Check our [troubleshooting guide](../README.md#troubleshooting) or [open an issue](https://github.com/dimensigon/aishell/issues).

---

## 📊 What You'll Build

By completing all tutorials, you'll build:

### 🏥 Complete Health Monitoring System
- Parallel async health checks
- Custom application monitors
- Real-time diagnostics dashboard
- Alert and notification systems

### 🤖 Production AI Agents
- DatabaseMaintenanceAgent (backup, optimize, cleanup)
- FileProcessingAgent (batch operations, validation)
- DataMigrationAgent (safe data transfers)
- Multi-agent orchestration systems

### 🛠️ Tool Ecosystem
- 10+ validated tools
- Risk-classified operations
- LLM-integrated descriptions
- Complete audit trails

### 🔒 Safety Framework
- Multi-layer risk assessment
- Approval workflow system
- SQL injection protection
- Compliance logging

---

## 🎯 Best Practices

### While Learning:

1. **Follow Sequential Order**: Tutorials build on each other
2. **Type Code Yourself**: Don't just copy-paste
3. **Experiment**: Modify examples to understand concepts
4. **Test Thoroughly**: Run all example code
5. **Read Error Messages**: They're educational
6. **Build Projects**: Apply concepts to real problems

### After Completing Tutorials:

1. **Review Architecture**: Re-read main [README.md](../README.md) with new understanding
2. **Explore Advanced Topics**: Dive into [API docs](../docs/api/)
3. **Join Community**: Share your projects, get help
4. **Contribute**: Add your own tutorials or examples
5. **Build Real Systems**: Apply to production use cases

---

## 📝 Contributing New Tutorials

Want to add a tutorial? We welcome contributions!

### Tutorial Guidelines:

**Structure:**
- Clear table of contents
- Progressive difficulty
- Hands-on examples
- Complete working code
- Troubleshooting section
- Best practices

**Format:**
- Markdown with code blocks
- Descriptive headings
- Visual diagrams (when helpful)
- Estimated completion time
- Prerequisites list

**Quality Standards:**
- All code must be tested
- Examples must be copy-pasteable
- Clear explanations
- Real-world relevance
- Professional writing

### Submission Process:

1. Create tutorial in `/tutorials/` directory
2. Follow naming: `##-descriptive-name.md`
3. Update this index (README.md)
4. Add to main README.md tutorials section
5. Submit pull request with:
   - Tutorial file
   - Example code (if applicable)
   - Updated index files
   - Brief description of what's covered

**Questions?** Open an issue with the `tutorial` label.

---

## 📚 Additional Resources

### Documentation
- **[Main README](../README.md)**: Complete project overview
- **[Architecture Guide](../docs/architecture/)**: System design documents
- **[API Reference](../docs/api/)**: Detailed API documentation
- **[Module Guides](../docs/guides/)**: Deep dives into each module

### Examples
- **[Configuration Examples](../examples/configurations/)**: Sample configs
- **[Custom Module Example](../examples/custom-module/)**: Build your own module
- **[Integration Scripts](../examples/scripts/)**: Automation scripts

### Support
- **Issues**: https://github.com/dimensigon/aishell/issues
- **Discussions**: https://github.com/dimensigon/aishell/discussions
- **Documentation**: https://ai-shell.readthedocs.io

---

## 🎓 Certification Path (Future)

We're working on an AI-Shell certification program:

- **Level 1**: AI-Shell Fundamentals (Tutorials 01-02)
- **Level 2**: Agent Development (Tutorials 03-04)
- **Level 3**: Production Deployment (Advanced topics)

Stay tuned for updates!

---

## 🗺️ Tutorial Roadmap

**Upcoming Tutorials:**

- **05**: Multi-Agent Orchestration
- **06**: Advanced LLM Integration
- **07**: Enterprise Security Patterns
- **08**: Performance Optimization
- **09**: Monitoring & Observability
- **10**: Cloud Deployment Strategies

**Want a specific tutorial?** Request it in [Issues](https://github.com/dimensigon/aishell/issues) with the `tutorial-request` label.

---

## 📊 Tutorial Statistics

- **Total Tutorials**: 4
- **Total Learning Time**: ~3 hours
- **Difficulty Levels**: 1 Beginner, 2 Intermediate, 1 Advanced
- **Hands-On Projects**: 15+
- **Code Examples**: 100+
- **Topics Covered**: Health checks, agents, tools, safety, validation, async patterns

---

**Ready to begin?** Start with [Tutorial 01: Health Check System →](./01-health-checks-tutorial.md)

**Questions?** Check the main [README.md](../README.md) or [open an issue](https://github.com/dimensigon/aishell/issues).

Happy Learning! 🚀
