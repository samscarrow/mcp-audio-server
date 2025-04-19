# Error Codes

The MCP Audio Server uses standardized error codes to provide consistent error responses. This page documents all possible error codes, their meanings, and how to resolve them.

## Error Response Format

All error responses follow this format:

```json
{
  "error_code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "additional": "error details"
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Audio Processing Errors

| Error Code | HTTP Status | Description | Resolution |
|------------|-------------|-------------|------------|
| `DECODING_ERROR` | 400 | Failed to decode the audio file | Verify the audio file is not corrupted and matches the specified format |
| `INVALID_AUDIO` | 400 | The audio data is invalid or corrupted | Provide a valid audio file in a supported format |
| `EMPTY_FILE` | 400 | The audio file contains no data | Provide a non-empty audio file |
| `FILE_TOO_LARGE` | 413 | The audio file exceeds the size limit | Reduce the file size or duration |
| `UNSUPPORTED_FORMAT` | 400 | The audio format is not supported | Use one of the supported formats: WAV, MP3, OGG, FLAC, M4A |
| `PROCESSING_ERROR` | 500 | Error while analyzing the audio | Retry with a different audio file or contact support with the correlation ID |

## Validation Errors

| Error Code | HTTP Status | Description | Resolution |
|------------|-------------|-------------|------------|
| `VALIDATION_ERROR` | 400 | Request validation failed | Check the error details and correct the request format |
| `MISSING_FIELD` | 400 | A required field is missing | Include all required fields in the request |
| `INVALID_OPTION` | 400 | One or more options are invalid | Check the documentation for valid option values |
| `SCHEMA_ERROR` | 400 | The request does not match the expected schema | Review the API documentation for the correct request format |

## Server Errors

| Error Code | HTTP Status | Description | Resolution |
|------------|-------------|-------------|------------|
| `INTERNAL_ERROR` | 500 | An unexpected server error occurred | Retry the request or contact support with the correlation ID |
| `SERVER_BUSY` | 503 | The server is currently overloaded | Wait and retry after the time specified in the `Retry-After` header |
| `TIMEOUT` | 408 | The request processing timed out | Retry with a smaller audio file or simpler analysis options |
| `RESOURCE_LIMIT_EXCEEDED` | 429 | Server resource limits were exceeded | Reduce the complexity of the request or try again later |

## Resource Errors

| Error Code | HTTP Status | Description | Resolution |
|------------|-------------|-------------|------------|
| `RESOURCE_NOT_FOUND` | 404 | The requested resource was not found | Check the resource identifier |
| `DEPENDENCY_ERROR` | 503 | A required dependency is unavailable | Check the server status or contact support |
| `CACHE_ERROR` | 500 | Error accessing the cache | Retry the request |

## Example Error Scenarios

### Invalid Audio Format

```json
{
  "error_code": "UNSUPPORTED_FORMAT",
  "message": "The provided audio format 'aac' is not supported",
  "details": {
    "format": "aac",
    "supported_formats": ["wav", "mp3", "ogg", "flac", "m4a"]
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Corrupted Audio File

```json
{
  "error_code": "DECODING_ERROR",
  "message": "Failed to decode audio file: Invalid file structure",
  "details": {
    "format": "wav",
    "error": "FFmpeg reported: Invalid WAV header"
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Server Busy

```json
{
  "error_code": "SERVER_BUSY",
  "message": "Server is currently busy. Please retry after 5 seconds.",
  "details": {
    "retry_after": 5
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
