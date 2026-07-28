# Security Audit

Uploaded documents are untrusted data. Text extracted from them is data, never
instructions; the existing provider system prompt states this correctly.

## Critical

- None proven by execution.

## High

1. **Authorization is absent from document, element, job, export, and provider-read
   routes.** Any network client can list, read, mutate, delete, translate, export,
   and download documents. Provider-write protection also fails open when
   `ADMIN_API_TOKEN` is empty.
2. **Untrusted PDFs are parsed in a network-capable worker with the same image and
   writable document volume.** There is no non-root user or Compose hardening.
3. **Export can destroy translated-region content.** Redaction occurs before fit
   validation; overflow leaves a blank region. This is also a data-integrity P0.

## Medium

- MIME validation trusts extension plus a five-byte signature; parser validation
  happens asynchronously.
- Administrator-controlled provider URLs allow SSRF to worker-reachable services.
  This is a powerful explicit feature and needs a documented host allowlist policy.
- No rate limiting, CSRF strategy, request-size proxy limit, malware scanning, or
  retention worker exists.
- File responses do not re-resolve/validate stored paths at access time.
- Errors from providers/export may expose internal endpoint or parser details.
- No security headers are configured at the web/API boundary.
- Current dependency pins were not vulnerability-scanned successfully in this audit.

## Low

- Default development secret is publicly known.
- No structured audit log records document access or administrator changes.
- CORS supports all methods/headers for configured origins.

## Required P0 remediation

- Fail closed when no admin token is configured and authorize every `/api/*`
  document/provider operation; preserve public liveness/readiness only.
- Make the frontend consistently send the token without putting it in URLs.
- Preflight replacement fit before redaction.
- Run containers as non-root and apply `no-new-privileges`, dropped capabilities,
  and read-only filesystems where compatible.
- Add regression tests for unauthorized access, empty-token behavior, overflow
  source preservation, and accurate unresolved-work status.

## Post-P0 security status

- API authorization and empty-token fail-open behavior are fixed and regression-tested.
- Export redaction data loss is fixed and regression-tested.
- API/worker/web containers are configured non-root with read-only roots, dropped capabilities, `no-new-privileges`, and explicit writable mounts.
- Runtime validation of those container controls is still blocked by the stopped Docker daemon. Treat full worker isolation as unresolved until the hardened stack is started and penetration-tested; the P1 gate therefore remains closed.
