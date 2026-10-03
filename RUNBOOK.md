# Workforce Management Platform � Operations Runbook

## 1. Application returns HTTP 500

1. Open Render ? Workforce Management Platform ? Logs.
2. Find the request timestamp and traceback.
3. Identify whether the failure is application, database, or configuration related.
4. Reproduce locally if possible.
5. Fix the root cause.
6. Run the relevant pytest tests.
7. Deploy the verified fix.
8. Confirm `/health` returns HTTP 200.

## 2. Login returns 401

1. Verify username/email and password.
2. Check that the authentication endpoint is reachable.
3. Check the JWT/token response.
4. Confirm the token is being sent in the Authorization header.
5. Check token expiry/invalid-token handling.
6. Retest login and the protected endpoint.

## 3. User receives 403 Forbidden

1. Confirm the user is authenticated.
2. Check the user's server-side role.
3. Verify the endpoint's RBAC requirement.
4. Do not bypass authorization in the frontend.
5. Retest the endpoint with an authorized and unauthorized role.

## 4. Employee search is slow

1. Reproduce the slow request.
2. Check logs and request timing.
3. Review the SQL query and filters.
4. Check indexes and pagination.
5. Run the performance tests.
6. Retest the endpoint after the change.

## 5. Duplicate records or IDs appear

1. Check the database constraints.
2. Review the transaction and commit behavior.
3. Reproduce with concurrent requests if applicable.
4. Inspect application logs.
5. Run the concurrency/regression tests.
6. Confirm that retrying does not create duplicate state.

## 6. Frontend shows stale data

1. Open browser developer tools.
2. Inspect the API request and response.
3. Confirm the backend returned the current data.
4. Check frontend state/update logic.
5. Refresh and repeat the request.
6. Retest the affected workflow.

## 7. PostgreSQL connection failure

1. Check Render service status and logs.
2. Verify the DATABASE_URL environment variable exists and is correct.
3. Do not expose database credentials in logs or source control.
4. Check database connectivity from the application.
5. Review connection timeout/pool settings.
6. Check `/health` and application logs after recovery.
7. Run database-related tests before deployment.

## 8. Docker cannot connect to PostgreSQL

1. Confirm Docker containers are running.
2. Check environment variables.
3. Verify the PostgreSQL service name/network configuration.
4. Verify the application uses the container database hostname rather than localhost.
5. Check database readiness.
6. Review container logs.
7. Retest the application after correcting the configuration.

## 9. Deployment failure

1. Open Render ? Deploys.
2. Open the failed deployment.
3. Review build logs.
4. Identify the first meaningful error.
5. Fix the issue locally.
6. Run the test suite.
7. Commit and push the verified fix.
8. Confirm the new deployment becomes Live.

## 10. Rollback

1. Identify the failing production commit.
2. Identify the last verified good commit.
3. Confirm the rollback target.
4. Use the documented Git rollback procedure.
5. Verify database migration compatibility before rollback.
6. Deploy the rollback target.
7. Verify `/health`, login, and critical API flows.
8. Record the incident and follow-up action.

## 11. General incident rules

- Never commit passwords, tokens, or database credentials.
- Do not modify production data during troubleshooting unless the change is explicitly authorized.
- Capture logs and timestamps before making changes.
- Prefer reproducing failures in an isolated environment.
- Run tests after every corrective change.
- Record important incidents and corrective actions.
