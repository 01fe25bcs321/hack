# AI Provider Modes

DocFusion AI supports two analysis modes:

## Public AI — Google Gemini

The backend uses the Google GenAI Python SDK. The Gemini API key is loaded only from `GEMINI_API_KEY` in `.env`; it is never sent to the frontend.

## Private AI — Ollama

The backend can call an Ollama server at `OLLAMA_BASE_URL`, defaulting to `http://localhost:11434`. The user selects an installed Ollama model in the frontend. Source content is sent to the local Ollama endpoint instead of Google.

Example:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT=180
```

Install Ollama separately, start it, and pull a model:

```powershell
ollama pull gemma3:4b
```

Then start DocFusion AI. The Sources page checks `/api/ai/providers`, lists available Ollama models, and allows the user to choose Public AI or Private AI before analysis.

Cryptographic operations do not depend on either AI provider. SHA-256, Ed25519 signing, and independent verification continue to work without Gemini or Ollama.
