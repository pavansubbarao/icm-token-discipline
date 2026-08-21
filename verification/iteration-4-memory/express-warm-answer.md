# Where and when Express sets the ETag response header

Source: FRESH record card `.icm/records/express-etag-header.md` (all 6 anchors sha-verified against the current repo), plus one grep across `lib/` confirming no new set-sites exist. Repo: /home/claude/repos/express-M.

## The one place in core

Express core sets the ETag header in exactly one place: **`res.send`** — `this.set('ETag', etag)` at **lib/response.js:189**. `res.json` and `res.jsonp` build a body and call `res.send`; `res.render` funnels to `res.send` too — so all inherit this logic. (Grep-verified: no other `set('ETag'` site in `lib/`.)

## Full condition set (lib/response.js:161–191)

ETag is generated and set iff **all** of:

1. **No ETag already set** on the response: `!this.get('ETag')` (line 163).
2. **`etag fn` app setting is a function**: `typeof etagFn === 'function'` where `etagFn = app.get('etag fn')` (line 163). It is not a function when the `etag` setting is `false`.
3. **`len !== undefined`** (line 187): a body length was determined — i.e. the body chunk is not `undefined` and no `Transfer-Encoding` header is set.
4. **The generator returns truthy**: `etag = etagFn(chunk, encoding)` must yield a value (lines 187–189).

Afterward: `req.fresh` may flip the status to **304** (line 194); for 204/304 the body and entity headers are stripped but **ETag is kept** (lines 197–202).

## App settings and defaults

- **Default**: `app.set('etag', 'weak')` in `defaultConfiguration` — **lib/application.js:95**. So by default Express sends weak ETags (`W/"..."`) on `res.send`-family responses.
- **Trigger**: `app.set('etag', val)` compiles the generator — **lib/application.js:364–365**: `this.set('etag fn', compileETag(val))`.
- **`compileETag`** (**lib/utils.js:130–152**): function → used as-is; `true` or `'weak'` → `exports.wetag`; `'strong'` → `exports.etag`; `false` → `undefined` (disables generation); anything else → `TypeError`.
- **Generators**: `exports.etag` (strong, **lib/utils.js:40**) and `exports.wetag` (weak, **lib/utils.js:51**), both produced by `createETagGenerator` (**lib/utils.js:249–250**), which wraps the `etag` npm package over the body Buffer.

## sendFile / static path (different mechanism)

- **`res.sendFile`** does not use the logic above: it passes `opts.etag = this.app.enabled('etag')` (**lib/response.js:402**) into the **`send`** module, which generates its own **stat-based weak ETag** (from file size + mtime). Only the on/off state of the `etag` setting carries over — the weak/strong choice does **not**. `res.download` delegates to `sendFile` (**lib/response.js:483**), so same behavior.
- **`express.static`** is the **`serve-static`** module re-exported at **lib/express.js:79**; it has its **own `etag` option (default `true`)**, entirely independent of app settings — a static file gets an ETag unless `express.static(root, { etag: false })` is passed.
- `node_modules` is absent in this repo; `send`/`serve-static` behavior stated here is their documented contract (as recorded on the card).

## Files I read

| File | How much | Bytes |
|---|---|---|
| /home/claude/icm-token-discipline/SKILL.md | full | 9,587 |
| /home/claude/repos/express-M/.icm/records/express-etag-header.md | full, via `icm_records.sh recall` output (incl. freshness header) | 1,573 |

No Express source file was opened. Non-read tool output entering context: one Grep for `ETag` across `lib/` (20 lines, ~1.4 KB) and one `wc -c` line (~0.1 KB).

## Load report

- SKILL.md → 9,587 B → ~2.4k tokens
- record card (recall output) → ~1,750 B → ~0.45k tokens
- Grep output → ~1,400 B → ~0.35k tokens
- wc/mkdir output → ~120 B → ~0.03k tokens
- **Stage total ≈ 12.9 KB ≈ 3.2k tokens** — under the ~8k stage budget.
- Session floor (system prompt, tool schemas, task prompt) is separate and not counted above.
- Session hygiene: single-question session; `/clear` before the next task.
- These are bytes÷4 estimates; real numbers come from `/context` and `/cost` in Claude Code.

Card status: answered from the existing FRESH card — no re-filing needed (no new derivation performed).
