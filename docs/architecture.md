# Architecture

DocFusion AI uses a FastAPI service, SQLite persistence, modular ingestion services, a Gemini analysis provider, a deterministic normalization/fusion layer, and an independent cryptographic verification layer.

Frontend is static HTML/CSS/JavaScript served by FastAPI. Source files are extracted into normalized text, hashed with SHA-256, analyzed by Gemini using structured JSON, reconciled, mapped to provenance, serialized canonically, hashed, signed with Ed25519, and rendered as JSON/PDF.
