# Operations and troubleshooting

## Configuration

Runtime limits are documented in `.env.example`. Translation provider details belong
in the Settings screen, not environment files. The browser never receives decrypted
API keys.

## Health

- `GET /health/live` checks the API process.
- `GET /health/ready` verifies database and Redis connectivity.
- the Settings connection test calls the configured provider with a minimal request.

## Common failures

- **Provider unavailable**: verify the URL is reachable from the API container. For
  a host Ollama instance, use `host.docker.internal`, not `localhost`.
- **Password-protected PDF**: decrypt a copy before upload; the original is rejected.
- **Overflow warning**: edit the affected block or shorten the translation, then export.
- **Worker unavailable**: inspect `docker compose logs worker redis`.
- **Insufficient disk**: free space on the Docker volume before retrying export.

Back up PostgreSQL and the document volume together. Rotate `ADMIN_API_TOKEN`
regularly. Changing the encryption key makes existing provider secrets unreadable.

