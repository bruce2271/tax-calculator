import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.form_1065_liquidation import (calc_736_split, calc_736a_character,
                                               calc_liquidating_distribution)


def prop(name, basis, fmv, klass="other"):
    return {"name": name, "basis": basis, "fmv": fmv, "klass": klass}


# ── §736 — splitting a payment to a retiring partner ─────────────────────────

def test_a_capital_intensive_partnership_keeps_everything_in_736b():
    """The carve-out only reaches a general partner where capital is not material."""
    r = calc_736_split(total_payment=300_000, receivables_share=50_000,
                       goodwill_share=40_000, other_property_share=200_000,
                       service_partnership=False, general_partner=True)
    assert r["section_736b"] == 290_000
    assert r["section_736a"] == 10_000
    assert not r["carve_out_applies"]


def test_a_service_partnership_pushes_receivables_and_goodwill_into_736a():
    r = calc_736_split(total_payment=300_000, receivables_share=50_000,
                       goodwill_share=40_000, other_property_share=200_000,
                       service_partnership=True, general_partner=True)
    assert r["section_736b"] == 200_000
    assert r["section_736a"] == 100_000
    assert r["carve_out_applies"]


def test_the_agreement_can_pull_goodwill_back_into_736b():
    """The one drafting decision that moves money from ordinary to capital."""
    r = calc_736_split(total_payment=300_000, receivables_share=50_000,
                       goodwill_share=40_000, other_property_share=200_000,
                       service_partnership=True, general_partner=True,
                       goodwill_in_agreement=True)
    assert r["section_736b"] == 240_000
    assert r["section_736a"] == 60_000


def test_a_limited_partner_never_gets_the_carve_out():
    r = calc_736_split(total_payment=300_000, receivables_share=50_000,
                       goodwill_share=40_000, other_property_share=200_000,
                       service_partnership=True, general_partner=False)
    assert not r["carve_out_applies"]
    assert r["section_736b"] == 290_000


def test_the_agreement_is_irrelevant_when_the_carve_out_does_not_apply():
    a = calc_736_split(300_000, 50_000, 40_000, 200_000, service_partnership=False,
                       general_partner=True, goodwill_in_agreement=True)
    b = calc_736_split(300_000, 50_000, 40_000, 200_000, service_partnership=False,
                       general_partner=True, goodwill_in_agreement=False)
    assert a["section_736b"] == b["section_736b"]


def test_the_two_halves_always_add_to_the_payment():
    r = calc_736_split(total_payment=300_000, receivables_share=50_000,
                       goodwill_share=40_000, other_property_share=200_000,
                       service_partnership=True, general_partner=True)
    assert r["section_736a"] + r["section_736b"] == 300_000


def test_736a_is_never_negative_when_property_exceeds_the_payment():
    r = calc_736_split(total_payment=100_000, other_property_share=200_000)
    assert r["section_736a"] == 0


# ── §736(a) character ────────────────────────────────────────────────────────

def test_a_payment_geared_to_income_is_a_distributive_share():
    r = calc_736a_character(determined_by_income=True)
    assert r["kind"] == "distributive share"


def test_a_fixed_payment_is_a_guaranteed_payment():
    r = calc_736a_character(determined_by_income=False)
    assert r["kind"] == "guaranteed payment"
    assert "707(c)" in r["note"]


# ── §731(a)(2) — loss, which a current distribution can never produce ────────

def test_money_only_liquidation_below_basis_produces_a_loss():
    r = calc_liquidating_distribution(outside_basis=50_000, cash=30_000)
    assert r["loss_731"] == 20_000
    assert r["gain_731"] == 0


def test_money_above_basis_still_produces_gain():
    r = calc_liquidating_distribution(outside_basis=50_000, cash=80_000)
    assert r["gain_731"] == 30_000 and r["loss_731"] == 0


def test_loss_is_allowed_when_only_hot_assets_come_out():
    r = calc_liquidating_distribution(
        outside_basis=60_000, cash=10_000,
        properties=[prop("Receivables", 20_000, 25_000, klass="hot")])
    assert r["loss_available"]
    assert r["loss_731"] == 30_000        # 60,000 − 10,000 − 20,000


def test_any_other_property_switches_the_loss_off():
    """The structural reason: other property can absorb a step-up, so basis has somewhere
    to go and there is nothing left to recognise."""
    r = calc_liquidating_distribution(
        outside_basis=60_000, cash=10_000,
        properties=[prop("Receivables", 20_000, 25_000, klass="hot"),
                    prop("Land", 5_000, 40_000)])
    assert not r["loss_available"]
    assert r["loss_731"] == 0
    assert r["basis_to_property"] == 50_000


# ── §732(b) — basis is substituted, and can go up ────────────────────────────

def test_property_takes_the_whole_remaining_basis():
    r = calc_liquidating_distribution(outside_basis=80_000,
                                      properties=[prop("Land", 30_000, 90_000)])
    assert r["allocations"]["Land"] == 80_000
    assert r["step_up"] == 50_000


def test_money_comes_off_before_the_substituted_basis_is_struck():
    r = calc_liquidating_distribution(outside_basis=80_000, cash=25_000,
                                      properties=[prop("Land", 30_000, 90_000)])
    assert r["allocations"]["Land"] == 55_000


def test_basis_can_also_come_down_on_a_liquidation():
    r = calc_liquidating_distribution(outside_basis=20_000,
                                      properties=[prop("Land", 30_000, 90_000)])
    assert r["allocations"]["Land"] == 20_000
    assert r["step_down"] == 10_000


def test_a_step_up_goes_to_appreciated_property_first():
    """§732(c)(2)(B), the mirror of the decrease rule.

    50,000 of step-up against 40,000 of appreciation. Clause (i) puts 40,000 into the
    appreciated asset. Clause (ii) then spreads the remaining 10,000 in proportion to fair
    market value across **all** the properties, not only the ones clause (i) missed — so
    the appreciated asset picks up a second slice and ends above its own value."""
    r = calc_liquidating_distribution(
        outside_basis=100_000,
        properties=[prop("Appreciated", 20_000, 60_000),
                    prop("Flat", 30_000, 30_000)])
    assert r["allocations"]["Appreciated"] == pytest.approx(66_666.667, abs=0.01)
    assert r["allocations"]["Flat"] == pytest.approx(33_333.333, abs=0.01)


def test_a_step_up_is_shared_in_proportion_to_appreciation():
    r = calc_liquidating_distribution(
        outside_basis=70_000,
        properties=[prop("A", 10_000, 40_000),     # 30,000 appreciation
                    prop("B", 10_000, 20_000)])    # 10,000 appreciation
    # 50,000 of step-up, but only 40,000 of appreciation, so 40,000 goes 30:10 and the
    # remaining 10,000 goes by value 40:20.
    assert r["allocations"]["A"] == pytest.approx(46_666.667, abs=0.01)
    assert r["allocations"]["B"] == pytest.approx(23_333.333, abs=0.01)


def test_hot_assets_are_never_stepped_up():
    """They can only ever take the partnership's basis, which is what makes a loss
    possible in the first place."""
    r = calc_liquidating_distribution(
        outside_basis=90_000,
        properties=[prop("Inventory", 20_000, 50_000, klass="hot"),
                    prop("Land", 10_000, 40_000)])
    assert r["allocations"]["Inventory"] == 20_000
    assert r["allocations"]["Land"] == 70_000


def test_hot_assets_are_still_served_first_when_basis_is_short():
    r = calc_liquidating_distribution(
        outside_basis=15_000,
        properties=[prop("Inventory", 20_000, 50_000, klass="hot"),
                    prop("Land", 10_000, 40_000)])
    assert r["allocations"]["Inventory"] == 15_000
    assert r["allocations"]["Land"] == 0


# ── Invariants ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kw", [
    dict(outside_basis=80_000, properties=[prop("L", 30_000, 90_000)]),
    dict(outside_basis=20_000, properties=[prop("L", 30_000, 90_000)]),
    dict(outside_basis=100_000, properties=[prop("A", 20_000, 60_000),
                                            prop("F", 30_000, 30_000)]),
    dict(outside_basis=90_000, cash=10_000,
         properties=[prop("I", 20_000, 50_000, klass="hot"), prop("L", 10_000, 40_000)]),
])
def test_the_whole_remaining_basis_lands_somewhere(kw):
    """§732(b) substitutes the entire outside basis less money, so unlike a current
    distribution nothing is left stranded once other property is in the mix."""
    r = calc_liquidating_distribution(**kw)
    assert r["basis_to_property"] == pytest.approx(r["basis_available"], abs=0.01)
    assert r["unabsorbed"] == pytest.approx(0, abs=0.01)


@pytest.mark.parametrize("kw", [
    dict(outside_basis=50_000, cash=30_000),
    dict(outside_basis=50_000, cash=80_000),
    dict(outside_basis=60_000, cash=10_000,
         properties=[prop("R", 20_000, 25_000, klass="hot")]),
])
def test_gain_and_loss_are_mutually_exclusive(kw):
    r = calc_liquidating_distribution(**kw)
    assert not (r["gain_731"] > 0 and r["loss_731"] > 0)
