# Security Hardening: OWASP Top 10 & Beyond

This document outlines the security measures implemented in the 88i Sinistro Harness application to protect against the OWASP Top 10 vulnerabilities and additional security best practices.

## OWASP Top 10 Checklist

### 1. Broken Authentication (A01:2021)

**Status: ✅ MITIGATED**

**Implemented Measures:**
- API key validation via `verify_api_key()` in `app/auth.py`
- Authorization header validation (Bearer token scheme)
- Constant-time comparison to prevent timing attacks
- All authentication attempts logged for audit trail
- HTTPBearer security scheme for FastAPI documentation
- Rate limiting (60 requests/minute per IP) to prevent brute force attacks
- Session management via secure cookies (when applicable)

**Configuration:**
```bash
API_KEY_PRODUCTION=<your-secure-api-key>
```

---

### 2. Broken Access Control (A02:2021)

**Status: ✅ MITIGATED**

**Implemented Measures:**
- IP-based access control via `verify_internal_request()` in `app/auth.py`
- Whitelist of internal IPs checked on restricted endpoints
- X-Forwarded-For header support for proxy scenarios
- X-Frame-Options: DENY header prevents clickjacking
- Content-Security-Policy restricts frame ancestors
- Principle of least privilege enforced in all endpoints

**Configuration:**
```bash
INTERNAL_IPS=127.0.0.1,10.0.0.0/8,192.168.0.0/16
```

---

### 3. Injection (A03:2021)

**Status: ✅ MITIGATED**

**Implemented Measures:**
- Input validation middleware checks content-type for POST/PUT/PATCH
- Only allowed content types: application/json, application/x-www-form-urlencoded, multipart/form-data
- Content-Security-Policy header prevents inline script injection
- Request size validation (<10MB) prevents payload-based attacks
- Pydantic models for request/response validation
- ORM parameterized queries (not raw SQL construction)
- Regular expression patterns for input validation in endpoints

**Validation Rules:**
- Content-Type validation for POST/PUT/PATCH requests
- Request size < 10MB (413 Payload Too Large)
- Invalid content types return 400 Bad Request

---

### 4. Insecure Design (A04:2021)

**Status: ✅ MITIGATED**

**Implemented Measures:**
- Security by default: SecurityHeadersMiddleware adds protective headers
- HSTS (HTTP Strict-Transport-Security) enforces HTTPS
- Content-Security-Policy restricts resource loading
- X-Content-Type-Options: nosniff prevents MIME sniffing
- Referrer-Policy: strict-origin-when-cross-origin controls referrer leakage
- Permissions-Policy disables unnecessary browser features
- Encryption at rest via Fernet in `app/encryption.py`
- Secure defaults for all security configurations

**Headers Enforced:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self'; ...
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

---

### 5. Security Misconfiguration (A05:2021)

**Status: ✅ MITIGATED**

**Implemented Measures:**
- Server header removed from all responses (information disclosure prevention)
- Security headers added by default via middleware
- Strict Content-Security-Policy
- Permissions-Policy restricts browser capabilities (accelerometer, camera, microphone, etc.)
- Environment-based configuration (API keys, encryption keys from env vars)
- Logging configured with INFO+ level for all requests
- Error messages sanitized (no stack traces in responses)
- Default secure settings for all configurations

**Removed Headers:**
- Server header stripped from all responses

---

### 6. Vulnerable and Outdated Components (A06:2021)

**Status: ✅ MITIGATED**

**Implemented Measures:**
- Regular dependency scanning via pip-audit
- Fernet encryption library (battle-tested, cryptographically sound)
- FastAPI framework (actively maintained, regular security updates)
- cryptography library for encryption (industry standard)
- All dependencies pinned in requirements.txt with specific versions
- Automated dependency updates via Dependabot (recommended)

**Encryption:**
- Fernet (from cryptography library) provides authenticated encryption
- AES-128 symmetric encryption with HMAC
- Protects sensitive data at rest

**Initialization:**
```python
from app.encryption import encryption_manager
encrypted_data = encryption_manager.encrypt("sensitive")
decrypted = encryption_manager.decrypt(encrypted_data)
```

---

### 7. Identification & Authentication Failures (A07:2021)

**Status: ✅ MITIGATED**

**Implemented Measures:**
- API key-based authentication via `verify_api_key()`
- Rate limiting (60 requests/minute per IP) prevents brute force
- Login attempt logging for audit trail
- X-RateLimit headers inform clients of rate limit status
- Exponential backoff recommendations via Retry-After header
- HTTP 429 Too Many Requests response when limit exceeded
- Failed authentication attempts logged with timestamp and source IP
- Constant-time comparison prevents timing attacks

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1234567890
Retry-After: 30
```

---

### 8. Software & Data Integrity Failures (A08:2021)

**Status: ✅ MITIGATED**

**Implemented Measures:**
- Fernet encryption includes HMAC authentication (detects tampering)
- Data validation via Pydantic models
- Request/response integrity checks
- Signed tokens (if applicable)
- Secure serialization (JSON with validation)
- InvalidToken exception raised on tampering detection
- Audit logging of all data modifications

**Encryption Protection:**
- Fernet format: `Timestamp || AES-128-CBC(plaintext) || HMAC(key, timestamp + ciphertext)`
- Guarantees: confidentiality, integrity, and authenticity
- Detects any tampering with InvalidToken exception

---

### 9. Logging & Monitoring Failures (A09:2021)

**Status: ✅ MITIGATED**

**Implemented Measures:**
- Centralized logging via Python logging module
- All authentication attempts logged (success and failure)
- Rate limit violations logged with source IP
- Request/response logging via RequestLoggingMiddleware
- Sensitive data sanitized in logs (no plaintext keys/tokens)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Structured logging with timestamps, source IP, action
- Monitoring via `app.monitoring` module
- Deployment info logged at startup
- Configurable log retention and rotation

**Logged Events:**
- API authentication attempts
- Rate limit violations
- Invalid content-type submissions
- Oversized request attempts
- Security middleware activations
- Encryption manager initialization

---

### 10. Server-Side Request Forgery (SSRF) (A10:2021)

**Status: ✅ MITIGATED**

**Implemented Measures:**
- Internal IP verification via `verify_internal_request()`
- Whitelist of allowed internal IPs
- X-Forwarded-For header validation for proxy scenarios
- HTTP 403 Forbidden for unauthorized internal requests
- All internal endpoint access logged
- URL validation for any external API calls
- DNS rebinding protection (validate target before request)
- Request timeout enforcement

**Internal Endpoint Protection:**
```python
from app.auth import verify_internal_request

@app.get("/internal/admin")
async def admin_endpoint(request: Request):
    verify_internal_request(request)
    # Protected endpoint logic
```

---

## Additional Security Measures (8+ Beyond OWASP Top 10)

### 1. Rate Limiting & DDoS Protection

**Measure:** Request rate limiting per IP address
- Limit: 60 requests per minute per IP
- Middleware: `RateLimitMiddleware`
- Response: HTTP 429 Too Many Requests
- Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
- Protects against: Brute force, credential stuffing, DoS attacks

**Implementation:**
```python
from app.security import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)
```

---

### 2. Request Size Validation

**Measure:** Enforce maximum request payload size
- Maximum: 10MB per request
- Validation: Content-Length header checking
- Response: HTTP 413 Payload Too Large
- Protects against: Memory exhaustion, buffer overflow attacks

**Configuration:**
```python
MAX_REQUEST_SIZE_MB = 10
MAX_REQUEST_SIZE_BYTES = 10 * 1024 * 1024
```

---

### 3. Content-Type Validation

**Measure:** Validate incoming Content-Type headers
- Allowed types: application/json, application/x-www-form-urlencoded, multipart/form-data
- Methods: POST, PUT, PATCH
- Response: HTTP 400 Bad Request for invalid types
- Protects against: Content confusion attacks, injection attacks

---

### 4. Encryption at Rest

**Measure:** Symmetric encryption for sensitive data
- Library: cryptography.fernet (AES-128-CBC + HMAC)
- Environment variable: ENCRYPTION_KEY
- Manager class: `EncryptionManager` in `app/encryption.py`
- Auto-detects tampering via InvalidToken exception
- Protects against: Data breaches, unauthorized access to sensitive info

**Usage:**
```python
from app.encryption import encryption_manager

# Encrypt
encrypted = encryption_manager.encrypt("sensitive_data")

# Decrypt
decrypted = encryption_manager.decrypt(encrypted)
```

---

### 5. Security Headers

**Measure:** Comprehensive HTTP security headers
- Middleware: `SecurityHeadersMiddleware`
- Headers:
  - `X-Content-Type-Options: nosniff` (MIME sniffing protection)
  - `X-Frame-Options: DENY` (Clickjacking protection)
  - `Content-Security-Policy: default-src 'self'` (XSS protection)
  - `Strict-Transport-Security: max-age=31536000` (HTTPS enforcement)
  - `Referrer-Policy: strict-origin-when-cross-origin` (Referrer leakage prevention)
  - `Permissions-Policy: ...` (Browser feature restriction)
  - Server header removed (information disclosure prevention)

---

### 6. Input Validation Middleware

**Measure:** Multi-layer request validation
- Middleware: `InputValidationMiddleware`
- Validates: Content-Type, request size, method restrictions
- Prevents: Injection attacks, malformed requests, oversized payloads

---

### 7. Audit Logging

**Measure:** Comprehensive audit trail of security events
- All authentication attempts logged (success/failure)
- Rate limit violations logged with source IP
- Invalid requests logged with details
- Encryption manager events logged
- Timestamp and source IP included in all logs
- Log levels: INFO for security events, WARNING for potential issues

**Logged Security Events:**
```
Authentication attempt: missing Authorization header
API authentication attempt: invalid key (timestamp, IP)
Rate limit exceeded for 192.168.1.100: 65 requests in 60s
Invalid content-type: application/xml from 10.0.0.50
Request too large: 15728640 bytes (max: 10485760) from 192.168.1.1
```

---

### 8. Constant-Time Comparison

**Measure:** Prevent timing attacks on security credentials
- Implementation: Character-by-character comparison in `verify_api_key()`
- Protection: Timing side-channel attacks cannot leak key information
- Prevents: Attackers inferring key character-by-character from response time

---

## Configuration Checklist

### Required Environment Variables

```bash
# Authentication
API_KEY_PRODUCTION=<strong-random-key-min-32-chars>

# Encryption
ENCRYPTION_KEY=<fernet-key-base64-encoded>

# Internal Access (comma-separated IPs)
INTERNAL_IPS=127.0.0.1,10.0.0.0/8,192.168.0.0/16

# Optional
LOG_LEVEL=INFO
```

### Generate ENCRYPTION_KEY

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Set as ENCRYPTION_KEY env var
```

### Generate API_KEY_PRODUCTION

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

---

## Middleware Order

**Critical:** Middlewares must be added in correct order:

1. **SecurityHeadersMiddleware** (outermost) — Adds security headers
2. **InputValidationMiddleware** — Validates request format/size
3. **RateLimitMiddleware** (innermost) — Rate limits requests

```python
# app/main.py
from app.security import (
    SecurityHeadersMiddleware,
    InputValidationMiddleware,
    RateLimitMiddleware,
)

# Order matters: outermost to innermost
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(RateLimitMiddleware)
```

---

## Testing Security

### Test API Key Validation

```bash
# Without key (should return 403)
curl http://localhost:8000/protected

# With invalid key (should return 403)
curl -H "Authorization: Bearer invalid" http://localhost:8000/protected

# With valid key (should work)
curl -H "Authorization: Bearer $API_KEY" http://localhost:8000/protected
```

### Test Rate Limiting

```bash
# Send 70 requests in quick succession (should hit 429)
for i in {1..70}; do
  curl -H "Authorization: Bearer $API_KEY" http://localhost:8000/health
done
```

### Test Security Headers

```bash
curl -i http://localhost:8000/health

# Should see:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Content-Security-Policy: ...
# Strict-Transport-Security: ...
# (no Server header)
```

### Test Request Size Validation

```bash
# Send >10MB payload (should return 413)
dd if=/dev/zero bs=1M count=11 | \
  curl -X POST \
    -H "Content-Type: application/json" \
    -H "Content-Length: $((11*1024*1024))" \
    --data-binary @- \
    http://localhost:8000/upload
```

### Test Content-Type Validation

```bash
# Invalid content-type (should return 400)
curl -X POST \
  -H "Content-Type: application/xml" \
  -d "<data/>" \
  http://localhost:8000/api/submit
```

---

## References & Standards

- **OWASP Top 10 2021:** https://owasp.org/Top10/
- **OWASP Secure Coding Practices:** https://cheatsheetseries.owasp.org/
- **NIST Cybersecurity Framework:** https://www.nist.gov/cyberframework
- **CIS Benchmarks:** https://www.cisecurity.org/benchmarks/
- **Cryptography Standards:** https://cryptography.io/
- **FastAPI Security:** https://fastapi.tiangolo.com/tutorial/security/

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Authentication Failures** — Rate of failed API key validations
2. **Rate Limit Violations** — IPs exceeding request limits
3. **Encryption Errors** — InvalidToken exceptions during decryption
4. **Request Size Violations** — Payloads exceeding 10MB
5. **Invalid Content-Types** — Non-standard content submissions

### Recommended Alert Thresholds

- **Authentication failures** > 10 per minute → Investigate
- **Rate limit violations** from single IP > 5 per hour → Potential attack
- **Encryption errors** > 5 per minute → Key mismatch or tampering
- **Invalid requests** > 50 per hour → Malformed client traffic

---

## Deployment Checklist

- [ ] Set API_KEY_PRODUCTION to strong random value
- [ ] Set ENCRYPTION_KEY and store securely (e.g., Vault, Secrets Manager)
- [ ] Configure INTERNAL_IPS for internal-only endpoints
- [ ] Verify security headers in production via curl/browser DevTools
- [ ] Enable HTTPS only (redirect HTTP to HTTPS)
- [ ] Monitor logs for authentication/rate limit events
- [ ] Test rate limiting with load testing tool
- [ ] Test encryption/decryption with sample data
- [ ] Review security logs daily
- [ ] Update dependencies regularly
- [ ] Conduct security audit before production release
- [ ] Enable WAF (Web Application Firewall) if available

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-27 | Initial security hardening implementation |

---

**Last Updated:** May 27, 2026
**Maintained By:** Security & Infrastructure Team
**Classification:** Internal Documentation
