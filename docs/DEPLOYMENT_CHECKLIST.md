# Agentic AI-Shell Production Deployment Checklist

**Version**: 2.0.0  
**Coverage**: 25.29% (5,883 tests)  
**Last Updated**: 2025-10-12

## ✅ Pre-Deployment Validation

### 1. Code Quality & Testing
- [x] All tests passing (5,883 tests collected)
- [x] Coverage above 25% threshold (25.29%)  
- [x] No critical security vulnerabilities
- [x] Code review completed
- [x] Documentation updated

### 2. Dependencies
- [ ] All Python dependencies in `requirements.txt` verified
- [ ] Optional web dependencies in `requirements-web.txt` reviewed
- [ ] No deprecated packages
- [ ] License compliance checked

### 3. Configuration
- [ ] Environment variables documented
- [ ] Secrets management configured (use `.env` for local, secrets manager for prod)
- [ ] Database connections tested
- [ ] API keys properly secured

## 🚀 Deployment Steps

### 1. Prepare Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-web.txt  # If using web interface
```

### 2. Run Pre-Deployment Tests
```bash
# Run full test suite
pytest tests/ -v

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Check for security issues
bandit -r src/ -ll
```

### 3. CI/CD Pipeline Validation
- [ ] GitHub Actions workflows configured
- [ ] All CI jobs passing
- [ ] Code coverage reporting to Codecov
- [ ] Security scanning enabled

### 4. Database Setup
```bash
# Initialize database migrations
# Configure connection strings
# Test database connectivity
```

### 5. Deploy Application
```bash
# Build package
python -m build

# Install package
pip install dist/agentic_aishell-*.whl

# Run application
agentic-aishell
```

## 📊 Post-Deployment Validation

### 1. Smoke Tests
- [ ] Application starts successfully
- [ ] Database connections working
- [ ] MCP clients initialized
- [ ] UI renders correctly
- [ ] Basic commands execute

### 2. Integration Tests
- [ ] LLM providers responding
- [ ] Vector search functioning
- [ ] Plugin system loading
- [ ] Security modules active

### 3. Performance Checks
- [ ] Response time under 200ms for basic queries
- [ ] Memory usage stable
- [ ] CPU usage acceptable
- [ ] No memory leaks detected

## 🔒 Security Checklist

- [ ] SQL injection protection active (SQL Guard)
- [ ] Input sanitization enabled
- [ ] RBAC permissions configured
- [ ] Audit logging enabled
- [ ] Encryption keys rotated
- [ ] PII redaction working
- [ ] Rate limiting configured

## 📈 Monitoring & Observability

### Metrics to Track
- [ ] Application uptime
- [ ] Response times
- [ ] Error rates
- [ ] Test coverage trends
- [ ] Security scan results
- [ ] Performance metrics

### Logging
- [ ] Application logs configured
- [ ] Error tracking enabled (Sentry/similar)
- [ ] Audit trail active
- [ ] Log rotation configured

## 🔄 Rollback Plan

### If Deployment Fails
1. Stop application
2. Revert to previous version
3. Restore database backup
4. Verify rollback successful
5. Investigate failure cause

### Rollback Commands
```bash
# Git rollback
git revert HEAD
git push

# Package rollback
pip install agentic-aishell==<previous-version>
```

## 📦 PyPI Release Preparation

### 1. Version Bump
```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
# Tag release
git tag -a v2.0.0 -m "Release v2.0.0 - 5883 tests, 25.29% coverage"
git push --tags
```

### 2. Build Package
```bash
python -m build
twine check dist/*
```

### 3. Test Upload (PyPI Test)
```bash
twine upload --repository testpypi dist/*
```

### 4. Production Upload
```bash
twine upload dist/*
```

## 🎯 Success Criteria

✅ **Deployment Successful If:**
- All smoke tests pass
- No critical errors in logs
- Performance within acceptable limits
- Security scans pass
- User acceptance testing complete

## 📞 Support & Escalation

**Issues During Deployment:**
- Check GitHub Issues: https://github.com/dimensigon/aishell/issues
- Review logs: `tail -f logs/aishell.log`
- Monitor metrics dashboard
- Contact: [Team contact info]

## 📚 Additional Resources

- [Testing Guide](TESTING_GUIDE.md)
- [CI/CD Integration](CI_CD_INTEGRATION.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

---

**Deployment Sign-Off:**

- [ ] QA Team Approved
- [ ] Security Team Approved
- [ ] DevOps Team Approved
- [ ] Product Owner Approved

**Deployed By:** _____________  
**Date:** _____________  
**Version:** 2.0.0  
**Commit:** 635d4cc
