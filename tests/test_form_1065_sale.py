import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.form_1065_sale import (calc_704c_transfer, calc_743b,
                                        calc_751a_ordinary, calc_amount_realized,
                                        calc_buyer_basis, calc_sale_of_interest)


def hot(name, basis, fmv, klass="receivable", cap=None):
    a = {"name": name, "basis": basis, "fmv": fmv, "klass": klass}
    if cap is not None:
        a["cap"] = cap
    return a


# ── §752(d) — the debt is part of the price ──────────────────────────────────

def test_debt_relief_is_part_of_the_amount_realised():
    ar = calc_amount_realized(cash=50_000, liabilities_relieved=30_000)
    assert ar["total"] == 80_000


def test_an_interest_sold_for_no_cash_can_still_produce_gain():
    """The classic §752(d) trap."""
    r = calc_sale_of_interest(cash=0, liabilities_relieved=40_000, outside_basis=25_000)
    assert r["total_gain"] == 15_000


def test_property_taken_in_exchange_counts_at_value():
    ar = calc_amount_realized(cash=10_000, property_fmv=25_000, liabilities_relieved=5_000)
    assert ar["total"] == 40_000


# ── §741 — the plain case ────────────────────────────────────────────────────

def test_a_sale_with_no_hot_assets_is_entirely_capital():
    r = calc_sale_of_interest(cash=100_000, outside_basis=60_000,
                              holding_period_months=24)
    assert r["ordinary_751a"] == 0
    assert r["capital_741"] == 40_000
    assert r["long_term"]


def test_holding_period_decides_long_or_short_term():
    assert not calc_sale_of_interest(cash=1, holding_period_months=12)["long_term"]
    assert calc_sale_of_interest(cash=1, holding_period_months=13)["long_term"]


def test_a_loss_on_sale_is_a_capital_loss():
    r = calc_sale_of_interest(cash=40_000, outside_basis=70_000, holding_period_months=24)
    assert r["total_gain"] == -30_000
    assert r["capital_741"] == -30_000
    assert "loss" in r["character"]


# ── §751(a) — hot assets ─────────────────────────────────────────────────────

def test_the_partners_share_of_hot_asset_gain_is_ordinary():
    r = calc_sale_of_interest(
        cash=100_000, outside_basis=60_000, ownership_pct=0.25,
        hot_assets=[hot("Receivables", 0, 80_000)])
    assert r["ordinary_751a"] == 20_000        # 25% of 80,000
    assert r["capital_741"] == 20_000          # the residual


def test_ordinary_income_can_sit_alongside_a_capital_loss():
    """The pattern to recognise on sight: the sale made money, and the partner still
    reports a capital loss because §751(a) took more than the whole gain."""
    r = calc_sale_of_interest(
        cash=100_000, outside_basis=90_000, ownership_pct=0.50,
        hot_assets=[hot("Receivables", 0, 60_000)])
    assert r["total_gain"] == 10_000
    assert r["ordinary_751a"] == 30_000
    assert r["capital_741"] == -20_000
    assert r["ordinary_with_capital_loss"]


def test_inventory_need_not_be_substantially_appreciated_on_a_sale():
    """The substantially-appreciated test is in §751(b) and applies to distributions. On a
    sale under §751(a) any inventory item counts, however small the gain."""
    r = calc_sale_of_interest(cash=100_000, outside_basis=60_000, ownership_pct=1.0,
                              hot_assets=[hot("Inventory", 100_000, 101_000,
                                              klass="inventory")])
    assert r["ordinary_751a"] == 1_000


def test_depreciation_recapture_is_an_unrealised_receivable():
    """§751(c) flush language. A cash-basis partnership with no receivables on its books
    can still hold §751 assets through recapture."""
    r = calc_751a_ordinary([hot("Machine recapture", 20_000, 90_000,
                                klass="recapture", cap=45_000)])
    assert r["ordinary"] == 45_000       # capped at the recapture potential, not the gain


def test_a_hot_asset_standing_at_a_loss_does_not_shelter_another():
    r = calc_751a_ordinary([hot("Good receivable", 0, 50_000),
                            hot("Bad receivable", 30_000, 10_000)])
    assert r["ordinary"] == 50_000


def test_each_hot_asset_is_reported_separately():
    r = calc_751a_ordinary([hot("A", 0, 40_000), hot("B", 10_000, 30_000)],
                           ownership_pct=0.5)
    assert [x["partner_share"] for x in r["rows"]] == [20_000, 10_000]


def test_form_8308_is_required_whenever_751a_applies():
    with_hot = calc_sale_of_interest(cash=10, hot_assets=[hot("R", 0, 100)])
    without = calc_sale_of_interest(cash=10)
    assert with_hot["form_8308_required"]
    assert not without["form_8308_required"]


# ── The two halves always add back ───────────────────────────────────────────

@pytest.mark.parametrize("kw", [
    dict(cash=100_000, outside_basis=60_000),
    dict(cash=100_000, outside_basis=90_000, ownership_pct=0.5,
         hot_assets=[hot("R", 0, 60_000)]),
    dict(cash=0, liabilities_relieved=40_000, outside_basis=25_000),
    dict(cash=40_000, outside_basis=70_000),
    dict(cash=50_000, property_fmv=20_000, liabilities_relieved=30_000,
         outside_basis=60_000, ownership_pct=0.25,
         hot_assets=[hot("R", 0, 80_000), hot("I", 5_000, 25_000, klass="inventory")]),
])
def test_ordinary_plus_capital_equals_the_total_gain(kw):
    """§751(a) splits the gain; it never changes how much there is."""
    r = calc_sale_of_interest(**kw)
    assert r["ordinary_751a"] + r["capital_741"] == pytest.approx(r["total_gain"])


# ── The buyer's side ─────────────────────────────────────────────────────────

def test_buyer_basis_includes_the_debt_stepped_into():
    b = calc_buyer_basis(purchase_price=50_000, liabilities_assumed=30_000)
    assert b["outside_basis"] == 80_000


def test_without_a_754_election_inside_basis_does_not_move():
    r = calc_743b(buyer_outside_basis=80_000, share_of_inside_basis=45_000)
    assert r["adjustment"] == 0
    assert r["potential_adjustment"] == 35_000
    assert not r["applies"]


def test_a_754_election_steps_the_buyers_share_of_inside_basis_up():
    r = calc_743b(80_000, 45_000, election_in_effect=True)
    assert r["adjustment"] == 35_000 and r["applies"]


def test_a_substantial_built_in_loss_makes_the_adjustment_mandatory():
    """§743(d). The rule cannot be used selectively to preserve losses."""
    r = calc_743b(40_000, 90_000, election_in_effect=False,
                  substantial_built_in_loss=True)
    assert r["applies"] and r["mandatory"]
    assert r["adjustment"] == -50_000


def test_the_adjustment_can_be_negative_under_an_election_too():
    r = calc_743b(40_000, 90_000, election_in_effect=True)
    assert r["adjustment"] == -50_000


# ── §704(c) follows the interest ─────────────────────────────────────────────

def test_the_704c_balance_transfers_to_the_buyer():
    """Reg. §1.704-3(a)(7). Built-in gain attaches to the property, so selling the interest
    does not wash it away."""
    t = calc_704c_transfer(seller_item_n=47_500)
    assert t["transferred"] == 47_500


def test_nothing_transfers_when_there_is_no_704c_balance():
    assert calc_704c_transfer(0)["transferred"] == 0
    assert "nothing transfers" in calc_704c_transfer(0)["note"]


def test_a_built_in_loss_balance_transfers_as_well():
    assert calc_704c_transfer(-30_000)["transferred"] == -30_000
