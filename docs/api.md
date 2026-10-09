# API

- GET `/api/health`
- POST `/api/sources/upload` multipart `files`
- POST `/api/sources/url` JSON `{url}`
- POST `/api/sources/text` JSON `{name,content}`
- GET `/api/sources`
- GET `/api/sources/{source_id}`
- POST `/api/analyze`
- POST `/api/documents/generate` JSON `{title,analysis}`
- GET `/api/documents/{document_id}`
- GET `/api/documents/{document_id}/download?format=pdf|json`
- GET `/api/documents/{document_id}/verification-package`
- POST `/api/verify` multipart `document`, optional `signature`, optional `public_key`
