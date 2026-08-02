"""The model ladder, and the two failures it exists to stop.

Both happened in this repo: a find-and-replace version bump that produced ids
which do not exist, and thirty-six references to models Google had shut down.
"""
import pytest

from visions.core.router import (
    Lane, Model, NoRouteAvailable, REGISTRY, RetiredModel, Status,
    audit, escalate, estimate_usd, get, ladder, route,
)


# --- the failures this exists to stop -------------------------------------

@pytest.mark.parametrize("dead", [
    "gemini-3-pro-preview", "gemini-2.0-flash",
    "gemini-2.0-flash-lite", "gemini-3.1-flash-lite-preview",
])
def test_a_shut_down_model_cannot_be_routed_to(dead):
    with pytest.raises(RetiredModel):
        get(dead)


def test_a_retired_model_names_its_replacement():
    """A retired id is not an unknown id. Naming the successor is the
    difference between a five-second fix and an afternoon."""
    with pytest.raises(RetiredModel, match="gemini-3.1-pro-preview"):
        get("gemini-3-pro-preview")


@pytest.mark.parametrize("invented", [
    "gemini-3.1-pro",               # no bare 3.1 pro exists
    "gemini-3.1-flash",             # no bare 3.1 flash exists
    "gemini-3.1-pro-image-preview", # the pro image model is gemini-3-pro-image
    "gemini-3.6-pro",               # the 3.x line is flash-only
])
def test_ids_a_version_bump_invents_are_rejected(invented):
    with pytest.raises(LookupError):
        get(invented)


def test_there_is_no_3_6_pro():
    """Flash reached 3.6; Pro never did. Checked because it was argued."""
    assert not [m for m in REGISTRY if m.id.startswith("gemini-3.6") and "pro" in m.id]
    assert get("gemini-3.6-flash").status is Status.STABLE


# --- the ladder -----------------------------------------------------------

def test_the_ladder_is_ordered_cheapest_capable_first():
    rungs = ladder(Lane.TEXT)
    assert [m.rung for m in rungs] == sorted(m.rung for m in rungs)
    assert rungs[0].id == "gemini-3.1-flash-lite"


def test_no_retired_model_ever_appears_on_a_ladder():
    for lane in Lane:
        assert all(m.status is not Status.RETIRED for m in ladder(lane))


def test_routing_asks_for_capabilities_not_model_names():
    """The point: a call site says what it needs, so a retirement is one
    registry edit rather than a grep across sixty files."""
    assert route(needs=["classify"]).id == "gemini-3.1-flash-lite"
    # Cheapest that qualifies, not most capable: 2.5 Pro is stable, has
    # deep_reasoning, and costs less than 3.1 Pro Preview.
    assert route(needs=["deep_reasoning"]).id == "gemini-2.5-pro"
    assert route(lane=Lane.IMAGE, needs=["4k"]).id == "gemini-3-pro-image"


def test_cheapest_that_qualifies_wins_not_the_best():
    """A classifier must not be routed to the Pro tier."""
    picked = route(needs=["classify"])
    assert picked.output_usd < get("gemini-3.1-pro-preview").output_usd


def test_the_top_of_the_pro_tier_is_reachable_by_floor():
    """Getting 3.1 Pro means asking for it by rung, not by name."""
    assert route(needs=["deep_reasoning"], floor="gemini-3.1-pro-preview").id \
        == "gemini-3.1-pro-preview"


def test_excluding_previews_removes_the_preview_rung():
    rungs = ladder(Lane.TEXT, allow_preview=False)
    assert all(m.status is not Status.PREVIEW for m in rungs)
    assert "gemini-3.1-pro-preview" not in [m.id for m in rungs]


def test_an_impossible_request_says_so_rather_than_guessing():
    with pytest.raises(NoRouteAvailable):
        route(needs=["telepathy"])


def test_floor_pins_a_minimum_without_naming_the_model():
    picked = route(needs=["chat"], floor="gemini-3.6-flash")
    assert picked.rung >= get("gemini-3.6-flash").rung


# --- escalation -----------------------------------------------------------

def test_escalate_climbs_one_rung():
    cheap = route(needs=["classify"])
    better = escalate(cheap)
    assert better is not None and better.rung > cheap.rung


def test_escalation_terminates_at_the_top():
    top = ladder(Lane.TEXT)[-1]
    assert escalate(top) is None


def test_escalating_repeatedly_reaches_the_top_without_looping():
    m, seen = ladder(Lane.TEXT)[0], set()
    while m is not None:
        assert m.id not in seen, "escalation revisited a rung"
        seen.add(m.id)
        m = escalate(m)
    assert len(seen) == len(ladder(Lane.TEXT))


# --- cost -----------------------------------------------------------------

def test_estimate_uses_per_image_pricing_for_the_image_lane():
    nano2 = get("gemini-3.1-flash-image")
    assert estimate_usd(nano2, images=10) == pytest.approx(0.67)


def test_nano_banana_2_is_not_priced_at_the_2_5_rate():
    """The bug that rode in with the version bump: the id moved from
    gemini-2.5-flash-image and kept 2.5's $0.039, a 42% undercount."""
    assert get("gemini-3.1-flash-image").per_image_usd == pytest.approx(0.067)


def test_the_ladder_is_capability_ordered_and_cost_is_not_monotonic():
    """A real quirk, worth pinning so nobody "fixes" the ordering later.

    gemini-2.5-pro is a Pro-tier model whose INPUT is $1.25 — cheaper than both
    flashes below it on the ladder ($1.50) — while its output is dearer. So the
    rungs are ordered by capability, and cost crosses over. For an
    input-dominated workload the Pro tier can be the cheaper choice, which is
    the opposite of the usual advice.
    """
    rungs = ladder(Lane.TEXT)
    assert [m.rung for m in rungs] == sorted(m.rung for m in rungs)

    pro25 = get("gemini-2.5-pro")
    flash35 = get("gemini-3.5-flash")
    assert pro25.rung > flash35.rung
    assert pro25.input_usd < flash35.input_usd
    assert pro25.output_usd > flash35.output_usd


def test_input_heavy_work_can_be_cheaper_on_the_pro_tier():
    """1M input, 5k output — the shape of a cache-heavy agent turn."""
    pro25 = estimate_usd(get("gemini-2.5-pro"), input_tokens=1_000_000, output_tokens=5_000)
    flash35 = estimate_usd(get("gemini-3.5-flash"), input_tokens=1_000_000, output_tokens=5_000)
    assert pro25 < flash35


# --- audit ----------------------------------------------------------------

def test_audit_separates_retired_from_unknown():
    report = audit(["gemini-3-pro-preview", "gemini-3.1-pro", "gemini-3.6-flash"])
    assert report["gemini-3-pro-preview"].startswith("RETIRED")
    assert report["gemini-3.1-pro"].startswith("UNKNOWN")
    assert report["gemini-3.6-flash"].startswith("ok")


def test_the_registry_has_no_duplicate_ids():
    ids = [m.id for m in REGISTRY]
    assert len(ids) == len(set(ids))


def test_every_live_model_declares_at_least_one_capability():
    for m in REGISTRY:
        if m.status is not Status.RETIRED:
            assert m.capabilities, f"{m.id} can be routed to but claims nothing"
