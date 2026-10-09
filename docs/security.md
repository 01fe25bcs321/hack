# Security and privacy

DocFusion AI uses SHA-256 for integrity hashes and Ed25519 for document signatures. Verification is deterministic and does not depend on an AI provider.

Source classification values are PUBLIC, INTERNAL, CONFIDENTIAL, and RESTRICTED. Classification is recorded as source metadata and carried into generated documents. Generating a lower-classification output from CONFIDENTIAL or RESTRICTED sources is blocked. PUBLIC outputs redact common email addresses, phone numbers, employee IDs, and 12-digit ID numbers before the document is hashed and signed. Pattern-based redaction is a useful baseline, not a guarantee that every kind of sensitive information is detected; review public documents before distribution.

The application records audit events for source processing, document generation, verification comparisons, and accept/decline decisions. The retired Access Key / Manager Access workflow is not used.
