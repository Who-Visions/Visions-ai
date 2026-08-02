"""Pick a Gemini model by what the task needs, and refuse dead ones.

Visions had its model ids spread across sixty files as bare constants. Twice
that went wrong in ways nothing caught:

- A version bump done by find-and-replace produced `gemini-3.1-pro`,
  `gemini-3.1-flash` and `gemini-3.1-pro-image-preview`. None exist. About
  ninety call sites pointed at models the API does not serve.
- `main` carried thirty-six references to models Google had already SHUT DOWN —
  `gemini-3-pro-preview`, `gemini-2.0-flash`, `gemini-2.0-flash-lite`. Not
  deprecated. Off.

Both are the same failure: a model id is a fact about the outside world stored
as a string literal, and string literals do not expire. This module makes the
registry the single place that knows, gives every entry a lifecycle, and
refuses to hand back anything retired.

## The ladder

Rungs are ordered by capability within a lane, cheapest first. `route()` picks
the lowest rung that satisfies the request; `escalate()` climbs one. Nothing
here calls an API — this decides WHICH model, and the caller does the work.
That keeps it testable without a key and honest about what it knows.

Prices are per the published pricing page and are used for ordering and for
reporting an estimate, never as a claim about a bill.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional


class Status(str, Enum):
    STABLE = "stable"
    PREVIEW = "preview"      # usable in production; tighter limits, 2-week deprecation notice
    RETIRED = "retired"      # endpoint is gone; routing here is a hard error


class Lane(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    LIVE = "live"


@dataclass(frozen=True)
class Model:
    id: str
    lane: Lane
    status: Status
    rung: int                  # position on the ladder; higher = more capable
    input_usd: float = 0.0     # per 1M tokens
    output_usd: float = 0.0
    per_image_usd: float = 0.0
    note: str = ""
    #: What this rung can do that the one below cannot.
    capabilities: frozenset = field(default_factory=frozenset)


#: Transcribed from ai.google.dev/gemini-api/docs/models and the pricing page,
#: 2026-08-02. Retired entries are kept ON PURPOSE — deleting them would turn a
#: precise "that model is off, use X" into a vague "unknown model", and the
#: whole point is to say which one and what replaced it.
REGISTRY: tuple[Model, ...] = (
    # --- text ladder, cheapest first ------------------------------------
    Model("gemini-3.1-flash-lite", Lane.TEXT, Status.STABLE, rung=10,
          input_usd=0.25, output_usd=1.50,
          note="high-volume, simple classification and extraction",
          capabilities=frozenset({"chat", "classify"})),
    Model("gemini-3.5-flash-lite", Lane.TEXT, Status.STABLE, rung=20,
          input_usd=0.30, output_usd=2.50,
          note="cheapest 3.5; high-throughput execution",
          capabilities=frozenset({"chat", "classify", "tools"})),
    Model("gemini-3.6-flash", Lane.TEXT, Status.STABLE, rung=30,
          input_usd=1.50, output_usd=7.50,
          note="latest flash; balances speed with intelligence",
          capabilities=frozenset({"chat", "classify", "tools", "multimodal", "grounding"})),
    Model("gemini-3.5-flash", Lane.TEXT, Status.STABLE, rung=40,
          input_usd=1.50, output_usd=9.00,
          note="most intelligent for SUSTAINED agentic and coding work — "
               "newer is not the same as better here",
          capabilities=frozenset({"chat", "classify", "tools", "multimodal",
                                  "grounding", "sustained"})),
    Model("gemini-3.1-pro-preview", Lane.TEXT, Status.PREVIEW, rung=50,
          input_usd=2.00, output_usd=12.00,
          note="top of the Pro tier. There is no 3.6 Pro; the 3.x line is flash-only",
          capabilities=frozenset({"chat", "classify", "tools", "multimodal",
                                  "grounding", "sustained", "deep_reasoning"})),
    Model("gemini-2.5-pro", Lane.TEXT, Status.STABLE, rung=45,
          input_usd=1.25, output_usd=10.00,
          note="the STABLE pro, one rung below 3.1 Pro Preview — use when a "
               "preview's deprecation window is unacceptable",
          capabilities=frozenset({"chat", "classify", "tools", "multimodal",
                                  "grounding", "sustained", "deep_reasoning"})),

    # --- image ladder ---------------------------------------------------
    Model("gemini-3.1-flash-lite-image", Lane.IMAGE, Status.STABLE, rung=10,
          per_image_usd=0.0336, note="Nano Banana 2 Lite; 1K",
          capabilities=frozenset({"generate", "edit"})),
    Model("gemini-3.1-flash-image", Lane.IMAGE, Status.STABLE, rung=20,
          per_image_usd=0.067, note="Nano Banana 2; 1K",
          capabilities=frozenset({"generate", "edit", "high_volume"})),
    Model("gemini-3-pro-image", Lane.IMAGE, Status.STABLE, rung=30,
          per_image_usd=0.134, note="Nano Banana Pro; studio 4K, text rendering",
          capabilities=frozenset({"generate", "edit", "high_volume", "4k", "text_render"})),

    # Older but live — the repo still calls these, so the registry must know
    # them or `audit` reports a false UNKNOWN on a model that works.
    Model("gemini-3-flash-preview", Lane.TEXT, Status.PREVIEW, rung=25,
          input_usd=0.50, output_usd=3.00,
          note="frontier-class at a fraction of the cost",
          capabilities=frozenset({"chat", "classify", "tools", "multimodal", "grounding"})),
    Model("gemini-2.5-flash", Lane.TEXT, Status.STABLE, rung=15,
          input_usd=0.30, output_usd=2.50, note="2.5 price-performance workhorse",
          capabilities=frozenset({"chat", "classify", "tools", "multimodal"})),
    Model("gemini-2.5-computer-use-preview-10-2025", Lane.TEXT, Status.PREVIEW, rung=35,
          input_usd=1.25, output_usd=10.00, note="drives a browser UI",
          capabilities=frozenset({"chat", "tools", "multimodal", "computer_use"})),

    # --- image, 2.5 ------------------------------------------------------
    Model("gemini-2.5-flash-image", Lane.IMAGE, Status.STABLE, rung=5,
          per_image_usd=0.039, note="Nano Banana (2.5); superseded by 3.1-flash-image",
          capabilities=frozenset({"generate", "edit"})),

    # --- live -----------------------------------------------------------
    Model("gemini-3.1-flash-live-preview", Lane.LIVE, Status.PREVIEW, rung=10,
          input_usd=0.75, output_usd=4.50, note="audio-to-audio realtime dialogue",
          capabilities=frozenset({"audio"})),

    # --- retired: kept so the error can name the replacement ------------
    Model("gemini-3-pro-preview", Lane.TEXT, Status.RETIRED, rung=0,
          note="shut down -> gemini-3.1-pro-preview"),
    Model("gemini-2.0-flash", Lane.TEXT, Status.RETIRED, rung=0,
          note="shut down -> gemini-3.6-flash"),
    Model("gemini-2.0-flash-lite", Lane.TEXT, Status.RETIRED, rung=0,
          note="shut down -> gemini-3.1-flash-lite"),
    Model("gemini-3.1-flash-lite-preview", Lane.TEXT, Status.RETIRED, rung=0,
          note="shut down -> gemini-3.1-flash-lite"),
)

_BY_ID = {m.id: m for m in REGISTRY}


class RetiredModel(LookupError):
    """Raised when something asks for a model whose endpoint is gone."""


class NoRouteAvailable(LookupError):
    """No live model in the lane satisfies the requested capabilities."""


def get(model_id: str) -> Model:
    """Look a model up, refusing retired ids with the replacement named.

    A retired id is not an unknown id. Saying "that is off, use this instead"
    is the difference between a five-second fix and an afternoon.
    """
    model = _BY_ID.get(model_id)
    if model is None:
        raise LookupError(
            f"{model_id!r} is not in the registry. If Google has published it, "
            "add it here rather than inlining the string at the call site — "
            "that is how ~90 references to models that never existed got in."
        )
    if model.status is Status.RETIRED:
        raise RetiredModel(f"{model_id!r} is {model.note}")
    return model


def ladder(lane: Lane = Lane.TEXT, *, allow_preview: bool = True) -> list[Model]:
    """Live models in a lane, cheapest-capable first."""
    rungs = [m for m in REGISTRY
             if m.lane is lane and m.status is not Status.RETIRED
             and (allow_preview or m.status is not Status.PREVIEW)]
    return sorted(rungs, key=lambda m: (m.rung, m.input_usd + m.per_image_usd))


def route(
    *,
    lane: Lane = Lane.TEXT,
    needs: Iterable[str] = (),
    allow_preview: bool = True,
    floor: Optional[str] = None,
) -> Model:
    """The cheapest live model that can do the job.

    `needs` are capability names, not model names — that is the whole point.
    A call site says what it requires ("deep_reasoning", "4k") and the ladder
    decides, so a model retirement is one registry edit rather than a grep.

    `floor` pins a minimum rung when a caller knows a cheap model will not do,
    without hardcoding which model that is.
    """
    wanted = frozenset(needs)
    rungs = ladder(lane, allow_preview=allow_preview)
    if floor:
        rungs = [m for m in rungs if m.rung >= get(floor).rung]
    for model in rungs:
        if wanted <= model.capabilities:
            return model
    raise NoRouteAvailable(
        f"no live {lane.value} model provides {sorted(wanted)}"
        + ("" if allow_preview else " (previews excluded — try allow_preview=True)")
    )


def escalate(model: Model, *, allow_preview: bool = True) -> Optional[Model]:
    """The next rung up, or None at the top.

    For retry-on-weak-answer: route cheap, escalate on failure. Climbing beats
    starting at the top, because most requests do not need the top and the ones
    that do announce themselves by failing.
    """
    for candidate in ladder(model.lane, allow_preview=allow_preview):
        if candidate.rung > model.rung:
            return candidate
    return None


def estimate_usd(model: Model, *, input_tokens: int = 0, output_tokens: int = 0,
                 images: int = 0) -> float:
    """Rough cost of a call. An estimate for ordering, not a bill."""
    return (input_tokens * model.input_usd / 1e6
            + output_tokens * model.output_usd / 1e6
            + images * model.per_image_usd)


def audit(model_ids: Iterable[str]) -> dict[str, str]:
    """Report on ids found in a codebase: retired, unknown, or fine.

    Built to be pointed at a repo, because the way this went wrong was ninety
    string literals nobody could see at once.
    """
    report: dict[str, str] = {}
    for mid in sorted(set(model_ids)):
        model = _BY_ID.get(mid)
        if model is None:
            report[mid] = "UNKNOWN — not a published model id"
        elif model.status is Status.RETIRED:
            report[mid] = f"RETIRED — {model.note}"
        else:
            report[mid] = f"ok ({model.status.value})"
    return report
