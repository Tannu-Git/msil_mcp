# Operations Runbook

**Document Version**: 2.0  
**Last Updated**: January 31, 2026  
**Classification**: Internal

---

## 1. Overview

This runbook provides operational procedures for the MSIL MCP Platform, including deployment, monitoring, incident response, and maintenance tasks.

---

## 2. Service Health Checks

### 2.1 Health Check Endpoints

```
┌──────────────────────────────────────────────────────────────┐
│                   HEALTH CHECK MATRIX                        │
├──────────────────┬───────────────────────┬──────────────────┤
│ Service          │ Endpoint              │ Expected Status  │
├──────────────────┼───────────────────────┼──────────────────┤
│ MCP Server       │ /health               │ 200 OK           │
│ MCP Server Ready │ /ready                │ 200 OK           │
│ Admin Portal     │ /api/health           │ 200 OK           │
│ Chat UI          │ /                     │ 200 OK           │
│ PostgreSQL       │ pg_isready            │ accepting        │
│ Redis            │ redis-cli ping        │ PONG             │
└──────────────────┴───────────────────────┴──────────────────┘
```

### 2.2 Quick Health Check Script

```bash
#!/bin/bash
# healthcheck.sh

echo "=== MCP Platform Health Check ==="

# MCP Server
curl -sf http://mcp-server:8000/health && echo "✓ MCP Server: Healthy" || echo "✗ MCP Server: Unhealthy"

# Admin Portal
curl -sf http://admin-portal:3001/api/health && echo "✓ Admin Portal: Healthy" || echo "✗ Admin Portal: Unhealthy"

# Chat UI
curl -sf http://chat-ui:3000/ && echo "✓ Chat UI: Healthy" || echo "✗ Chat UI: Unhealthy"

# PostgreSQL
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d mcp -c "SELECT 1" &>/dev/null && echo "✓ PostgreSQL: Healthy" || echo "✗ PostgreSQL: Unhealthy"

# Redis
redis-cli -h $REDIS_HOST ping | grep -q PONG && echo "✓ Redis: Healthy" || echo "✗ Redis: Unhealthy"

echo "================================="
```

---

## 3. Deployment Procedures

### 3.1 Pre-Deployment Checklist

```
□ Review change request and approvals
□ Verify staging environment tests passed
□ Check current production metrics baseline
□ Confirm rollback plan
□ Notify stakeholders of deployment window
□ Verify backup completed (if database changes)
□ Confirm monitoring dashboards accessible
```

### 3.2 Standard Deployment (Kubernetes)

```bash
# Step 1: Update image tag in deployment
kubectl set image deployment/mcp-server \
  mcp-server=msil-mcp-server:v2.1.0 \
  -n mcp-production

# Step 2: Monitor rollout
kubectl rollout status deployment/mcp-server \
  -n mcp-production --timeout=300s

# Step 3: Verify pods healthy
kubectl get pods -n mcp-production \
  -l app=mcp-server -o wide

# Step 4: Verify health endpoint
kubectl exec -it deploy/mcp-server -n mcp-production -- \
  curl -s localhost:8000/health

# Step 5: Run smoke tests
./scripts/smoke-tests.sh production
```

### 3.3 Blue-Green Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                  BLUE-GREEN DEPLOYMENT                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────┐        ┌───────────────┐                │
│  │  Blue (v1)    │ ◄───── │   ALB/NLB     │ (Current)      │
│  │  Active       │        └───────────────┘                │
│  └───────────────┘              │                          │
│                                 │ Switch                    │
│  ┌───────────────┐              ▼                          │
│  │  Green (v2)   │        ┌───────────────┐                │
│  │  Standby      │ ◄───── │   ALB/NLB     │ (After)       │
│  └───────────────┘        └───────────────┘                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Deploy to green environment
kubectl apply -f kubernetes/green-deployment.yaml -n mcp-production

# Wait for green to be healthy
kubectl rollout status deployment/mcp-server-green -n mcp-production

# Run validation tests against green
./scripts/validate-green.sh

# Switch traffic (update service selector)
kubectl patch service mcp-server -n mcp-production \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Monitor for issues (10 minutes)
sleep 600

# If successful, scale down blue
kubectl scale deployment/mcp-server-blue --replicas=0 -n mcp-production
```

### 3.4 Rollback Procedure

```bash
# Immediate rollback
kubectl rollout undo deployment/mcp-server -n mcp-production

# Rollback to specific revision
kubectl rollout undo deployment/mcp-server \
  --to-revision=5 -n mcp-production

# Verify rollback
kubectl rollout status deployment/mcp-server -n mcp-production
```

---

## 4. Incident Response

### 4.1 Severity Matrix

| Severity | Impact | Response Time | Examples |
|----------|--------|---------------|----------|
| **P1 Critical** | Complete outage | 15 minutes | All tools failing, DB down |
| **P2 High** | Major degradation | 30 minutes | >50% error rate, auth failure |
| **P3 Medium** | Partial impact | 2 hours | Single tool failing, slow response |
| **P4 Low** | Minor issue | 24 hours | UI glitch, log warnings |

### 4.2 Incident Response Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 INCIDENT RESPONSE FLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ Detect  │───►│ Triage  │───►│Mitigate │───►│ Resolve │  │
│  │         │    │& Notify │    │         │    │         │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       │              │              │              │        │
│       ▼              ▼              ▼              ▼        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ Alert   │    │ Create  │    │ Apply   │    │ Post    │  │
│  │ Trigger │    │ Incident│    │ Fix     │    │ Mortem  │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Common Incident Playbooks

#### 4.3.1 High Error Rate (>5%)

```bash
# 1. Check current error rates
kubectl logs -l app=mcp-server -n mcp-production --tail=100 | grep ERROR

# 2. Check resource utilization
kubectl top pods -n mcp-production

# 3. Check backend connectivity
kubectl exec -it deploy/mcp-server -n mcp-production -- \
  curl -v https://apim.msil.com/health

# 4. If APIM issue, check circuit breaker status
kubectl exec -it deploy/mcp-server -n mcp-production -- \
  curl localhost:8000/metrics | grep circuit_breaker

# 5. If needed, temporarily disable affected tools
curl -X PATCH https://admin.mcp.msil.com/api/admin/tools/affected_tool \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"enabled": false}'
```

#### 4.3.2 Database Connection Issues

```bash
# 1. Check PostgreSQL status
kubectl exec -it sts/postgresql -n mcp-production -- pg_isready

# 2. Check connection pool status
kubectl exec -it deploy/mcp-server -n mcp-production -- \
  curl localhost:8000/metrics | grep db_pool

# 3. Check for connection leaks
kubectl exec -it sts/postgresql -n mcp-production -- \
  psql -U mcp -c "SELECT count(*) FROM pg_stat_activity WHERE state='idle';"

# 4. If needed, restart server pods (graceful)
kubectl rollout restart deployment/mcp-server -n mcp-production
```

#### 4.3.3 Memory/CPU Exhaustion

```bash
# 1. Check current usage
kubectl top pods -n mcp-production --sort-by=memory

# 2. Check for memory leaks
kubectl logs deploy/mcp-server -n mcp-production | grep -i memory

# 3. Scale up if needed
kubectl scale deployment/mcp-server --replicas=6 -n mcp-production

# 4. Check HPA status
kubectl get hpa -n mcp-production

# 5. If leak suspected, trigger restart
kubectl rollout restart deployment/mcp-server -n mcp-production
```

#### 4.3.4 Authentication Failures

```bash
# 1. Check Azure AD connectivity
kubectl exec -it deploy/mcp-server -n mcp-production -- \
  curl -v https://login.microsoftonline.com/{tenant}/.well-known/openid-configuration

# 2. Check JWKS cache
kubectl exec -it deploy/mcp-server -n mcp-production -- \
  curl localhost:8000/debug/jwks-status

# 3. Verify certificate validity
openssl s_client -connect login.microsoftonline.com:443 -servername login.microsoftonline.com

# 4. Clear JWKS cache if corrupted
kubectl exec -it deploy/mcp-server -n mcp-production -- \
  curl -X POST localhost:8000/debug/clear-jwks-cache
```

---

## 5. Maintenance Procedures

### 5.1 Scheduled Maintenance Window

| Activity | Frequency | Window | Duration |
|----------|-----------|--------|----------|
| Security patches | Weekly | Sunday 02:00-04:00 IST | 2 hours |
| Database maintenance | Monthly | 1st Sunday 01:00-05:00 IST | 4 hours |
| Kubernetes upgrades | Quarterly | Planned window | 8 hours |
| Certificate rotation | Quarterly | Before expiry | 1 hour |

### 5.2 Database Maintenance

```bash
# 1. Take backup before maintenance
pg_dump -h $DB_HOST -U mcp -d mcp | gzip > backup_$(date +%Y%m%d).sql.gz
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://msil-mcp-backups/manual/

# 2. Vacuum and analyze
psql -h $DB_HOST -U mcp -d mcp -c "VACUUM ANALYZE;"

# 3. Reindex if needed
psql -h $DB_HOST -U mcp -d mcp -c "REINDEX DATABASE mcp;"

# 4. Check table sizes
psql -h $DB_HOST -U mcp -d mcp -c "
SELECT tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC
LIMIT 10;"
```

### 5.3 Log Rotation & Cleanup

```bash
# Clean audit logs older than 365 days (immutable, query only)
# Note: S3 WORM prevents deletion - use lifecycle policies instead

# Clean cache older than 24 hours
redis-cli -h $REDIS_HOST --scan --pattern "cache:*" | xargs -L 1000 redis-cli -h $REDIS_HOST DEL

# Archive CloudWatch logs (automated via retention policy)
aws logs put-retention-policy \
  --log-group-name /mcp/production/server \
  --retention-in-days 365
```

### 5.4 Certificate Rotation

```bash
# 1. Generate new certificate
openssl req -new -key server.key -out server.csr
# Submit to CA...

# 2. Update Kubernetes secret
kubectl create secret tls mcp-tls-new \
  --cert=new-server.crt --key=server.key \
  -n mcp-production --dry-run=client -o yaml | kubectl apply -f -

# 3. Update ingress to use new secret
kubectl patch ingress mcp-ingress -n mcp-production \
  -p '{"spec":{"tls":[{"secretName":"mcp-tls-new"}]}}'

# 4. Verify certificate
curl -v https://mcp.msil.com 2>&1 | grep "expire date"
```

---

## 6. Troubleshooting Guide

### 6.1 Common Issues

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| 401 Unauthorized | Token expired | Refresh token |
| 403 Forbidden | Insufficient permissions | Check RBAC policies |
| 429 Too Many Requests | Rate limit exceeded | Wait or request limit increase |
| 500 Internal Error | Backend failure | Check logs, verify backend |
| 503 Service Unavailable | Circuit breaker open | Wait for recovery |
| Slow responses | Resource exhaustion | Scale up, check DB |

### 6.2 Log Analysis Queries

```bash
# Find errors in last hour
aws logs filter-log-events \
  --log-group-name /mcp/production/server \
  --start-time $(date -d "1 hour ago" +%s000) \
  --filter-pattern "ERROR"

# Find failed tool executions
aws logs filter-log-events \
  --log-group-name /mcp/production/server \
  --filter-pattern '{ $.status = "error" && $.event_type = "tool_execution" }'

# Find slow requests (>5s)
aws logs filter-log-events \
  --log-group-name /mcp/production/server \
  --filter-pattern '{ $.duration_ms > 5000 }'

# Find specific user's activity
aws logs filter-log-events \
  --log-group-name /mcp/production/server \
  --filter-pattern '{ $.user_id = "user@msil.com" }'
```

### 6.3 Performance Diagnostics

```bash
# Get current metrics
kubectl exec -it deploy/mcp-server -n mcp-production -- \
  curl localhost:8000/metrics | grep -E "request_duration|requests_total|error"

# Check database query performance
psql -h $DB_HOST -U mcp -d mcp -c "
SELECT query, calls, mean_time, total_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;"

# Check Redis memory usage
redis-cli -h $REDIS_HOST INFO memory

# Check network latency to backend
kubectl exec -it deploy/mcp-server -n mcp-production -- \
  time curl -o /dev/null -s -w "%{time_total}\n" https://apim.msil.com/health
```

---

## 7. Backup & Recovery

### 7.1 Backup Schedule

| Component | Frequency | Retention | Location |
|-----------|-----------|-----------|----------|
| PostgreSQL | Hourly | 24 hours | RDS snapshots |
| PostgreSQL | Daily | 30 days | RDS + S3 |
| PostgreSQL | Weekly | 1 year | S3 Glacier |
| Redis | Every 6 hours | 7 days | S3 |
| Kubernetes configs | Daily | 90 days | S3 |
| Audit logs | Continuous | 7 years | S3 WORM |

### 7.2 Recovery Procedures

#### Database Point-in-Time Recovery

```bash
# 1. Identify target recovery time
TARGET_TIME="2026-01-31 10:30:00"

# 2. Restore from RDS snapshot
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier mcp-production \
  --target-db-instance-identifier mcp-recovery \
  --restore-time "$TARGET_TIME" \
  --db-subnet-group-name mcp-db-subnet

# 3. Wait for instance available
aws rds wait db-instance-available \
  --db-instance-identifier mcp-recovery

# 4. Verify data integrity
psql -h mcp-recovery... -U mcp -d mcp -c "SELECT COUNT(*) FROM tools;"

# 5. Switch connection string (update secret)
kubectl create secret generic mcp-db-secret \
  --from-literal=url="postgresql://mcp:xxx@mcp-recovery.xxx.rds.amazonaws.com:5432/mcp" \
  -n mcp-production --dry-run=client -o yaml | kubectl apply -f -

# 6. Restart services
kubectl rollout restart deployment/mcp-server -n mcp-production
```

---

## 8. Contacts & Escalation

### 8.1 Escalation Matrix

| Level | Role | Contact | SLA |
|-------|------|---------|-----|
| L1 | On-call Engineer | oncall@nagarro.com | 15 min |
| L2 | Platform Lead | platform-lead@nagarro.com | 30 min |
| L3 | Architect | architect@nagarro.com | 1 hour |
| L4 | VP Engineering | vp-eng@nagarro.com | 2 hours |

### 8.2 External Contacts

| Service | Support | Priority Line |
|---------|---------|---------------|
| AWS Support | AWS Console | Business/Enterprise |
| Azure AD | Microsoft Support | Premium Support |
| Nagarro | support@nagarro.com | +91-xxx-xxx-xxxx |

---

*Document Classification: Internal | Last Review: January 31, 2026*
