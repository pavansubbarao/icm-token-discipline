# Incident: app-server requests intermittently hang under load — causal candidates

Workspace: /home/claude/repos/codex-S (Rust monorepo under `codex-rs/`, 102 crate dirs).
Method: scaling §2 — hierarchy (never read flat) → name/dependency triage → one subagent
survey of secondary suspects → sliced reads of candidates only.

## Candidates (2–3) + rationale

**1. codex-app-server — primary candidate (dispatch/routing core).**
- Requests are processed **serially**: the single processor loop awaits `process_request(...)`
  inline (`app-server/src/lib.rs:1049-1056`). Any stall in one handler freezes every request
  on every connection.
- Responses/notifications flow through a **bounded** `outgoing` channel, cap 128
  (`lib.rs:474`, cap from `app-server-transport/src/transport/mod.rs:25`) drained by **one**
  outbound router task (`lib.rs:846-899`).
- The router protects itself with `try_send` + disconnect-slow-connection
  (`app-server/src/transport.rs:157-163`), **but** for connections marked non-disconnectable
  it falls back to an **untimed blocking** `writer.send(...).await` (`transport.rs:169`).
  Chain: one stalled writer → router blocks → outgoing channel fills → processor loop blocks
  enqueueing a response → all requests hang. Intermittent and load-proportional by construction.

**2. codex-app-server-transport — the stall source the router blocks on.**
- Untimed `websocket_writer.send(...)` awaits in the write pump
  (`transport/remote_control/websocket.rs:962, 982, 1055`), with tokio mutexes
  (`state.lock().await`, `client_tracker.lock().await`) held around awaited I/O
  (`websocket.rs:946-1010, 1101+`). A slow/half-dead peer wedges the write path, which
  back-pressures the shared cap-128 channel into candidate 1's router.

**3. codex-app-server-daemon — the daemon-interaction leg (with its substrate).**
- Depends on transport + uds. Survey findings: `uds` accept/connect have **no timeout**
  (`uds/src/lib.rs:145,150`), so the daemon's accept/connect path can hang under load; the
  counterpart `app-server-client` runs a **single dispatch `select!` loop** whose untimed
  `stream.send().await` stalls both the reader and its cap-8 `command_tx`
  (`app-server-client/src/remote.rs:986, 220-463`) — requests to/through the daemon wedge.

**Cleared by triage/survey:** `app-server-protocol` (32k lines, pure types/serde — CLEAR),
`async-utils` (CLEAR). `stdio-to-uds` and `websocket-client` show untimed-I/O smells but sit
off the primary request path (secondary hardening targets, not causal candidates).

## Subagent survey summary (one subagent, secondary suspects, returned 10 lines)

- app-server-protocol: CLEAR. async-utils: CLEAR.
- app-server-client: SUSPECT — untimed `stream.send().await` in single dispatch `select!`
  loop stalls reader + bounded cap-8 `command_tx` (remote.rs:986, 220-463). **Promoted.**
- uds: SUSPECT — accept/connect untimed (lib.rs:145,150); underlies daemon transport. Strong secondary.
- stdio-to-uds: SUSPECT — connect/copy/shutdown untimed; `try_join!` hangs if peer never closes (lib.rs:13-33).
- websocket-client: SUSPECT — connect/TLS/WS handshake untimed after happy-eyeballs race (dialer.rs:48,100-129).

## Files I read (main session — slices only, never whole files)

- `codex-rs/app-server/src/lib.rs` — lines 846-903, 966-1000, 1040-1067 (~120 lines of 1,200+)
- `codex-rs/app-server/src/transport.rs` — lines 200-254, 151-186 (~90 lines)
- Grep-only (no full reads): `app-server-transport/src/transport/remote_control/websocket.rs`,
  `transport/mod.rs`, `app-server/src/message_processor.rs`, candidate `Cargo.toml`s
- Skill refs: SKILL.md, scaling.md §2 (sliced), memory.md protocol+template (sliced)
- Never opened in main session: the other ~95 crates, all of app-server-protocol (32k lines),
  all test files, the survey crates (subagent only)

## Load report (est. tokens = bytes ÷ 4; real numbers live in /context and /cost)

| Load (main session, repo) | est. tokens |
|---|---|
| Hierarchy: crate listing + dep edges + sizes (3 shell passes) | ~820 |
| Triage greps: channels, sends, capacities, dispatch sites (5 passes) | ~1,100 |
| Sliced reads: lib.rs 846-903 / 966-1000 / 1040-1067 | ~1,650 |
| Sliced reads: transport.rs 200-254 / 151-186 | ~1,280 |
| Subagent's 10-line answer (transcript never entered session) | ~190 |
| **Repo total** | **~5,000 (≤8k budget — met)** |

Session floor (system prompt, tool schemas, skill files ~4.5k incl. SKILL.md + 3 reference
slices + one ToolSearch fetch) is separate from the stage budget. Stage split 02a/02b was
prepared but not triggered: locate-phase loads ran ~1.9k, leaving inspect-phase room within
one session. Filed: `.icm/records/app-server-hang-under-load.md` (stamped, 5 anchors).
Session hygiene: stage complete — next stage (verify/remediate) should start after /clear,
loading STATE/this card, not scrollback. These are estimates.
