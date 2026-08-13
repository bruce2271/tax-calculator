import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.form_1065_distributions import (calc_704c_1b, calc_735_character,
                                                 calc_751b_flag,
                                                 calc_current_distribution)


def prop(name, basis, fmv, klass="other"):
    return {"name": name, "basis": basis, "fmv": fmv, "klass": klass}


# ── §731(a) — when a distribution is taxable ─────────────────────────────────

def test_cash_within_basis_is_tax_free():
    r = calc_current_distribution(outside_basis=50_000, cash=30_000)
    assert r["gain_731"] == 0
    assert r["ending_basis"] == 20_000


def test_cash_above_basis_produces_gain():
    r = calc_current_distribution(outside_basis=50_000, cash=80_000)
    assert r["gain_731"] == 30_000
    assert r["ending_basis"] == 0


def test_property_never_produces_gain_however_appreciated():
    """The whole point of §731(a)(1): only money is tested against basis."""
    r = calc_current_distribution(outside_basis=10_000,
                                  properties=[prop("Land", 10_000, 500_000)])
    assert r["gain_731"] == 0
    assert r["allocations"]["Land"] == 10_000


def test_a_current_distribution_can_never_produce_a_loss():
    """§731(a)(2) allows loss only in liquidation."""
    r = calc_current_distribution(outside_basis=100_000, cash=10_000,
                                  properties=[prop("Kit", 5_000, 1_000)])
    assert r["loss_recognised"] == 0
    assert r["ending_basis"] == 85_000


def test_marketable_securities_count_as_money():
    """§731(c)."""
    r = calc_current_distribution(outside_basis=40_000, marketable_securities=60_000)
    assert r["money"] == 60_000
    assert r["gain_731"] == 20_000


def test_a_reduction_in_the_share_of_debt_counts_as_money():
    """§752(b) — the classic way a partner is taxed on a distribution of nothing at all."""
    r = calc_current_distribution(outside_basis=15_000, liability_relief=25_000)
    assert r["gain_731"] == 10_000


def test_money_from_every_source_is_added_before_the_test():
    r = calc_current_distribution(outside_basis=50_000, cash=20_000,
                                  marketable_securities=20_000, liability_relief=20_000)
    assert r["money"] == 60_000
    assert r["gain_731"] == 10_000


# ── §732(a) — basis of the distributed property ──────────────────────────────

def test_property_takes_carryover_basis_when_basis_is_ample():
    r = calc_current_distribution(outside_basis=100_000,
                                  properties=[prop("Land", 30_000, 90_000)])
    assert r["allocations"]["Land"] == 30_000
    assert r["ending_basis"] == 70_000


def test_basis_is_capped_and_never_stepped_up_in_a_current_distribution():
    """§732(a)(2). The partner's basis runs out, so the property takes less than the
    partnership's basis and the difference is simply lost."""
    r = calc_current_distribution(outside_basis=20_000,
                                  properties=[prop("Land", 30_000, 90_000)])
    assert r["allocations"]["Land"] == 20_000
    assert r["basis_lost"] == 10_000
    assert r["ending_basis"] == 0


def test_money_is_taken_out_before_property_gets_any_basis():
    r = calc_current_distribution(outside_basis=50_000, cash=40_000,
                                  properties=[prop("Land", 30_000, 90_000)])
    assert r["basis_after_money"] == 10_000
    assert r["allocations"]["Land"] == 10_000


def test_hot_assets_are_served_before_other_property():
    """§732(c)(1): receivables and inventory take basis first, so a shortfall falls on the
    capital asset rather than on the ordinary-income assets."""
    r = calc_current_distribution(
        outside_basis=25_000,
        properties=[prop("Land", 40_000, 80_000),
                    prop("Inventory", 20_000, 22_000, klass="hot")])
    assert r["allocations"]["Inventory"] == 20_000
    assert r["allocations"]["Land"] == 5_000


# ── §732(c) — allocating a shortfall across properties ───────────────────────

def test_a_shortfall_hits_depreciated_property_first():
    """§732(c)(3)(A): the decrease goes to unrealised depreciation before anything else.

    Basis of 60,000 against 50,000 available, so 10,000 has to come off. The machine
    carries 15,000 of unrealised depreciation, which absorbs the whole decrease — the
    appreciated land is not touched at all."""
    r = calc_current_distribution(
        outside_basis=50_000,
        properties=[prop("Machine", 40_000, 25_000),
                    prop("Land", 20_000, 60_000)])
    assert r["allocations"]["Machine"] == 30_000
    assert r["allocations"]["Land"] == 20_000
    assert r["basis_to_property"] == 50_000


def test_a_decrease_larger_than_the_depreciation_spills_onto_the_appreciated_asset():
    """Same two assets, less basis. The machine's 15,000 of depreciation goes first, and
    the remaining 15,000 is then spread over what is left."""
    r = calc_current_distribution(
        outside_basis=30_000,
        properties=[prop("Machine", 40_000, 25_000),
                    prop("Land", 20_000, 60_000)])
    assert r["allocations"]["Machine"] == pytest.approx(16_666.667, abs=0.01)
    assert r["allocations"]["Land"] == pytest.approx(13_333.333, abs=0.01)
    assert sum(r["allocations"].values()) == pytest.approx(30_000)


def test_depreciation_shortfall_is_shared_in_proportion_to_the_depreciation():
    r = calc_current_distribution(
        outside_basis=70_000,
        properties=[prop("A", 50_000, 40_000),     # 10,000 depreciation
                    prop("B", 50_000, 20_000)])    # 30,000 depreciation
    # 30,000 of decrease, spread 10:30 → A gives up 7,500, B gives up 22,500
    assert r["allocations"]["A"] == pytest.approx(42_500)
    assert r["allocations"]["B"] == pytest.approx(27_500)


def test_a_shortfall_beyond_all_depreciation_falls_on_remaining_basis():
    r = calc_current_distribution(
        outside_basis=30_000,
        properties=[prop("A", 40_000, 35_000),     # 5,000 depreciation
                    prop("B", 40_000, 60_000)])    # none
    # Total basis 80,000, available 30,000 → decrease 50,000. First 5,000 to A's
    # depreciation, then 45,000 across 35,000 and 40,000 in proportion.
    assert sum(r["allocations"].values()) == pytest.approx(30_000)
    assert r["allocations"]["A"] == pytest.approx(14_000)
    assert r["allocations"]["B"] == pytest.approx(16_000)


def test_no_property_can_take_a_negative_basis():
    r = calc_current_distribution(outside_basis=0,
                                  properties=[prop("A", 40_000, 10_000),
                                              prop("B", 10_000, 90_000)])
    assert all(v >= 0 for v in r["allocations"].values())
    assert sum(r["allocations"].values()) == 0


# ── §737 — other property back to a contributing partner ─────────────────────

def test_737_recognises_the_lesser_of_precontribution_gain_and_the_excess():
    r = calc_current_distribution(outside_basis=20_000,
                                  properties=[prop("Land B", 30_000, 90_000)],
                                  net_precontribution_gain=50_000,
                                  seven_year_property=True)
    assert r["gain_737"] == 50_000      # excess is 70,000, capped by the 704(c) balance


def test_737_is_capped_by_the_excess_of_value_over_basis():
    r = calc_current_distribution(outside_basis=80_000,
                                  properties=[prop("Land B", 30_000, 90_000)],
                                  net_precontribution_gain=50_000,
                                  seven_year_property=True)
    assert r["gain_737"] == 10_000      # 90,000 − 80,000


def test_737_does_not_apply_outside_the_seven_year_window():
    r = calc_current_distribution(outside_basis=20_000,
                                  properties=[prop("Land B", 30_000, 90_000)],
                                  net_precontribution_gain=50_000,
                                  seven_year_property=False)
    assert r["gain_737"] == 0


def test_737_gain_raises_basis_before_732_runs():
    """§737(c)(1). The gain is added to outside basis first, so the distributed property
    can absorb more of it and less basis is lost."""
    without = calc_current_distribution(outside_basis=20_000,
                                        properties=[prop("Land B", 30_000, 90_000)])
    with_737 = calc_current_distribution(outside_basis=20_000,
                                         properties=[prop("Land B", 30_000, 90_000)],
                                         net_precontribution_gain=50_000,
                                         seven_year_property=True)
    assert without["allocations"]["Land B"] == 20_000
    assert with_737["allocations"]["Land B"] == 30_000     # full carryover now fits
    assert with_737["basis_lost"] == 0


def test_737_does_not_apply_when_only_money_is_distributed():
    r = calc_current_distribution(outside_basis=20_000, cash=30_000,
                                  net_precontribution_gain=50_000,
                                  seven_year_property=True)
    assert r["gain_737"] == 0
    assert r["gain_731"] == 10_000


# ── §704(c)(1)(B) — the contributed property goes to someone else ────────────

def test_704c1b_triggers_inside_seven_years():
    r = calc_704c_1b(built_in_gain_remaining=45_000,
                     distributed_to_another_partner=True, years_since_contribution=3)
    assert r["triggered"] and r["gain"] == 45_000


def test_704c1b_does_not_trigger_after_seven_years():
    r = calc_704c_1b(45_000, True, 7)
    assert not r["triggered"] and r["gain"] == 0


def test_704c1b_does_not_trigger_on_a_return_to_the_contributor():
    r = calc_704c_1b(45_000, False, 3)
    assert not r["triggered"]


def test_704c1b_carries_a_built_in_loss_through_as_well():
    r = calc_704c_1b(-20_000, True, 2)
    assert r["triggered"] and r["gain"] == -20_000


# ── §735 — character after the distribution ──────────────────────────────────

def test_receivables_stay_ordinary_for_ever():
    t = calc_735_character("receivable", years_held_by_partner=30)
    assert t["tainted"] and t["years"] is None


def test_inventory_taint_expires_after_five_years():
    assert calc_735_character("inventory", 4)["tainted"]
    assert not calc_735_character("inventory", 5)["tainted"]


def test_other_property_takes_the_partners_own_character():
    assert not calc_735_character("capital", 1)["tainted"]


# ── §751(b) ──────────────────────────────────────────────────────────────────

def test_a_shift_in_hot_asset_share_is_flagged():
    assert calc_751b_flag(0.50, 0.30)["disproportionate"]


def test_a_proportionate_distribution_is_not_flagged():
    assert not calc_751b_flag(0.50, 0.50)["disproportionate"]


# ── Invariants ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kw", [
    dict(outside_basis=50_000, cash=30_000),
    dict(outside_basis=50_000, cash=80_000),
    dict(outside_basis=20_000, properties=[prop("Land", 30_000, 90_000)]),
    dict(outside_basis=100_000, cash=10_000,
         properties=[prop("A", 40_000, 20_000), prop("B", 30_000, 70_000)]),
    dict(outside_basis=25_000,
         properties=[prop("Inv", 20_000, 22_000, klass="hot"), prop("L", 40_000, 80_000)]),
    dict(outside_basis=20_000, properties=[prop("Land B", 30_000, 90_000)],
         net_precontribution_gain=50_000, seven_year_property=True),
])
def test_basis_is_conserved(kw):
    """Every dollar of basis available for property is either allocated to property or
    stays in the interest. Nothing is created and nothing leaks."""
    r = calc_current_distribution(**kw)
    assert r["basis_to_property"] + r["ending_basis"] == pytest.approx(
        r["basis_for_property"])


@pytest.mark.parametrize("kw", [
    dict(outside_basis=50_000, cash=80_000),
    dict(outside_basis=20_000, properties=[prop("Land", 30_000, 90_000)]),
    dict(outside_basis=0, properties=[prop("A", 40_000, 10_000)]),
])
def test_outside_basis_never_goes_negative(kw):
    assert calc_current_distribution(**kw)["ending_basis"] >= 0


def test_gain_and_ending_basis_are_mutually_exclusive_for_money_only():
    """If money forced gain, basis is exhausted; if basis survives, there was no gain."""
    for ob, cash in [(50_000, 30_000), (50_000, 80_000), (50_000, 50_000)]:
        r = calc_current_distribution(outside_basis=ob, cash=cash)
        assert not (r["gain_731"] > 0 and r["ending_basis"] > 0)
