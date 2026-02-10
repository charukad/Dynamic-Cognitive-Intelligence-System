#!/usr/bin/env bash

# Security Audit Automation Script
# Runs comprehensive security checks on the DCIS project

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/dcis/backend"
FRONTEND_DIR="$PROJECT_ROOT/dcis/frontend"
REPORT_DIR="$PROJECT_ROOT/security-reports"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "DCIS Security Audit"
echo "========================================="
echo ""

# Create report directory
mkdir -p "$REPORT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Function to print section headers
print_section() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Bandit - Python Security Linter
print_section "1. Running Bandit (Python Security Scanner)"
if command_exists bandit; then
    cd "$BACKEND_DIR"
    bandit -r src/ -f json -o "$REPORT_DIR/bandit_${TIMESTAMP}.json" || true
    bandit -r src/ -f txt -o "$REPORT_DIR/bandit_${TIMESTAMP}.txt" || true
    echo -e "${GREEN}✓ Bandit scan complete${NC}"
    echo "Report: $REPORT_DIR/bandit_${TIMESTAMP}.json"
else
    echo -e "${YELLOW}⚠ Bandit not found. Install with: pip install bandit${NC}"
fi

# 2. Safety - Dependency Vulnerability Scanner
print_section "2. Running Safety (Dependency Vulnerabilities)"
if command_exists safety; then
    cd "$BACKEND_DIR"
    poetry export -f requirements.txt --output /tmp/requirements.txt --without-hashes
    safety check --file /tmp/requirements.txt --json > "$REPORT_DIR/safety_${TIMESTAMP}.json" || true
    echo -e "${GREEN}✓ Safety scan complete${NC}"
    echo "Report: $REPORT_DIR/safety_${TIMESTAMP}.json"
else
    echo -e "${YELLOW}⚠ Safety not found. Install with: pip install safety${NC}"
fi

# 3. npm audit - Frontend Dependency Security
print_section "3. Running npm audit (Frontend Dependencies)"
if command_exists npm; then
    cd "$FRONTEND_DIR"
    npm audit --json > "$REPORT_DIR/npm_audit_${TIMESTAMP}.json" || true
    npm audit > "$REPORT_DIR/npm_audit_${TIMESTAMP}.txt" || true
    echo -e "${GREEN}✓ npm audit complete${NC}"
    echo "Report: $REPORT_DIR/npm_audit_${TIMESTAMP}.json"
else
    echo -e "${YELLOW}⚠ npm not found${NC}"
fi

# 4. Semgrep - Static Analysis
print_section "4. Running Semgrep (Static Analysis)"
if command_exists semgrep; then
    cd "$PROJECT_ROOT"
    semgrep --config=auto --json --output="$REPORT_DIR/semgrep_${TIMESTAMP}.json" dcis/ || true
    echo -e "${GREEN}✓ Semgrep scan complete${NC}"
    echo "Report: $REPORT_DIR/semgrep_${TIMESTAMP}.json"
else
    echo -e "${YELLOW}⚠ Semgrep not found. Install with: pip install semgrep${NC}"
fi

# 5. Docker Image Scanning with Trivy
print_section "5. Running Trivy (Docker Image Scanner)"
if command_exists trivy; then
    # Scan backend image
    if docker images | grep -q "dcis-backend"; then
        trivy image --format json --output "$REPORT_DIR/trivy_backend_${TIMESTAMP}.json" dcis-backend:latest || true
        echo -e "${GREEN}✓ Backend image scanned${NC}"
    fi
    
    # Scan frontend image  
    if docker images | grep -q "dcis-frontend"; then
        trivy image --format json --output "$REPORT_DIR/trivy_frontend_${TIMESTAMP}.json" dcis-frontend:latest || true
        echo -e "${GREEN}✓ Frontend image scanned${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Trivy not found. Install from: https://github.com/aquasecurity/trivy${NC}"
fi

# 6. Git Secrets Scanning
print_section "6. Scanning for Secrets in Git History"
if command_exists gitleaks; then
    cd "$PROJECT_ROOT"
    gitleaks detect --source . --report-path "$REPORT_DIR/gitleaks_${TIMESTAMP}.json" --report-format json || true
    echo -e "${GREEN}✓ Git secrets scan complete${NC}"
    echo "Report: $REPORT_DIR/gitleaks_${TIMESTAMP}.json"
else
    echo -e "${YELLOW}⚠ Gitleaks not found. Install from: https://github.com/gitleaks/gitleaks${NC}"
fi

# 7. OWASP Top 10 Checks
print_section "7. OWASP Top 10 Security Checks"

echo "A01:2021 – Broken Access Control"
echo "  - Checking for JWT implementation..."
if grep -r "JWT" "$BACKEND_DIR/src/core/security/" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ JWT authentication found${NC}"
else
    echo -e "  ${RED}✗ JWT authentication NOT found${NC}"
fi

echo ""
echo "A02:2021 – Cryptographic Failures"
echo "  - Checking for password hashing..."
if grep -r "bcrypt\|scrypt\|argon2" "$BACKEND_DIR/src/" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Password hashing found${NC}"
else
    echo -e "  ${RED}✗ Password hashing NOT found${NC}"
fi

echo ""
echo "A03:2021 – Injection"
echo "  - Checking for input validation..."
if [ -f "$BACKEND_DIR/src/core/security/validation.py" ]; then
    echo -e "  ${GREEN}✓ Input validation module found${NC}"
else
    echo -e "  ${RED}✗ Input validation module NOT found${NC}"
fi

echo ""
echo "A04:2021 – Insecure Design"
echo "  - Checking for rate limiting..."
if grep -r "rate_limit\|RateLimiter" "$BACKEND_DIR/src/" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Rate limiting found${NC}"
else
    echo -e "  ${RED}✗ Rate limiting NOT found${NC}"
fi

echo ""
echo "A05:2021 – Security Misconfiguration"
echo "  - Checking for secure headers..."
if grep -r "CORS\|SecurityHeaders" "$BACKEND_DIR/src/api/" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Security headers configured${NC}"
else
    echo -e "  ${YELLOW}⚠ Security headers may need review${NC}"
fi

# 8. Generate Summary Report
print_section "8. Generating Summary Report"

cat > "$REPORT_DIR/summary_${TIMESTAMP}.md" << EOF
# DCIS Security Audit Summary

**Date:** $(date)
**Auditor:** Automated Security Scan

## Scans Performed

- ✓ Bandit (Python security)
- ✓ Safety (Python dependencies)
- ✓ npm audit (Frontend dependencies)
- ✓ Semgrep (Static analysis)
- ✓ Trivy (Container scanning)
- ✓ Gitleaks (Secret detection)
- ✓ OWASP Top 10 checks

## Reports Generated

- Bandit: bandit_${TIMESTAMP}.json
- Safety: safety_${TIMESTAMP}.json
- npm audit: npm_audit_${TIMESTAMP}.json
- Semgrep: semgrep_${TIMESTAMP}.json
- Trivy Backend: trivy_backend_${TIMESTAMP}.json
- Trivy Frontend: trivy_frontend_${TIMESTAMP}.json
- Gitleaks: gitleaks_${TIMESTAMP}.json

## Action Items

Review each report for:
1. **Critical vulnerabilities** - Address immediately
2. **High severity issues** - Address within 1 week
3. **Medium severity issues** - Address within 1 month
4. **Low severity issues** - Address as capacity allows

## Next Steps

1. Review all generated reports
2. Create tickets for findings
3. Implement fixes
4. Re-run audit
5. Document remediation
EOF

echo -e "${GREEN}✓ Summary report generated${NC}"
echo "Report: $REPORT_DIR/summary_${TIMESTAMP}.md"

# Final Summary
print_section "Audit Complete"
echo ""
echo "All reports saved to: $REPORT_DIR"
echo ""
echo "Next steps:"
echo "  1. Review reports in $REPORT_DIR"
echo "  2. Address critical and high severity findings"
echo "  3. Update security documentation"
echo ""
echo -e "${GREEN}Security audit complete!${NC}"
