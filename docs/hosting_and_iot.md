# Hosting, the IoT data path, and PostgreSQL

Status: the application, its tests and the migration tool have been run on **PostgreSQL 16** locally (the whole backend suite
passes on both SQLite and PostgreSQL). It has **not been deployed** yet: creating the Render, Neon and Vercel accounts and
entering their secrets is yours to do (steps below). Read the Render logs of the first start.

## Can we use Render?
Yes. Render runs the API (a normal FastAPI service) and can also host PostgreSQL. What matters for a device that uploads
continuously:

| Point | What to know |
|---|---|
| Free web service | It **sleeps when idle** and a cold start takes tens of seconds. Fine for a demo you wake up first. For boards that upload all day use an always-on paid instance. |
| Database | Check the *current* Render and Neon plans and limits before relying on a free tier: free databases are small and may expire or suspend. Neon's free tier is about 0.5 GB, which is why the raw CSI retention rule exists. |
| Region | Put the API **and** the database in the same region (the blueprint uses Singapore; Neon has a matching region). One upload makes several database round trips, so a database in another region multiplies the latency of every request. |
| Cold start and the bridge | The bridge keeps packets in a bounded queue and retries, so a sleeping or restarting API delays data instead of losing it (up to the queue size, 20,000 packets, about 3 minutes at 100 packets/s). |

Recommendation: Render (API, Singapore, always-on once you run real boards) + Neon or Render Postgres in the same region + Vercel
for the frontend. Nothing here is Render-specific, so moving later is a configuration change.

## Why PostgreSQL, and what changed to get there
SQLite does not enforce foreign keys, stores timestamps as text and allows a single writer. PostgreSQL enforces the schema,
handles concurrent uploads and is what production uses (`ENVIRONMENT=production` refuses SQLite). Running the full suite on it
found real bugs that SQLite had hidden; all are fixed and covered by tests:

- the seed inserted a sensing event for a device id that did not exist (a foreign key SQLite ignored);
- roles and activity types are seeded with fixed ids, so PostgreSQL's id counters were behind and the next insert collided
  (`sync_postgres_sequences()` runs after seeding and after a data copy);
- timestamps are stored as UTC without a time zone, and comparing them with time-zone-aware values was shifted by the database
  server's own zone (the booking reminder test caught it); the connection is now pinned to UTC;
- a room with two residents returned whichever came first in database order for the emergency view; it now picks the resident
  the alert names, otherwise a stable order;
- `postgres://` URLs (some hosts hand these out) are accepted, and several tests no longer assume SQLite's leniency.

CI now runs the whole backend suite twice: on SQLite and on a PostgreSQL 16 service container.

## The data path for real IoT devices
```
ESP32-S3 TX ──ESP-NOW──► ESP32-S3 RX ──USB serial──► bridge (PC) ──HTTPS, keep-alive──► API ──► PostgreSQL
        ~100 frames/s          CSI lines            queue + retry          batches of 50        bulk insert
```
What makes it fast, in the order it matters over a real network:

1. **The serial reader never waits for the network.** The bridge hands packets to a sender thread. Before, each upload blocked the
   reader, so a slow network meant lost serial data.
2. **One persistent connection (keep-alive).** A new HTTPS connection costs two to three extra round trips before any data moves.
3. **Batches of up to 50 packets, or 250 ms, whichever comes first** (the API accepts up to 100). Throughput of one sender is
   about *batch size / (round trip + server time)*, so bigger batches matter most when the round trip is long.
4. **Compact I/Q (`iq_b64`).** The 104 int8 values go as base64 instead of a JSON integer list, which cuts the request by about
   43% (a 50-packet request: 34.2 KB as a list, 19.3 KB compact, measured). The API expands it, so the stored format is unchanged.
5. **Store and forward.** A failed batch is retried in order with exponential backoff; the queue is bounded and, when full, drops
   the *oldest* packets and counts them. A wrong token (401/403) stops the bridge. Nothing is dropped silently.
6. **One multi-row insert per request** on the server instead of one statement per packet.

### Measured locally (Windows PC, PostgreSQL 16 on the same machine, `tools/ingest_benchmark.py`)
| Setup | Request size | Round trip p50 | Server time p50 | One sender sustains |
|---|---|---|---|---|
| Old: batches of 10, new connection each, integer list | 6.8 KB | 26 ms | n/a (not measured then) | 431 packets/s |
| New code, same pattern (batch 10, new connection) | 6.8 KB | 21 ms | 7 ms | 472 packets/s |
| Batch 50, keep-alive, integer list | 34.2 KB | 16 ms | 12 ms | 2,443 packets/s |
| Batch 50, keep-alive, compact | 19.3 KB | 15 ms | 13 ms | 2,604 packets/s |
| Batch 100, keep-alive, compact | 38.7 KB | 21 ms | 18 ms | 3,461 packets/s |

The radio produces about 100 packets/s, so locally there is roughly 25 times headroom. **These numbers say nothing about the
internet**: there the round trip dominates. Arithmetic, not a measurement: with a 150 ms round trip, the old pattern (batches of
10, a new TLS connection each time, about four round trips per upload) tops out near 16 packets/s, below the radio rate, while
batches of 50 on a kept-alive connection allow about 290 packets/s. Measure your real path by running the benchmark and the
bridge against the hosted API.

### Reporting: what is measured and where you see it
- Every ingest response carries `server_ms` and an `X-Process-Ms` header.
- The bridge sends its previous round trip, queue depth and dropped count in `X-Client-*` headers, and stamps each packet with
  the time it was read.
- `GET /sensing/devices/{id}/live` returns `delivery`: server time (p50/p95), **ingest delay** (bridge read → server received,
  which includes batching and network time and depends on the two clocks agreeing), the bridge's own round trip, its queue depth,
  and packets it had to drop. The packet stream panel shows them. They are kept in memory per server process (the last 200
  requests), so they reset on restart and each instance reports its own traffic.
- The bridge prints the same on its status line, and the final summary lists retries and drops.

## Retention rule for raw CSI
`raw_csi_telemetry` is the high-volume table (about 500 bytes a packet: roughly 160 MB an hour for one board at 90 packets/s,
before indexes). It is a **rolling window**; detections, alerts and audit history are never touched.

- Packets the detector has **already analysed or skipped** are deleted once older than `RAW_CSI_RETENTION_HOURS` (default 24).
- If the table passes `RAW_CSI_MAX_ROWS` (default 300,000), the oldest analysed packets go first.
- Packets the detector has **not** processed yet are never deleted by age, so a stopped detector cannot lose data. If the table is
  over the cap with nothing deletable, the status says `over_cap_with_nothing_deletable` instead of dropping them silently.
- A background thread applies the rule every `RAW_CSI_PRUNE_INTERVAL_SECONDS` (default 600). `GET /sensing/retention`
  (system admin and facility manager) shows the policy, how full the table is, and what the last prune removed.

On a small database the row cap sets the window: 150,000 rows is about 28 minutes of one board at 90 packets/s. That is enough
for the detector (windows are about 250 packets) and for the live view; it is not an archive. If you need to keep raw data for
research, export it before it ages out or move to the Phase 2 design below.

## Steps you do (accounts and secrets stay with you)
1. **Database**: create a Neon project (or a Render Postgres) in the region you will use for Render, and copy the connection
   string (`postgresql://USER:PASS@HOST/DB?sslmode=require`).
2. **Render**: New > Blueprint, connect this GitHub repo (`render.yaml`). In the dashboard set:
   - `DATABASE_URL` = the connection string
   - `ALLOWED_ORIGINS` = your Vercel URL (set after step 3, then redeploy)
   - `SEED_PASSWORD` = a password only you know (12+ characters)
3. **Vercel**: import the repo, root directory `frontend`, build env `VITE_API_BASE=https://<your-service>.onrender.com`.
4. Open the Vercel URL and log in with the demo emails below and your `SEED_PASSWORD`.

Demo emails: `blesson@wifisense.com` (system admin), `elizabeth@wifisense.com` (care facility manager), `abhinand@wifisense.com`
(corporate facility manager), `mary@wifisense.com` (caregiver), `tomy@wifisense.com` (corporate staff),
`mathew.varghese@wifisense.com` (doctor), `john@wifisense.com` (family member).

Notes: seeding runs once, when the database is empty; changing `SEED_PASSWORD` later does not change existing accounts. Payments
are a sandbox; no real money is involved. `healthCheckPath` is `/health`, which exists on the `demo/all-features` branch.

## Moving existing data from SQLite (optional, controlled)
`backend/migrate_sqlite_to_postgres.py` copies a SQLite database into an **empty** PostgreSQL database. It reads a copy of the
source (the file is never modified), builds the schema with `alembic upgrade head`, copies in foreign-key order inside one
transaction, skips raw CSI, resets the id counters and compares row counts. Rows whose required parent does not exist (SQLite
allowed them, PostgreSQL does not) are listed, and `--orphans skip` drops them.

    python migrate_sqlite_to_postgres.py --source hardware_test.db --target "postgresql://..." --orphans skip           # look first
    python migrate_sqlite_to_postgres.py --source hardware_test.db --target "postgresql://..." --orphans skip --yes     # then do it

Tested on a copy of `hardware_test.db`: 40 tables, 1,954 rows, one dangling sensing event skipped, 337,542 raw packets not
copied, counts matched, and the migrated database served logins and alerts through the API. For a fresh hosted demo you do not
need it: the app seeds itself.

## Connecting the ESP32-S3 boards to the hosted API
The receiver is read over USB by `tools/csi_serial_bridge.py` on the PC beside it; point the bridge at the hosted API:

    python tools/csi_serial_bridge.py --port COM4 --api https://<your-service>.onrender.com --token <device token>

Register the receiver on the hosted site first (Devices page, source "live") to get its token, which is shown once. Use HTTPS;
never put the token in the firmware or the repository. The wire format is in `docs/firmware_contract.md`. Use `--wire list` only
against an API that predates `iq_b64`.

## Phase 2: if the data volume grows
Do these in order, only when a measurement says you need the next one:

1. **More boards on one API** works as is: each bridge is an independent sender with its own token and queue, and the API
   handles uploads concurrently. Watch `server_ms` p95 and the bridge queue depth.
2. **Detect off the request path.** Detection currently runs inside the upload request when a window completes. Moving it to a
   worker (a second Render service, or a thread pool) shortens uploads. The `event_id` column already marks unprocessed packets.
3. **Partition by time** (`raw_csi_telemetry` by day) so retention becomes `DROP PARTITION` instead of `DELETE`, which is much
   cheaper than deleting millions of rows. Needs a migration; PostgreSQL supports it natively.
4. **Boards that upload directly over Wi-Fi** (no PC bridge): use MQTT over TLS to a broker, or WebSocket, and have a small
   consumer write to PostgreSQL. This is a protocol change, not a rewrite, because packet validation lives in one place.
5. **Time-series database** (TimescaleDB on PostgreSQL) if you need long raw history with compression.
6. **Live view over WebSocket/SSE** instead of one-second polling when many people watch.

None of these is built; the first two are small, the rest are real projects. Do not start them without a measured problem.
