# Express ETag: default configuration and where/when the header is set

Repo: /home/claude/repos/express-M. Answered from the sha-anchored record card
`.icm/records/express-etag-header.md` (filed 2026-08-21). Recall flagged one STALE anchor
(`lib/application.js:95`); that line was re-verified against the source before answering —
all other anchors were sha-confirmed FRESH and are trusted without re-reading.

## Default configuration

- **Default setting: `this.set('etag', 'strong')` — `lib/application.js:95`**, inside
  `app.defaultConfiguration()` ("default settings" block). NOTE: this repo differs from
  upstream Express, whose default is `'weak'`; this is exactly the change that made the
  record card's anchor stale.
- Setting the `'etag'` value triggers compilation (`app.set` switch, `lib/application.js:364-365`):
  `this.set('etag fn', compileETag(val))`.
- `compileETag` (`lib/utils.js:130-152`) maps: a function → used as-is; `true` or `'weak'` →
  weak generator (`wetag`, `lib/utils.js:51`); `'strong'` → strong generator (`lib/utils.js:40`);
  `false` → `undefined` (disables ETags); anything else → `TypeError`.
- Both generators wrap the `etag` npm package over the body Buffer. **Net default in this repo:
  `'etag fn'` is the STRONG ETag generator.**

## Where and under what conditions the header is set

Core sets the ETag header in exactly **one** place: **`res.send` — `lib/response.js:189`,
`this.set('ETag', etag)`**. Conditions (logic at `lib/response.js:161-191`), all required:

1. The response has **no ETag header already set**;
2. The app's **`'etag fn'` setting is a function** (i.e. ETag generation not disabled via
   `app.set('etag', false)`);
3. **`len !== undefined`** — a content length was determined, which requires the body
   `chunk !== undefined` and no `Transfer-Encoding` header;
4. The generator `etagFn(chunk, encoding)` returns a **truthy** value.

Downstream behavior and related paths:

- `res.json`, `res.jsonp`, and `res.render` all funnel through `res.send`, so they get ETags
  under the same conditions.
- After setting, if `req.fresh` the status flips to **304** (`lib/response.js:194`); the
  204/304 body-strip (`lib/response.js:197-202`) removes body-related headers but keeps ETag.
- `res.sendFile` does **not** use this path: it wires `opts.etag = this.app.enabled('etag')`
  (`lib/response.js:402`) into the `send` module, which generates its own stat-based **weak**
  ETag — the app's weak/strong choice does not carry over, only enabled/disabled.
  `res.download` delegates to `sendFile` (`lib/response.js:483`).
- `express.static` is `serve-static` (`lib/express.js:79`) with its own `etag` option
  (default on), independent of the app-level setting.

## Files I read

- `/home/claude/icm-token-discipline/SKILL.md` (required skill entry)
- `/home/claude/icm-token-discipline/references/memory.md` (rule-8 protocol)
- `/home/claude/repos/express-M/.icm/records/express-etag-header.md` (record card: via recall
  output, then re-read for the update edit)
- `/home/claude/repos/express-M/lib/application.js` — **slice only** (grep hunks around lines
  18-24, 92-98, 361-368) to re-verify the stale anchor. No other repo source was read; all
  other claims come from sha-FRESH card anchors.

## Load report (estimates; real numbers: /context and /cost)

| Load | Bytes | Est. tokens |
|---|---|---|
| SKILL.md | 9,587 | ~2,400 |
| references/memory.md | 3,253 | ~815 |
| recall output (card + freshness) | ~1,800 | ~450 |
| grep slice lib/application.js | ~700 | ~175 |
| card re-read (for edit) | 1,573 | ~395 |
| wc/stamp/check outputs | ~600 | ~150 |
| **Total** | **~17.5 KB** | **~4.4k** |

Session floor (system prompt, tool schemas) is separate and not counted here. Within the ~8k
stage budget; the record card replaced a full multi-file re-derivation (~5-8k saved).
Filed: card `.icm/records/express-etag-header.md` updated ('weak'→'strong' default) and
re-stamped; all 6 anchors FRESH. Session hygiene: stage complete — `/clear` before next task.
