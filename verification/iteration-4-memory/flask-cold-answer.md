# How `flask run` decides which host and port to bind

Repository: `/home/claude/repos/flask-M` (Flask source tree). All paths below are relative to that root.

## 1. Entry-point chain

- `pyproject.toml:82` — console script `flask = "flask.cli:main"`.
- `src/flask/cli.py:1122-1123` — `def main(): cli.main()`.
- `src/flask/cli.py:1110` — `cli = FlaskGroup(...)`, an instance of `FlaskGroup` (class at `src/flask/cli.py:531`).
- `FlaskGroup.__init__` (`src/flask/cli.py:563-598`) registers `run_command` as the `run` subcommand at line 594.

## 2. CLI options and defaults (the primary source)

`run_command` is defined at `src/flask/cli.py:882-993` (`@click.command("run", ...)` at 882, function at 935):

- `--host` / `-h` — `src/flask/cli.py:883`: `@click.option("--host", "-h", default="127.0.0.1", help="The interface to bind to.")`
- `--port` / `-p` — `src/flask/cli.py:884`: `@click.option("--port", "-p", default=5000, help="The port to bind to.")`

So with nothing else set, the dev server binds **127.0.0.1:5000**. Related options declared alongside (886-933): `--cert` (via `CertParamType`, cli.py:780), `--key` (validated by `_validate_key`, cli.py:828), `--reload/--no-reload` (default `None`), `--debugger/--no-debugger` (default `None`), `--with-threads/--without-threads` (default `True`), `--extra-files`, `--exclude-patterns` (both `SeparatedPathType`, cli.py:867). `run_command.params.insert(0, _debug_option)` at cli.py:996 adds `--debug/--no-debug` (option object at cli.py:485-490).

## 3. Environment variables — the `auto_envvar_prefix` mechanism

`FlaskGroup.__init__` sets, at `src/flask/cli.py:585`:

```python
extra["context_settings"].setdefault("auto_envvar_prefix", "FLASK")
```

This is Click's automatic-envvar feature: for any option without an explicit `envvar`, Click derives one as `<PREFIX>_<COMMAND-PATH>_<OPTION-NAME>` and uses it when the option was not given on the command line. For the `run` subcommand that yields:

- `FLASK_RUN_HOST` → fills `--host`
- `FLASK_RUN_PORT` → fills `--port`

(likewise `FLASK_RUN_CERT`, `FLASK_RUN_KEY`, `FLASK_RUN_RELOAD`, `FLASK_RUN_DEBUGGER`, `FLASK_RUN_EXTRA_FILES`, `FLASK_RUN_EXCLUDE_PATTERNS`; `SeparatedPathType.convert` at cli.py:873-879 splits multi-path envvar values on `os.path.pathsep`). There is no host/port-specific code in Flask for this — the wiring is entirely the one `auto_envvar_prefix` line at cli.py:585 plus Click's option resolution. An explicit CLI flag always beats the env var.

## 4. Dotenv behavior (how those env vars can come from files)

Because env vars must exist *before* Click resolves the `run` options, dotenv loading happens eagerly at group level, before the subcommand runs:

- `FlaskGroup.__init__` prepends `_env_file_option` first in `params` (cli.py:577; comment at 573-576: "--env-file must come first so that it is eagerly evaluated before --app"; the option object at cli.py:517+ is eager per the comment at 515-516).
- `_env_file_callback` (`src/flask/cli.py:493-512`): if a `-e/--env-file PATH` value was given, or default loading is enabled, it calls `load_dotenv(value, load_defaults=ctx.obj.load_dotenv_defaults)` (line 510). Passing `--env-file` without python-dotenv installed raises `BadParameter` (501-506).
- `load_dotenv` (`src/flask/cli.py:698-763`):
  - No-op returning `False` if `python-dotenv` is not importable; prints a yellow tip to stderr if `.env`/`.flaskenv` exist anyway (735-743).
  - With `load_defaults=True`, searches upward from the CWD via `dotenv.find_dotenv(name, usecwd=True)` for **`.flaskenv` first, then `.env`** and merges their values with `data |= ...` (747-752), so `.env` overrides `.flaskenv`; an explicit `path` is merged last and overrides both (754-755).
  - Values are written to `os.environ` **only if the key is not already set** (757-761) — the real environment always wins over any dotenv file.
- Default loading can be disabled two ways: `FlaskGroup(load_dotenv=False)` (cli.py:568, 590), or the env var `FLASK_SKIP_DOTENV` — `ScriptInfo.__init__` stores `self.load_dotenv_defaults = get_load_dotenv(load_dotenv_defaults)` (cli.py:322), the ScriptInfo being built in `FlaskGroup.make_context` with `load_dotenv_defaults=self.load_dotenv` (cli.py:670-674). `get_load_dotenv` (`src/flask/helpers.py:36-48`) returns the default when `FLASK_SKIP_DOTENV` is unset/empty, else `val.lower() in ("0", "false", "no")` — i.e. any truthy value like `FLASK_SKIP_DOTENV=1` skips the default files.

Net effect: a `.flaskenv`/`.env` file containing `FLASK_RUN_HOST=0.0.0.0` / `FLASK_RUN_PORT=8000` populates `os.environ` before option parsing, and Click's auto-envvar then feeds those into `--host`/`--port`.

## 5. Effective precedence for host and port

1. Explicit CLI flag: `flask run --host H --port P` (cli.py:883-884)
2. Real environment: `FLASK_RUN_HOST` / `FLASK_RUN_PORT` (via `auto_envvar_prefix="FLASK"`, cli.py:585)
3. `--env-file PATH` file values (cli.py:510, 754-755)
4. `.env` (cli.py:748-752)
5. `.flaskenv` (loaded first, lowest file priority)
6. Hardcoded defaults `127.0.0.1` / `5000` (cli.py:883-884)

(3-5 act by setting the env vars of level 2 and never overwrite pre-existing environment values, cli.py:757-761.)

## 6. Final handoff to the WSGI server

`run_command` body (`src/flask/cli.py:954-993`):

1. Loads the app lazily: `app = info.load_app()` (955); import errors are deferred under the reloader (957-966), raised immediately otherwise (968-971).
2. `debug = get_debug_flag()` (973); unset `--reload`/`--debugger` default to that debug flag (975-979).
3. `show_server_banner(debug, info.app_import_path)` (981; function at 766-777).
4. Hands off to **Werkzeug's dev server** — `run_simple` is imported at cli.py:19 (`from werkzeug import run_simple`) and called at cli.py:983-993:

```python
run_simple(host, port, app,
           use_reloader=reload, use_debugger=debugger, threaded=with_threads,
           ssl_context=cert, extra_files=extra_files, exclude_patterns=exclude_patterns)
```

The already-resolved `host` and `port` values are passed positionally; Werkzeug does the actual socket bind.

## 7. What `flask run` does NOT consult

- **`SERVER_NAME` config is ignored by `flask run`** — `SERVER_NAME` appears nowhere in `src/flask/cli.py` (grep verified). It is only used for routing/URL building (e.g. `src/flask/app.py:537`) and as a host:port fallback inside `Flask.run()` (`src/flask/app.py:633`, fallback parse at 721-727), which is the *other*, programmatic way to start the dev server.
- `FlaskGroup.make_context` sets `os.environ["FLASK_RUN_FROM_CLI"] = "true"` (`src/flask/cli.py:667`) precisely so that an unguarded `app.run()` in the imported module becomes a no-op under the CLI — the CLI's own host/port resolution always governs.

---

## Files I read

Every file opened this session, how much of it, and bytes loaded (estimates for partial reads at ~40 B/line):

| File | How much | Bytes loaded |
|---|---|---|
| `/home/claude/icm-token-discipline/SKILL.md` | full (57 lines, mandated) | 9,587 |
| `/home/claude/icm-token-discipline/references/memory.md` | full (50 lines, card format) | 3,253 |
| `/home/claude/repos/flask-M/src/flask/cli.py` (36,836 B total) | slices only: 485-519, 555-600, 660-680 (sed), 690-779, 866-1000, 1115-1128 + 3 grep line-hit lists (~341 of 1,127 lines) | ~12,500 |
| `/home/claude/repos/flask-M/src/flask/helpers.py` | grep -A9 `get_load_dotenv` + sed 45-49 (~15 lines) | ~600 |
| `/home/claude/repos/flask-M/src/flask/app.py` | grep hits + 7 context lines (SERVER_NAME, `def run(`) | ~700 |
| `/home/claude/repos/flask-M/pyproject.toml` | 1 grep hit line | ~40 |
| directory listings / `wc -c` outputs | 3 short command outputs | ~500 |

## Load report

- SKILL.md: 9,587 B ≈ 2,397 tok (skill overhead, mandated)
- references/memory.md: 3,253 B ≈ 813 tok (card protocol)
- src/flask/cli.py slices: ~12,500 B ≈ 3,125 tok
- src/flask/helpers.py slice: ~600 B ≈ 150 tok
- src/flask/app.py grep slices: ~700 B ≈ 175 tok
- pyproject.toml: ~40 B ≈ 10 tok
- listings/misc command output: ~500 B ≈ 125 tok

**Total loaded: ~27,200 B ≈ ~6,800 tokens** (~4,400 excluding skill-infrastructure reads,
inside the ~8k stage budget). Session floor (system prompt, tool schemas) is separate and
not counted here. Rules applied: recall-before-analysis (cold — no card existed), measure-
before-reading (cli.py 36.8 KB → grep + 6 slices, never whole), no re-reads, batched
commands. Filed: `.icm/records/flask-run-host-port-binding.md` (stamped). These are
byte/4 estimates; real numbers come from `/context` and `/cost` in Claude Code.
Session hygiene: stage complete — next stage should start after `/clear`.
