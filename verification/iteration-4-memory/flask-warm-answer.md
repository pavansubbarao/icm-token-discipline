# How `flask run` decides which host and port to bind

Answered from a FRESH record card (`.icm/records/flask-run-host-port-binding.md`, filed 2026-08-21; all six anchors verified fresh by `icm_records.sh recall` at answer time). No source files were re-read.

## 1. Entry point
- `pyproject.toml:82` registers the console script `flask = "flask.cli:main"` → `main()` in `src/flask/cli.py`, which invokes `cli`, a `FlaskGroup` instance defined at `src/flask/cli.py:1110`.

## 2. CLI options and defaults
- `run_command` (`src/flask/cli.py:935`, option decorators at `src/flask/cli.py:882-897`):
  - `--host` / `-h`, default `127.0.0.1` (line 883)
  - `--port` / `-p`, default `5000` (line 884)

## 3. Environment variables and the wiring mechanism
- `FlaskGroup.__init__` (`src/flask/cli.py:563-598`) sets `context_settings["auto_envvar_prefix"] = "FLASK"` at line 585.
- That is Click's auto-envvar mechanism: any option not supplied on the command line is filled from the environment variable named `PREFIX_COMMANDPATH_OPTION` — here `FLASK_RUN_HOST` and `FLASK_RUN_PORT`. So env vars beat the built-in defaults but lose to explicit flags.

## 4. Dotenv behavior
- The group has an eager `-e` / `--env-file` option (`src/flask/cli.py:517`) whose callback `_env_file_callback` (`src/flask/cli.py:493-512`) calls `load_dotenv` (`src/flask/cli.py:698-763`).
- `load_dotenv` locates `.flaskenv` and `.env` via `dotenv.find_dotenv(usecwd=True)` and merges: explicit `--env-file` path > `.env` > `.flaskenv`. It writes into `os.environ` **only keys not already set**, so real environment variables always win over dotenv files. It is a silent no-op if `python-dotenv` is not installed.
- Default `.env`/`.flaskenv` discovery is skipped when `FLASK_SKIP_DOTENV` is truthy — `get_load_dotenv` in `src/flask/helpers.py:36-48` — threaded through `ScriptInfo.load_dotenv_defaults` (`src/flask/cli.py:322`, set in `FlaskGroup.make_context`, `src/flask/cli.py:670-674`).
- Because dotenv loading happens eagerly during group parsing, the values it injects are visible to Click's auto-envvar lookup when `run` later resolves its options.

## 5. Effective precedence
CLI flag (`--host`/`--port`) > real environment variable (`FLASK_RUN_HOST`/`FLASK_RUN_PORT`) > `--env-file` file > `.env` > `.flaskenv` > built-in defaults `127.0.0.1:5000`.

## 6. Final handoff to the WSGI server
- In the body of `run_command` (`src/flask/cli.py:973-996`), Flask calls Werkzeug's dev server: `run_simple(host, port, app, use_reloader=..., use_debugger=...` (both derived from `get_debug_flag()`), `threaded=with_threads, ssl_context=cert)` at `src/flask/cli.py:983-993`. `run_simple` is imported at `src/flask/cli.py:19`.

## 7. What is *not* consulted
- `SERVER_NAME` config is never read by `flask run` (zero references in `cli.py`); only `app.run` uses it (`src/flask/app.py:633`, `721-727`).
- The CLI sets `FLASK_RUN_FROM_CLI=true` (`src/flask/cli.py:667`), which turns `app.run()` into a no-op when running under the CLI, so the CLI path above is authoritative.

## Files I read
- `/home/claude/icm-token-discipline/SKILL.md` (required skill entry)
- `.icm/records/flask-run-host-port-binding.md` — via `scripts/icm_records.sh recall` output (not a direct Read)
- Repository source files read this session: **none** — all file/line facts come from the fresh record card.

## Load report
| Item | Bytes | Est. tokens (bytes ÷ 4) |
|---|---|---|
| icm-token-discipline/SKILL.md | 9,587 | ~2,400 |
| record card via recall stdout (incl. freshness header) | ~2,000 | ~500 |
| wc/mkdir tool output | ~200 | ~50 |
| **Stage total** | **~11,800** | **~2,950** |

- Session floor (system prompt, tool schemas, auto-loaded context) is separate from and larger than this stage total.
- Stage total is well under the ~8k budget; the record card replaced what would otherwise have been several thousand tokens of `cli.py` reads.
- Session hygiene: this stage is done — `/clear` (or a fresh session) before the next stage.
- These are estimates; real numbers come from `/context` (composition) and `/cost` (spend) in Claude Code.
