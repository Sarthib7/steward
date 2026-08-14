# Cognee remember / add / recall APIs

Date: 2026-08-14
Ticket: Research: Cognee remember, add, and recall APIs for Slack and custom text provenance

## Verdict

For Steward v1 Slack text, Remembered Facts (custom non-URL text), seed notes, and GitHub body text that is not a bare HTTP URL: call permanent `cognee.remember(..., dataset_name=...)` with plain text (or `DataItem`), and call `cognee.recall(..., datasets=[...], top_k=...)` for ask/digest. Do not use bare `http(s)` strings as the sole `data` value when you mean "store this message"; that path scrapes the page. Prefer `remember()` over legacy `add()` + `cognify()` unless Steward needs a staged pipeline. Pin Cognee to the same target as the HackNight demo: `cognee[fastembed] @ git+https://github.com/topoteretes/cognee.git@dev`, which currently reports `1.5.0.dev1` on the `dev` branch tip. Attach Slack/GitHub permalinks in `DataItem.external_metadata` for durable provenance, and also put the permalink in the stored text (or resolve via `datasets.list_data` + `data_id`) if ask/digest must cite it without a separate join. Demo already uses this remember/recall pattern on dataset `"slack"`.

## Evidence

### remember()

**VERIFIED** (https://docs.cognee.ai/python-api/remember):

```python
async def remember(
    data: Union[
        BinaryIO,
        list[BinaryIO],
        str,
        list[str],
        DataItem,
        list[DataItem],
        MemoryEntry,
    ],
    dataset_name: str = "main_dataset",
    *,
    session_id: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunker: Optional[Any] = None,
    custom_prompt: Optional[str] = None,
    run_in_background: bool = False,
    self_improvement: bool = True,
    session_ids: Optional[List[str]] = None,
    dry_run: bool = False,
    **kwargs,
) -> Union[RememberResult, DryRunEstimate]
```

**VERIFIED** behaviour quotes (same page + https://docs.cognee.ai/core-concepts/main-operations/remember):

- "`remember()` is the main ingestion entry point in Cognee v1.0."
- "Without `session_id`, it stores permanent memory by running the ingestion pipeline for you."
- "With `session_id`, it stores session memory in the cache for fast short-term retrieval."
- "When `self_improvement=True`, Cognee also runs `improve()` to enrich the graph or bridge session content into permanent memory."
- Permanent mode: "Plain text is stored directly as memory content." / "HTTP/HTTPS URLs are fetched and passed through the ingestion pipeline."
- Session mode: "In session-memory mode, a URL string is stored in the session cache as text. It is not fetched or scraped."
- Default dataset: `"main_dataset"`.
- Docs position legacy path as: "`remember()` composes Add → Cognify → Improve under the hood" (core concepts Remember page).

**VERIFIED** HackNight demo call (https://raw.githubusercontent.com/qdrant-labs/cognee-demo-slack/main/app.py):

```python
DATASET = "slack"
...
await cognee.remember(text, dataset_name=DATASET)
```

No `session_id` in the demo (permanent memory). No `DataItem`.

### add() / cognify()

**VERIFIED** `add()` signature (https://docs.cognee.ai/python-api/add):

```python
async def add(
    data: Union[BinaryIO, list[BinaryIO], str, list[str], DataItem, list[DataItem]],
    dataset_name: str = 'main_dataset',
    user: User = None,
    node_set: Optional[List[str]] = None,
    ...
    incremental_loading: bool = True,
    data_per_batch: Optional[int] = 2000,
    ...
)
```

**VERIFIED** text vs URL typing on `add` (same page):

- Text strings: "any string that is not a `file://`, `s3://`, `http://` or `https://` URL and does not point to an existing local file."
- "url: A web link url (https or http)" is a supported input type and is scraped.

**VERIFIED** legacy framing (https://docs.cognee.ai/core-concepts/main-operations/legacy-operations/add):

- "`add()` is a legacy operation. In Cognee v1.0, most users should use remember() instead, which replaces the `add()` + `cognify()` + `memify()` workflow with a single call."
- "`add()` is ingestion-only: no embeddings, no graph yet."

**VERIFIED** `cognify()` signature (https://docs.cognee.ai/python-api/cognify):

```python
async def cognify(
    datasets: Union[str, list[str], list[UUID]] = None,
    user: User = None,
    graph_model: BaseModel = KnowledgeGraph,
    chunker = TextChunker,
    chunk_size: int = None,
    ...
    run_in_background: bool = False,
    incremental_loading: bool = True,
    ...
    dry_run: bool = False,
)
```

**VERIFIED** prerequisite: "Must have data previously added via `cognee.add()`."

**INFERRED**: Steward should not call `add`+`cognify` for v1 Slack/fact/seed/GitHub text unless it needs to inspect or pause between ingest and graph build. Demo does not call them.

### recall()

**VERIFIED** signature (https://docs.cognee.ai/python-api/recall):

```python
async def recall(
    query_text: str,
    query_type: SearchType | None = None,
    *,
    datasets: list[str] | None = None,
    dataset_ids: list[UUID] | None = None,
    top_k: int = 15,
    auto_route: bool = True,
    scope: str | list[str] | None = None,
    # plus keyword-only options...
) -> list[RecallResponse]
```

**VERIFIED** behaviour quotes (same page):

- "`recall()` is the main retrieval entry point in Cognee v1.0."
- "`top_k` … Maximum number of results to return." Default `15`.
- "When both `datasets` and `dataset_ids` are omitted, retrieval spans every dataset the current user has `read` access to."
- Optional `session_id` enables session-aware retrieval.
- "`include_references` … Default `False`. When set to `True`, appends a deterministic `Evidence:` block … from the retrieved chunks or graph context."
- Chunk `metadata` keys documented: `data_id`, `chunk_id`, `chunk_index`, `document_name` (not `external_metadata`).
- "Populate memory first with `remember()` (or the legacy `add()` + `cognify()` sequence)."

**VERIFIED** demo call (https://raw.githubusercontent.com/qdrant-labs/cognee-demo-slack/main/app.py):

```python
results = await cognee.recall(text, datasets=[DATASET], top_k=5)
```

### HTTP URL vs plain text containing a permalink

**VERIFIED** docs routing (https://docs.cognee.ai/core-concepts/main-operations/remember):

- "**HTTP/HTTPS URLs as strings** — fetched and ingested in permanent mode"
- "**Raw text strings** — e.g. `"Einstein was born in Ulm."`"
- Permanent: "HTTP/HTTPS URLs are fetched and passed through the ingestion pipeline."
- Session: URL string "is stored in the session cache as text. It is not fetched or scraped."

**VERIFIED** web scrape path (https://docs.cognee.ai/guides/web-url-ingestion):

- "`remember()` recognizes the URL, fetches the page, extracts content according to your rules, and builds the knowledge graph in one call."
- Example data: `"https://en.wikipedia.org/api/rest_v1/page/html/Large_language_model"`.

**VERIFIED** legacy URL scrape note (https://docs.cognee.ai/core-concepts/main-operations/legacy-operations/add):

- "Passing an `http://` or `https://` URL to `cognee.add()` triggers **web page scraping** — the URL is fetched and its response is saved as HTML for processing."

**VERIFIED** implementation on `dev` (`https://raw.githubusercontent.com/topoteretes/cognee/dev/cognee/tasks/ingestion/save_data_item_to_storage.py`):

```python
parsed_url = urlparse(data_item)
...
elif parsed_url.scheme == "http" or parsed_url.scheme == "https":
    await validate_outbound_url(data_item)
    urls_to_page_contents = await fetch_page_content(data_item)
    return await save_data_to_file(urls_to_page_contents[data_item], file_extension="html")
```

**INFERRED**: A string whose `urlparse(...).scheme` is `http`/`https` (typically a bare permalink, or any string that parses with that scheme) is scraped in permanent `remember`/`add`. A normal message body that only *contains* a Slack or GitHub permalink (scheme empty under `urlparse`) is treated as plain text and stored, including the embedded URL characters. Do not pass a lone `html_url` / Slack permalink as `data` if Steward already has the text body and only wants a citation.

**Not determined**: Exact edge cases for strings that start with `https://` and continue with trailing prose (whether fetch fails or still scrapes) were not executed in this session. Only the `urlparse` scheme branch was verified.

### Provenance / external_metadata

**VERIFIED** `DataItem` on remember (https://docs.cognee.ai/core-concepts/main-operations/remember):

```python
await cognee.remember(
    DataItem(
        data="Einstein was born in Ulm.",
        label="biography-note",
        external_metadata={"source": "wiki"},
        data_id=None,
    )
)
```

**VERIFIED** storage semantics (https://docs.cognee.ai/python-api/add and https://docs.cognee.ai/python-api/datasets):

- "`label` and `external_metadata` are stored on the relational `Data` record. They are not propagated into the knowledge graph automatically and are not searchable via `cognee.search()`."
- "`datasets.list_data` … This is the API to use when you want to read back `DataItem` fields stored during `cognee.add()`, such as `label` and `external_metadata`."
- Example print: `print(item.label, item.external_metadata)`.
- "`external_metadata` is stored on the relational `Data` record only. It is not placed into the vector store or knowledge graph and is not returned by `cognee.search()`."

**VERIFIED** recall citations (https://docs.cognee.ai/python-api/recall):

- `include_references=True` Evidence bullets: ``- chunk N of document NAME (data_id: …, chunk_id: …): "snippet"``.
- Chunk metadata documents `data_id` / `chunk_id` / `chunk_index` / `document_name` only.

**INFERRED** for Steward citations:

1. **Preferred structured store**: `remember(DataItem(data=<message or fact text>, label=..., external_metadata={"permalink": "<slack url>", "html_url": "<github url>", ...}), dataset_name=...)`.
2. **To surface a human URL in ask/digest without a join**: also put the permalink in the ingested text body (prefix or footer). Docs do not define a "prefix permalink" API; this is application composition so the model/context can see the URL, or Steward can join Evidence `data_id` → `datasets.list_data` → `external_metadata`.
3. **`node_set`**: use only if Steward needs graph-scoped tags; not a permalink field.

**Not determined**: Whether `remember()`'s returned `RememberResult` exposes the new `data_id` without calling `list_data`. Not verified in this session.

### Demo pin vs 1.5.0.dev

**VERIFIED** demo requirements (https://raw.githubusercontent.com/qdrant-labs/cognee-demo-slack/main/requirements.txt):

```
cognee[fastembed] @ git+https://github.com/topoteretes/cognee.git@dev
```

No semver pin. No `pyproject.toml` in that repo (404 on raw `pyproject.toml`).

**VERIFIED** `dev` branch package version (https://raw.githubusercontent.com/topoteretes/cognee/dev/pyproject.toml):

```
version = "1.5.0.dev1"
```

**VERIFIED** demo APIs already match current docs (`remember` / `recall`, dataset `"slack"`, `top_k=5`). README: https://raw.githubusercontent.com/qdrant-labs/cognee-demo-slack/main/README.md.

**VERIFIED** 1.5.0-related data-id change (https://docs.cognee.ai/core-concepts/main-operations/legacy-operations/add):

- "Records added before Cognee 1.5.0 had ids derived from `content_hash + user_id + tenant_id` and a single record could be shared by several datasets. The upgrade migration splits those shared records per dataset — see `run_migrations`. Ids issued before the split keep resolving, so data ids you stored externally remain valid."

**INFERRED** breaking differences that would change Steward v1 if it assumed older Cognee:

1. Primary API is `remember`/`recall` (v1.0+), not `add`/`cognify`/`search` alone. Demo already on the new API via `@dev`.
2. Data row identity is dataset-scoped as of 1.5.0 migration docs; external caches of `data_id` should follow current semantics.
3. Floating `@dev` means Steward's pin moves when `dev` moves; the demo does not freeze `1.5.0.dev1`.

**Not determined**: A full changelog delta "demo commit X vs 1.5.0.dev1" beyond the floating `@dev` pin and the documented 1.5.0 data-id migration. No separate published "1.5.0.dev" tag was required for this note; live `dev` pyproject is `1.5.0.dev1`.

### Slack-specific helpers

**VERIFIED** HackNight demo is generic text ingest wrapped in Slack slash commands (`/cognee-remember`, `/cognee-ask`). No Cognee Slack SDK helper in `app.py`.

**VERIFIED** optional bulk Slack connector via dlt (https://docs.cognee.ai/cognee-cloud/connections/external-data-sources):

```python
from dlt.sources.slack import slack_source
source = slack_source(selected_channels=["general", "engineering"], start_date=...)
await cognee.add(source, dataset_name="slack_data")
```

Requires `pip install "dlt[slack]"`, then legacy `add` (and typically `cognify`). Extracts "channels, messages, users, threads."

**INFERRED**: For Steward's per-message Remember / facts / seed notes path, use generic `remember` + text/`DataItem` like the demo. Use `dlt[slack]` only if Steward later wants bulk channel history ingest, not for slash-command or webhook text.

**Not determined**: Whether Cognee's own HTTP service Slack OAuth routers (hinted in `dev` pyproject cryptography comment) expose a remember helper suitable for Steward. Not fetched as a supported public "remember Slack message" API in docs searched this session.

## Blind spots

- No live install/run of Cognee in this session; signatures and behaviour come from docs + GitHub raw sources only.
- Did not execute `urlparse` / fetch on mixed "URL + trailing prose" strings.
- Did not confirm whether `include_references` Evidence ever embeds `external_metadata` fields (docs list only `data_id` / `chunk_id` / document name).
- Did not pin a specific git SHA for `@dev`; version `1.5.0.dev1` is tip-of-`dev` at fetch time.
- Did not compare Steward design docs against this note (ticket said findings only).

## One-line gist for the map

Steward v1 should permanent-`remember` plain text or `DataItem` (permalink in `external_metadata` and/or body) and `recall` by dataset/`top_k`, matching the HackNight `@dev` pin (`1.5.0.dev1` tip), and must not pass bare http(s) URLs as Slack/GitHub text ingest.
