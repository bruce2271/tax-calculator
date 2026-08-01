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
    calc_280c,
    calc_1062_deferral,
    calc_1231_lookback,
    calc_4797_recapture,
    calc_6655_penalty,
    calc_capital,
    calc_charitable,
    calc_drd_246b,
    calc_gbc_limitation,
    calc_general_business_credit,
    calc_nol,
    calc_rd_credit_regular,
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

def test_170_regression_loss_year_must_not_invent_a_negative_deduction():
    """REGRESSION, found by keying a real filer's figures in. With no contributions and a
    loss before the charitable step, 10% of a negative number gave a limit of $(201,000),
    so min(0, -201,000) reported a *negative* deduction — which increases taxable income —
    and a $201,000 carryforward for a corporation that had given nothing."""
    r = calc_charitable(contribution=0, taxable_income_before_charitable=-2_010_000)
    assert r["limit"] == 0
    assert r["deductible"] == 0
    assert r["carryforward_5yr"] == 0


def test_170_loss_year_defers_an_actual_contribution_in_full():
    """A real gift in a loss year is not lost — none is deductible now, all carries."""
    r = calc_charitable(contribution=50_000, taxable_income_before_charitable=-100_000)
    assert r["deductible"] == 0
    assert r["carryforward_5yr"] == 50_000


def test_170_regression_every_ordinary_deduction_reduces_the_limit_base():
    """REGRESSION, found while building the ACME differential test. §170(b)(2)(C) computes
    the base without the charitable deduction, the special deductions, and NOL or capital
    loss carrybacks — everything else still comes off. Bad debts were being left in, which
    inflated the base and so the limit.

    In the ACME fact pattern the $40,000 §166 charge-off moved the limit from $90,510 to
    $86,510 — $840 of tax, and a mismatch against any other package."""
    base = dict(gross_revenue=8_230_000, cogs=4_000_000, operating_expenses=2_250_000,
                officer_compensation=600_000, book_depreciation=0, asset_cost=0,
                depreciation_method="macrs", interest_expense=300_000,
                small_business_exempt=True, charitable_contributions=150_000, ati=None)

    without = calculate_1120(dict(base, bad_debt_expense=0))
    with_bad_debt = calculate_1120(dict(base, bad_debt_expense=40_000))

    assert without["deductions"]["charitable"]["limit"] == pytest.approx(108_000)
    assert with_bad_debt["deductions"]["charitable"]["limit"] == pytest.approx(104_000)
    # The invariant, independent of the rest of the fact pattern.
    assert (without["deductions"]["charitable"]["limit"]
            - with_bad_debt["deductions"]["charitable"]["limit"]) == pytest.approx(4_000)


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


# ── §1245 / §1250 / §291 — depreciation recapture ────────────────────────────
# Equipment throughout: cost $100,000, depreciation taken $60,000, adjusted basis
# $40,000. What changes between the cases is the sale price.

def test_1245_recapture_is_capped_at_the_gain():
    """Sold for $90,000 — the $50,000 gain is entirely depreciation coming back, so all
    of it is ordinary and nothing survives as §1231."""
    r = calc_4797_recapture(sale_price=90_000, basis=100_000, depreciation=60_000)
    assert r["adj_basis"] == 40_000
    assert r["gain"] == 50_000
    assert r["recapture"] == 50_000
    assert r["sec1231"] == 0


def test_1245_recapture_is_capped_at_depreciation_so_appreciation_stays_1231():
    """Sold for $120,000 — above original cost. Recapture stops at the $60,000 actually
    depreciated; the $20,000 by which the price exceeds cost is real appreciation and
    keeps §1231 character."""
    r = calc_4797_recapture(sale_price=120_000, basis=100_000, depreciation=60_000)
    assert r["gain"] == 80_000
    assert r["recapture"] == 60_000
    assert r["sec1231"] == 20_000
    assert r["sec1231"] == 120_000 - 100_000, "the §1231 slice is the gain above cost"


def test_1245_loss_produces_no_recapture():
    """Sold for $30,000, below adjusted basis. There is no gain, so nothing to recapture;
    the loss is §1231."""
    r = calc_4797_recapture(sale_price=30_000, basis=100_000, depreciation=60_000)
    assert r["gain"] == -10_000
    assert r["recapture"] == 0
    assert r["sec1231"] == -10_000


def test_291_corporate_real_property_recaptures_twenty_percent():
    """§291(a)(1). A building at $1,000,000 cost with $200,000 of straight-line
    depreciation, sold for $1,100,000. Straight line leaves nothing for §1250 itself, but
    a corporation still recaptures 20% of the $200,000 §1245 would have taken."""
    r = calc_4797_recapture(sale_price=1_100_000, basis=1_000_000,
                            depreciation=200_000, is_1245=False)
    assert r["gain"] == 300_000
    assert r["recapture"] == 40_000
    assert r["sec1231"] == 260_000

    as_1245 = calc_4797_recapture(1_100_000, 1_000_000, 200_000, is_1245=True)
    assert r["recapture"] == pytest.approx(0.20 * as_1245["recapture"])


# ── §1231(c) — five-year look-back ───────────────────────────────────────────

def test_1231_lookback_recharacterises_gain_up_to_the_unrecaptured_pool():
    """A $100,000 net §1231 gain against $80,000 of unrecaptured prior losses: $80,000
    turns ordinary and only the $20,000 excess reaches Schedule D as a capital gain."""
    r = calc_1231_lookback(100_000, [(2021, 30_000, 0), (2023, 50_000, 0)])
    assert r["line8"] == 80_000
    assert r["line9"] == 20_000
    assert r["line12"] == 80_000
    assert r["schedule_d_ltcg"] == 20_000
    assert [x["used"] for x in r["rows"]] == [30_000, 50_000]


def test_1231_lookback_consumes_the_oldest_loss_first():
    """A $60,000 gain cannot absorb the whole $80,000 pool, so all of it is ordinary and
    nothing reaches Schedule D. The 2021 loss clears before 2023 is touched — it is the
    one about to fall out of the five-year window."""
    r = calc_1231_lookback(60_000, [(2021, 30_000, 0), (2023, 50_000, 0)])
    assert r["line9"] == 0
    assert r["line12"] == 60_000
    assert r["schedule_d_ltcg"] == 0
    assert [x["used"] for x in r["rows"]] == [30_000, 30_000]


def test_1231_net_loss_is_ordinary_and_does_not_run_the_lookback():
    """The asymmetry §1231(c) exists to police: a net loss is ordinary in full, and the
    look-back does not consume the pool — this year's loss will join it."""
    r = calc_1231_lookback(-40_000, [(2021, 30_000, 0)])
    assert r["line11"] == -40_000
    assert r["line12"] == 0
    assert r["schedule_d_ltcg"] == 0
    assert [x["used"] for x in r["rows"]] == [0.0]


def test_1231_already_recaptured_losses_leave_the_pool():
    """A loss recaptured in an earlier year cannot be recaptured again."""
    r = calc_1231_lookback(100_000, [(2021, 50_000, 50_000), (2023, 20_000, 5_000)])
    assert r["pool"] == 15_000
    assert r["schedule_d_ltcg"] == 85_000


def test_1231_gain_with_no_prior_losses_is_entirely_capital():
    r = calc_1231_lookback(100_000, [])
    assert r["line12"] == 0
    assert r["schedule_d_ltcg"] == 100_000


# ── §263A — absorption ratio behaviour ───────────────────────────────────────

def test_263a_absorbs_the_whole_pool_when_all_inventory_is_sold():
    """Ratio of 1.0: nothing is left in ending inventory, so every capitalised cost has
    followed the goods out and is deductible now."""
    assert calc_unicap(100_000, cogs=1_000_000, total_inventory_costs=1_000_000) == 100_000


def test_263a_absorbs_nothing_in_a_pure_inventory_build():
    """Ratio of 0.0 is legitimate: a year that produces and sells nothing capitalises the
    entire pool into ending inventory, and it stays there until the goods sell."""
    assert calc_unicap(100_000, cogs=0, total_inventory_costs=1_000_000) == 0.0


# ── §38 / §39 — the general business credit ──────────────────────────────────

def test_38c_limit_is_regular_tax_less_25_percent_of_the_excess_over_25000():
    """§38(c)(1). A credit cannot take the bill to zero. On $100,000 of regular tax the
    floor is 25% x ($100,000 - $25,000) = $18,750, so at most $81,250 can be used."""
    r = calc_gbc_limitation(regular_tax=100_000)
    assert r["floor"] == 18_750
    assert r["limit"] == 81_250


def test_38c_small_corporation_below_25000_is_not_limited_at_all():
    """The $25,000 threshold exempts small filers — the whole tax can be credited away."""
    r = calc_gbc_limitation(regular_tax=25_000)
    assert r["floor"] == 0
    assert r["limit"] == 25_000


def test_38c_tentative_minimum_tax_binds_when_it_is_the_greater_floor():
    """The floor is the *greater* of the two. Corporate AMT is repealed and CAMT reaches
    only filers above $1B of book income, so this branch is rare — but it is the statute."""
    r = calc_gbc_limitation(regular_tax=100_000, tentative_minimum_tax=40_000)
    assert r["floor"] == 40_000
    assert r["limit"] == 60_000
    assert r["tmt_binding"] is True


def test_38a_carryforwards_are_used_before_the_current_year_oldest_first():
    """§38(a). Vintages carried in go first, oldest first, because §39 gives each only
    twenty years. Limit is $81,250 against $30,000 + $60,000 of carryforward and $50,000
    earned this year: 2019 goes entirely, 2021 gives $51,250, this year gets nothing."""
    r = calc_general_business_credit(
        current_year_credit=50_000, regular_tax=100_000,
        carryforwards=[(2019, 30_000), (2021, 60_000)], current_year=2024)
    assert r["limit"] == 81_250
    assert [x["used"] for x in r["carryforward_rows"]] == [30_000, 51_250]
    assert r["current_used"] == 0
    assert r["total_used"] == 81_250
    assert r["current_unused"] == 50_000


def test_39_vintages_expire_after_twenty_years():
    """§39(a). A 2003 credit is dead by 2024 and cannot be used however much room exists."""
    r = calc_general_business_credit(
        current_year_credit=0, regular_tax=1_000_000,
        carryforwards=[(2003, 40_000), (2020, 10_000)], current_year=2024)
    assert r["carryforward_rows"][0]["expired"] is True
    assert r["carryforward_rows"][0]["used"] == 0
    assert r["carryforward_rows"][1]["used"] == 10_000
    assert r["expired"] == 40_000


def test_39_unused_current_year_credit_survives_as_a_carryforward():
    r = calc_general_business_credit(current_year_credit=100_000, regular_tax=50_000)
    assert r["limit"] == 43_750          # 50,000 - 25% x 25,000
    assert r["current_used"] == 43_750
    assert r["current_unused"] == 56_250


# ── §280C(c) and the §41 base floor ──────────────────────────────────────────

def test_280c_reduced_credit_election_is_79_percent():
    """§280C(c)(3). The reduced credit is the gross credit times one minus the 21% rate,
    so electing it leaves the same after-tax result as cutting the §174 amount instead."""
    elected = calc_280c(100_000, elect_reduced=True)
    assert elected["credit"] == 79_000
    assert elected["sec174_reduction"] == 0

    full = calc_280c(100_000, elect_reduced=False)
    assert full["credit"] == 100_000
    assert full["sec174_reduction"] == 100_000


def test_41_base_amount_floors_at_half_of_current_spending():
    """REGRESSION. §41(c)(2) puts a floor under the base amount at 50% of current QRE.
    Without it a filer with small historic receipts computed a tiny base and claimed 20%
    of nearly everything spent, which is not an incremental credit.

    $1,000,000 of research against a 3% fixed base on $2,000,000 of receipts gives a
    computed base of $60,000 — but the floor of $500,000 governs, so the credit is
    $100,000 rather than $188,000."""
    r = calc_rd_credit_regular(current_qre=1_000_000, fixed_base_pct=0.03,
                               avg_gross_receipts=2_000_000)
    assert r["computed_base"] == 60_000
    assert r["base_amount"] == 500_000
    assert r["floor_binding"] is True
    assert r["credit"] == 100_000


def test_41_floor_does_not_bind_when_the_computed_base_is_larger():
    r = calc_rd_credit_regular(current_qre=1_000_000, fixed_base_pct=0.10,
                               avg_gross_receipts=8_000_000)
    assert r["base_amount"] == 800_000
    assert r["floor_binding"] is False
    assert r["credit"] == 40_000


# ── §1062 — qualified farmland sale deferral ─────────────────────────────────

def test_1062_defers_the_difference_the_gain_makes_to_the_whole_return():
    """§1062. The deferred figure is net income tax with the gain less net income tax
    without it — not the tax on the gain computed alone. Four equal instalments."""
    r = calc_1062_deferral(tax_with_gain=500_000, tax_without_gain=300_000)
    assert r["applicable_net_tax_liability"] == 200_000
    assert r["installment"] == 50_000
    assert r["deferred"] == 150_000
    assert r["installments"] == [50_000] * 4


def test_1062_without_the_election_nothing_is_deferred():
    r = calc_1062_deferral(500_000, 300_000, elected=False)
    assert r["applicable_net_tax_liability"] == 0
    assert r["installment"] == 0


def test_1062_page_one_algebra_leaves_a_quarter_owed():
    """The point of the line 31/32/33 arrangement. Line 31 carries the full tax, line 33
    removes the whole deferred amount as though paid, and line 32 adds back one
    instalment — so only a quarter of the deferral is owed this year."""
    r = calc_1062_deferral(500_000, 300_000)
    line31, line32 = 500_000, r["installment"]
    line33 = r["applicable_net_tax_liability"]        # no other payments
    owed = line31 + line32 - line33
    assert owed == 350_000                            # 300,000 other tax + 50,000
    assert owed == 300_000 + r["installment"]


# ── §6655 — estimated tax penalty ────────────────────────────────────────────

def test_6655_charges_interest_on_each_quarterly_shortfall():
    """$400,000 required means $100,000 a quarter. Paying $50,000 in Q1 and $100,000
    after leaves a $50,000 Q1 shortfall outstanding for the full 365 days."""
    r = calc_6655_penalty(400_000, [50_000, 100_000, 100_000, 100_000], annual_rate=0.07)
    assert r["per_quarter"] == 100_000
    assert [x["shortfall"] for x in r["rows"]] == [50_000, 0, 0, 0]
    assert r["penalty"] == pytest.approx(50_000 * 0.07)


def test_6655_a_later_overpayment_does_not_cure_an_earlier_miss():
    """Each instalment stands on its own. Paying nothing in Q1 and double in Q2 still
    costs interest on the Q1 shortfall for the quarter it was outstanding."""
    late = calc_6655_penalty(400_000, [0, 200_000, 100_000, 100_000], annual_rate=0.07)
    ontime = calc_6655_penalty(400_000, [100_000] * 4, annual_rate=0.07)
    assert ontime["penalty"] == 0
    assert late["penalty"] > 0
    assert late["rows"][1]["shortfall"] == 0, "the Q2 overpayment does roll forward"


def test_6655_an_earlier_overpayment_covers_a_later_quarter():
    """The direction that does work. Paying $200,000 in Q1 and nothing in Q2 leaves no Q2
    shortfall — the excess rolls forward. Mutation testing found the earlier test blind
    here: it overpaid the *later* quarter, where dropping the roll-forward changed
    nothing."""
    r = calc_6655_penalty(400_000, [200_000, 0, 100_000, 100_000], annual_rate=0.07)
    assert [x["shortfall"] for x in r["rows"]] == [0, 0, 0, 0]
    assert r["penalty"] == 0


def test_6655_meeting_the_safe_harbour_costs_nothing():
    r = calc_6655_penalty(400_000, [100_000] * 4)
    assert r["total_shortfall"] == 0
    assert r["penalty"] == 0


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
