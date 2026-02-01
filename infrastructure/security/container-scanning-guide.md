# Container Security Scanning Configuration

## Overview
This directory contains configuration for automated container security scanning using multiple tools:
- **Trivy**: Vulnerability and misconfiguration scanning
- **Grype**: CVE vulnerability scanning  
- **Snyk**: Container and dependency scanning
- **Docker Bench**: CIS Docker Benchmark compliance
- **Hadolint**: Dockerfile best practices
- **Syft**: SBOM (Software Bill of Materials) generation

## Scanning Tools

### 1. Trivy
**Purpose**: Comprehensive vulnerability and IaC scanning

**Features**:
- CVE detection in OS packages and application dependencies
- Kubernetes manifest scanning
- Dockerfile misconfiguration detection
- Secret detection

**Configuration**: `.trivyignore` file for suppressing false positives

**Usage**:
```bash
# Scan Docker image
trivy image mcp-server:latest

# Scan with severity filter
trivy image --severity CRITICAL,HIGH mcp-server:latest

# Generate JSON report
trivy image -f json -o trivy-report.json mcp-server:latest
```

### 2. Grype
**Purpose**: CVE vulnerability scanning

**Features**:
- Fast vulnerability scanning
- Multiple output formats
- Extensive vulnerability database

**Usage**:
```bash
# Scan Docker image
grype mcp-server:latest

# Fail on high severity
grype mcp-server:latest --fail-on high

# Scan SBOM
grype sbom:sbom.spdx.json
```

### 3. Snyk
**Purpose**: Developer-first security scanning

**Features**:
- Container vulnerability scanning
- Dependency scanning
- Fix suggestions
- Integration with CI/CD

**Setup**:
```bash
# Set Snyk token
export SNYK_TOKEN=your-token-here

# Scan container
snyk container test mcp-server:latest --file=Dockerfile.hardened
```

### 4. Docker Bench Security
**Purpose**: CIS Docker Benchmark compliance

**Features**:
- Host configuration checks
- Docker daemon configuration
- Container runtime checks
- Security operations checks

**Usage**:
```bash
# Run Docker Bench
docker run -it --net host --pid host --userns host --cap-add audit_control \
  -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
  -v /var/lib:/var/lib \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/lib/systemd:/usr/lib/systemd \
  -v /etc:/etc --label docker_bench_security \
  docker/docker-bench-security
```

### 5. Hadolint
**Purpose**: Dockerfile linting

**Features**:
- Best practice validation
- Common mistake detection
- Security recommendations

**Usage**:
```bash
# Lint Dockerfile
hadolint Dockerfile.hardened

# Ignore specific rules
hadolint --ignore DL3008 Dockerfile.hardened
```

### 6. Syft
**Purpose**: SBOM generation

**Features**:
- Generate SPDX/CycloneDX SBOMs
- Multi-format support
- Dependency relationship mapping

**Usage**:
```bash
# Generate SBOM
syft mcp-server:latest -o spdx-json > sbom.spdx.json

# Generate CycloneDX format
syft mcp-server:latest -o cyclonedx-json > sbom.cyclonedx.json
```

## CI/CD Integration

### GitHub Actions Workflow
The `.github/workflows/container-security.yml` workflow runs on:
- Push to main/develop branches
- Pull requests
- Daily scheduled scan (2 AM UTC)

### Workflow Jobs
1. **trivy-scan**: Vulnerability and config scanning
2. **grype-scan**: CVE scanning
3. **snyk-scan**: Comprehensive security analysis
4. **docker-bench**: CIS compliance check
5. **hadolint**: Dockerfile linting
6. **sbom-generation**: Generate and scan SBOM
7. **cve-monitoring**: Monitor base image CVEs
8. **security-report**: Consolidated report generation

## Vulnerability Management

### Severity Levels
- **CRITICAL**: Immediate action required (block deployment)
- **HIGH**: Fix within 7 days
- **MEDIUM**: Fix within 30 days
- **LOW**: Fix within 90 days
- **NEGLIGIBLE**: Informational

### Scan Thresholds
```yaml
# GitHub Actions configuration
fail-build: true
severity-cutoff: high  # Fail on HIGH and above
```

### False Positive Suppression

**Trivy** (`.trivyignore`):
```
# Suppress specific CVE
CVE-2023-12345

# Suppress with expiration
CVE-2023-12346 exp:2024-12-31

# Suppress for specific package
pkg:pypi/package-name CVE-2023-12347
```

**Grype** (`.grype.yaml`):
```yaml
ignore:
  - vulnerability: CVE-2023-12345
    fix-state: wont-fix
    reason: "False positive - not applicable to our use case"
```

## Security Scan Reports

### Viewing Results

**GitHub Security Tab**:
- Navigate to: Repository → Security → Code scanning alerts
- View detailed vulnerability information
- Track remediation status

**Artifacts**:
- Download scan results from GitHub Actions artifacts
- Available for 90 days

### Report Formats
- **SARIF**: GitHub Security integration
- **JSON**: Programmatic processing
- **HTML**: Human-readable reports
- **JUnit**: Test integration

## Local Scanning

### Quick Scan Script
```bash
#!/bin/bash
# scan-container.sh

IMAGE="mcp-server:latest"

echo "🔍 Running Trivy scan..."
trivy image --severity CRITICAL,HIGH $IMAGE

echo "🔍 Running Grype scan..."
grype $IMAGE --fail-on high

echo "🔍 Running Hadolint..."
hadolint Dockerfile.hardened

echo "✅ Scans complete!"
```

### Pre-commit Hook
```bash
# .git/hooks/pre-push
#!/bin/bash
echo "Running security scans before push..."
./scripts/scan-container.sh
```

## Remediation Workflow

### 1. Identify Vulnerability
- Review scan results in GitHub Security
- Assess severity and exploitability
- Check if fix is available

### 2. Determine Fix Strategy
- **Upgrade dependency**: Preferred if fix available
- **Apply patch**: If upgrade not possible
- **Suppress**: If false positive or not applicable
- **Accept risk**: Document if no fix available

### 3. Implement Fix
```bash
# Update base image
FROM python:3.13.2-slim-bookworm  # Updated version

# Update Python package
pip install package-name==1.2.3  # Fixed version
```

### 4. Verify Fix
```bash
# Rebuild and rescan
docker build -t mcp-server:latest .
trivy image mcp-server:latest
```

### 5. Document Decision
```markdown
## CVE-2023-12345
**Status**: Suppressed
**Reason**: Not applicable - affected code path not used
**Expiration**: 2024-12-31
**Reviewer**: security-team@company.com
```

## Best Practices

### 1. Regular Scanning
- ✅ Scan on every commit
- ✅ Daily scheduled scans
- ✅ Scan before production deployment

### 2. Base Image Management
- ✅ Use specific version tags (not `latest`)
- ✅ Monitor base image updates
- ✅ Rebuild images regularly

### 3. Vulnerability Database Updates
- ✅ Keep scanner tools updated
- ✅ Refresh CVE databases daily
- ✅ Subscribe to security advisories

### 4. SBOM Management
- ✅ Generate SBOM for all releases
- ✅ Store SBOMs with container images
- ✅ Use SBOMs for license compliance

### 5. Compliance Tracking
- ✅ Track scan coverage
- ✅ Measure time-to-fix
- ✅ Report on security posture

## Integration with Registry

### Harbor Integration
```bash
# Enable vulnerability scanning in Harbor
# Configure Trivy adapter
# Set scan-on-push policy
```

### AWS ECR Integration
```bash
# Enable ECR image scanning
aws ecr put-image-scanning-configuration \
  --repository-name mcp-server \
  --image-scanning-configuration scanOnPush=true
```

## Troubleshooting

### Common Issues

**Issue**: Scan fails with rate limit error
**Solution**: Use authenticated API access
```bash
export TRIVY_USERNAME=your-username
export TRIVY_PASSWORD=your-token
```

**Issue**: False positives
**Solution**: Add to ignore file with justification

**Issue**: Scan takes too long
**Solution**: Use cached vulnerability database
```bash
trivy image --cache-dir /tmp/trivy-cache mcp-server:latest
```

## Resources

### Documentation
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Grype Documentation](https://github.com/anchore/grype)
- [Snyk Documentation](https://docs.snyk.io/)
- [Docker Bench Security](https://github.com/docker/docker-bench-security)
- [Hadolint](https://github.com/hadolint/hadolint)

### Security Standards
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [NIST SP 800-190](https://csrc.nist.gov/publications/detail/sp/800-190/final)
- [OWASP Container Security](https://owasp.org/www-project-docker-top-10/)

### Vulnerability Databases
- [National Vulnerability Database (NVD)](https://nvd.nist.gov/)
- [GitHub Security Advisories](https://github.com/advisories)
- [Snyk Vulnerability DB](https://snyk.io/vuln/)
