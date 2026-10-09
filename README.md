
## AI provider selection

DocFusion AI supports two AI modes from the Sources page:

- **Public AI — Google Gemini:** cloud analysis using the backend's `GEMINI_API_KEY`.
- **Private AI — Local Ollama:** local analysis through an Ollama server, normally `http://localhost:11434`.

For Ollama, install Ollama, start it, and pull a model such as:

```powershell
ollama pull gemma3:4b
```

Configure `.env` if required:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT=180
```

The frontend automatically checks Ollama and lists installed models. Select **Private AI — Local Ollama** before running analysis.


## Access control

DocFusion AI does not use application-level access keys. Upload, AI analysis, signed document generation, download, verification, and change review are available directly through the application. Cryptographic signing and verification remain part of the document trust workflow.



## Recent product improvements

- Professional light UI refresh across dashboard, workspace, document view, and verification.
- Verification compares substantive document content independently of the uploaded filename, validates both the trusted and candidate signatures, and reports exact JSON field paths and before/after values.
- Candidate acceptance creates a newly signed current version and removes the superseded document plus generated verification files; decline leaves the current trusted document unchanged and records the decision.
- Dashboard KPIs include citation coverage, unresolved conflicts, provenance coverage, unsupported claims without source links, extraction success, OCR status, and redaction counts. Metrics are computed from stored records and should not be interpreted as independently benchmarked accuracy.
- Sources can be classified as PUBLIC, INTERNAL, CONFIDENTIAL, or RESTRICTED. PUBLIC document generation redacts common PII patterns before hashing/signing, and generation is blocked when it would lower a CONFIDENTIAL/RESTRICTED source's classification.
- Scanned PDF extraction attempts PyMuPDF's Tesseract OCR integration when text extraction finds blank pages. Tesseract must be installed separately on Windows for OCR to work; sources needing OCR are flagged instead of silently treated as fully extracted.
