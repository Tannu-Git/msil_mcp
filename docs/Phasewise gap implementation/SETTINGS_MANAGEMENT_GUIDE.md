# Settings Management Guide

**Document Version**: 1.0  
**Date**: January 31, 2026  
**Status**: Complete

---

## Overview

The MSIL MCP Server provides comprehensive settings management through the Admin Portal. All P0 and P1 configuration settings can be viewed and modified through a centralized Settings UI at `/settings`.

---

## Features

### 1. Centralized Configuration
- All system settings in one place
- Organized by logical categories
- Real-time updates without server restart (runtime changes)
- Visual indicators for changed values

### 2. Categories

#### 🛡️ Authentication & Security
- **OAuth2 Enabled**: Enable/disable OAuth2 authentication
- **JWT Algorithm**: Token signing algorithm (HS256)
- **Access Token Expiry**: Token validity in minutes (default: 60)
- **Refresh Token Expiry**: Refresh token validity in days (default: 7)

#### 🔐 Policy Engine
- **OPA Enabled**: Enable Open Policy Agent for RBAC
- **OPA URL**: Open Policy Agent server URL

#### 📋 Audit & Compliance
- **Audit Enabled**: Enable comprehensive audit logging
- **S3 Bucket**: AWS S3 bucket for audit storage
- **Retention Days**: Audit log retention period (default: 365 days)

#### ⚡ Resilience
- **Circuit Breaker Threshold**: Failures before circuit opens (default: 5)
- **Recovery Timeout**: Seconds before circuit recovery (default: 60)
- **Max Retry Attempts**: Maximum retry count (default: 3)
- **Retry Base**: Exponential backoff base in seconds (default: 2)

#### 🚦 Rate Limiting
- **Rate Limiting Enabled**: Enable API rate limiting
- **Per User Limit**: Requests per minute per user (default: 100)
- **Per Tool Limit**: Requests per minute per tool (default: 50)

#### 📦 Batch Execution
- **Max Concurrency**: Parallel tool executions in batch (default: 10)
- **Max Batch Size**: Maximum tools per batch request (default: 20)

#### 💾 Cache & Redis
- **Redis Enabled**: Enable Redis caching
- **Redis URL**: Redis connection string
- **Cache TTL**: Default cache time-to-live in seconds (default: 300)

#### 🌐 API Gateway
- **Gateway Mode**: API mode (mock or msil_apim)
- **Mock API URL**: Mock API base URL for testing
- **MSIL APIM URL**: Production APIM base URL

#### 🗄️ Database
- **Database URL**: PostgreSQL connection string (read-only)
- **Pool Size**: Database connection pool size (default: 5)
- **Max Overflow**: Maximum overflow connections (default: 10)

#### 🤖 OpenAI
- **Model**: OpenAI model to use (default: gpt-4-turbo-preview)
- **Max Tokens**: Maximum tokens per request (default: 4096)

#### ⚙️ System
- **App Name**: Application name (read-only)
- **App Version**: Application version (read-only)
- **Debug Mode**: Enable debug logging
- **Log Level**: Logging level (DEBUG, INFO, WARNING, ERROR)

---

## API Endpoints

### Get All Settings
```http
GET /api/admin/settings
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "authentication": {
    "oauth2_enabled": true,
    "jwt_algorithm": "HS256",
    "jwt_access_token_expire_minutes": 60,
    "jwt_refresh_token_expire_days": 7
  },
  "policy": {
    "opa_enabled": true,
    "opa_url": "http://localhost:8181"
  },
  ...
}
```

### Get Settings by Category
```http
GET /api/admin/settings/{category}
Authorization: Bearer <jwt_token>
```

Example: `GET /api/admin/settings/resilience`

**Response:**
```json
{
  "circuit_breaker_failure_threshold": 5,
  "circuit_breaker_recovery_timeout": 60,
  "retry_max_attempts": 3,
  "retry_exponential_base": 2
}
```

### Update Setting
```http
PUT /api/admin/settings/{category}/{key}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "value": <new_value>
}
```

Example: Update retry attempts
```http
PUT /api/admin/settings/resilience/retry_max_attempts
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "value": 5
}
```

**Response:**
```json
{
  "success": true,
  "message": "Setting resilience.retry_max_attempts updated successfully",
  "new_value": 5,
  "note": "This is a runtime change. Update .env file for persistence."
}
```

---

## Usage

### Admin Portal UI

1. **Navigate to Settings**
   - Login to Admin Portal (http://localhost:3001)
   - Click "Settings" in the sidebar

2. **View Settings**
   - Settings are organized by category
   - Each category displays all related settings
   - Current values are shown in input fields

3. **Modify Settings**
   - Change the value in the input field
   - A "Save" button appears next to changed values
   - Click "Save" to apply the change
   - Success/error message displays at the top

4. **Reload Settings**
   - Click "Reload" button in the header
   - Fetches latest values from server
   - Discards unsaved local changes

### Programmatic Access

```typescript
// Get all settings
const settings = await api.get('/admin/settings');

// Get category settings
const resilience = await api.get('/admin/settings/resilience');

// Update setting
await api.put('/admin/settings/resilience/retry_max_attempts', {
  value: 5
});
```

---

## Security

### Authorization
- **Admin Only**: All settings endpoints require admin role
- **JWT Required**: Bearer token must be present in Authorization header
- **Audit Logged**: All settings changes are logged to audit trail

### Sensitive Data
- Passwords and secrets are masked in responses
- Database URLs show `***` for password portion
- API keys and tokens are redacted

### Example Masking:
```
Original: postgresql://user:password123@localhost/db
Masked:   postgresql://user:***@localhost/db
```

---

## Persistence

### Runtime vs Persistent Changes

**Runtime Changes** (via Admin Portal):
- Update settings in memory
- Take effect immediately
- Lost on server restart

**Persistent Changes** (via .env file):
1. Update `.env` file with new values
2. Restart server to load changes
3. Settings persist across restarts

### Recommended Workflow

1. **Testing**: Use Admin Portal for quick testing
2. **Development**: Update `.env` file and restart
3. **Production**: Use environment variables or config management

### Example .env Update:
```env
# Resilience Settings
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
RETRY_MAX_ATTEMPTS=3
RETRY_EXPONENTIAL_BASE=2

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_USER=100
RATE_LIMIT_PER_TOOL=50
```

---

## Monitoring

### Audit Trail
All settings changes are logged with:
- User who made the change
- Setting key and new value
- Timestamp
- Correlation ID

View in: **Audit Logs** → Filter by `event_type: config_change`

### Example Audit Entry:
```json
{
  "event_id": "evt-123",
  "event_type": "config_change",
  "user_id": "admin@msil.com",
  "action": "update_setting",
  "metadata": {
    "config_key": "RETRY_MAX_ATTEMPTS",
    "new_value": "5"
  },
  "timestamp": "2026-01-31T10:30:00Z"
}
```

---

## Validation

### Type Validation
- Boolean fields: checkbox (true/false)
- Number fields: numeric input with validation
- String fields: text input

### Range Validation
Settings have sensible ranges:
- **Retry attempts**: 1-10
- **Circuit breaker threshold**: 1-20
- **Rate limits**: 1-1000 req/min
- **Batch size**: 1-50 tools
- **Token expiry**: 1-1440 minutes (24 hours max)

### Error Handling
```json
{
  "detail": "Invalid value for resilience.retry_max_attempts: must be between 1 and 10"
}
```

---

## Best Practices

### 1. Test Changes First
- Use development environment
- Test with small changes
- Monitor logs and metrics

### 2. Document Changes
- Note why settings were changed
- Track in version control (.env)
- Update team documentation

### 3. Monitor Impact
- Watch circuit breaker state after threshold changes
- Monitor retry attempts after changing retry settings
- Check rate limit violations after limit adjustments

### 4. Gradual Rollouts
- Change one setting at a time
- Observe for 15-30 minutes
- Roll back if issues occur

### 5. Backup Configuration
```bash
# Backup current settings
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/settings > settings-backup.json
```

---

## Troubleshooting

### Settings Not Saving
1. Check admin permissions
2. Verify JWT token is valid
3. Check server logs for errors
4. Ensure setting key is configurable

### Changes Not Taking Effect
1. Some settings require server restart
2. Check if setting is runtime-modifiable
3. Verify value format is correct
4. Check for validation errors

### Server Restart Required For:
- Database connection changes
- Redis URL changes
- JWT secret changes
- OpenAI API key changes

### Runtime Modifiable:
- Rate limits
- Circuit breaker thresholds
- Retry attempts
- Batch sizes
- Cache TTL
- Feature toggles (enabled/disabled)

---

## Examples

### Increase Rate Limits
```bash
# Increase user rate limit to 200 req/min
curl -X PUT http://localhost:8000/api/admin/settings/rate_limiting/rate_limit_per_user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": 200}'
```

### Adjust Circuit Breaker
```bash
# Make circuit breaker more sensitive (3 failures)
curl -X PUT http://localhost:8000/api/admin/settings/resilience/circuit_breaker_failure_threshold \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": 3}'
```

### Increase Retry Attempts
```bash
# Increase retries to 5
curl -X PUT http://localhost:8000/api/admin/settings/resilience/retry_max_attempts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": 5}'
```

### Enable Debug Mode
```bash
# Enable debug logging
curl -X PUT http://localhost:8000/api/admin/settings/system/debug \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": true}'
```

---

## Summary

The Settings Management UI provides:

✅ **Centralized Configuration** - All settings in one place  
✅ **Real-time Updates** - Changes take effect immediately  
✅ **Security** - Admin-only access with JWT authentication  
✅ **Audit Trail** - All changes logged for compliance  
✅ **Validation** - Type and range checking  
✅ **Categorization** - Logical grouping of related settings  
✅ **Read-only Protection** - Sensitive settings cannot be changed  
✅ **Visual Feedback** - Clear indication of changed values  

The Admin Portal is now the **single source of truth** for managing all aspects of the MSIL MCP Server.

---

## Support

For issues or questions:
- Check the Audit Logs for settings changes
- Review server logs for errors
- Backup settings before making changes
- Contact system administrator for production changes
