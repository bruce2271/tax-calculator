"""Correctness tests for the Form 1120 tax engine.

Two kinds of test live here and the distinction matters:

  * Tests marked IRS Pub 542 reproduce a worked example published by the IRS. The
    expected figure is the Service's own answer, not an answer this project chose.
  * Tests marked REGRESSION pin a bug that actually shipped in this project and was
    fixed. Each one states what went wrong, because a test whose purpose is forgotten
    gets "fixed" by deleting it.
"""

import pytest

from calculators.form_1120 import (
    calc_163j,
    calc_capital,
    calc_charitable,
    calc_drd_246b,
    calc_nol,
    calc_unicap,
    calculate_1120,
)


# ── §1211 / §1212 — capital losses ───────────────────────────────────────────
# IRS Pub 542, "Capital Losses": a corporation with a $3,000 net short-term capital
# gain and a $9,000 net long-term capital loss has a $6,000 net capital loss, which it
# carries back three years. In the carryback year it had $8,000 net short-term and
# $5,000 net long-term gain; the carryover is applied against the short-term gain
# first, leaving a $7,000 net capital gain.

def test_1211_capital_loss_cannot_offset_ordinary_income():
    """IRS Pub 542. A net capital loss contributes nothing to income — it may only
    offset capital gains (§1211(a))."""
    r = calc_capital(short_term_gain=3_000, long_term_gain=-9_000)
    assert r["net_capital_gain"] == 0
    assert r["capital_loss_carryforward"] == 6_000


def test_1212_carryover_absorbed_in_the_receiving_year():
    """IRS Pub 542. $8,000 + $5,000 of gain absorbs the $6,000 carryover, leaving
    $7,000 of net capital gain."""
    r = calc_capital(short_term_gain=8_000, long_term_gain=5_000,
                     capital_loss_carryforward=6_000)
    assert r["net_capital_gain"] == 7_000
    assert r["capital_loss_carryforward"] == 0


def test_1211_regression_loss_year_reports_zero_not_negative():
    """REGRESSION. Total income once used the raw net capital figure, so a capital loss
    reduced ordinary income. Taxable income came out $40,000 instead of $70,000."""
    r = calc_capital(short_term_gain=0, long_term_gain=-30_000)
    assert r["net_capital_gain"] == 0, "a capital loss must never reduce ordinary income"


# ── §243 / §246(b) — dividends-received deduction ────────────────────────────
# IRS Pub 542, "Dividends-Received Deduction": both examples use $100,000 of dividends
# from a 20%-owned corporation, so the rate is 65%.

def test_246b_limit_applies_when_no_nol_results():
    """IRS Pub 542 Example 2. A $30,000 operating loss leaves $70,000 of taxable income
    before the deduction. The full $65,000 would leave $5,000 of income — no NOL — so
    the limit bites: 65% x $70,000 = $45,500."""
    r = calc_drd_246b(divs=100_000, ownership_pct=20, taxable_inc_before_drd=70_000)
    assert r["rate"] == 0.65
    assert r["allowed"] == 45_500
    assert r["nol_rule"] is False


def test_246b_limit_switched_off_when_full_drd_creates_an_nol():
    """IRS Pub 542 Example 1 — the trap. A $75,000 operating loss leaves $25,000 of
    taxable income. The full $65,000 deduction produces a $(40,000) NOL, so §246(b)(2)
    turns the limit off and the whole $65,000 is allowed — more than the $16,250 the
    limit alone would have given."""
    r = calc_drd_246b(divs=100_000, ownership_pct=20, taxable_inc_before_drd=25_000)
    assert r["nol_rule"] is True
    assert r["allowed"] == 65_000
    assert r["allowed"] > r["step2"], "the NOL exception must beat the limited amount"


@pytest.mark.parametrize("pct,rate", [(0, 0.50), (19, 0.50), (20, 0.65), (79, 0.65),
                                      (80, 1.00), (100, 1.00)])
def test_243_rate_brackets(pct, rate):
    """§243(a). The brackets turn at 20% and 80% ownership."""
    assert calc_drd_246b(100_000, pct, 10_000_000)["rate"] == rate


# ── §172 — net operating losses ──────────────────────────────────────────────

def test_172_post_2017_nol_capped_at_80_percent():
    """§172(a). A 2018-or-later NOL cannot wipe out taxable income; 80% is the ceiling."""
    r = calc_nol(taxable_income_before_nol=500_000, nol_carryforward=900_000)
    assert r["nol_used"] == 400_000
    assert r["taxable_income"] == 100_000
    assert r["remaining_carryforward"] == 500_000


def test_172_pre_2018_vintage_offsets_everything_before_the_80_percent_pool():
    """§172 as amended. Pre-2018 tranches are used first and are not subject to the 80%
    limit; the post-2017 pool is then capped at 80% of what is left.

    $300,000 pre-2018 absorbs $300,000 of the $500,000, and the remaining $200,000 is
    reduced by at most 80% x $200,000 = $160,000."""
    r = calc_nol(taxable_income_before_nol=500_000, nol_carryforward=900_000,
                 pre2018_carryforward=300_000)
    assert r["pre2018_used"] == 300_000
    assert r["post2017_used"] == 160_000
    assert r["nol_used"] == 460_000
    assert r["taxable_income"] == 40_000


def test_172_pre_2018_vintage_can_eliminate_taxable_income_entirely():
    """§172 as amended — the point of tracking vintage at all.

    A pre-2018 tranche large enough to cover the whole year wipes taxable income out.
    A 2018-or-later tranche of the same size could only reach 80%, leaving $100,000.
    Mutation testing found the earlier test blind here: its pre-2018 pool was smaller
    than 80% of taxable income, so capping it changed nothing."""
    pre = calc_nol(taxable_income_before_nol=500_000, nol_carryforward=0,
                   pre2018_carryforward=500_000)
    assert pre["nol_used"] == 500_000
    assert pre["taxable_income"] == 0

    post = calc_nol(taxable_income_before_nol=500_000, nol_carryforward=500_000)
    assert post["taxable_income"] == 100_000, "a 2018+ NOL can never reach zero"


def test_172_loss_year_generates_a_carryforward():
    r = calc_nol(taxable_income_before_nol=-250_000, nol_carryforward=0)
    assert r["new_nol_generated"] == 250_000
    assert r["taxable_income"] == 0


# ── §163(j) — business interest ──────────────────────────────────────────────

def test_163j_limit_is_30_percent_of_ati_with_indefinite_carryforward():
    r = calc_163j(interest_expense=500_000, ati=1_000_000)
    assert r["ati_limit"] == 300_000
    assert r["deductible"] == 300_000
    assert r["excess_carryforward"] == 200_000


def test_163j_small_business_is_outside_the_limitation_entirely():
    """§163(j)(3). Under the §448(c) threshold the limit does not apply at all — not a
    larger limit, no limit."""
    r = calc_163j(interest_expense=500_000, ati=0, exempt=True)
    assert r["deductible"] == 500_000
    assert r["excess_carryforward"] == 0


# ── §170(b)(2) — charitable contributions ────────────────────────────────────

def test_170_ten_percent_limit_and_five_year_carryforward():
    r = calc_charitable(contribution=90_000, taxable_income_before_charitable=500_000)
    assert r["limit"] == 50_000
    assert r["deductible"] == 50_000
    assert r["carryforward_5yr"] == 40_000


# ── §263A — UNICAP ───────────────────────────────────────────────────────────

def test_263a_absorption_ratio():
    """Simplified absorption method: the share of the indirect-cost pool that follows
    goods actually sold. $700k of $1,000k left inventory, so 70% is absorbed."""
    assert calc_unicap(indirect_costs=100_000, cogs=700_000,
                       total_inventory_costs=1_000_000) == 70_000


def test_263a_regression_capitalised_costs_must_not_vanish():
    """REGRESSION — the worst bug this project shipped. Costs were stripped out of
    lines 12-20 and handed to calc_unicap, but cogs and total_inventory_costs were both
    still zero, so the ratio was zero and the whole pool evaporated: $1.6M left the
    return without appearing anywhere. Guard the degenerate input."""
    assert calc_unicap(1_600_030, 0, 0) == 0.0, "documents the failing shape"
    assert calc_unicap(1_600_030, 700_000, 1_000_000) > 0, \
        "with a real inventory pool the costs must reach COGS"


# ── calculate_1120 — the whole return ────────────────────────────────────────

def _inputs(**over):
    base = dict(gross_revenue=5_000_000, cogs=0, operating_expenses=0,
                dividends_received=0, ownership_pct=0, meals_entertainment=0,
                interest_expense=0, charitable_contributions=0,
                officer_compensation=0, book_depreciation=0, asset_cost=0,
                depreciation_method="macrs", nol_carryforward=0, ati=None)
    base.update(over)
    return base


def test_1120_regression_ati_none_must_not_crash():
    """REGRESSION. `ati` was present in the dict but set to None, so `.get('ati', 0)`
    returned None rather than the default and the 30% multiplication raised TypeError,
    taking out the whole Results Summary page."""
    r = calculate_1120(_inputs(interest_expense=100_000))
    assert r["deductions"]["interest"]["deductible"] >= 0


def test_1120_regression_dividends_belong_in_total_income():
    """REGRESSION. The DRD was deducted while the gross dividend was never added to
    total income, understating taxable income by the full dividend."""
    without = calculate_1120(_inputs())
    with_divs = calculate_1120(_inputs(dividends_and_inclusions=200_000))
    assert with_divs["income"]["total_income"] - without["income"]["total_income"] == 200_000


def test_1120_taxable_income_flows_to_tax_at_21_percent():
    r = calculate_1120(_inputs(operating_expenses=1_000_000))
    ti = r["taxable_income"]["taxable_income"]
    assert ti == 4_000_000
    assert r["tax"]["regular_tax"] == pytest.approx(ti * 0.21)


def test_1120_nol_deduction_reaches_the_return():
    r = calculate_1120(_inputs(operating_expenses=4_500_000, nol_carryforward=1_000_000))
    # Line 28 is 500,000; the 80% cap allows 400,000.
    assert r["taxable_income"]["before_nol"] == 500_000
    assert r["taxable_income"]["nol"]["nol_used"] == 400_000
    assert r["taxable_income"]["taxable_income"] == 100_000
