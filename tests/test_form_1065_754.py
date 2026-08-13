import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.form_1065_754 import (CAPITAL, ORDINARY, calc_734b, calc_743b,
                                       calc_755_734b, calc_755_743b,
                                       calc_previously_taxed_capital,
                                       calc_substantial_basis_reduction,
                                       calc_substantial_built_in_loss)


def asset(name, basis, fmv, klass=CAPITAL):
    return {"name": name, "basis": basis, "fmv": fmv, "klass": klass}


# ── Reg. §1.743-1(d) — the transferee's share of inside basis ────────────────

def test_previously_taxed_capital_is_cash_plus_loss_less_gain():
    r = calc_previously_taxed_capital(hypothetical_cash=100_000, tax_loss_allocated=5_000,
                                      tax_gain_allocated=40_000, liability_share=30_000)
    assert r["previously_taxed_capital"] == 65_000
    assert r["share_of_inside_basis"] == 95_000


def test_liabilities_are_added_after_the_capital_figure():
    a = calc_previously_taxed_capital(hypothetical_cash=50_000)
    b = calc_previously_taxed_capital(hypothetical_cash=50_000, liability_share=20_000)
    assert b["previously_taxed_capital"] == a["previously_taxed_capital"]
    assert b["share_of_inside_basis"] - a["share_of_inside_basis"] == 20_000


# ── §743(b) ──────────────────────────────────────────────────────────────────

def test_no_election_means_no_adjustment():
    r = calc_743b(outside_basis=100_000, share_of_inside_basis=60_000)
    assert r["adjustment"] == 0
    assert r["potential"] == 40_000
    assert not r["applies"]


def test_an_election_steps_the_buyers_share_up():
    r = calc_743b(100_000, 60_000, election=True)
    assert r["adjustment"] == 40_000 and r["direction"] == "increase"


def test_the_adjustment_can_be_downward():
    r = calc_743b(40_000, 90_000, election=True)
    assert r["adjustment"] == -50_000 and r["direction"] == "decrease"


def test_a_substantial_built_in_loss_forces_the_adjustment_without_an_election():
    r = calc_743b(40_000, 90_000, election=False, substantial_built_in_loss=True)
    assert r["applies"] and r["mandatory"] and r["adjustment"] == -50_000


# ── §743(d) — when it becomes mandatory ──────────────────────────────────────

def test_the_entity_test_looks_at_inside_basis_against_value():
    assert calc_substantial_built_in_loss(inside_basis=1_000_000,
                                          fmv=700_000)["entity_test"]
    assert not calc_substantial_built_in_loss(inside_basis=1_000_000,
                                              fmv=800_000)["entity_test"]


def test_the_threshold_is_exceeded_not_merely_met():
    assert not calc_substantial_built_in_loss(inside_basis=250_000, fmv=0)["mandatory"]
    assert calc_substantial_built_in_loss(inside_basis=250_001, fmv=0)["mandatory"]


def test_the_transferee_test_catches_a_partnership_that_passes_the_entity_test():
    """Added in 2017 to close the workaround: the partnership overall need not be
    loss-making for one incoming partner to inherit a large built-in loss."""
    r = calc_substantial_built_in_loss(inside_basis=1_000_000, fmv=1_000_000,
                                       transferee_loss_share=300_000)
    assert not r["entity_test"]
    assert r["transferee_test"] and r["mandatory"]


# ── §734(b) ──────────────────────────────────────────────────────────────────

def test_gain_recognised_on_a_distribution_raises_inside_basis():
    r = calc_734b(gain_recognised=20_000, election=True)
    assert r["from_gain_or_loss"] == 20_000 and r["adjustment"] == 20_000


def test_loss_recognised_by_the_distributee_pushes_inside_basis_down():
    """§734(b)(2)(A) is the mirror of §734(b)(1)(A). A loss is only possible on a
    liquidating distribution, so this is the one source on this page that a current
    distribution can never produce."""
    r = calc_734b(loss_recognised=15_000, election=True)
    assert r["from_gain_or_loss"] == -15_000
    assert r["adjustment"] == -15_000 and r["direction"] == "decrease"


def test_gain_and_loss_on_the_same_line_net_against_each_other():
    r = calc_734b(gain_recognised=20_000, loss_recognised=5_000, election=True)
    assert r["from_gain_or_loss"] == 15_000


def test_basis_destroyed_by_the_732a2_cap_is_put_back():
    """The answer to 'what happens to the basis lost on a distribution' — nothing, unless
    there is an election, and then §734(b) restores it to the assets left behind."""
    r = calc_734b(partnership_basis_in_distributed=30_000, distributee_basis=20_000,
                  election=True)
    assert r["from_basis_difference"] == 10_000
    assert r["adjustment"] == 10_000


def test_a_stepped_up_distributee_basis_pushes_inside_basis_down():
    r = calc_734b(partnership_basis_in_distributed=20_000, distributee_basis=50_000,
                  election=True)
    assert r["adjustment"] == -30_000 and r["direction"] == "decrease"


def test_the_two_sources_are_kept_apart_because_755_treats_them_differently():
    r = calc_734b(gain_recognised=20_000, partnership_basis_in_distributed=30_000,
                  distributee_basis=20_000, election=True)
    assert r["from_gain_or_loss"] == 20_000
    assert r["from_basis_difference"] == 10_000
    assert r["adjustment"] == 30_000


def test_without_an_election_nothing_happens_but_the_potential_is_reported():
    r = calc_734b(gain_recognised=20_000)
    assert r["adjustment"] == 0 and r["potential"] == 20_000


def test_a_large_downward_adjustment_is_mandatory():
    assert calc_substantial_basis_reduction(-250_001)["mandatory"]
    assert not calc_substantial_basis_reduction(-250_000)["mandatory"]
    assert not calc_substantial_basis_reduction(900_000)["mandatory"]


# ── §755 for a §743(b) adjustment ────────────────────────────────────────────

def test_the_ordinary_class_takes_its_own_hypothetical_gain():
    assets = [asset("Receivables", 0, 40_000, ORDINARY),
              asset("Land", 100_000, 200_000, CAPITAL)]
    r = calc_755_743b(adjustment=70_000, assets=assets, transferee_pct=0.5)
    assert r["to_ordinary"] == 20_000        # 50% of the 40,000 ordinary gain
    assert r["to_capital"] == 50_000         # the residual


def test_the_capital_class_can_move_the_opposite_way_to_the_total():
    """A positive §743(b) adjustment can still push the capital class down, because the
    capital class takes the residual after the ordinary class is served."""
    assets = [asset("Receivables", 0, 100_000, ORDINARY),
              asset("Land", 200_000, 150_000, CAPITAL)]
    r = calc_755_743b(adjustment=60_000, assets=assets, transferee_pct=1.0)
    assert r["to_ordinary"] == 100_000
    assert r["to_capital"] == -40_000
    assert r["capital_is_opposite"]


def test_within_a_class_the_adjustment_follows_unrealised_gain():
    assets = [asset("A", 0, 30_000, CAPITAL), asset("B", 0, 10_000, CAPITAL)]
    r = calc_755_743b(adjustment=40_000, assets=assets)
    assert r["allocations"]["A"] == pytest.approx(30_000)
    assert r["allocations"]["B"] == pytest.approx(10_000)


def test_an_asset_at_its_basis_takes_none_of_the_adjustment():
    assets = [asset("Appreciated", 0, 50_000, CAPITAL),
              asset("Flat", 20_000, 20_000, CAPITAL)]
    r = calc_755_743b(adjustment=50_000, assets=assets)
    assert r["allocations"]["Flat"] == 0
    assert r["allocations"]["Appreciated"] == pytest.approx(50_000)


def test_the_allocation_adds_back_to_the_adjustment():
    assets = [asset("R", 0, 40_000, ORDINARY), asset("L", 100_000, 200_000, CAPITAL)]
    r = calc_755_743b(adjustment=70_000, assets=assets, transferee_pct=0.5)
    assert sum(r["allocations"].values()) == pytest.approx(70_000)


# ── §755 for a §734(b) adjustment ────────────────────────────────────────────

def test_adjustment_from_recognised_gain_goes_only_to_capital_property():
    assets = [asset("Receivables", 0, 40_000, ORDINARY),
              asset("Land", 100_000, 200_000, CAPITAL)]
    r = calc_755_734b(from_gain_or_loss=20_000, from_basis_difference=0,
                      distributed_class=CAPITAL, assets=assets)
    assert r["allocations"].get("Receivables", 0) == 0
    assert r["allocations"]["Land"] == pytest.approx(20_000)


def test_adjustment_from_basis_difference_goes_to_the_same_class():
    """Ordinary basis is restored to ordinary assets, not to the land."""
    assets = [asset("Inventory", 10_000, 30_000, ORDINARY),
              asset("Land", 100_000, 200_000, CAPITAL)]
    r = calc_755_734b(from_gain_or_loss=0, from_basis_difference=15_000,
                      distributed_class=ORDINARY, assets=assets)
    assert r["allocations"]["Inventory"] == pytest.approx(15_000)
    assert r["allocations"].get("Land", 0) == 0


def test_a_downward_adjustment_cannot_drive_a_basis_negative():
    """§755(c) and Reg. §1.755-1(c)(4). A decrease the class cannot absorb is held in
    suspense until the partnership acquires property of that class — it does not create a
    negative basis, and it is not simply discarded."""
    assets = [asset("Land", 10_000, 40_000, CAPITAL)]
    r = calc_755_734b(from_gain_or_loss=-50_000, from_basis_difference=0,
                      distributed_class=CAPITAL, assets=assets)
    assert r["allocations"]["Land"] == -10_000
    assert r["suspended"] == 40_000


def test_a_class_with_no_basis_suspends_the_whole_decrease():
    assets = [asset("Land", 0, 0, CAPITAL)]
    r = calc_755_734b(from_gain_or_loss=-50_000, from_basis_difference=0,
                      distributed_class=CAPITAL, assets=assets)
    assert r["allocations"]["Land"] == 0
    assert r["suspended"] == 50_000


def test_an_upward_adjustment_is_never_capped():
    assets = [asset("Land", 10_000, 40_000, CAPITAL)]
    r = calc_755_734b(from_gain_or_loss=50_000, from_basis_difference=0,
                      distributed_class=CAPITAL, assets=assets)
    assert r["allocations"]["Land"] == 50_000
    assert r["suspended"] == 0


def test_the_two_sources_can_land_on_different_classes_at_once():
    assets = [asset("Inventory", 10_000, 30_000, ORDINARY),
              asset("Land", 100_000, 200_000, CAPITAL)]
    r = calc_755_734b(from_gain_or_loss=20_000, from_basis_difference=15_000,
                      distributed_class=ORDINARY, assets=assets)
    assert r["allocations"]["Land"] == pytest.approx(20_000)
    assert r["allocations"]["Inventory"] == pytest.approx(15_000)
    assert sum(r["allocations"].values()) == pytest.approx(35_000)


# ── Invariants ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("adjustment,pct", [
    (70_000, 0.5), (-40_000, 1.0), (0, 0.25), (125_000, 0.3),
])
def test_a_743b_allocation_always_sums_to_the_adjustment(adjustment, pct):
    assets = [asset("R", 0, 40_000, ORDINARY), asset("I", 5_000, 15_000, ORDINARY),
              asset("L", 100_000, 200_000, CAPITAL), asset("M", 80_000, 50_000, CAPITAL)]
    r = calc_755_743b(adjustment, assets, pct)
    # A cent is the meaningful tolerance for money; the residual is float dust.
    assert sum(r["allocations"].values()) == pytest.approx(adjustment, abs=0.01)


def test_outside_and_inside_basis_agree_once_the_adjustment_is_made():
    """The whole point of the election, stated as an identity: after §743(b) the buyer's
    share of inside basis equals what they paid."""
    ptc = calc_previously_taxed_capital(hypothetical_cash=60_000, liability_share=30_000)
    adj = calc_743b(outside_basis=140_000,
                    share_of_inside_basis=ptc["share_of_inside_basis"], election=True)
    assert ptc["share_of_inside_basis"] + adj["adjustment"] == 140_000
