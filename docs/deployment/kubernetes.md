# Kubernetes Deployment Guide

**Version:** 1.0.0
**Last Updated:** October 28, 2025
**Target Audience:** DevOps engineers, Kubernetes administrators

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Kubernetes Manifests](#kubernetes-manifests)
4. [Helm Charts](#helm-charts)
5. [Configuration Management](#configuration-management)
6. [Scaling Strategies](#scaling-strategies)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Production Best Practices](#production-best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deploying AI-Shell on Kubernetes with production-ready configurations, including high availability, auto-scaling, monitoring, and security best practices.

### Deployment Options

- **Standalone**: Single namespace deployment
- **Multi-tenant**: Multiple isolated deployments
- **Hybrid**: Mix of shared and isolated resources

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │          aishell Namespace                     │    │
│  │                                                │    │
│  │  ┌──────────────┐      ┌──────────────┐      │    │
│  │  │   Ingress    │      │   Service    │      │    │
│  │  │  Controller  │─────►│ (LoadBalancer)│     │    │
│  │  └──────────────┘      └──────┬───────┘      │    │
│  │                               │               │    │
│  │  ┌────────────────────────────▼─────────┐    │    │
│  │  │      AI-Shell Deployment             │    │    │
│  │  │  ┌──────┐  ┌──────┐  ┌──────┐       │    │    │
│  │  │  │ Pod1 │  │ Pod2 │  │ Pod3 │       │    │    │
│  │  │  └──────┘  └──────┘  └──────┘       │    │    │
│  │  └──────────────────────────────────────┘    │    │
│  │                                                │    │
│  │  ┌──────────────┐      ┌──────────────┐      │    │
│  │  │  PostgreSQL  │      │    Redis     │      │    │
│  │  │  StatefulSet │      │  StatefulSet │      │    │
│  │  └──────────────┘      └──────────────┘      │    │
│  │                                                │    │
│  │  ┌──────────────┐      ┌──────────────┐      │    │
│  │  │ ConfigMap    │      │   Secrets    │      │    │
│  │  └──────────────┘      └──────────────┘      │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Components

- Kubernetes cluster 1.24+ (recommended: 1.28+)
- kubectl CLI installed and configured
- Helm 3.0+ (for Helm deployment)
- Container registry access (Docker Hub, ECR, GCR, etc.)
- Persistent volume provisioner
- Ingress controller (nginx, Traefik, etc.)

### Cluster Resources

**Minimum Requirements:**
- 3 worker nodes
- 4 vCPU per node
- 16 GB RAM per node
- 100 GB storage per node

**Recommended Production:**
- 5+ worker nodes
- 8 vCPU per node
- 32 GB RAM per node
- 500 GB storage per node

### Setup kubectl

```bash
# Configure kubectl
kubectl cluster-info
kubectl get nodes

# Create namespace
kubectl create namespace aishell

# Set default namespace
kubectl config set-context --current --namespace=aishell
```

---

## Kubernetes Manifests

### Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aishell
  labels:
    app.kubernetes.io/name: aishell
    app.kubernetes.io/version: "2.0.0"
```

### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aishell-config
  namespace: aishell
data:
  # Application configuration
  APP_ENV: "production"
  LOG_LEVEL: "info"

  # Database configuration
  DB_HOST: "postgresql.aishell.svc.cluster.local"
  DB_PORT: "5432"
  DB_NAME: "aishell"

  # Redis configuration
  REDIS_HOST: "redis.aishell.svc.cluster.local"
  REDIS_PORT: "6379"

  # LLM configuration
  LLM_PROVIDER: "ollama"
  LLM_MODEL: "llama2"

  # Feature flags
  MULTI_TENANCY_ENABLED: "false"
  RBAC_ENABLED: "true"
  AUDIT_ENABLED: "true"
```

### Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: aishell-secrets
  namespace: aishell
type: Opaque
stringData:
  # Database credentials
  DB_USER: "aishell"
  DB_PASSWORD: "change-me-in-production"

  # Redis password
  REDIS_PASSWORD: "change-me-in-production"

  # Application secrets
  SECRET_KEY: "generate-a-secure-random-key"
  JWT_SECRET: "generate-a-jwt-secret"

  # API keys
  ANTHROPIC_API_KEY: "your-anthropic-api-key"
  OPENAI_API_KEY: "your-openai-api-key"
```

**Note**: In production, use sealed-secrets, external-secrets, or a secrets manager (Vault, AWS Secrets Manager, etc.).

### Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aishell
  namespace: aishell
  labels:
    app: aishell
    version: "2.0.0"
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: aishell
  template:
    metadata:
      labels:
        app: aishell
        version: "2.0.0"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: aishell
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000

      containers:
      - name: aishell
        image: aishell/aishell:2.0.0
        imagePullPolicy: IfNotPresent

        ports:
        - name: http
          containerPort: 8000
          protocol: TCP

        env:
        # Load from ConfigMap
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: aishell-config
              key: APP_ENV

        # Load from Secrets
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: aishell-secrets
              key: DB_PASSWORD

        envFrom:
        - configMapRef:
            name: aishell-config
        - secretRef:
            name: aishell-secrets

        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi

        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3

        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: tmp
          mountPath: /tmp

      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: aishell-data
      - name: config
        configMap:
          name: aishell-config
      - name: tmp
        emptyDir: {}

      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - aishell
              topologyKey: kubernetes.io/hostname
```

### Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: aishell
  namespace: aishell
  labels:
    app: aishell
spec:
  type: ClusterIP
  selector:
    app: aishell
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
```

### Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aishell
  namespace: aishell
  annotations:
    # nginx ingress
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"

    # Rate limiting
    nginx.ingress.kubernetes.io/limit-rps: "100"
    nginx.ingress.kubernetes.io/limit-connections: "50"

    # Timeouts
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"

    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://aishell.example.com"

    # cert-manager
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - aishell.example.com
    secretName: aishell-tls
  rules:
  - host: aishell.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: aishell
            port:
              number: 80
```

### PersistentVolumeClaim

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: aishell-data
  namespace: aishell
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: standard  # or gp3, pd-ssd, etc.
  resources:
    requests:
      storage: 100Gi
```

### PostgreSQL StatefulSet

```yaml
# postgresql-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: aishell
spec:
  serviceName: postgresql
  replicas: 3
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:14-alpine
        ports:
        - containerPort: 5432
          name: postgresql
        env:
        - name: POSTGRES_DB
          value: aishell
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: aishell-secrets
              key: DB_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: aishell-secrets
              key: DB_PASSWORD
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        resources:
          requests:
            cpu: 500m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 8Gi
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - aishell
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - aishell
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: standard
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
  namespace: aishell
spec:
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None
```

### Redis StatefulSet

```yaml
# redis-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: aishell
spec:
  serviceName: redis
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
        - redis-server
        - --requirepass
        - $(REDIS_PASSWORD)
        - --appendonly
        - "yes"
        ports:
        - containerPort: 6379
          name: redis
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: aishell-secrets
              key: REDIS_PASSWORD
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 1Gi
        volumeMounts:
        - name: data
          mountPath: /data
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: standard
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: aishell
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  clusterIP: None
```

### ServiceAccount and RBAC

```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aishell
  namespace: aishell
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: aishell
  namespace: aishell
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: aishell
  namespace: aishell
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: aishell
subjects:
- kind: ServiceAccount
  name: aishell
  namespace: aishell
```

### Deploy All Resources

```bash
# Apply all manifests
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f rbac.yaml
kubectl apply -f pvc.yaml
kubectl apply -f postgresql-statefulset.yaml
kubectl apply -f redis-statefulset.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Verify deployment
kubectl get all -n aishell
kubectl get pvc -n aishell
kubectl get ingress -n aishell

# Check pod logs
kubectl logs -f deployment/aishell -n aishell
```

---

## Helm Charts

### Helm Chart Structure

```
aishell-chart/
├── Chart.yaml
├── values.yaml
├── values-prod.yaml
├── values-staging.yaml
├── templates/
│   ├── NOTES.txt
│   ├── _helpers.tpl
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── serviceaccount.yaml
│   └── tests/
│       └── test-connection.yaml
└── charts/
    ├── postgresql/
    └── redis/
```

### Chart.yaml

```yaml
apiVersion: v2
name: aishell
description: AI-Shell Kubernetes Helm Chart
version: 2.0.0
appVersion: "2.0.0"
keywords:
  - aishell
  - ai
  - database
  - shell
home: https://aishell.example.com
sources:
  - https://github.com/your-org/aishell
maintainers:
  - name: AI-Shell Team
    email: team@aishell.example.com
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
  - name: redis
    version: "17.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
```

### values.yaml

```yaml
# Default values for aishell

replicaCount: 3

image:
  repository: aishell/aishell
  tag: "2.0.0"
  pullPolicy: IfNotPresent

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

securityContext:
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: false
  allowPrivilegeEscalation: false

service:
  type: ClusterIP
  port: 80
  targetPort: 8000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: aishell.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: aishell-tls
      hosts:
        - aishell.example.com

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

persistence:
  enabled: true
  storageClass: standard
  size: 100Gi
  accessMode: ReadWriteOnce

postgresql:
  enabled: true
  auth:
    username: aishell
    password: changeme
    database: aishell
  primary:
    persistence:
      size: 100Gi

redis:
  enabled: true
  auth:
    password: changeme
  master:
    persistence:
      size: 10Gi

config:
  appEnv: production
  logLevel: info
  multiTenancyEnabled: false
  rbacEnabled: true
  auditEnabled: true

secrets:
  anthropicApiKey: ""
  openaiApiKey: ""
  secretKey: ""
  jwtSecret: ""
```

### Install Helm Chart

```bash
# Add Bitnami repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install chart
helm install aishell ./aishell-chart \
  --namespace aishell \
  --create-namespace \
  --values values-prod.yaml

# Upgrade chart
helm upgrade aishell ./aishell-chart \
  --namespace aishell \
  --values values-prod.yaml

# Uninstall chart
helm uninstall aishell --namespace aishell

# View release
helm list -n aishell
helm status aishell -n aishell
```

---

## Configuration Management

### External Secrets Operator

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: aishell
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: aishell
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: aishell-secrets
  namespace: aishell
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: aishell-secrets
    creationPolicy: Owner
  data:
  - secretKey: DB_PASSWORD
    remoteRef:
      key: aishell/production/db-password
  - secretKey: ANTHROPIC_API_KEY
    remoteRef:
      key: aishell/production/anthropic-api-key
```

---

## Scaling Strategies

### Horizontal Pod Autoscaler (HPA)

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aishell
  namespace: aishell
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aishell
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
```

### Pod Disruption Budget

```yaml
# pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: aishell
  namespace: aishell
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: aishell
```

---

## Monitoring and Logging

### ServiceMonitor (Prometheus)

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: aishell
  namespace: aishell
spec:
  selector:
    matchLabels:
      app: aishell
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### Grafana Dashboard ConfigMap

```yaml
# grafana-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aishell-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  aishell-dashboard.json: |
    {
      "dashboard": {
        "title": "AI-Shell Metrics",
        "panels": [...]
      }
    }
```

---

## Production Best Practices

### Security Hardening

1. **Network Policies**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: aishell-network-policy
  namespace: aishell
spec:
  podSelector:
    matchLabels:
      app: aishell
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - protocol: TCP
      port: 5432
```

2. **Pod Security Standards**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aishell
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Resource Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: aishell-quota
  namespace: aishell
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "10"
```

---

## Troubleshooting

### Common Issues

```bash
# Check pod status
kubectl get pods -n aishell
kubectl describe pod <pod-name> -n aishell

# View logs
kubectl logs -f deployment/aishell -n aishell
kubectl logs --previous <pod-name> -n aishell

# Execute commands in pod
kubectl exec -it <pod-name> -n aishell -- /bin/bash

# Check events
kubectl get events -n aishell --sort-by='.lastTimestamp'

# Debug networking
kubectl run debug --rm -it --image=nicolaka/netshoot -n aishell -- /bin/bash
```

---

**Document Version:** 2.0.0
**Last Updated:** October 28, 2025
**Next Review:** January 2026
