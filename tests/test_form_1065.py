"""Correctness tests for the partnership engine.

The loss limitation cases reproduce the worked example in
`Form_1065_Partnership_Interview_Prep.md` §3.2, so the expected figures come from the
study notes rather than from this code.
"""

import pytest

from calculators.form_1065 import (
    calc_752_shares,
    calc_capital_account,
    calc_loss_limitations,
    calc_outside_basis,
)


# ── §704(d) → §465 → §469 ────────────────────────────────────────────────────

def test_the_three_limitations_each_stop_a_different_slice():
    """The worked example from the prep notes. A $48,000 allocable loss meets three
    limitations in turn and only $2,000 survives:

        §704(d)  outside basis $46,500          suspends  $1,500
        §465     at risk       $31,500          suspends $15,000
        §469     passive income $2,000          suspends $29,500
    """
    r = calc_loss_limitations(allocable_loss=48_000, outside_basis=46_500,
                              at_risk_amount=31_500, passive_income=2_000)
    assert r["after_704d"] == 46_500
    assert r["suspended_704d"] == 1_500
    assert r["after_465"] == 31_500
    assert r["suspended_465"] == 15_000
    assert r["deductible"] == 2_000
    assert r["suspended_469"] == 29_500


def test_nothing_is_lost_only_deferred():
    """The invariant across any facts: what is deductible plus what is suspended must
    equal the allocable loss. A limitation defers a loss, it never destroys it."""
    r = calc_loss_limitations(48_000, 46_500, 31_500, passive_income=2_000)
    assert r["deductible"] + r["total_suspended"] == r["allocable_loss"]


def test_the_order_matters_465_applies_to_what_704d_allowed():
    """§465 is measured against what basis already let through, not against the raw
    loss. With basis of $10,000 and $40,000 at risk, basis is the binding constraint and
    the at-risk figure never comes into play."""
    r = calc_loss_limitations(allocable_loss=50_000, outside_basis=10_000,
                              at_risk_amount=40_000, materially_participates=True)
    assert r["after_704d"] == 10_000
    assert r["after_465"] == 10_000, "§465 cannot allow more than §704(d) already did"
    assert r["suspended_465"] == 0
    assert r["deductible"] == 10_000


def test_material_participation_switches_469_off_entirely():
    """§469 only reaches passive activities. A materially participating partner takes
    everything §465 allowed, with no passive income needed."""
    passive = calc_loss_limitations(50_000, 60_000, 60_000, passive_income=0)
    active = calc_loss_limitations(50_000, 60_000, 60_000, materially_participates=True)
    assert passive["deductible"] == 0
    assert passive["suspended_469"] == 50_000
    assert active["deductible"] == 50_000
    assert active["suspended_469"] == 0


def test_nonrecourse_debt_is_where_704d_and_465_diverge():
    """The classic leveraged fact pattern. Ordinary nonrecourse debt creates outside
    basis under §752, so §704(d) is satisfied — but it is not an at-risk amount under
    §465, so the loss stops there anyway."""
    liab = calc_752_shares(recourse=0, nonrecourse=100_000)
    r = calc_loss_limitations(allocable_loss=90_000,
                              outside_basis=20_000 + liab["total"],
                              at_risk_amount=20_000 + liab["at_risk_portion"],
                              materially_participates=True)
    assert r["suspended_704d"] == 0, "nonrecourse debt gives basis"
    assert r["deductible"] == 20_000
    assert r["suspended_465"] == 70_000, "but no at-risk amount"


def test_qualified_nonrecourse_real_estate_financing_is_at_risk():
    """§465(b)(6). Real estate financing from a commercial lender is the exception —
    nonrecourse for state law, but at risk for §465."""
    liab = calc_752_shares(qualified_nonrecourse=100_000)
    assert liab["at_risk_portion"] == 100_000
    assert liab["not_at_risk"] == 0


# ── §705 — outside basis ─────────────────────────────────────────────────────

def test_distributions_are_applied_before_losses():
    """Reg. §1.704-1(d)(2) fixes the order: income up, then distributions down, then
    losses. The distribution consumes basis the loss would otherwise have used.

    Beginning $50,000, a $30,000 distribution and a $40,000 loss. Taking the
    distribution first leaves $20,000 of basis, so only $20,000 of loss is allowed and
    $20,000 is suspended — not the $10,000 that netting them would suggest."""
    r = calc_outside_basis(beginning=50_000, distributions=30_000, losses=40_000)
    assert r["loss_allowed_by_basis"] == 20_000
    assert r["loss_suspended_704d"] == 20_000
    assert r["ending_basis"] == 0


def test_a_distribution_beyond_basis_is_gain_not_negative_basis():
    """§731(a)(1). Outside basis floors at zero; the excess is capital gain."""
    r = calc_outside_basis(beginning=10_000, distributions=25_000)
    assert r["ending_basis"] == 0
    assert r["gain_731a"] == 15_000


def test_a_liability_share_decrease_is_a_deemed_distribution():
    """§752(b). Relief from debt is cash for this purpose, and can trigger §731(a) gain
    without the partner receiving anything."""
    r = calc_outside_basis(beginning=5_000, liability_decrease=20_000)
    assert r["gain_731a"] == 15_000


def test_tax_exempt_income_raises_basis():
    """§705(a)(1)(B). Income that is never taxed still adds basis — otherwise it would
    be taxed later as gain on distribution or sale."""
    r = calc_outside_basis(beginning=10_000, tax_exempt_income=5_000)
    assert r["ending_basis"] == 15_000


def test_nondeductible_expenses_reduce_basis_without_a_deduction():
    """§705(a)(2)(B). Fines and the disallowed half of meals never produce a deduction
    but still consume basis — symmetry with tax-exempt income."""
    r = calc_outside_basis(beginning=10_000, nondeductible=3_000)
    assert r["ending_basis"] == 7_000


# ── §704(b) capital account against outside basis ────────────────────────────

def test_capital_account_and_outside_basis_diverge_on_contributed_property():
    """Contributed property enters the capital account at fair market value and outside
    basis at the contributor's adjusted basis. Land worth $100,000 with a $30,000 basis
    opens a $70,000 gap on day one — which is exactly the §704(c) built-in gain."""
    ob = calc_outside_basis(contributions=30_000)
    ca = calc_capital_account(contributions_fmv=100_000)
    assert ob["ending_basis"] == 30_000
    assert ca["ending"] == 100_000
    assert ca["ending"] - ob["ending_basis"] == 70_000


def test_liabilities_are_in_basis_and_not_in_the_capital_account():
    """The other structural difference. A partner's share of debt is basis under §752
    and is never part of the §704(b) capital account."""
    ob = calc_outside_basis(contributions=10_000, liability_increase=90_000)
    ca = calc_capital_account(contributions_fmv=10_000)
    assert ob["ending_basis"] == 100_000
    assert ca["ending"] == 10_000
