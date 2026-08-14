# Wayfinder tracker (local markdown)

This repo has no `docs/agents/` tracker and no `## Agent skills` block. Wayfinder work lives here as markdown.

## Labels

| Label | Role |
| --- | --- |
| `wayfinder:map` | The map issue for one effort |
| `wayfinder:research` | AFK: facts from docs or APIs |
| `wayfinder:grilling` | HITL: one decision via live questions |
| `wayfinder:prototype` | HITL: cheap artifact to react to |
| `wayfinder:task` | Work that unblocks a decision |

A ticket takes exactly one `wayfinder:<type>` label. The map takes `wayfinder:map` only.

## Layout

- Map: `docs/wayfinder/maps/<NN>-<slug>.md`
- Child tickets: `docs/wayfinder/tickets/<NN>-<slug>.md`
- Research notes: `docs/wayfinder/research/<slug>.md` (linked from the ticket, not pasted)

`<NN>` is the issue id. Refer to a ticket by its **title**, with the path inside the name.

## Header fields

Every map and ticket file starts with:

```
- Status: open | closed
- Labels: `wayfinder:...`
- Assignee: (unclaimed) | <name>
- Parent: (none) | [title](relative-path)
- Blocked-by: (none) | [title](relative-path), ...
```

- **Claim:** set `Assignee` before any work. Empty / `(unclaimed)` means unclaimed.
- **Close:** set `Status: closed` and add a resolution comment.
- **Native blocking:** this tracker has none. `Blocked-by` is the blocking edge.

## Wayfinding operations

**Create the map:** add a file under `docs/wayfinder/maps/` with `Labels: wayfinder:map`. Fill Destination, Notes, Decisions so far (empty at chart), Not yet specified, Out of scope.

**Create a child ticket:** add a file under `docs/wayfinder/tickets/`. `Parent` points at the map. Body is `## Question` only. Assets and answers go in comments or linked files.

**Wire blocking:** after files exist, set each ticket's `Blocked-by` to the tickets that must close first. A ticket is unblocked when every listed blocker has `Status: closed`, or when `Blocked-by` is `(none)`.

**Frontier query:** child tickets of the map where `Status` is `open`, `Assignee` is `(unclaimed)`, and every `Blocked-by` ticket is `closed` or the field is `(none)`.

**Claim:** set `Assignee` on that file.

**Resolve:** append under `## Comments` a resolution comment (the answer, plus links to notes or prototypes). Set `Status: closed`. On the map, append one gist line under Decisions so far. Do not restate the full answer on the map.

**Research notes:** write `docs/wayfinder/research/<slug>.md`. Link it from the ticket comment. Do not use git branches unless a later session needs isolation.

**Comments:** append under `## Comments`. Do not edit older comments.
