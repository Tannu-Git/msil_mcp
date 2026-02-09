# MSIL MCP Server - AWS EC2 Deployment Guide

Complete single-command deployment on AWS EC2 t4g.nano (~$3-5/month)

## 🚀 Quick Start (3 Steps)

### Step 1: Prerequisites
```bash
# Install AWS CLI (if not already installed)
# macOS: brew install awscli
# Windows: Download from https://aws.amazon.com/cli/
# Linux: apt-get install awscli

# Configure AWS credentials
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region (ap-northeast-1 recommended), Output (json)
```

### Step 2: Launch EC2 Instance
```bash
# Download the launcher script
curl -O https://raw.githubusercontent.com/Tannu-Git/msil_mcp/master/launch-ec2-aws.sh
chmod +x launch-ec2-aws.sh

# Run it (takes ~5 minutes)
./launch-ec2-aws.sh

# Output will show:
# - Public IP address
# - SSH command to access instance
# - SSH key file location
```

### Step 3: Deploy Application
```bash
# SSH into the instance (from script output)
ssh -i msil-mcp-key.pem ec2-user@<PUBLIC_IP>

# Deployment starts automatically and will show when ready
# Or manually run:
./deploy-aws-ec2.sh

# Wait 10-15 minutes for full deployment
```

---

## 📍 What Gets Deployed

```
Single EC2 t4g.nano Instance
├── FastAPI Backend (port 8000)
│   ├── OpenAPI imports
│   ├── Tool management
│   ├── Service booking
│   ├── Exposure governance
│   └── SQLite database (/data/db/msil_mcp.db)
│
├── Admin UI (React/Vite)
│   ├── Dashboard
│   ├── Tool management
│   ├── User management
│   ├── Authorization policies
│   └── Audit logs
│
├── Chat UI (React/Vite)
│   ├── MCP chat interface
│   ├── Tool execution
│   └── Conversation history
│
└── Nginx Reverse Proxy (ports 80, 443)
    ├── SSL/TLS termination
    ├── Static file serving
    └── API routing
```

---

## 🔐 Access & Credentials

After deployment completes, you'll see:

```
Admin UI: https://<PUBLIC_IP>/admin
Chat UI: https://<PUBLIC_IP>/chat
Backend API: https://<PUBLIC_IP>/api

Demo Credentials:
  Email: admin@msil.com
  Password: admin123
```

⚠️ **SSL Certificate**: Self-signed (browser will show warning - click "Advanced" → "Proceed")

---

## 💾 Costs

| Item | Monthly Cost |
|------|-------------|
| EC2 t4g.nano | $2.81 |
| EBS 40GB (gp3) | $4-6 |
| Data transfer | ~$0.50 |
| **Total** | **~$7-9/month** |

---

## 📊 Storage & Database

**SQLite Database Location**: `/data/db/msil_mcp.db`

**Database Features**:
- ✅ Automatically initialized with schema
- ✅ Persistent across restarts
- ✅ VACUUMed daily (auto-maintenance)
- ✅ Backup snapshots available

**Backup Strategy**:
```bash
# Manual backup (SSH into instance)
aws ec2 create-snapshot --volume-id vol-xxxxx --description "MSIL MCP Backup"

# Or automate with cron:
0 2 * * * /usr/local/bin/aws-snapshot-ebs.sh
```

---

## 🛠️ Common Commands

### SSH Access
```bash
ssh -i msil-mcp-key.pem ec2-user@<PUBLIC_IP>
```

### View Deployment Logs
```bash
# Real-time logs
docker-compose -f /opt/msil_mcp/docker-compose-aws.yml logs -f backend

# Or
tail -f /data/logs/backend.log
```

### Restart Services
```bash
systemctl restart msil-mcp

# Or manual
docker-compose -f /opt/msil_mcp/docker-compose-aws.yml restart
```

### Stop Services
```bash
systemctl stop msil-mcp

# Or
docker-compose -f /opt/msil_mcp/docker-compose-aws.yml down
```

### View System Resources
```bash
htop
df -h  # Disk usage
free -m  # Memory usage
```

---

## 🔄 Updates & Maintenance

### Redeploy Latest Code
```bash
cd /opt/msil_mcp
git pull origin master
docker-compose -f docker-compose-aws.yml build --no-cache
docker-compose -f docker-compose-aws.yml restart
```

### Database Maintenance
```bash
# SQLite VACUUM (manual)
sqlite3 /data/db/msil_mcp.db "VACUUM;"

# Check database size
du -sh /data/db/msil_mcp.db

# Export backup
cp /data/db/msil_mcp.db /data/backups/msil_mcp_$(date +%Y%m%d).db
```

---

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check Docker daemon
docker ps

# View error logs
docker-compose -f /opt/msil_mcp/docker-compose-aws.yml logs backend

# Restart all services
systemctl restart msil-mcp
```

### Memory Issues on t4g.nano
```bash
# Monitor memory usage
free -m
watch -n 1 'free -m'

# Current limits:
# - Backend: 256MB max
# - Nginx: 64MB max
```

### Database Not Accessible
```bash
# Check SQLite file exists
ls -lh /data/db/msil_mcp.db

# Check permissions
stat /data/db/msil_mcp.db

# Verify from backend
docker exec msil-backend ls -lh /data/db/msil_mcp.db
```

### SSL Certificate Issues
```bash
# Check cert expiry
openssl x509 -in /etc/ssl/certs/msil/cert.pem -text -noout | grep -A 2 "Not"

# Regenerate self-signed cert (valid 1 year)
openssl req -x509 -newkey rsa:2048 \
  -keyout /etc/ssl/certs/msil/key.pem \
  -out /etc/ssl/certs/msil/cert.pem \
  -days 365 -nodes -subj "/CN=$(hostname)"
```

---

## 🎯 Performance Tuning

**For t4g.nano (0.5GB RAM):**

1. **Enable Swap** (if needed)
   ```bash
   # Add 1GB swap to EBS volume
   sudo dd if=/dev/zero of=/data/swapfile bs=1G count=1
   sudo mkswap /data/swapfile
   sudo swapon /data/swapfile
   ```

2. **Database Indexes** (if slow queries)
   ```bash
   sqlite3 /data/db/msil_mcp.db << 'EOF'
   CREATE INDEX idx_users_role ON users(role);
   CREATE INDEX idx_permissions_bundle ON permissions(bundle_id);
   EOF
   ```

3. **Nginx Caching** (static files)
   ```nginx
   # Already enabled in default config
   add_header Cache-Control "public, max-age=3600";
   ```

---

## 📈 Scaling Next Steps

When ready to scale beyond demo:

1. **RDS PostgreSQL**: ~$15/month after free tier
   ```bash
   DATABASE_URL="postgresql+asyncpg://user:pass@rds-endpoint/dbname"
   ```

2. **ElastiCache Redis**: ~$15/month for caching
   ```bash
   REDIS_ENABLED=true
   REDIS_URL="redis://cache-endpoint:6379/0"
   ```

3. **Application Load Balancer**: ~$15/month for HA
   - Distribute traffic across multi-AZ instances

4. **CloudFront CDN**: ~$5/month for static assets
   - Geographic distribution of UIs

---

## ⚡ Expected Performance

- **First Request**: ~3-5 seconds (cold start)
- **Subsequent Requests**: <500ms average
- **DB Queries**: ~50-100ms average
- **Concurrent Users**: 50-100 for demo (burst capable)
- **Uptime**: 99.5%+ (single instance, no SLA)

---

## 🔒 Security Notes

### Current Setup (Demo)
- ⚠️ CORS: Set to `*` (allows all origins)
- ⚠️ SSL: Self-signed certificate
- ⚠️ Demo Mode: Auth bypass enabled
- ⚠️ Database: SQLite (no encryption)

### For Production
- Update CORS to specific Vercel/CloudFront domains
- Use AWS ACM certificate
- Disable demo mode
- Enable database encryption (EBS)
- Use RDS with encryption
- Add WAF (Web Application Firewall)
- Enable VPC isolation

---

## 📞 Support

### Debug Information
```bash
# Gather debug info for support
(
  echo "=== System Info ==="
  uname -a
  echo "=== Docker Status ==="
  docker ps
  echo "=== Memory Usage ==="
  free -m
  echo "=== Disk Usage ==="
  df -h /data
  echo "=== Recent Logs ==="
  tail -50 /data/logs/backend.log
) > debug-info.txt
```

### Common Issues Repository
See `docs/troubleshooting/` for:
- Connection issues
- Database problems
- Performance optimization
- SSL/TLS errors

---

## 🎓 Learning Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Docker Compose**: https://docs.docker.com/compose/
- **Nginx Reverse Proxy**: https://nginx.org/en/docs/
- **AWS EC2**: https://aws.amazon.com/ec2/
- **SQLite**: https://www.sqlite.org/

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Tested On**: t4g.nano with Amazon Linux 2
