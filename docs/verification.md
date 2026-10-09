# Document verification

DocFusion AI verifies canonical document content with SHA-256 and Ed25519. The Verification page lets a user select the currently trusted document and upload a candidate JSON document. File names do not determine whether the documents match.

- If substantive content matches and the candidate hash/signature validate, the page reports that nothing was tampered with.
- Otherwise, it reports the candidate filename, JSON field path, previous trusted value, candidate value, trusted signature status, and candidate signature status. The browser cannot read the user's full local folder path; it can report the uploaded filename and fields within the document.
- Accepting a candidate re-signs its content as a new trusted version and deletes the superseded trusted document and its generated files. An audit event remains to record the decision.
- Declining records the review as declined and leaves the current trusted document unchanged.

A separate public-key upload is not required for exported DocFusion JSON files because the signature package is embedded in the signed JSON. Cryptographic key material remains part of the verification protocol, not a user-facing access-key feature.
