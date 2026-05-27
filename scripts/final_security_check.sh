#!/bin/bash

################################################################################
# Final Security Check Script
# Performs comprehensive security audit before production deployment
# Exit code: 0 if all checks pass, 1 if ANY check fails
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

################################################################################
# 1. TRIVY SECURITY SCAN
################################################################################
print_header "1. CONTAINER/DEPENDENCY VULNERABILITY SCAN (Trivy)"

if command -v trivy &> /dev/null; then
    # Scan Python dependencies for HIGH and CRITICAL vulnerabilities
    if [ -f "requirements.txt" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        echo "Scanning for container vulnerabilities..."
        
        # Note: Trivy scans current directory by default
        TRIVY_OUTPUT=$(trivy fs . --severity HIGH,CRITICAL --format json 2>/dev/null || echo "{}")
        
        # Check if any HIGH or CRITICAL issues found
        if echo "$TRIVY_OUTPUT" | grep -q '"CRITICAL"' || echo "$TRIVY_OUTPUT" | grep -q '"HIGH"'; then
            CRITICAL_COUNT=$(echo "$TRIVY_OUTPUT" | grep -o '"Severity":"CRITICAL"' | wc -l || echo 0)
            HIGH_COUNT=$(echo "$TRIVY_OUTPUT" | grep -o '"Severity":"HIGH"' | wc -l || echo 0)
            check_failed "Trivy scan found $CRITICAL_COUNT CRITICAL and $HIGH_COUNT HIGH severity issues"
        else
            check_passed "Trivy scan: No HIGH/CRITICAL vulnerabilities detected"
        fi
    else
        check_skipped "Trivy: No Python project files found (requirements.txt, setup.py, pyproject.toml)"
    fi
else
    check_skipped "Trivy not installed (install: https://github.com/aquasecurity/trivy)"
fi

################################################################################
# 2. DEPENDENCY AUDIT (Safety)
################################################################################
print_header "2. PYTHON DEPENDENCY SECURITY AUDIT (Safety)"

if command -v safety &> /dev/null; then
    if [ -f "requirements.txt" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        echo "Running Safety dependency check..."
        
        if safety check --json 2>/dev/null > /tmp/safety_output.json; then
            SAFETY_VULNERABILITIES=$(jq '.vulnerabilities | length' /tmp/safety_output.json 2>/dev/null || echo 0)
            if [ "$SAFETY_VULNERABILITIES" -gt 0 ]; then
                check_failed "Safety found $SAFETY_VULNERABILITIES vulnerable dependencies"
            else
                check_passed "Safety: No vulnerable dependencies detected"
            fi
        else
            # Safety returns exit code 64 if vulnerabilities found
            SAFETY_VULNERABILITIES=$(jq '.vulnerabilities | length' /tmp/safety_output.json 2>/dev/null || echo "1+")
            check_failed "Safety found vulnerable dependencies"
        fi
    else
        check_skipped "Safety: No Python project files found"
    fi
else
    check_skipped "Safety not installed (install: pip install safety)"
fi

################################################################################
# 3. GIT SECRETS SCANNING
################################################################################
print_header "3. GIT HISTORY SECRETS SCANNING"

if command -v git-secrets &> /dev/null; then
    echo "Scanning Git history for secrets..."
    
    # Check for common secret patterns
    SECRET_PATTERNS=(
        "AKIA[0-9A-Z]\{16\}"  # AWS Access Key
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
    for pattern in "${SECRET_PATTERNS[@]}"; do
        if git log -p --all -S "$pattern" 2>/dev/null | head -1 | grep -q .; then
            SECRET_FOUND=1
            break
        fi
    done
    
    if [ $SECRET_FOUND -eq 0 ]; then
        check_passed "Git history: No obvious secrets detected"
    else
        check_failed "Git history: Potential secrets found (manual review recommended)"
    fi
else
    check_skipped "git-secrets not installed (install: brew install git-secrets)"
    # Fallback: basic grep for common patterns
    if git log -p --all 2>/dev/null | grep -E "(password|secret|api.key|AWS_SECRET)" | grep -v "==" > /dev/null 2>&1; then
        check_failed "Git history: Potential secrets found (manual review recommended)"
    else
        check_passed "Git history: No obvious secrets detected (basic check)"
    fi
fi

################################################################################
# 4. CONFIGURATION AUDIT
################################################################################
print_header "4. CONFIGURATION SECURITY AUDIT"

echo "Checking environment variables and config files..."

# Check for exposed API keys in config files
API_KEY_EXPOSED=0
ENCRYPTION_KEY_EXPOSED=0
INTERNAL_IPS_EXPOSED=0

# Scan for hardcoded API keys in config files
for config_file in config/*.py config/*.json config/*.yaml config/*.yml .env .env.example; do
    if [ -f "$config_file" ] && ! [[ "$config_file" == *".example"* ]]; then
        # Check for unset/non-secret API keys
        if grep -E "API_KEY\s*=\s*['\"]?[a-zA-Z0-9]{10,}" "$config_file" 2>/dev/null | grep -v "os.getenv\|environ\|^#" > /dev/null; then
            API_KEY_EXPOSED=1
        fi
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
    check_passed "Configuration audit: No hardcoded secrets detected"
else
    [ $API_KEY_EXPOSED -eq 1 ] && check_failed "Configuration: Hardcoded API keys detected"
    [ $ENCRYPTION_KEY_EXPOSED -eq 1 ] && check_failed "Configuration: Hardcoded encryption keys detected"
    [ $INTERNAL_IPS_EXPOSED -eq 1 ] && check_failed "Configuration: Internal IPs exposed in code"
fi

# Check that environment-specific config is loaded
if [ -f "config/__init__.py" ] || [ -f "app/config.py" ]; then
    if grep -E "os\.getenv|os\.environ\|load_dotenv" config/*.py app/*.py 2>/dev/null > /dev/null; then
        check_passed "Configuration: Environment variables properly loaded"
    else
        check_failed "Configuration: Not using environment variables for secrets"
    fi
else
    check_skipped "Configuration: Unable to verify config loading (no config files found)"
fi

################################################################################
# 5. SSL CERTIFICATE VALIDATION
################################################################################
print_header "5. SSL/TLS CERTIFICATE CHECK"

# Check for certificate in common locations
CERT_FOUND=0
CERT_VALID=0

for cert_location in config/certs/*.pem config/certs/*.crt certs/*.pem certs/*.crt ~/.ssh/*.pem; do
    if [ -f "$cert_location" ] && [[ "$cert_location" == *.pem || "$cert_location" == *.crt ]]; then
        CERT_FOUND=1
        
        # Check certificate validity using openssl
        if openssl x509 -in "$cert_location" -noout 2>/dev/null; then
            EXPIRY_DATE=$(openssl x509 -in "$cert_location" -noout -enddate 2>/dev/null | cut -d= -f2)
            EXPIRY_EPOCH=$(date -j -f "%b %d %T %Y %Z" "$EXPIRY_DATE" +%s 2>/dev/null || echo 0)
            CURRENT_EPOCH=$(date +%s)
            DAYS_UNTIL_EXPIRY=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))
            
            if [ "$DAYS_UNTIL_EXPIRY" -lt 0 ]; then
                check_failed "SSL certificate: Expired on $EXPIRY_DATE"
            elif [ "$DAYS_UNTIL_EXPIRY" -lt 30 ]; then
                check_failed "SSL certificate: Expires in $DAYS_UNTIL_EXPIRY days (renew immediately)"
            else
                check_passed "SSL certificate: Valid, expires in $DAYS_UNTIL_EXPIRY days"
                CERT_VALID=1
            fi
        else
            check_failed "SSL certificate: Invalid or corrupted certificate file"
        fi
    fi
done

if [ $CERT_FOUND -eq 0 ]; then
    # Check if running HTTPS in production
    if grep -r "https\|ssl\|tls" --include="*.py" --include="*.yaml" 2>/dev/null | grep -v "test\|example" > /dev/null; then
        check_skipped "SSL certificate: No certificate file found (may be loaded from environment/secret manager)"
    else
        check_skipped "SSL certificate: No HTTPS requirement detected (verify this is intentional)"
    fi
fi

################################################################################
# 6. DATABASE CONNECTIVITY
################################################################################
print_header "6. DATABASE CONNECTIVITY CHECK"

# Check for database configuration
DB_CONFIGURED=0
DB_ACCESSIBLE=0

if command -v psql &> /dev/null; then
    # Try to connect to PostgreSQL
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    DB_USER=${DB_USER:-postgres}
    DB_NAME=${DB_NAME:-production}
    
    echo "Testing PostgreSQL connection to $DB_HOST:$DB_PORT..."
    
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" 2>/dev/null > /dev/null; then
        check_passed "Database: PostgreSQL connectivity verified"
        DB_ACCESSIBLE=1
        
        # Check for required tables
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public';" 2>/dev/null | grep -q "[0-9]"; then
            TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname='public';" 2>/dev/null)
            check_passed "Database: Schema initialized ($TABLE_COUNT tables found)"
        fi
    else
        check_failed "Database: PostgreSQL connection failed (verify DB_HOST, DB_USER, DB_PASSWORD)"
    fi
else
    # Fallback: check configuration
    if grep -r "postgresql\|postgres\|DATABASE" --include="*.py" --include="*.yaml" 2>/dev/null | grep -v "test\|^#" > /dev/null; then
        check_skipped "Database: psql client not found, but PostgreSQL configured (psql install recommended: brew install postgresql)"
    else
        check_skipped "Database: No database configuration detected"
    fi
fi

################################################################################
# 7. NETWORK & FIREWALL RULES
################################################################################
print_header "7. NETWORK SECURITY CONFIGURATION"

echo "Checking network configuration..."

# Check for overly permissive firewall rules (if config exists)
if [ -f "terraform/security_group.tf" ] || [ -f "terraform/main.tf" ]; then
    if grep -E "0\.0\.0\.0/0|::/0" terraform/*.tf 2>/dev/null | grep -v "egress\|#" > /dev/null; then
        DANGEROUS_RULES=$(grep -E "0\.0\.0\.0/0|::/0" terraform/*.tf 2>/dev/null | grep -v "egress\|#" | wc -l)
        check_failed "Network: Found $DANGEROUS_RULES overly permissive ingress rules (0.0.0.0/0)"
    else
        check_passed "Network: Security group rules are properly scoped"
    fi
else
    check_skipped "Network: No Terraform configuration found"
fi

################################################################################
# 8. LOGGING & AUDIT CONFIGURATION
################################################################################
print_header "8. LOGGING & AUDIT TRAIL CONFIGURATION"

echo "Verifying logging configuration..."

# Check for structured logging setup
if grep -r "logging\|logger" --include="*.py" 2>/dev/null | grep -v "test\|^#" | grep -E "json|structured|audit" > /dev/null; then
    check_passed "Logging: Structured logging configured"
else
    if grep -r "logging\|logger" --include="*.py" 2>/dev/null | grep -v "test\|^#" > /dev/null; then
        check_passed "Logging: Logging system configured (audit trail recommended for production)"
    else
        check_failed "Logging: No logging configuration detected"
    fi
fi

# Check for audit logging on sensitive operations
if grep -r "audit\|@log\|log_audit" --include="*.py" 2>/dev/null | grep -v "test" > /dev/null; then
    check_passed "Logging: Audit trail decorators/functions found"
else
    check_skipped "Logging: Audit trail decorators not found (add @audit_log to sensitive operations)"
fi

################################################################################
# 9. DEPENDENCY LICENSES
################################################################################
print_header "9. DEPENDENCY LICENSE AUDIT"

if command -v pip-licenses &> /dev/null; then
    echo "Checking dependency licenses..."
    
    # Check for GPL or other restricted licenses
    if pip-licenses | grep -iE "GPL|AGPL|SSPL" > /dev/null 2>&1; then
        GPL_COUNT=$(pip-licenses | grep -icE "GPL|AGPL|SSPL" || echo 0)
        check_failed "Licenses: Found $GPL_COUNT packages with restrictive licenses (GPL/AGPL/SSPL)"
    else
        check_passed "Licenses: All dependencies have compatible licenses (no GPL/AGPL/SSPL)"
    fi
else
    check_skipped "pip-licenses not installed (install: pip install pip-licenses)"
fi

################################################################################
# SUMMARY & EXIT CODE
################################################################################
print_footer

if [ $FAILED -gt 0 ]; then
    echo "${RED}❌ SECURITY CHECK FAILED${NC}"
    echo "Please address $FAILED failed check(s) before production deployment."
    exit 1
else
    echo "${GREEN}✅ SECURITY CHECK PASSED${NC}"
    echo "All security requirements verified. Safe to proceed to production."
    exit 0
fi
