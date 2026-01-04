# Validate Local Deployment

Validate that the Docker deployment works correctly in local mode.

## Steps

1. Navigate to the deploy directory
2. Start containers with local overrides (no Caddy, ports exposed)
3. Wait for health check to pass
4. Verify all services are running (app, postgres, minio, redis)
5. Test API endpoints (/health, /docs)
6. Test MinIO console accessibility
7. Report results

## Commands to Run

```bash
cd deploy && ./validate-local.sh
```

## Expected Outcome

All services should start and pass health checks:
- App: http://localhost:8000/health
- Swagger: http://localhost:8000/docs
- MinIO Console: http://localhost:9003 (minioadmin/minioadmin)

## Cleanup

```bash
cd deploy && ./validate-local.sh --cleanup
```
