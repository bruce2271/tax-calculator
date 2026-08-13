import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.form_1065_formation import (calc_721_contribution, calc_724_taint,
                                             calc_disguised_sale, calc_holding_period,
                                             calc_item_n, calc_services_interest)


# ── §721 / §722 / §723 — the plain case ──────────────────────────────────────

def test_contributing_appreciated_property_is_tax_free():
    r = calc_721_contribution(property_basis=40_000, property_fmv=100_000)
    assert r["gain_total"] == 0
    assert r["outside_basis"] == 40_000          # §722 — adjusted basis, not value
    assert r["partnership_basis"] == 40_000      # §723 — carryover
    assert r["built_in_gain"] == 60_000          # follows the contributor under §704(c)


def test_book_capital_takes_value_while_basis_takes_cost():
    """The gap between these two figures is the entire reason §704(c) exists."""
    r = calc_721_contribution(property_basis=40_000, property_fmv=100_000)
    assert r["book_capital"] == 100_000
    assert r["tax_capital"] == 40_000
    assert r["book_capital"] - r["tax_capital"] == r["built_in_gain"]


def test_contributing_loss_property_does_not_recognise_the_loss_either():
    r = calc_721_contribution(property_basis=100_000, property_fmv=60_000)
    assert r["gain_total"] == 0
    assert r["outside_basis"] == 100_000
    assert r["built_in_gain"] == -40_000


def test_cash_contribution_creates_no_built_in_gain():
    r = calc_721_contribution(cash=50_000)
    assert r["outside_basis"] == 50_000
    assert r["built_in_gain"] == 0
    assert r["book_capital"] == 50_000


# ── §752 — where a contribution becomes taxable ──────────────────────────────

def test_liability_relief_reduces_basis_but_not_below_zero():
    """AB 40,000 property carrying a 70,000 mortgage; the partner keeps a 25% share of the
    debt, so 52,500 of relief is a deemed distribution of money under §752(b)."""
    r = calc_721_contribution(property_basis=40_000, property_fmv=100_000,
                              liability_assumed=70_000, retained_liability_share=0.25)
    assert r["net_relief"] == 52_500
    assert r["gain_731"] == 12_500      # §731(a)(1) — relief in excess of basis
    assert r["outside_basis"] == 0


def test_gain_forced_by_liability_relief_raises_the_partnerships_basis():
    """Otherwise the same gain would be taxed twice — once to the partner now, once to the
    partnership on sale."""
    r = calc_721_contribution(property_basis=40_000, property_fmv=100_000,
                              liability_assumed=70_000, retained_liability_share=0.25)
    assert r["partnership_basis"] == 52_500
    assert r["built_in_gain"] == 47_500


def test_a_partner_can_end_up_with_negative_tax_capital():
    r = calc_721_contribution(property_basis=40_000, property_fmv=100_000,
                              liability_assumed=70_000, retained_liability_share=0.25)
    assert r["tax_capital"] == -17_500
    assert r["book_capital"] == 30_000


def test_relief_within_basis_is_not_taxable():
    r = calc_721_contribution(property_basis=100_000, property_fmv=150_000,
                              liability_assumed=60_000, retained_liability_share=0.25)
    assert r["gain_731"] == 0
    assert r["outside_basis"] == 55_000      # 100,000 − 45,000 relief


def test_keeping_the_whole_liability_means_no_relief_at_all():
    r = calc_721_contribution(property_basis=40_000, property_fmv=100_000,
                              liability_assumed=70_000, retained_liability_share=1.0)
    assert r["net_relief"] == 0
    assert r["outside_basis"] == 40_000


def test_a_share_of_other_partnership_debt_adds_basis_with_no_offset():
    r = calc_721_contribution(cash=10_000, other_liability_share=90_000)
    assert r["outside_basis"] == 100_000
    assert r["tax_capital"] == 10_000


def test_other_partnership_debt_can_absorb_relief_that_would_otherwise_be_gain():
    r = calc_721_contribution(property_basis=40_000, property_fmv=100_000,
                              liability_assumed=70_000, retained_liability_share=0.25,
                              other_liability_share=20_000)
    assert r["gain_731"] == 0
    assert r["outside_basis"] == 7_500


# ── §721(b) — the investment company exception ───────────────────────────────

def test_investment_company_contribution_recognises_gain():
    r = calc_721_contribution(property_basis=40_000, property_fmv=100_000,
                              is_investment_company=True)
    assert r["gain_721b"] == 60_000
    assert r["outside_basis"] == 100_000     # basis stepped up by the gain
    assert r["partnership_basis"] == 100_000
    assert r["built_in_gain"] == 0           # nothing left for §704(c) to chase


def test_investment_company_exception_does_not_recognise_losses():
    r = calc_721_contribution(property_basis=100_000, property_fmv=60_000,
                              is_investment_company=True)
    assert r["gain_721b"] == 0
    assert r["outside_basis"] == 100_000


def test_721b_gain_is_measured_before_liability_relief_is_tested():
    """Ordering matters: the §721(b) gain raises basis, which can stop relief from
    producing a second gain under §731(a)(1)."""
    r = calc_721_contribution(property_basis=40_000, property_fmv=100_000,
                              liability_assumed=70_000, retained_liability_share=0.25,
                              is_investment_company=True)
    assert r["gain_721b"] == 60_000
    assert r["gain_731"] == 0
    assert r["outside_basis"] == 47_500


# ── §724 — character taint ───────────────────────────────────────────────────

def test_unrealised_receivables_are_ordinary_for_ever():
    t = calc_724_taint("receivable")
    assert t["tainted"] and t["years"] is None


def test_inventory_and_capital_loss_property_are_tainted_for_five_years():
    assert calc_724_taint("inventory")["years"] == 5
    assert calc_724_taint("capital_loss")["years"] == 5


def test_ordinary_capital_property_carries_no_taint():
    t = calc_724_taint("capital")
    assert not t["tainted"] and t["years"] is None


# ── §1223 — holding periods ──────────────────────────────────────────────────

def test_capital_and_1231_property_tack_the_interest_holding_period():
    assert calc_holding_period("capital")["interest_tacks"]
    assert calc_holding_period("1231")["interest_tacks"]


def test_inventory_and_cash_do_not_tack_the_interest():
    assert not calc_holding_period("inventory")["interest_tacks"]


def test_the_partnership_always_tacks_regardless_of_character():
    for ch in ("capital", "1231", "inventory", "receivable"):
        assert calc_holding_period(ch)["partnership_tacks"]


def test_contributing_cash_and_capital_property_splits_the_holding_period():
    assert calc_holding_period("capital", has_cash=True)["split"]
    assert not calc_holding_period("capital", has_cash=False)["split"]


# ── §707(a)(2)(B) — disguised sale ───────────────────────────────────────────

def test_a_distribution_within_two_years_is_presumed_a_sale():
    d = calc_disguised_sale(contribution_fmv=100_000, distribution=40_000, months_apart=18)
    assert d["presumed_sale"]
    assert d["sale_fraction"] == pytest.approx(0.40)


def test_the_presumption_flips_after_two_years():
    d = calc_disguised_sale(contribution_fmv=100_000, distribution=40_000, months_apart=25)
    assert not d["presumed_sale"]


def test_exactly_two_years_is_still_inside_the_presumption():
    assert calc_disguised_sale(100_000, 40_000, 24)["presumed_sale"]


def test_no_distribution_means_nothing_to_test():
    assert not calc_disguised_sale(100_000, 0, 6)["presumed_sale"]


# ── Interests for services ───────────────────────────────────────────────────

def test_a_capital_interest_for_services_is_taxable_compensation():
    r = calc_services_interest("capital", 80_000)
    assert r["taxable"] and r["income"] == 80_000 and r["basis"] == 80_000


def test_a_profits_interest_is_not_taxable_on_grant():
    r = calc_services_interest("profits", 80_000)
    assert not r["taxable"] and r["income"] == 0 and r["basis"] == 0


def test_an_unvested_capital_interest_mentions_the_83b_election():
    assert "83(b)" in calc_services_interest("capital", 80_000, vested=False)["note"]


# ── Schedule K-1 Item N ──────────────────────────────────────────────────────

def test_item_n_rolls_forward():
    n = calc_item_n(prior_unrecognized=60_000, current_built_in_gain=25_000,
                    allocated_this_year=10_000)
    assert n["ending"] == 75_000


def test_a_new_contribution_starts_item_n_at_its_built_in_gain():
    assert calc_item_n(current_built_in_gain=60_000)["ending"] == 60_000


def test_item_n_carries_built_in_loss_as_a_negative():
    assert calc_item_n(current_built_in_gain=-40_000)["ending"] == -40_000


# ── The tie the app relies on ────────────────────────────────────────────────

@pytest.mark.parametrize("kw", [
    dict(property_basis=40_000, property_fmv=100_000),
    dict(property_basis=100_000, property_fmv=60_000),
    dict(cash=25_000, property_basis=40_000, property_fmv=100_000),
    dict(property_basis=40_000, property_fmv=100_000,
         liability_assumed=70_000, retained_liability_share=0.25),
    dict(property_basis=40_000, property_fmv=100_000,
         liability_assumed=70_000, retained_liability_share=0.25,
         other_liability_share=20_000),
    dict(property_basis=40_000, property_fmv=100_000, is_investment_company=True),
])
def test_the_two_capital_accounts_always_differ_by_the_built_in_gain(kw):
    """The identity the app leans on. Book capital takes value, tax capital takes cost, and
    whatever separates them is exactly the §704(c) layer that Item N reports — so the K-1
    can never show a built-in gain the capital accounts do not support. It holds even when
    the contribution was taxable, because recognised gain raises both sides at once."""
    r = calc_721_contribution(**kw)
    assert r["book_capital"] - r["tax_capital"] == pytest.approx(r["built_in_gain"])
    assert calc_item_n(current_built_in_gain=r["built_in_gain"])["ending"] == \
        pytest.approx(r["book_capital"] - r["tax_capital"])
