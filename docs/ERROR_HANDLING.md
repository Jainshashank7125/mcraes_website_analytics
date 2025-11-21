# Production-Level Error Handling System

This document describes the comprehensive error handling system implemented across all backend endpoints to provide user-friendly error messages while maintaining detailed logging for debugging.

## Overview

The error handling system ensures that:
1. **Users see friendly, non-technical error messages** - No jargon, clear explanations
2. **Developers get detailed technical information** - Full error details logged for debugging
3. **Consistent error format** - All errors follow the same structure
4. **Automatic error conversion** - Technical errors are automatically converted to user-friendly messages

## Architecture

### Core Components

1. **Exception Classes** (`app/core/exceptions.py`)
   - Custom exception classes for different error types
   - User-friendly message mapping
   - Automatic technical detail logging

2. **Error Handlers** (`app/core/error_handlers.py`)
   - FastAPI exception handlers
   - Unified error response format
   - Validation error formatting

3. **Error Utilities** (`app/core/error_utils.py`)
   - Decorator for automatic error handling
   - Context-aware error conversion

4. **Frontend Error Handler** (`frontend/src/utils/errorHandler.js`)
   - Extracts user-friendly messages from API responses
   - Handles both old and new error formats

## Error Response Format

All errors follow this consistent format:

```json
{
  "error": {
    "message": "User-friendly error message",
    "error_code": "ERROR_CODE",
    "details": {
      "error_type": "ExceptionType",
      "context": "where the error occurred"
    }
  }
}
```

### Example Error Responses

**Authentication Error:**
```json
{
  "error": {
    "message": "Your session has expired. Please sign in again.",
    "error_code": "AUTH_ERROR",
    "details": {
      "error_type": "AuthenticationException",
      "context": "signing in"
    }
  }
}
```

**Database Error:**
```json
{
  "error": {
    "message": "Unable to connect to the database. Please try again in a moment.",
    "error_code": "DATABASE_CONNECTION_ERROR",
    "details": {
      "error_type": "DatabaseException",
      "context": "fetching brands"
    }
  }
}
```

**Validation Error:**
```json
{
  "error": {
    "message": "Please check your input: email: This field is required.",
    "error_code": "VALIDATION_ERROR",
    "details": {
      "validation_errors": [...]
    }
  }
}
```

## Exception Types

### BaseAPIException
Base class for all API exceptions. Includes:
- User-friendly message
- Technical message (logged, not sent to client)
- Error code
- Additional details

### Specific Exception Classes

1. **DatabaseException** (500)
   - Database connection errors
   - Query errors
   - Constraint violations

2. **AuthenticationException** (401)
   - Invalid tokens
   - Expired sessions
   - Wrong credentials

3. **ValidationException** (400)
   - Invalid input
   - Missing required fields
   - Format errors

4. **NotFoundException** (404)
   - Resource not found
   - Brand not found
   - Item doesn't exist

5. **ExternalServiceException** (502)
   - GA4 API errors
   - Scrunch AI errors
   - Agency Analytics errors

6. **ConfigurationException** (500)
   - Missing configuration
   - Invalid settings

## Error Message Mappings

Common technical errors are automatically mapped to user-friendly messages:

| Technical Error Pattern | User-Friendly Message |
|------------------------|----------------------|
| Connection/Network errors | "Unable to connect to the database. Please try again in a moment." |
| Authentication/Token errors | "Your session has expired. Please sign in again." |
| Invalid credentials | "The email or password you entered is incorrect." |
| Email already exists | "An account with this email already exists." |
| Not found errors | "The requested item could not be found." |
| GA4 errors | "Unable to fetch Google Analytics data. Please check your configuration." |
| Scrunch errors | "Unable to fetch data from Scrunch AI. Please try again later." |
| Validation errors | "Please check your input and try again." |
| Date format errors | "Please enter dates in the format YYYY-MM-DD (e.g., 2024-01-15)." |

## Usage in Endpoints

### Using the Decorator (Recommended)

```python
from app.core.error_utils import handle_api_errors

@router.get("/data/brands")
@handle_api_errors(context="fetching brands")
async def get_brands():
    # Your code here - exceptions are automatically handled
    supabase = SupabaseService()
    result = supabase.client.table("brands").select("*").execute()
    return result.data
```

### Manual Exception Handling

```python
from app.core.exceptions import NotFoundException, handle_exception

@router.get("/data/brand/{id}")
async def get_brand(id: int):
    try:
        brand = await fetch_brand(id)
        if not brand:
            raise NotFoundException(
                user_message=f"Brand with ID {id} could not be found.",
                technical_message=f"Brand {id} not found in database"
            )
        return brand
    except NotFoundException:
        raise  # Re-raise custom exceptions
    except Exception as e:
        raise handle_exception(e, context="fetching brand")
```

## Frontend Integration

The frontend automatically extracts user-friendly messages:

```javascript
import { getErrorMessage } from '../utils/errorHandler'

try {
  const data = await api.get('/api/v1/data/brands')
} catch (error) {
  const userMessage = getErrorMessage(error)
  showError(userMessage) // Shows user-friendly message
}
```

The `getErrorMessage` utility:
- Extracts `error.error.message` (new format)
- Falls back to `error.detail` (old format)
- Provides sensible defaults

## Logging

All errors are logged with full technical details:

```
ERROR - API Error [DATABASE_ERROR]: Connection refused
User Message: Unable to connect to the database. Please try again in a moment.
Details: {'error_type': 'ConnectionError', 'context': 'fetching brands'}
Traceback: [full stack trace]
```

This ensures:
- **Users** see friendly messages
- **Developers** can debug with full technical details
- **Logs** contain all necessary information

## Benefits

1. **User Experience**
   - Clear, actionable error messages
   - No technical jargon
   - Consistent error format

2. **Developer Experience**
   - Automatic error handling
   - Detailed logging
   - Easy debugging

3. **Maintainability**
   - Centralized error handling
   - Consistent error format
   - Easy to update messages

4. **Security**
   - No sensitive information leaked
   - Technical details only in logs
   - Safe error messages

## Error Codes Reference

| Error Code | Description | HTTP Status |
|-----------|-------------|-------------|
| `DATABASE_ERROR` | Database-related errors | 500 |
| `DATABASE_CONNECTION_ERROR` | Connection issues | 500 |
| `DATABASE_QUERY_ERROR` | Query execution errors | 500 |
| `AUTH_ERROR` | Authentication errors | 401 |
| `AUTH_INVALID` | Invalid token/session | 401 |
| `AUTH_EXPIRED` | Expired session | 401 |
| `AUTH_CREDENTIALS_ERROR` | Wrong credentials | 401 |
| `VALIDATION_ERROR` | Input validation errors | 400 |
| `NOT_FOUND` | Resource not found | 404 |
| `GA4_ERROR` | Google Analytics errors | 502 |
| `SCRUNCH_ERROR` | Scrunch AI errors | 502 |
| `AGENCY_ANALYTICS_ERROR` | Agency Analytics errors | 502 |
| `TIMEOUT_ERROR` | Request timeout | 504 |
| `RATE_LIMIT_ERROR` | Too many requests | 429 |
| `PERMISSION_ERROR` | Access denied | 403 |

## Testing Error Handling

To test error handling:

1. **Database Errors**: Disconnect database or use invalid query
2. **Authentication Errors**: Use expired/invalid token
3. **Validation Errors**: Send invalid input data
4. **Not Found Errors**: Request non-existent resource
5. **External Service Errors**: Disconnect external APIs

All errors should return user-friendly messages while logging technical details.

