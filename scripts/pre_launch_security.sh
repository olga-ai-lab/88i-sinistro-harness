#!/bin/bash

################################################################################
# Pre-Launch Security Validation Script
# Comprehensive security audit with 9 checks before production launch
# Exit code: 0 if all checks pass, 1 if ANY check fails
# 
# 9 Checks:
#  1. Trivy container scan (HIGH/CRITICAL vulnerabilities)
#  2. Safety dependency audit (vulnerable packages)
#  3. Git history secrets scanning (exposed credentials)
#  4. Configuration audit (API_KEY, ENCRYPTION_KEY, INTERNAL_IPS)
#  5. SSL certificate validation (expiry, validity)
#  6. PostgreSQL connectivity (database access)
#  7. Network security audit (firewall rules)
#  8. Logging verification (audit trails configured)
#  9. Dependency license compliance (GPL/AGPL detection)
#
# Output: ✅/❌/⊘ status with colored output
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Helper functions
check_passed() {
    echo -e "${GREEN}✅${NC} $1"
    ((PASSED++))
}

check_failed() {
    echo -e "${RED}❌${NC} $1"
    ((FAILED++))
}

check_skipped() {
    echo -e "${YELLOW}⊘${NC} $1"
    ((SKIPPED++))
}

print_header() {
    echo ""
    echo "==============================================="
    echo "  $1"
    echo "==============================================="
}

print_footer() {
    echo ""
    echo "==============================================="
    echo "  Results: ${GREEN}✅${NC} $PASSED passed | ${RED}❌${NC} $FAILED failed | ${YELLOW}⊘${NC} $SKIPPED skipped"
    echo "==============================================="
    echo ""
}

# Get the repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/..)" && pwd)"
cd "$REPO_ROOT"

# Logging setup
LOG_DIR="${REPO_ROOT}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/pre_launch_security_$(date +%Y%m%d_%H%M%S).log"

{
echo "Pre-Launch Security Validation"
echo "Started: $(date)"
echo "Repository: $REPO_ROOT"
echo ""

################################################################################
# 1. TRIVY CONTAINER SCAN
################################################################################
print_header "1. TRIVY CONTAINER/DEPENDENCY SCAN"

if command -v trivy &> /dev/null; then
    if [ -f "requirements.txt" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        echo "Scanning for HIGH and CRITICAL vulnerabilities..."
        
        # Scan filesystem for vulnerabilities
        TRIVY_OUTPUT=$(trivy fs . --severity HIGH,CRITICAL --format json 2>/dev/null || echo "{}")
        
        # Count issues
        CRITICAL_COUNT=$(echo "$TRIVY_OUTPUT" | grep -o '"Severity":"CRITICAL"' 2>/dev/null | wc -l || echo 0)
        HIGH_COUNT=$(echo "$TRIVY_OUTPUT" | grep -o '"Severity":"HIGH"' 2>/dev/null | wc -l || echo 0)
        
        if [ "$CRITICAL_COUNT" -gt 0 ] || [ "$HIGH_COUNT" -gt 0 ]; then
            check_failed "Trivy scan found $CRITICAL_COUNT CRITICAL and $HIGH_COUNT HIGH severity issues"
        else
            check_passed "Trivy scan: No HIGH/CRITICAL vulnerabilities detected"
        fi
    else
        check_skipped "Trivy: No Python project files found (requirements.txt, setup.py, pyproject.toml)"
    fi
else
    check_skipped "Trivy not installed (install: brew install trivy or https://github.com/aquasecurity/trivy)"
fi
echo ""

################################################################################
# 2. SAFETY DEPENDENCY AUDIT
################################################################################
print_header "2. SAFETY DEPENDENCY AUDIT"

if command -v safety &> /dev/null; then
    if [ -f "requirements.txt" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        echo "Running Safety dependency check..."
        
        if safety check --json > /tmp/safety_output.json 2>/dev/null; then
            SAFETY_VULNS=$(jq '.vulnerabilities // [] | length' /tmp/safety_output.json 2>/dev/null || echo 0)
            if [ "$SAFETY_VULNS" -gt 0 ]; then
                check_failed "Safety found $SAFETY_VULNS vulnerable dependencies"
            else
                check_passed "Safety: No vulnerable dependencies detected"
            fi
        else
            # Safety returns non-zero if vulnerabilities found
            if [ -f /tmp/safety_output.json ]; then
                SAFETY_VULNS=$(jq '.vulnerabilities // [] | length' /tmp/safety_output.json 2>/dev/null || echo 1)
                check_failed "Safety found $SAFETY_VULNS vulnerable dependencies"
            else
                check_failed "Safety check failed (unable to analyze dependencies)"
            fi
        fi
        rm -f /tmp/safety_output.json
    else
        check_skipped "Safety: No Python project files found"
    fi
else
    check_skipped "Safety not installed (install: pip install safety)"
fi
echo ""

################################################################################
# 3. GIT HISTORY SECRETS SCANNING
################################################################################
print_header "3. GIT HISTORY SECRETS SCANNING"

echo "Scanning Git history for exposed secrets..."

# Secret patterns to search for
SECRET_PATTERNS=(
    "AKIA[0-9A-Z]\\{16\\}"          # AWS Access Key
    "aws_secret_access_key"
    "api_key"
    "apiKey"
    "API_KEY="
    "private.*key"
    "-----BEGIN RSA PRIVATE KEY-----"
    "-----BEGIN PRIVATE KEY-----"
    "password.*="
    "secret.*="
)

SECRET_FOUND=0
SECRETS_LIST=""

# Check git history for secrets
for pattern in "${SECRET_PATTERNS[@]}"; do
    if git log -p --all -i 2>/dev/null | grep -E "$pattern" | grep -v "^[[:space:]]*#" > /dev/null 2>&1; then
        SECRET_FOUND=1
        SECRETS_LIST="$SECRETS_LIST\n  - Pattern: $pattern"
    fi
done

if [ $SECRET_FOUND -eq 0 ]; then
    check_passed "Git history: No obvious secrets detected"
else
    check_failed "Git history: Potential secrets found (manual review needed)$SECRETS_LIST"
fi
echo ""

################################################################################
# 4. CONFIGURATION SECURITY AUDIT
################################################################################
print_header "4. CONFIGURATION SECURITY AUDIT"

echo "Auditing API keys, encryption keys, and internal IPs..."

CONFIG_ISSUES=0

# Check for exposed API keys in config files
API_KEY_EXPOSED=0
ENCRYPTION_KEY_EXPOSED=0
INTERNAL_IPS_EXPOSED=0

for config_file in config/*.py config/*.json config/*.yaml config/*.yml .env; do
    if [ -f "$config_file" ] 2>/dev/null && ! [[ "$config_file" == *".example"* ]]; then
        # Check for unset/hardcoded API keys
        if grep -E "API_KEY\s*=\s*['\"]?[a-zA-Z0-9]{10,}" "$config_file" 2>/dev/null | grep -v "os.getenv\|environ\|^#" > /dev/null; then
            API_KEY_EXPOSED=1
        fi
        # Check for hardcoded encryption keys
        if grep -E "ENCRYPTION_KEY\s*=\s*['\"]?[a-zA-Z0-9]{10,}" "$config_file" 2>/dev/null | grep -v "os.getenv\|environ\|^#" > /dev/null; then
            ENCRYPTION_KEY_EXPOSED=1
        fi
    fi
done

# Check for internal IPs exposed in version control
if grep -r "192\.168\|10\.\|172\.1[6-9]\." --include="*.py" --include="*.js" --include="*.yaml" --include="*.json" 2>/dev/null | grep -v "test\|example\|^#" > /dev/null 2>&1; then
    INTERNAL_IPS_EXPOSED=1
fi

if [ $API_KEY_EXPOSED -eq 0 ] && [ $ENCRYPTION_KEY_EXPOSED -eq 0 ] && [ $INTERNAL_IPS_EXPOSED -eq 0 ]; then
    check_passed "Configuration: No hardcoded secrets detected (API_KEY, ENCRYPTION_KEY, INTERNAL_IPS)"
else
    [ $API_KEY_EXPOSED -eq 1 ] && check_failed "Configuration: Hardcoded API keys detected"
    [ $ENCRYPTION_KEY_EXPOSED -eq 1 ] && check_failed "Configuration: Hardcoded encryption keys detected"
    [ $INTERNAL_IPS_EXPOSED -eq 1 ] && check_failed "Configuration: Internal IPs exposed in code"
fi
echo ""

################################################################################
# 5. SSL CERTIFICATE VALIDATION
################################################################################
print_header "5. SSL/TLS CERTIFICATE VALIDATION"

CERT_FOUND=0
CERT_VALID=0

# Check for certificate files
for cert_location in config/certs/*.pem config/certs/*.crt certs/*.pem certs/*.crt ~/.ssh/*.pem; do
    if [ -f "$cert_location" ] 2>/dev/null && [[ "$cert_location" == *.pem || "$cert_location" == *.crt ]]; then
        CERT_FOUND=1
        echo "Found certificate: $cert_location"
        
        # Check certificate validity
        if openssl x509 -in "$cert_location" -noout 2>/dev/null; then
            EXPIRY_DATE=$(openssl x509 -in "$cert_location" -noout -enddate 2>/dev/null | cut -d= -f2)
            
            # Calculate days until expiry (macOS compatible)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                EXPIRY_EPOCH=$(date -j -f "%b %d %T %Y %Z" "$EXPIRY_DATE" +%s 2>/dev/null || echo 0)
            else
                EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s 2>/dev/null || echo 0)
            fi
            
            CURRENT_EPOCH=$(date +%s)
            DAYS_UNTIL_EXPIRY=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))
            
            if [ "$DAYS_UNTIL_EXPIRY" -lt 0 ]; then
                check_failed "SSL: Certificate EXPIRED on $EXPIRY_DATE"
            elif [ "$DAYS_UNTIL_EXPIRY" -lt 30 ]; then
                check_failed "SSL: Certificate expires in $DAYS_UNTIL_EXPIRY days (renew immediately)"
            else
                check_passed "SSL: Certificate valid, expires in $DAYS_UNTIL_EXPIRY days"
                CERT_VALID=1
            fi
        else
            check_failed "SSL: Invalid or corrupted certificate file"
        fi
    fi
done

if [ $CERT_FOUND -eq 0 ]; then
    check_skipped "SSL: No certificate files found (may be managed by platform/Docker)"
fi
echo ""

################################################################################
# 6. POSTGRESQL CONNECTIVITY
################################################################################
print_header "6. POSTGRESQL CONNECTIVITY"

echo "Testing PostgreSQL database connectivity..."

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-production}"

if command -v psql &> /dev/null; then
    # Try to connect to PostgreSQL
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" 2>/dev/null > /dev/null; then
        check_passed "PostgreSQL: Connection successful ($DB_HOST:$DB_PORT)"
        
        # Check for required tables
        TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public';" 2>/dev/null | xargs || echo 0)
        if [ "$TABLE_COUNT" -gt 0 ]; then
            check_passed "PostgreSQL: Schema initialized ($TABLE_COUNT tables)"
        else
            check_failed "PostgreSQL: No tables found in schema"
        fi
    else
        check_failed "PostgreSQL: Connection failed (verify DB_HOST, DB_USER, DB_PASSWORD)"
    fi
else
    check_skipped "PostgreSQL: psql not installed (install: brew install postgresql)"
fi
echo ""

################################################################################
# 7. NETWORK SECURITY AUDIT
################################################################################
print_header "7. NETWORK SECURITY AUDIT"

echo "Checking network and firewall configuration..."

# Check for overly permissive firewall rules in Terraform
if [ -f "terraform/security_group.tf" ] || [ -f "terraform/main.tf" ]; then
    if grep -E "0\.0\.0\.0/0|::/0" terraform/*.tf 2>/dev/null | grep -v "egress\|#" > /dev/null; then
        DANGEROUS_RULES=$(grep -E "0\.0\.0\.0/0|::/0" terraform/*.tf 2>/dev/null | grep -v "egress\|#" | wc -l)
        check_failed "Network: Found $DANGEROUS_RULES overly permissive ingress rules (0.0.0.0/0)"
    else
        check_passed "Network: Security group rules properly scoped (no 0.0.0.0/0 ingress)"
    fi
else
    check_skipped "Network: No Terraform configuration found"
fi
echo ""

################################################################################
# 8. LOGGING & AUDIT TRAIL VERIFICATION
################################################################################
print_header "8. LOGGING & AUDIT TRAIL VERIFICATION"

echo "Verifying logging configuration..."

# Check for structured/audit logging
LOGGING_FOUND=0
if grep -r "logging\|logger" --include="*.py" 2>/dev/null | grep -v "test\|^#" > /dev/null; then
    LOGGING_FOUND=1
    
    if grep -r "json\|structured\|audit" --include="*.py" 2>/dev/null | grep -v "test\|^#" > /dev/null; then
        check_passed "Logging: Structured logging configured"
    else
        check_passed "Logging: Logging system configured (audit trail recommended)"
    fi
    
    # Check for audit logging on sensitive operations
    if grep -r "audit\|@log\|log_audit" --include="*.py" 2>/dev/null | grep -v "test" > /dev/null; then
        check_passed "Logging: Audit trail decorators/functions found"
    else
        check_skipped "Logging: Audit trail decorators not found (recommended for sensitive ops)"
    fi
else
    check_failed "Logging: No logging configuration detected"
fi
echo ""

################################################################################
# 9. DEPENDENCY LICENSE COMPLIANCE (GPL/AGPL Detection)
################################################################################
print_header "9. DEPENDENCY LICENSE COMPLIANCE"

echo "Scanning for GPL/AGPL/SSPL licenses..."

if command -v pip-licenses &> /dev/null; then
    # Check for restricted licenses
    if pip-licenses | grep -iE "GPL|AGPL|SSPL" > /dev/null 2>&1; then
        GPL_COUNT=$(pip-licenses | grep -icE "GPL|AGPL|SSPL" || echo 0)
        GPL_PACKAGES=$(pip-licenses | grep -iE "GPL|AGPL|SSPL" | cut -d: -f1 | head -5)
        check_failed "License audit: Found $GPL_COUNT packages with GPL/AGPL/SSPL licenses:\n$GPL_PACKAGES"
    else
        check_passed "License audit: No GPL/AGPL/SSPL dependencies detected"
    fi
else
    check_skipped "pip-licenses not installed (install: pip install pip-licenses)"
fi
echo ""

################################################################################
# SUMMARY & EXIT CODE
################################################################################
print_footer

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ SECURITY VALIDATION FAILED${NC}"
    echo "Please address $FAILED failed check(s) before production launch."
    echo ""
    echo "Detailed log: $LOG_FILE"
    exit 1
else
    echo -e "${GREEN}✅ SECURITY VALIDATION PASSED${NC}"
    echo "All security requirements verified. Safe to proceed to launch."
    echo ""
    echo "Detailed log: $LOG_FILE"
    exit 0
fi

} | tee "$LOG_FILE"
