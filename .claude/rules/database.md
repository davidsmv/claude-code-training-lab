---
paths:
  - "src/db/**/*.sql"
---

# SQL rules

- Every SQL statement in the database module must run inside an explicit transaction boundary (`BEGIN` ... `COMMIT`, with `ROLLBACK` on failure).
- Do not rely on implicit autocommit.
