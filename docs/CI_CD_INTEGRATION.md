# CI/CD Integration Guide for AIShell

## Overview

This guide provides comprehensive instructions for integrating AIShell tests and coverage into continuous integration and deployment pipelines.

## Table of Contents

1. [GitHub Actions](#github-actions)
2. [GitLab CI](#gitlab-ci)
3. [Jenkins](#jenkins)
4. [Coverage Badges](#coverage-badges)
5. [Quality Gates](#quality-gates)
6. [Workflow Customization](#workflow-customization)
7. [Secrets Management](#secrets-management)
8. [Troubleshooting](#troubleshooting)

## GitHub Actions

### Complete Workflow

Create `.github/workflows/tests.yml`:

```yaml
name: Tests and Coverage

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  test:
    name: Test Python ${{ matrix.python-version }}
    runs-on: ${{ matrix.os }}

    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12', '3.13']

    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for better analysis

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests with coverage
      run: |
        pytest tests/ \
          --cov=. \
          --cov-report=xml \
          --cov-report=html \
          --cov-report=term-missing \
          -v \
          --junitxml=pytest-results.xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-${{ matrix.os }}-py${{ matrix.python-version }}
        fail_ci_if_error: false

    - name: Upload coverage to Coveralls
      if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'
      uses: coverallsapp/github-action@v2
      with:
        github-token: ${{ secrets.GITHUB_TOKEN }}

    - name: Archive coverage report
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: coverage-report-${{ matrix.os }}-py${{ matrix.python-version }}
        path: htmlcov/
        retention-days: 30

    - name: Archive test results
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: pytest-results-${{ matrix.os }}-py${{ matrix.python-version }}
        path: pytest-results.xml
        retention-days: 30

    - name: Publish test results
      uses: EnricoMi/publish-unit-test-result-action@v2
      if: always() && matrix.os == 'ubuntu-latest'
      with:
        files: pytest-results.xml

    - name: Check coverage threshold
      run: |
        coverage report --fail-under=20

  quality:
    name: Code Quality
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run flake8
      run: |
        flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics

    - name: Run pylint
      run: |
        pylint src/ --fail-under=7.0

    - name: Run mypy
      run: |
        mypy src/

    - name: Run bandit (security)
      run: |
        bandit -r src/ -f json -o bandit-report.json

    - name: Upload security report
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: security-report
        path: bandit-report.json

  integration:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: test

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run integration tests
      env:
        POSTGRES_HOST: localhost
        POSTGRES_PORT: 5432
        REDIS_HOST: localhost
        REDIS_PORT: 6379
      run: |
        pytest tests/ -m integration -v
```

### PR Comment with Coverage

Create `.github/workflows/pr-comment.yml`:

```yaml
name: Coverage Comment

on:
  workflow_run:
    workflows: ["Tests and Coverage"]
    types: [completed]

jobs:
  comment:
    runs-on: ubuntu-latest
    if: github.event.workflow_run.event == 'pull_request'

    steps:
    - name: Download coverage
      uses: actions/download-artifact@v4
      with:
        name: coverage-report-ubuntu-latest-py3.11

    - name: Generate coverage comment
      uses: py-cov-action/python-coverage-comment-action@v3
      with:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## GitLab CI

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - quality
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - venv/

.test_template: &test_template
  stage: test
  before_script:
    - python --version
    - pip install virtualenv
    - virtualenv venv
    - source venv/bin/activate
    - pip install -r requirements.txt
    - pip install -r requirements-dev.txt
  script:
    - pytest tests/ --cov=. --cov-report=xml --cov-report=html --cov-report=term
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
      junit: pytest-results.xml
    paths:
      - htmlcov/
    expire_in: 1 week
  coverage: '/TOTAL.*\s+(\d+%)$/'

test:python3.9:
  <<: *test_template
  image: python:3.9

test:python3.10:
  <<: *test_template
  image: python:3.10

test:python3.11:
  <<: *test_template
  image: python:3.11

test:python3.12:
  <<: *test_template
  image: python:3.12

code_quality:
  stage: quality
  image: python:3.11
  script:
    - pip install flake8 pylint mypy bandit
    - flake8 src/ tests/
    - pylint src/ --fail-under=7.0
    - mypy src/
    - bandit -r src/
  allow_failure: true

pages:
  stage: deploy
  dependencies:
    - test:python3.11
  script:
    - mkdir -p public
    - cp -r htmlcov/* public/
  artifacts:
    paths:
      - public
  only:
    - main
```

## Jenkins

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any

    parameters {
        choice(name: 'PYTHON_VERSION', choices: ['3.9', '3.10', '3.11', '3.12'], description: 'Python version')
    }

    environment {
        VENV = "${WORKSPACE}/venv"
        PATH = "${VENV}/bin:${PATH}"
    }

    stages {
        stage('Setup') {
            steps {
                sh """
                    python${params.PYTHON_VERSION} -m venv ${VENV}
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r requirements-dev.txt
                """
            }
        }

        stage('Test') {
            steps {
                sh """
                    pytest tests/ \
                        --cov=. \
                        --cov-report=xml \
                        --cov-report=html \
                        --junitxml=pytest-results.xml
                """
            }
            post {
                always {
                    junit 'pytest-results.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }

        stage('Quality Gate') {
            steps {
                script {
                    def coverage = sh(
                        script: "coverage report | grep TOTAL | awk '{print \$4}' | sed 's/%//'",
                        returnStdout: true
                    ).trim().toFloat()

                    if (coverage < 20) {
                        error("Coverage ${coverage}% is below threshold 20%")
                    }
                }
            }
        }

        stage('Security Scan') {
            steps {
                sh 'bandit -r src/ -f json -o bandit-report.json'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.json'
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
```

## Coverage Badges

### Codecov Badge

```markdown
[![codecov](https://codecov.io/gh/USERNAME/AIShell/branch/main/graph/badge.svg)](https://codecov.io/gh/USERNAME/AIShell)
```

### Coveralls Badge

```markdown
[![Coverage Status](https://coveralls.io/repos/github/USERNAME/AIShell/badge.svg?branch=main)](https://coveralls.io/github/USERNAME/AIShell?branch=main)
```

### Shields.io Dynamic Badge

```markdown
![Test Coverage](https://img.shields.io/badge/coverage-23%25-yellow)
```

### Generate Badge from coverage.json

```python
# scripts/generate_badge.py
import json

with open('coverage.json') as f:
    data = json.load(f)
    coverage = data['totals']['percent_covered']

    if coverage >= 80:
        color = 'brightgreen'
    elif coverage >= 60:
        color = 'green'
    elif coverage >= 40:
        color = 'yellow'
    elif coverage >= 20:
        color = 'orange'
    else:
        color = 'red'

    badge_url = f"https://img.shields.io/badge/coverage-{coverage:.0f}%25-{color}"
    print(badge_url)
```

## Quality Gates

### Coverage Threshold

```yaml
# pyproject.toml
[tool.coverage.report]
fail_under = 20
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

### Pre-merge Checks

```yaml
# .github/workflows/pr-checks.yml
name: PR Checks

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest tests/ --cov=. --cov-report=json

    - name: Check coverage delta
      run: |
        python scripts/check_coverage_delta.py \
          --current coverage.json \
          --base main \
          --threshold 20
```

## Workflow Customization

### Matrix Strategy

Test across multiple environments:

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python: ['3.9', '3.10', '3.11', '3.12']
    database: [postgres, mysql, sqlite]
    exclude:
      - os: windows-latest
        database: postgres
```

### Conditional Execution

```yaml
- name: Run slow tests
  if: github.event_name == 'schedule'
  run: pytest tests/ -m slow

- name: Deploy on success
  if: success() && github.ref == 'refs/heads/main'
  run: ./deploy.sh
```

### Caching

```yaml
- name: Cache pip packages
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

- name: Cache pytest cache
  uses: actions/cache@v4
  with:
    path: .pytest_cache
    key: ${{ runner.os }}-pytest-${{ hashFiles('tests/**/*.py') }}
```

## Secrets Management

### GitHub Secrets

Add secrets in repository settings:

```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  API_KEY: ${{ secrets.API_KEY }}
  ENCRYPTION_KEY: ${{ secrets.ENCRYPTION_KEY }}
```

### Environment Files

```yaml
- name: Create .env file
  run: |
    cat << EOF > .env
    DATABASE_URL=${{ secrets.DATABASE_URL }}
    API_KEY=${{ secrets.API_KEY }}
    EOF
```

### Vault Integration

```yaml
- name: Import Secrets
  uses: hashicorp/vault-action@v2
  with:
    url: ${{ secrets.VAULT_URL }}
    token: ${{ secrets.VAULT_TOKEN }}
    secrets: |
      secret/data/aishell database_url | DATABASE_URL ;
      secret/data/aishell api_key | API_KEY
```

## Troubleshooting

### Common Issues

#### 1. Coverage Not Uploading

```yaml
# Ensure coverage file exists
- name: Check coverage file
  run: |
    ls -la coverage.xml
    cat coverage.xml | head -20

# Add debug output
- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    verbose: true
```

#### 2. Tests Timeout

```yaml
# Increase timeout
- name: Run tests
  timeout-minutes: 30
  run: pytest tests/
```

#### 3. Out of Memory

```yaml
# Run tests in smaller batches
- name: Run tests
  run: |
    pytest tests/agents/ --cov=src/agents
    pytest tests/database/ --cov=src/database --cov-append
```

#### 4. Flaky Tests

```yaml
# Retry failed tests
- name: Run tests
  run: pytest tests/ --reruns 3 --reruns-delay 5
```

### Debug CI Logs

```yaml
- name: Debug info
  if: always()
  run: |
    echo "Python version: $(python --version)"
    echo "Pip version: $(pip --version)"
    echo "Installed packages:"
    pip list
    echo "Environment variables:"
    env | grep -v SECRET
```

## Best Practices

1. **Run tests on every push and PR**
2. **Use matrix builds** for multiple Python versions
3. **Cache dependencies** to speed up builds
4. **Upload artifacts** for debugging
5. **Set coverage thresholds** as quality gates
6. **Run security scans** regularly
7. **Use scheduled runs** for comprehensive tests
8. **Generate reports** for visibility
9. **Keep workflows DRY** with reusable actions
10. **Monitor CI performance** and optimize

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab CI Documentation](https://docs.gitlab.com/ee/ci/)
- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Codecov Documentation](https://docs.codecov.com/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)

---

**Last Updated**: 2025-10-12
**Version**: 2.0.0
**Maintainers**: AIShell DevOps Team
