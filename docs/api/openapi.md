# OpenAPI Specification

The complete OpenAPI specification for the MCP Audio Server is available below:

```yaml
!!swagger-ui ../openapi.yaml
```

You can also view this documentation in interactive form at the `/docs` endpoint of your running MCP Audio Server instance:

```
http://localhost:8000/docs
```

## Downloading the Specification

The OpenAPI specification is available in YAML format and can be downloaded from the running server:

```bash
curl -o openapi.yaml http://localhost:8000/openapi.yaml
```

## Using with API Tools

The OpenAPI specification can be imported into various API tools:

- **Postman**: Import the specification to create a collection
- **Swagger UI**: Open the specification in the Swagger Editor
- **Client Generation**: Use tools like OpenAPI Generator to create client libraries

## Schema Versioning

The API adheres to semantic versioning. The current schema version is specified in all responses via the `schema_version` field.

Breaking changes to the API will result in a new major version of the schema. Backward compatibility is maintained within the same major version.
