# Where and under what conditions Express sets the ETag response header

Repo: /home/claude/repos/express-M (Express 5.x layout). All line numbers verified in this repo on 2026-08-21.

## 1. The only place Express core sets the header: `res.send`

File: `lib/response.js`, function `send` (`res.send = function send(body)`, line 126).

- Line 162: `var etagFn = app.get('etag fn')`
- Line 163: `var generateETag = !this.get('ETag') && typeof etagFn === 'function'`
- Lines 185–191: the header write —
  ```js
  var etag;
  if (generateETag && len !== undefined) {
    if ((etag = etagFn(chunk, encoding))) {
      this.set('ETag', etag);         // line 189 — the single setHeader site in core
    }
  }
  ```

**Full condition set** (all must hold):
1. The response has **no ETag header already set** (`!this.get('ETag')`, line 163).
2. The app setting **`etag fn` is a function** (line 163) — i.e. the `etag` setting was not disabled with `false`.
3. **`len !== undefined`** (line 187), which requires (lines 167–183): the body `chunk !== undefined` **and** there is **no `Transfer-Encoding` header** on the response. (`res.send(null)` becomes `chunk = ''` at line 150, so an empty body still gets an ETag with length 0.)
4. The generator returns a **truthy value** (`etagFn(chunk, encoding)`, line 188).

Everything that produces a body funnels through here: `res.json`/`res.jsonp` call `this.send(body)`, and `res.render`'s default callback calls `res.send(str)` — so they inherit exactly these conditions. After the ETag is set, freshness is evaluated (`if (req.fresh) this.status(304)`, line 194; `req.fresh` in `lib/request.js:462–486` compares the response's ETag/Last-Modified via the `fresh` module); the 204/304 header strip (lines 197–202) removes Content-Type/Content-Length/Transfer-Encoding but **keeps the ETag**.

Performance detail: line 172 — when no ETag will be generated and the string chunk is < 1000 chars, Express computes `Buffer.byteLength` only; otherwise it converts the chunk to a Buffer (lines 176–179) so the same bytes feed both Content-Length and the ETag generator.

## 2. The generator functions

File: `lib/utils.js`.
- Line 17: `var etag = require('etag')` — the `etag` npm package (`^1.8.1`, package.json line 45) does the actual hashing.
- Line 40: `exports.etag = createETagGenerator({ weak: false })` — strong ETags.
- Line 51: `exports.wetag = createETagGenerator({ weak: true })` — weak ETags.
- Lines 249–257: `createETagGenerator(options)` returns `generateETag(body, encoding)` which coerces the body to a Buffer and returns `etag(buf, options)` (content-hash based).

## 3. The settings that control it

File: `lib/application.js`.
- **Default**: `defaultConfiguration` sets `this.set('etag', 'weak')` at **line 95** — so out of the box ETags are ON and weak.
- `app.set` trigger, lines 364–365: setting `'etag'` recompiles the derived setting — `this.set('etag fn', compileETag(val))`.
- `compileETag(val)` — `lib/utils.js:130–152`:
  - a **function** → used as-is (custom generator, signature `(body, encoding)`);
  - `true` or `'weak'` → `wetag` (weak ETag);
  - `'strong'` → `etag` (strong ETag);
  - `false` → `fn` stays `undefined` → condition 2 above fails → **ETag generation disabled**;
  - anything else → `TypeError: unknown value for etag function: <val>`.

So the relevant settings are `etag` (user-facing; default `'weak'`) and `etag fn` (derived; default `wetag`, populated automatically because `defaultConfiguration`'s `this.set('etag', 'weak')` runs through the same trigger).

## 4. The sendFile / download / static path

Here Express core does **not** set the header itself; it delegates to the `send` module.

- `res.sendFile` — `lib/response.js:373–415`. Line 402: `opts.etag = this.app.enabled('etag')`; line 403: `var file = send(req, pathname, opts)`. So the app's `etag` setting only passes an on/off boolean: any truthy setting (`'weak'`, `'strong'`, `true`, a custom function) → `true`; `false` → `false`. The weak/strong choice and any custom generator do **not** carry over.
- `res.download` — `lib/response.js:483` — `return this.sendFile(fullPath, opts, done)` — same path.
- `express.static` — `lib/express.js:79`: `exports.static = require('serve-static')` (`^2.2.0`, package.json line 59). serve-static forwards its own `etag` option (default enabled) to `send`; it is configured per-middleware (`express.static(root, { etag: false })`) and is **independent of the app's `etag` setting**.
- Inside `send` (`^1.1.0`, package.json line 58), when its `etag` option is enabled the module generates a **stat-based weak ETag** (from the file's size and mtime, `etag(stat)`) and sets the header while streaming — this is the documented contract of the pinned dependency versions; it could not be re-verified from source in this repo because `node_modules` is not installed.

## Summary table

| Path | Who sets the header | Condition |
|---|---|---|
| `res.send` / `res.json` / `res.jsonp` / `res.render` | Express core, `lib/response.js:189` | no existing ETag ∧ `etag fn` is a function ∧ body defined ∧ no Transfer-Encoding ∧ generator returns truthy |
| `res.sendFile` / `res.download` | `send` module | `app.enabled('etag')` (wired at `lib/response.js:402`); stat-based weak ETag |
| `express.static` | `send` via `serve-static` | middleware's own `etag` option (default on); app settings irrelevant |

Defaults: `etag` = `'weak'` (`lib/application.js:95`) → `etag fn` = `wetag` → weak content-hash ETags on all `res.send`-family responses with a defined body.

## Files I read

Skill/protocol files (full reads):
- /home/claude/icm-token-discipline/SKILL.md — full — 9,587 B
- /home/claude/icm-token-discipline/scripts/icm_records.sh — full — 4,128 B
- /home/claude/icm-token-discipline/references/memory.md — full — 3,253 B

Repo files (sliced reads only; no repo file read in full):
- /home/claude/repos/express-M/lib/response.js — lines 100–219 — 2,981 B
- /home/claude/repos/express-M/lib/response.js — lines 360–434 — 1,997 B
- /home/claude/repos/express-M/lib/utils.js — lines 28–55 — 538 B
- /home/claude/repos/express-M/lib/utils.js — lines 120–154 — 518 B
- /home/claude/repos/express-M/lib/utils.js — lines 238–259 — 378 B
- /home/claude/repos/express-M/lib/application.js — lines 85–102 — 490 B
- /home/claude/repos/express-M/lib/application.js — lines 352–376 — 648 B

Not read (located by grep only): lib/express.js, lib/request.js, package.json — cited lines come from grep output.

## Load report

| Source | Bytes | Est. tokens (B/4) |
|---|---|---|
| Skill + records protocol (session overhead, not repo analysis) | 16,968 | ~4,240 |
| Repo slices (7 reads) | 7,550 | ~1,890 |
| Grep/wc/ls tool output (map phase + recall) | ~3,000 | ~750 |
| **Total loaded this session** | **~27,500** | **~6,900** |

Repo-analysis load alone: ~10.5 KB ≈ ~2,650 tokens — within the ~8k stage budget. Session floor (system prompt, tool schemas) is separate and not counted here. These are estimates; real numbers come from `/context` and `/cost` in Claude Code. Recall ran first (cold — no records existed); a record card was filed after judgment: `.icm/records/express-etag-header.md` (stamped). Session hygiene: this stage is complete — next task should start fresh (`/clear`).
