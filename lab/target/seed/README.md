# Seed data

SQL files placed here are run by the Postgres image on first start (they are
mounted at `/docker-entrypoint-initdb.d`). Use them to load **throwaway** test
data and a `redkeep-test` account for authenticated scans.

Rules:

- Throwaway data only — no real customers, no real PII, no real payment data.
- Create a dedicated low-noise test user for the API auth passes (Phase 4).
- Keep credentials here consistent with `config.yaml -> auth`.

Example (`01-redkeep-seed.sql`):

```sql
-- Example only; adjust to the CRM schema.
-- INSERT INTO users (username, password_hash, role)
-- VALUES ('redkeep-test', '<bcrypt-of-test-password>', 'TESTER');
```

Files run in filename order, so prefix with `01-`, `02-`, etc.
