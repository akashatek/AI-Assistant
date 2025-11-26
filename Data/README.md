# AI Assistant - Data

```
> source ./dev.env

> psql $POSTGRES_URL -f tasks.sql

CREATE TABLE
GRANT
GRANT
INSERT 0 5
                  id                  |                       name                        | is_completed |          created_at           
--------------------------------------+---------------------------------------------------+--------------+-------------------------------
 f2f70ba3-9488-4599-ad3e-5fe0b5f4d25e | Configure PostgREST endpoint URL in index.js      | f            | 2025-11-26 12:58:32.936623+00
 906270a0-b4bc-45b3-895b-3575d5f47168 | Test adding a new task via POST request           | f            | 2025-11-26 12:58:32.936623+00
 d1707804-1f4c-4af9-97ee-29bd620742af | Verify task completion status updates via PATCH   | f            | 2025-11-26 12:58:32.936623+00
 b82abc4f-3d9a-4775-a2a3-cc05cfe741d3 | Load database schema into PostgREST configuration | t            | 2025-11-26 12:58:32.936623+00
 6acd4d2d-5581-4fa0-8d10-44a38116df2f | Finalize design review for fixed header/footer    | f            | 2025-11-26 12:58:32.936623+00
(5 rows)
```