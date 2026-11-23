# Security & Privacy

Facial photos are biometric-adjacent personal data. Applicable frameworks to review: **KVKK** (Türkiye, Law No. 6698) and **GDPR** where EU users are involved. This document is engineering guidance, not legal advice.

## Principles

1. **Not a medical device.** No diagnosis, disease names, drugs or treatments. Low quality / out-of-scope / low confidence ⇒ limited flow + dermatologist suggestion.
2. **Data minimisation.** Collect only what the recommendation needs. Unknown stays unknown.
3. **No raw images in the database.** Only metadata + private object-storage key with `expires_at`. Mock path does not persist images.
4. **Explicit consent** with versioned privacy notice before any upload; withdrawable; account deletion purges images, analyses and profile.
5. **Research data separation.** Research datasets, product data and user data are stored separately. No real participant images in the A/B/C study (synthetic profiles + public datasets). If real-participant data is ever needed: ethics committee approval/exemption, informed consent, access control, retention and deletion procedures **before** collection.

## Controls

| Area | Control |
|---|---|
| Transport | TLS everywhere; no cleartext in production builds |
| Auth | Password hashing (argon2/bcrypt), short-lived JWT, rate limiting on auth |
| Secrets | `.env` git-ignored; `.env.example` only; CI secrets in GitHub; never log secrets |
| Storage | Encrypted at rest; private buckets; signed short-lived URLs for masks/Grad-CAM |
| Retention | Face images auto-deleted after analysis window (default proposal: ≤ 30 days, to confirm) |
| Logging | No images, emails or profile contents in logs; request IDs only |
| Uploads | Size limit (`MAX_UPLOAD_MB`), magic-byte type check, EXIF stripped before storage |
| Dependencies | Pinned versions; CI lint/tests; enable Dependabot |
| LLM | Disabled by default; only rule-derived reasons and verified docs sent; no images or identifiers sent to providers |
| Licences | Dataset licences recorded; non-commercial datasets not used commercially; no unlicensed product images |

## Repository and Drive rules

- Never commit datasets, weights, face images, `.env`, service-account keys.
- Google Drive: no real facial photos; no restricted datasets before licence/sharing permissions are confirmed; no duplicates of source code or technical docs.

## Incident response

Revoke leaked credentials immediately, rotate secrets, assess affected data, notify per KVKK/GDPR timelines, document in `Meeting_Notes`.
