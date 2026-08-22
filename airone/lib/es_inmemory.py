"""An in-process stand-in for Elasticsearch, used by Pagoda's lite dev mode.

Why this can be faithful rather than a rough mock: every analysed field in
Pagoda's index mapping (``name``, ``attr.name``, ``attr.value``,
``entity.name``, ``referrals.name``) is declared with the ``keyword``
analyzer. A keyword analyzer emits the field value as a single token, so
``match`` and ``term`` both degrade to whole-value equality and there is no
tokenizer, stemmer or scorer to reproduce. What is left is a small, closed set
of query clauses -- all of them constructed inside
``airone.lib.elasticsearch`` -- which this module evaluates directly against
Python dicts.

Supported clauses: ``match_all``, ``ids``, ``term``, ``match``, ``regexp``,
``range``, ``exists``, ``bool`` (must / filter / should / must_not /
minimum_should_match) and ``nested`` (including ``inner_hits``). Supported
response features: ``_source`` filtering, ``from`` / ``size``,
``track_total_hits``, sorting (plain, ``_score`` and nested-filtered) and the
nested → filter → terms aggregation used by the "duplicated values" filter.

Known divergences from a real cluster, all of them benign for local work:

* ``_score`` counts matching ``must``/``should`` clauses instead of computing
  BM25. That reproduces the orderings Pagoda actually depends on (name matches
  outrank attribute matches) but not a real relevance ranking.
* Field paths are resolved structurally, which makes a query on a field of a
  doubly-nested object (``referrals.schema.id``) match from its parent's
  nested scope. A real cluster requires an explicit inner ``nested`` clause
  there, so this engine is the more permissive of the two.
* Index settings and mappings are accepted and ignored; there is no analysis
  chain to configure.

Run the suite against a real cluster before shipping anything that depends on
subtle search semantics -- see docs/content/lite-mode.md for how.
"""

import json
import os
import re
import threading
from datetime import date, datetime
from typing import Any

from elasticsearch import NotFoundError

# Sentinel used to sort documents that have no value for a sort key. Mirrors
# Elasticsearch's default ``"missing": "_last"`` for both sort directions.
_MISSING = object()


class _Store:
    """Process-wide document storage, keyed by index name then document id.

    Optionally mirrored to disk. A dev server that lost its index on every
    autoreload would leave existing items unsearchable until a manual
    re-index, which reads as a bug rather than a restart; persisting the index
    next to the SQLite file keeps the two in step. Tests disable persistence
    (see ``AironeTestCase``) so they stay isolated and fast.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._indices: dict[str, dict[str, dict[str, Any]]] = {}
        self._loaded: set[str] = set()

    @staticmethod
    def _persist_root() -> str | None:
        from django.conf import settings

        path = settings.ES_CONFIG.get("PERSIST_PATH")
        return str(path) if path else None

    def _persist_file(self, index: str) -> str | None:
        root = self._persist_root()
        if not root:
            return None
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", index)
        return os.path.join(root, "%s.json" % safe)

    def _load(self, index: str) -> None:
        if index in self._loaded:
            return
        self._loaded.add(index)

        path = self._persist_file(index)
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, encoding="utf-8") as handle:
                self._indices[index] = json.load(handle)
        except (OSError, ValueError):
            # A corrupt dev index is not worth failing a request over; the
            # next re-index rebuilds it.
            self._indices[index] = {}

    def flush(self, index: str) -> None:
        path = self._persist_file(index)
        if not path:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(self._indices.get(index, {}), handle)
        os.replace(tmp, path)

    def docs(self, index: str) -> dict[str, dict[str, Any]]:
        with self._lock:
            self._load(index)
            return self._indices.setdefault(index, {})

    def create(self, index: str) -> None:
        with self._lock:
            self._loaded.add(index)
            self._indices[index] = {}
            self.flush(index)

    def drop(self, index: str) -> None:
        with self._lock:
            self._loaded.add(index)
            self._indices.pop(index, None)
            path = self._persist_file(index)
            if path and os.path.exists(path):
                os.unlink(path)

    def reset(self) -> None:
        with self._lock:
            self._indices.clear()
            self._loaded.clear()


STORE = _Store()


# ---------------------------------------------------------------------------
# value helpers
# ---------------------------------------------------------------------------


def _flatten(values: list[Any]) -> list[Any]:
    out: list[Any] = []
    for value in values:
        if isinstance(value, list):
            out.extend(value)
        else:
            out.append(value)
    return out


def _traverse(base: Any, parts: list[str]) -> list[Any]:
    current: list[Any] = [base]
    for part in parts:
        nxt: list[Any] = []
        for item in current:
            if isinstance(item, dict) and part in item:
                nxt.append(item[part])
        current = _flatten(nxt)
    return current


def _strip_keyword(field: str) -> str:
    """Drop the ``.keyword`` sub-field suffix; multi-fields hold the same value."""
    return field[: -len(".keyword")] if field.endswith(".keyword") else field


class Scope:
    """The document (and optional nested sub-document) a clause is evaluated in."""

    __slots__ = ("root", "current", "path", "doc_id")

    def __init__(self, root: dict[str, Any], doc_id: str) -> None:
        self.root = root
        self.current: Any = root
        self.path = ""
        self.doc_id = doc_id

    def nested(self, path: str, sub_doc: Any) -> "Scope":
        child = Scope(self.root, self.doc_id)
        child.current = sub_doc
        child.path = path
        return child

    def values(self, field: str) -> list[Any]:
        """Every value a field path resolves to within this scope."""
        field = _strip_keyword(field)
        if self.path and field.startswith(self.path + "."):
            return _traverse(self.current, field[len(self.path) + 1 :].split("."))
        # A field may also be addressed by its full path from inside a nested
        # scope; fall back to the root document.
        return _traverse(self.root, field.split("."))


def _sub_documents(scope: Scope, path: str) -> list[Any]:
    """Nested sub-documents at ``path``, treating a lone object as a 1-element list."""
    if scope.path and path.startswith(scope.path + "."):
        base, parts = scope.current, path[len(scope.path) + 1 :].split(".")
    else:
        base, parts = scope.root, path.split(".")

    found = _traverse(base, parts)
    return [item for item in found if isinstance(item, dict)]


# ---------------------------------------------------------------------------
# scalar comparison
# ---------------------------------------------------------------------------


def _as_text(value: Any) -> str | None:
    """How Elasticsearch would index a JSON value into a ``text`` field.

    ``attr.value`` is mapped as text but holds booleans and numbers as well as
    strings, and ES stringifies them on the way in. Reproducing that is what
    makes ``{"regexp": {"attr.value": ".+"}}`` -- the "has any value" filter --
    match a boolean attribute the way it does on a real cluster.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    return str(value)


def _equals(stored: Any, wanted: Any) -> bool:
    if stored is None:
        return False
    left, right = _as_text(stored), _as_text(wanted)
    if right is None:
        return False
    if isinstance(stored, bool) or isinstance(wanted, bool):
        # A query for a boolean field arrives as "True"/"true"/True.
        return left == right.lower()
    # ES coerces query values to the mapped field type; comparing the string
    # forms covers the int-vs-str mismatches that survive that coercion.
    return left == right


def _lucene_regexp_to_python(pattern: str) -> str:
    """Translate a Lucene regexp into the equivalent Python one.

    The two dialects agree on almost everything Pagoda emits, with one
    consequential exception: Lucene has no anchor operators, so ``^`` and ``$``
    are ordinary literals there and special characters here. Entry names
    routinely contain both, and leaving them untranslated silently turns a
    matching query into a non-matching one.

    Character classes are tracked because ``^`` *is* a negation operator
    immediately inside ``[...]`` in both dialects.
    """
    out: list[str] = []
    in_class = False
    index = 0
    while index < len(pattern):
        char = pattern[index]

        if char == "\\" and index + 1 < len(pattern):
            # A Lucene backslash escapes the next character literally.
            out.append(re.escape(pattern[index + 1]))
            index += 2
            continue

        if in_class:
            if char == "]":
                in_class = False
            out.append(char)
        elif char == "[":
            in_class = True
            out.append(char)
        elif char in "^$":
            out.append("\\" + char)
        else:
            out.append(char)
        index += 1

    return "".join(out)


def _compile_regexp(pattern: str) -> "re.Pattern[str]":
    # Lucene's regexp is implicitly anchored (callers use fullmatch) and its
    # "." matches any character including a newline.
    return re.compile(_lucene_regexp_to_python(pattern), re.DOTALL)


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed: datetime | None = value
    elif isinstance(value, date):
        parsed = datetime(value.year, value.month, value.day)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
                try:
                    parsed = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue
            else:
                return None
    else:
        return None

    if parsed is not None and parsed.tzinfo is not None:
        parsed = parsed.astimezone(tz=None).replace(tzinfo=None)
    return parsed


# ---------------------------------------------------------------------------
# query evaluation
# ---------------------------------------------------------------------------


class _InnerHitCollector:
    """Per-document state gathered while a query is evaluated.

    Carries the ``inner_hits`` sub-documents and an approximate relevance
    score. The score counts how many ``should`` clauses the document matched,
    which is enough to reproduce the one ordering decision Pagoda delegates to
    relevance: simple search sorts by ``_score`` desc, and an entry whose
    *name* equals the search string matches strictly more clauses than one
    that only matched a substring regexp.
    """

    def __init__(self) -> None:
        self.declared: dict[str, dict[str, Any]] = {}
        self.hits: dict[str, list[dict[str, Any]]] = {}
        self.score = 0.0

    def declare(self, name: str, spec: dict[str, Any]) -> None:
        self.declared.setdefault(name, spec)
        self.hits.setdefault(name, [])

    def add(self, name: str, sub_doc: dict[str, Any]) -> None:
        self.hits.setdefault(name, []).append(sub_doc)

    def reset_hits(self) -> None:
        self.hits = {name: [] for name in self.declared}

    def render(self) -> dict[str, Any]:
        rendered: dict[str, Any] = {}
        for name, spec in self.declared.items():
            source_filter = spec.get("_source")
            hits = [
                {"_source": _filter_source(sub_doc, source_filter, nested_path=name)}
                for sub_doc in self.hits.get(name, [])
            ]
            rendered[name] = {"hits": {"total": {"value": len(hits)}, "hits": hits}}
        return rendered


def _as_clause_list(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]


#: Score every matching leaf clause contributes, mirroring the constant score
#: ES gives term-level queries.
_LEAF_SCORE = 1.0


def _match_clause(clause: dict[str, Any], scope: Scope, inner: _InnerHitCollector) -> bool:
    return _score_clause(clause, scope, inner) is not None


def _score_clause(clause: dict[str, Any], scope: Scope, inner: _InnerHitCollector) -> float | None:
    """Score a clause against a document, or return ``None`` if it does not match.

    Scoring matters because simple search orders by ``_score``. The rule that
    actually decides Pagoda's ordering is ES's: ``must`` and ``should`` add to
    the score, while ``filter`` and ``must_not`` only include/exclude. That is
    why an entry matched by *name* outranks one matched only through the
    attribute-value clause, which Pagoda wraps in a ``filter``.
    """
    if len(clause) != 1:
        # ES rejects multi-key query objects; be strict so bugs surface early.
        raise ValueError("query clause must have exactly one key: %r" % sorted(clause))

    ((kind, body),) = clause.items()

    match kind:
        case "match_all":
            return _LEAF_SCORE
        case "match_none":
            return None
        case "ids":
            wanted_ids = [str(x) for x in body.get("values", [])]
            return _LEAF_SCORE if scope.doc_id in wanted_ids else None
        case "term" | "match" | "match_phrase":
            ((field, wanted),) = body.items()
            if isinstance(wanted, dict):
                wanted = wanted.get("value", wanted.get("query"))
            hit = any(_equals(v, wanted) for v in scope.values(field))
            return _LEAF_SCORE if hit else None
        case "terms":
            ((field, wanted_list),) = body.items()
            values = scope.values(field)
            hit = any(_equals(v, w) for v in values for w in wanted_list)
            return _LEAF_SCORE if hit else None
        case "regexp":
            ((field, pattern),) = body.items()
            if isinstance(pattern, dict):
                pattern = pattern["value"]
            compiled = _compile_regexp(pattern)
            hit = any(
                text is not None and compiled.fullmatch(text) is not None
                for text in (_as_text(v) for v in scope.values(field))
            )
            return _LEAF_SCORE if hit else None
        case "exists":
            hit = any(v is not None for v in scope.values(body["field"]))
            return _LEAF_SCORE if hit else None
        case "range":
            ((field, spec),) = body.items()
            return _LEAF_SCORE if _match_range(scope.values(field), spec) else None
        case "bool":
            return _score_bool(body, scope, inner)
        case "nested":
            return _score_nested(body, scope, inner)
        case _:
            raise ValueError("unsupported query clause for lite mode: %r" % kind)


def _match_range(values: list[Any], spec: dict[str, Any]) -> bool:
    bounds = {k: v for k, v in spec.items() if k in ("gt", "gte", "lt", "lte")}
    if not bounds:
        # A bare {"format": ...} range is an existence check in practice.
        return any(v is not None for v in values)

    for value in values:
        moment = _as_datetime(value)
        if moment is None:
            continue
        ok = True
        for op, raw in bounds.items():
            limit = _as_datetime(raw)
            if limit is None:
                continue
            if op == "gt" and not moment > limit:
                ok = False
            elif op == "gte" and not moment >= limit:
                ok = False
            elif op == "lt" and not moment < limit:
                ok = False
            elif op == "lte" and not moment <= limit:
                ok = False
        if ok:
            return True
    return False


def _score_bool(body: dict[str, Any], scope: Scope, inner: _InnerHitCollector) -> float | None:
    must = _as_clause_list(body.get("must"))
    filters = _as_clause_list(body.get("filter"))
    must_not = _as_clause_list(body.get("must_not"))
    should = _as_clause_list(body.get("should"))

    score = 0.0

    for clause in must:
        sub_score = _score_clause(clause, scope, inner)
        if sub_score is None:
            return None
        score += sub_score

    # "filter" must match but contributes nothing to the score.
    for clause in filters:
        if _score_clause(clause, scope, inner) is None:
            return None

    for clause in must_not:
        if _score_clause(clause, scope, inner) is not None:
            return None

    if should:
        # Matches ES: "should" only becomes mandatory when nothing else is.
        default_minimum = 0 if (must or filters) else 1
        minimum = int(body.get("minimum_should_match", default_minimum))
        matched = 0
        for clause in should:
            sub_score = _score_clause(clause, scope, inner)
            if sub_score is not None:
                matched += 1
                score += sub_score
        if matched < minimum:
            return None

    return score


def _score_nested(body: dict[str, Any], scope: Scope, inner: _InnerHitCollector) -> float | None:
    path = body["path"]
    inner_hits_spec = body.get("inner_hits")
    name = (inner_hits_spec or {}).get("name", path) if inner_hits_spec is not None else None
    if name is not None:
        inner.declare(name, inner_hits_spec or {})

    query = body.get("query")
    scores: list[float] = []
    for sub_doc in _sub_documents(scope, path):
        child = scope.nested(path, sub_doc)
        sub_score = _LEAF_SCORE if query is None else _score_clause(query, child, inner)
        if sub_score is None:
            continue
        scores.append(sub_score)
        if name is not None:
            inner.add(name, sub_doc)
        else:
            # No inner_hits requested: the first match settles it.
            break

    if not scores:
        return None
    # ES defaults a nested query to score_mode="avg" over the matching children.
    return sum(scores) / len(scores)


# ---------------------------------------------------------------------------
# sorting
# ---------------------------------------------------------------------------


class _SortKey:
    """Orderable wrapper: honours the sort direction and keeps missing values last.

    Inverting the comparison here (rather than reversing the list) is what lets
    a multi-key sort mix ascending and descending clauses in a single pass, and
    keeps missing values at the end for both directions the way ES does.
    """

    __slots__ = ("rank", "descending")

    def __init__(self, value: Any, descending: bool) -> None:
        self.descending = descending
        self.rank: tuple[int, float, str] | None = None if value is _MISSING else _comparable(value)

    def __lt__(self, other: "_SortKey") -> bool:
        if self.rank is None or other.rank is None:
            # Missing last: a present value precedes a missing one, never the
            # other way round, whichever direction was asked for.
            return self.rank is not None
        if self.rank == other.rank:
            return False
        return self.rank > other.rank if self.descending else self.rank < other.rank

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _SortKey) and self.rank == other.rank

    def __hash__(self) -> int:
        return hash(self.rank)


def _normalise_sort(sort: Any) -> list[tuple[str, dict[str, Any]]]:
    """Flatten ES's several sort spellings into ``[(field, spec), ...]``.

    A clause may be a bare field name, ``{field: "asc"}``, ``{field: {...}}``,
    or -- as simple search does -- a single object carrying two fields at once.
    """
    if sort is None:
        elements: list[Any] = []
    elif isinstance(sort, list):
        elements = list(sort)
    else:
        elements = [sort]

    clauses: list[tuple[str, dict[str, Any]]] = []
    for element in elements:
        if isinstance(element, str):
            clauses.append((element, {"order": "asc"}))
            continue
        for field, spec in element.items():
            if isinstance(spec, str):
                spec = {"order": spec}
            clauses.append((field, spec))
    return clauses


def _sort_value(
    doc: dict[str, Any], doc_id: str, score: float, field: str, spec: dict[str, Any]
) -> Any:
    if field == "_score":
        return score

    scope = Scope(doc, doc_id)
    nested_spec = spec.get("nested")
    if nested_spec:
        path = nested_spec["path"]
        filter_clause = nested_spec.get("filter")
        collected: list[Any] = []
        for sub_doc in _sub_documents(scope, path):
            child = scope.nested(path, sub_doc)
            if filter_clause and not _match_clause(filter_clause, child, _InnerHitCollector()):
                continue
            collected.extend(v for v in child.values(field) if v is not None)
    else:
        collected = [v for v in scope.values(field) if v is not None]

    if not collected:
        return _MISSING

    if field.endswith("date_value"):
        collected = [_as_datetime(v) or v for v in collected]

    # ES resolves a multi-valued sort field with mode=min for asc, max for desc.
    pick = min if spec.get("order", "asc") == "asc" else max
    return pick(collected, key=_comparable)


def _comparable(value: Any) -> tuple[int, float, str]:
    if isinstance(value, datetime):
        return (0, value.timestamp(), "")
    if isinstance(value, bool):
        return (1, float(value), "")
    if isinstance(value, int | float):
        return (1, float(value), "")
    return (2, 0.0, str(value))


# ---------------------------------------------------------------------------
# _source filtering
# ---------------------------------------------------------------------------


def _filter_source(
    source: dict[str, Any], source_filter: Any, nested_path: str | None = None
) -> dict[str, Any]:
    if source_filter in (None, True):
        return source
    if source_filter is False:
        return {}

    fields = source_filter if isinstance(source_filter, list) else [source_filter]
    kept: dict[str, Any] = {}
    for field in fields:
        # Inside inner_hits the requested paths are absolute ("attr.name") but
        # the returned source is the nested object itself.
        relative = field
        if nested_path and field.startswith(nested_path + "."):
            relative = field[len(nested_path) + 1 :]
        head = relative.split(".")[0]
        if head in source:
            kept[head] = source[head]
    return kept


# ---------------------------------------------------------------------------
# aggregations
# ---------------------------------------------------------------------------


def _run_aggregations(aggs: dict[str, Any], scopes: list[Scope]) -> dict[str, Any]:
    return {name: _run_aggregation(spec, scopes) for name, spec in aggs.items()}


def _run_aggregation(spec: dict[str, Any], scopes: list[Scope]) -> dict[str, Any]:
    sub_aggs = spec.get("aggs") or spec.get("aggregations")

    if "nested" in spec:
        path = spec["nested"]["path"]
        child_scopes = [
            scope.nested(path, sub_doc)
            for scope in scopes
            for sub_doc in _sub_documents(scope, path)
        ]
        bucket: dict[str, Any] = {"doc_count": len(child_scopes)}
        if sub_aggs:
            bucket.update(_run_aggregations(sub_aggs, child_scopes))
        return bucket

    if "filter" in spec:
        collector = _InnerHitCollector()
        kept = [s for s in scopes if _match_clause(spec["filter"], s, collector)]
        bucket = {"doc_count": len(kept)}
        if sub_aggs:
            bucket.update(_run_aggregations(sub_aggs, kept))
        return bucket

    if "terms" in spec:
        terms = spec["terms"]
        field = terms["field"]
        counts: dict[str, int] = {}
        for scope in scopes:
            for value in scope.values(field):
                # Buckets of a text/keyword field come back as strings from ES.
                text = _as_text(value)
                if text is None:
                    continue
                counts[text] = counts.get(text, 0) + 1

        min_doc_count = int(terms.get("min_doc_count", 1))
        size = int(terms.get("size", 10))
        buckets = [
            {"key": key, "doc_count": count}
            for key, count in sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))
            if count >= min_doc_count
        ][:size]
        return {"buckets": buckets}

    raise ValueError("unsupported aggregation for lite mode: %r" % sorted(spec))


# ---------------------------------------------------------------------------
# client
# ---------------------------------------------------------------------------


class _Indices:
    """The ``client.indices`` namespace, reduced to what Pagoda calls."""

    def __init__(self, client: "InMemoryElasticsearch") -> None:
        self._client = client

    def create(self, index: str, **_: Any) -> dict[str, Any]:
        STORE.create(index)
        return {"acknowledged": True, "index": index}

    def delete(self, index: str, ignore_unavailable: bool = False, **_: Any) -> dict[str, Any]:
        STORE.drop(index)
        return {"acknowledged": True}

    def exists(self, index: str, **_: Any) -> bool:
        return index in STORE._indices

    def refresh(self, index: str | None = None, **_: Any) -> dict[str, Any]:
        return {"_shards": {"total": 1, "successful": 1, "failed": 0}}

    def put_settings(self, **_: Any) -> dict[str, Any]:
        return {"acknowledged": True}


class InMemoryElasticsearch:
    """Drop-in replacement for the subset of ``Elasticsearch`` that Pagoda uses."""

    def __init__(self, index: str) -> None:
        self._index = index
        self.indices = _Indices(self)

    # -- write path --------------------------------------------------------

    def index(self, *, id: Any, body: dict[str, Any], index: str | None = None, **_: Any) -> Any:
        index_name = index or self._index
        STORE.docs(index_name)[str(id)] = body
        STORE.flush(index_name)
        return {"result": "created", "_id": str(id)}

    def delete(self, *, id: Any, index: str | None = None, **_: Any) -> Any:
        index_name = index or self._index
        docs = STORE.docs(index_name)
        if str(id) not in docs:
            raise NotFoundError("document not found: %s" % id, meta=None, body=None)  # type: ignore[arg-type]
        del docs[str(id)]
        STORE.flush(index_name)
        return {"result": "deleted"}

    def bulk(self, *, body: list[dict[str, Any]], index: str | None = None, **_: Any) -> Any:
        index_name = index or self._index
        docs = STORE.docs(index_name)
        pending_id: str | None = None
        for element in body:
            if pending_id is None:
                action, meta = next(iter(element.items()))
                if action == "delete":
                    docs.pop(str(meta["_id"]), None)
                    continue
                pending_id = str(meta["_id"])
            else:
                docs[pending_id] = element
                pending_id = None
        STORE.flush(index_name)
        return {"errors": False, "items": []}

    def delete_by_query(self, *, query: dict[str, Any], index: str | None = None, **_: Any) -> Any:
        index_name = index or self._index
        docs = STORE.docs(index_name)
        collector = _InnerHitCollector()
        doomed = [
            doc_id
            for doc_id, source in list(docs.items())
            if _score_clause(query, Scope(source, doc_id), collector) is not None
        ]
        for doc_id in doomed:
            del docs[doc_id]
        STORE.flush(index_name)
        return {"deleted": len(doomed), "failures": [], "timed_out": False}

    def refresh(self, **_: Any) -> Any:
        return self.indices.refresh(index=self._index)

    # -- read path ---------------------------------------------------------

    def count(self, *, index: str | None = None, **_: Any) -> Any:
        return {"count": len(STORE.docs(index or self._index))}

    def get(self, *, id: Any, index: str | None = None, **_: Any) -> Any:
        index_name = index or self._index
        docs = STORE.docs(index_name)
        if str(id) not in docs:
            raise NotFoundError("document not found: %s" % id, meta=None, body=None)  # type: ignore[arg-type]
        return {"_index": index_name, "_id": str(id), "found": True, "_source": docs[str(id)]}

    def search(
        self,
        *,
        body: dict[str, Any] | None = None,
        index: str | None = None,
        size: int | None = None,
        from_: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        body = dict(body or {})
        index_name = index or self._index
        docs = STORE.docs(index_name)

        query = body.get("query", {"match_all": {}})
        source_filter = body.get("_source")
        sort_clauses = _normalise_sort(body.get("sort"))
        offset = from_ if from_ is not None else int(body.get("from", 0) or 0)
        limit = size if size is not None else body.get("size")

        matched: list[tuple[str, dict[str, Any], _InnerHitCollector]] = []
        scopes: list[Scope] = []
        for doc_id, source in docs.items():
            collector = _InnerHitCollector()
            scope = Scope(source, doc_id)
            score = _score_clause(query, scope, collector)
            if score is not None:
                collector.score = score
                matched.append((doc_id, source, collector))
                scopes.append(scope)

        if sort_clauses:

            def sort_key(
                item: tuple[str, dict[str, Any], _InnerHitCollector],
            ) -> tuple[_SortKey, ...]:
                return tuple(
                    _SortKey(
                        _sort_value(item[1], item[0], item[2].score, field, spec),
                        spec.get("order", "asc") == "desc",
                    )
                    for field, spec in sort_clauses
                )

            matched.sort(key=sort_key)

        total = len(matched)
        window = matched[offset:] if limit is None else matched[offset : offset + int(limit)]

        hits = [
            {
                "_index": index_name,
                "_id": doc_id,
                "_score": collector.score or 1.0,
                "_source": _filter_source(source, source_filter),
                **({"inner_hits": collector.render()} if collector.declared else {}),
            }
            for doc_id, source, collector in window
        ]

        response: dict[str, Any] = {
            "took": 0,
            "timed_out": False,
            "hits": {"total": {"value": total, "relation": "eq"}, "hits": hits},
        }

        aggs = body.get("aggs") or body.get("aggregations")
        if aggs:
            response["aggregations"] = _run_aggregations(aggs, scopes)

        return response
