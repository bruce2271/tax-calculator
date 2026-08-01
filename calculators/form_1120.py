"""
Form 1120 — U.S. Corporate Income Tax Calculator
Covers: Income, Deductions, §263A, §163(j), §162(m), Charitable, Bad Debt,
        Capital Gains/Losses, NOL, Depreciation (§179/Bonus/MACRS/Cost Seg),
        Regular Tax, CAMT, BEAT, Credits, Texas Franchise Tax, M-1 Reconciliation
"""

# ── MACRS Tables ──────────────────────────────────────────────────────────────
# Half-year convention rates (GDS)
MACRS_HALFYEAR = {
    5:  [0.2000, 0.3200, 0.1920, 0.1152, 0.1152, 0.0576],
    7:  [0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446],
    15: [0.0500, 0.0950, 0.0855, 0.0770, 0.0693, 0.0623, 0.0590, 0.0590,
         0.0591, 0.0590, 0.0591, 0.0590, 0.0591, 0.0590, 0.0591, 0.0295],
    39: None,  # handled separately (mid-month, straight-line)
}

BONUS_RATES = {2023: 0.80, 2024: 0.60, 2025: 0.40, 2026: 0.20, 2027: 0.0}

SECTION_179_LIMIT = 1_285_000
SECTION_179_PHASEOUT_START = 3_220_000

COST_SEG_SPLITS = {
    "5yr_personal":  0.175,  # midpoint of 15-20%
    "7yr_personal":  0.225,  # midpoint of 20-25%
    "15yr_land_imp": 0.125,  # midpoint of 10-15%
    # remainder → 39yr building
}


# ── Depreciation ──────────────────────────────────────────────────────────────

def calc_section_179(cost: float, total_placed_in_service: float) -> dict:
    limit = SECTION_179_LIMIT
    phaseout_excess = max(0, total_placed_in_service - SECTION_179_PHASEOUT_START)
    effective_limit = max(0, limit - phaseout_excess)
    deduction = min(cost, effective_limit)
    return {
        "deduction": deduction,
        "effective_limit": effective_limit,
        "phaseout_reduction": phaseout_excess,
    }


def calc_bonus(cost: float, year: int) -> dict:
    rate = BONUS_RATES.get(year, 0.0)
    deduction = cost * rate
    return {"deduction": deduction, "rate": rate, "remaining_basis": cost - deduction}


def calc_macrs(cost: float, life: int, year_placed: int, tax_year: int,
               convention: str = "half_year") -> dict:
    if life == 39:
        # Mid-month straight-line: first year = (months in service) / 12 / 39
        months = 6.5  # assume mid-year placement
        deduction = cost * (months / 12) / 39
        return {"deduction": deduction, "method": "SL 39yr mid-month"}
    rates = MACRS_HALFYEAR.get(life, [])
    yr_idx = tax_year - year_placed
    if yr_idx < 0 or yr_idx >= len(rates):
        return {"deduction": 0.0, "method": f"MACRS {life}yr"}
    deduction = cost * rates[yr_idx]
    return {"deduction": deduction, "method": f"MACRS {life}yr half-year"}


def calc_cost_segregation(building_cost: float, year: int, tax_year: int) -> dict:
    splits = {}
    total_deduction = 0.0
    bonus_rate = BONUS_RATES.get(year, 0.0)

    for label, pct in COST_SEG_SPLITS.items():
        amt = building_cost * pct
        life = int(label.split("yr")[0])
        bonus_dep = amt * bonus_rate
        remaining = amt - bonus_dep
        macrs_yr1 = remaining * MACRS_HALFYEAR[life][0] if life in MACRS_HALFYEAR and MACRS_HALFYEAR[life] else 0
        yr_dep = bonus_dep + macrs_yr1 if tax_year == year else 0
        splits[label] = {"amount": amt, "depreciation": yr_dep}
        total_deduction += yr_dep

    building_pct = 1 - sum(COST_SEG_SPLITS.values())
    building_amt = building_cost * building_pct
    building_dep = building_amt * (6.5 / 12) / 39
    splits["39yr_building"] = {"amount": building_amt, "depreciation": building_dep}
    total_deduction += building_dep

    no_seg_dep = building_cost * (6.5 / 12) / 39
    return {
        "splits": splits,
        "total_depreciation": total_deduction,
        "no_seg_depreciation": no_seg_dep,
        "tax_savings_vs_no_seg": (total_deduction - no_seg_dep) * 0.21,
    }


# ── §263A UNICAP ──────────────────────────────────────────────────────────────

def calc_unicap(indirect_costs: float, cogs: float, total_inventory_costs: float) -> float:
    """Simplified absorption ratio method."""
    if total_inventory_costs == 0:
        return 0.0
    ratio = cogs / total_inventory_costs
    return indirect_costs * ratio


# ── §163(j) Interest Expense Limitation ──────────────────────────────────────

def calc_163j(interest_expense: float, ati: float,
              carryforward: float = 0.0, exempt: bool = False) -> dict:
    """§163(j)(3): a taxpayer under the §448(c) gross receipts threshold is outside the
    limitation entirely, so all business interest stays deductible."""
    total = interest_expense + carryforward
    if exempt:
        return {"deductible": total, "excess_carryforward": 0.0,
                "ati_limit": total, "exempt": True}
    limit = max(0, ati * 0.30)
    deductible = min(total, limit)
    excess = max(0, total - limit)
    return {
        "deductible": deductible,
        "excess_carryforward": excess,
        "ati_limit": limit,
        "exempt": False,
    }


# ── Charitable Contributions ──────────────────────────────────────────────────

def calc_charitable(contribution: float, taxable_income_before_charitable: float) -> dict:
    """§170(b)(2). The limit floors at zero: in a loss year 10% of a negative figure is
    negative, which would otherwise produce a negative "deduction" that increases
    taxable income and conjures a carryforward out of a corporation that gave nothing."""
    limit = max(0.0, taxable_income_before_charitable * 0.10)
    deductible = min(contribution, limit)
    carryforward = max(0, contribution - deductible)
    return {"deductible": deductible, "carryforward_5yr": carryforward, "limit": limit}


# ── Form 4797 — depreciation recapture and the §1231 look-back ───────────────

def calc_4797_recapture(sale_price: float, basis: float, depreciation: float,
                        is_1245: bool = True) -> dict:
    """Form 4797 Part III. Recapture converts part of the gain from §1231 (capital
    treatment if it survives the look-back) into ordinary income.

    §1245 personal property recaptures the depreciation actually taken, capped at the
    gain — so gain above original cost stays §1231 and is never recaptured.

    §1250 real property held by a *corporation* is different. Straight-line depreciation
    leaves no additional depreciation for §1250 itself, but §291(a)(1) still recaptures
    20% of what §1245 would have taken. That 20% is a corporate-only rule; an individual
    selling the same building recaptures nothing here."""
    adj_basis = basis - depreciation
    gain = sale_price - adj_basis
    if gain <= 0:
        recapture = 0.0
    elif is_1245:
        recapture = min(gain, depreciation)
    else:
        recapture = 0.20 * min(gain, depreciation)
    return {"adj_basis": adj_basis, "gain": gain,
            "recapture": recapture, "sec1231": gain - recapture}


def calc_1231_lookback(net_1231: float, prior_losses) -> dict:
    """§1231(c). A net §1231 gain is ordinary income to the extent of net §1231 losses
    deducted in the five preceding years that have not already been recaptured.

    The asymmetry is the point of the section: a net §1231 loss is fully ordinary, while
    a net gain is capital. Without the look-back a taxpayer could alternate loss and gain
    years and take an ordinary deduction against a capital gain every time.

    `prior_losses` is an iterable of (year, loss, already_recaptured), oldest first.
    Line numbers below are Form 4797 Part I."""
    rows, pool = [], 0.0
    for year, loss, prior in prior_losses:
        avail = max(0.0, loss - prior)
        rows.append({"year": year, "loss": loss, "prior": prior,
                     "avail": avail, "used": 0.0})
        pool += avail

    if net_1231 <= 0:
        # A net loss is ordinary in full and leaves the look-back pool alone — it will
        # instead join the pool for the next five years.
        return {"pool": pool, "line8": 0.0, "line9": 0.0, "line11": net_1231,
                "line12": 0.0, "schedule_d_ltcg": 0.0, "rows": rows}

    line8 = pool
    remaining = net_1231
    for r in rows:                      # oldest first, so the oldest losses clear first
        r["used"] = min(r["avail"], remaining)
        remaining -= r["used"]
    line9 = max(0.0, net_1231 - line8)
    if line9 == 0:
        line12, schedule_d = net_1231, 0.0      # the whole gain is recaptured as ordinary
    else:
        line12, schedule_d = line8, line9       # pool ordinary, the excess is a LTCG
    return {"pool": pool, "line8": line8, "line9": line9, "line11": 0.0,
            "line12": line12, "schedule_d_ltcg": schedule_d, "rows": rows}


# ── Capital Gains / Losses ────────────────────────────────────────────────────

def calc_drd_246b(divs: float, ownership_pct: float,
                  taxable_inc_before_drd: float) -> dict:
    """§243 rate with the §246(b) taxable-income limit.

    The limit is switched off when the full deduction creates or increases a net
    operating loss (§246(b)(2)) — the classic trap, since the limited deduction
    would otherwise be larger than the one the statute actually allows."""
    if ownership_pct < 20:
        rate, label = 0.50, "50% — Less than 20% ownership (§243(a)(1))"
    elif ownership_pct < 80:
        rate, label = 0.65, "65% — 20–79% ownership (§243(a)(2))"
    else:
        rate, label = 1.00, "100% — 80%+ ownership, affiliated group (§243(a)(3))"
    step1 = divs * rate
    step2 = taxable_inc_before_drd * rate
    nol_rule = (taxable_inc_before_drd - step1) < 0
    allowed = step1 if nol_rule else min(step1, step2)
    note = ("NOL rule applies — Step 1 used (full DRD despite taxable income limit)"
            if nol_rule else
            f"Limited by {'Step 1 (dividends)' if step1 <= step2 else 'Step 2 (taxable income)'}")
    return {"rate": rate, "label": label, "step1": step1, "step2": step2,
            "nol_rule": nol_rule, "allowed": allowed, "note": note}


def calc_capital(short_term_gain: float, long_term_gain: float,
                 capital_loss_carryforward: float = 0.0) -> dict:
    net_gain = short_term_gain + long_term_gain - capital_loss_carryforward
    # C-corp: capital losses can only offset capital gains; taxed at ordinary rate
    includable = max(0, net_gain)
    new_carryforward = abs(min(0, net_gain))
    return {
        "net_capital_gain": includable,
        "capital_loss_carryforward": new_carryforward,
        "note": "C-corp capital gains taxed at ordinary 21% rate",
    }


# ── DRD ──────────────────────────────────────────────────────────────────────

def calc_drd(dividends: float, ownership_pct: float) -> dict:
    if ownership_pct < 0.20:
        rate, label = 0.50, "50% (< 20% ownership)"
    elif ownership_pct < 0.80:
        rate, label = 0.65, "65% (20–79% ownership)"
    else:
        rate, label = 1.00, "100% (≥ 80% ownership, affiliated group)"
    deduction = dividends * rate
    return {"deduction": deduction, "rate": rate, "label": label}


# ── §41 R&D Credit ────────────────────────────────────────────────────────────

def calc_rd_credit_asc(current_qre: float, avg_prior_3yr_qre: float) -> dict:
    if avg_prior_3yr_qre == 0:
        credit = current_qre * 0.06
        method = "ASC (no history) — 6%"
    else:
        credit = max(0, current_qre - 0.50 * avg_prior_3yr_qre) * 0.14
        method = "ASC — 14%"
    return {"credit": credit, "method": method}


def calc_rd_credit_regular(current_qre: float, fixed_base_pct: float,
                            avg_gross_receipts: float) -> dict:
    """§41(a)(1). 20% of qualified research spending above a base amount.

    §41(c)(2) puts a floor under that base: it can never be less than half of the
    current year's spending. Without the floor a company with small historic receipts
    would compute a tiny base and claim 20% of nearly everything it spent, which is not
    what an *incremental* credit is for."""
    fixed_base_pct = min(max(fixed_base_pct, 0.03), 0.16)
    computed_base = fixed_base_pct * avg_gross_receipts
    floor = 0.50 * current_qre
    base_amount = max(computed_base, floor)
    credit = max(0, current_qre - base_amount) * 0.20
    return {"credit": credit, "base_amount": base_amount,
            "computed_base": computed_base, "floor": floor,
            "floor_binding": floor > computed_base,
            "fixed_base_pct": fixed_base_pct}


def calc_280c(gross_credit: float, elect_reduced: bool = True,
              tax_rate: float = 0.21) -> dict:
    """§280C(c). The same research spending cannot both earn a credit and be deducted
    in full — that would subsidise it twice. Two ways to settle up:

      * reduce the amount capitalised under §174 by the credit, keeping the full credit
      * elect the reduced credit, which is the gross credit times (1 - 21%)

    The 79% is one minus the corporate rate, chosen so the two routes leave the same
    after-tax result and the election is genuinely neutral. Most filers elect it because
    it keeps the §174 pool untouched."""
    if elect_reduced:
        return {"credit": gross_credit * (1 - tax_rate),
                "sec174_reduction": 0.0, "elected": True,
                "note": f"Reduced credit elected — {1 - tax_rate:.0%} of the gross credit"}
    return {"credit": gross_credit, "sec174_reduction": gross_credit, "elected": False,
            "note": "Full credit taken; the §174 capitalised amount is reduced by it"}


def calc_gbc_limitation(regular_tax: float,
                        tentative_minimum_tax: float = 0.0) -> dict:
    """§38(c)(1). The general business credit cannot wipe out a tax bill entirely.

    It is capped at net income tax less the greater of the tentative minimum tax or 25%
    of regular tax above $25,000. Corporate AMT was repealed for 2018 onward and the
    replacement CAMT only reaches filers above $1B of book income, so for almost every
    corporation the tentative minimum tax is zero and the 25% rule binds.

    The $25,000 threshold means a small corporation is not limited at all."""
    twenty_five_pct_rule = 0.25 * max(0.0, regular_tax - 25_000)
    floor = max(tentative_minimum_tax, twenty_five_pct_rule)
    return {"limit": max(0.0, regular_tax - floor), "floor": floor,
            "twenty_five_pct_rule": twenty_five_pct_rule,
            "tmt_binding": tentative_minimum_tax > twenty_five_pct_rule}


def calc_general_business_credit(current_year_credit: float, regular_tax: float,
                                 carryforwards=(), tentative_minimum_tax: float = 0.0,
                                 current_year: int = 0) -> dict:
    """§38 and §39. Applies the §38(c) limit to the pool of available credits and splits
    what is left into carryforwards.

    §38(a) sets the order: amounts carried forward into this year are used first, oldest
    first, then the current year's credit. Using the oldest first matters because §39
    gives each vintage only twenty years before it expires unused.

    `carryforwards` is an iterable of (year, amount), oldest first.
    """
    lim = calc_gbc_limitation(regular_tax, tentative_minimum_tax)
    remaining = lim["limit"]

    rows = []
    for year, amount in carryforwards:
        expires_after = year + 20
        expired = current_year and expires_after < current_year
        available = 0.0 if expired else amount
        used = min(available, remaining)
        remaining -= used
        rows.append({"year": year, "amount": amount, "expired": bool(expired),
                     "expires_after": expires_after, "used": used,
                     "remaining": amount - used})

    current_used = min(current_year_credit, remaining)
    total_used = sum(r["used"] for r in rows) + current_used
    return {
        "limit": lim["limit"], "floor": lim["floor"],
        "tmt_binding": lim["tmt_binding"],
        "carryforward_rows": rows,
        "carryforward_used": sum(r["used"] for r in rows),
        "current_used": current_used,
        "total_used": total_used,
        # §39: one year back, twenty forward. Unused current-year credit becomes this
        # year's vintage; unused prior vintages keep their own clocks.
        "current_unused": current_year_credit - current_used,
        "prior_unused": sum(r["remaining"] for r in rows if not r["expired"]),
        "expired": sum(r["amount"] for r in rows if r["expired"]),
    }


# ── NOL ───────────────────────────────────────────────────────────────────────

def calc_nol(taxable_income_before_nol: float, nol_carryforward: float,
             pre2018_carryforward: float = 0.0) -> dict:
    """§172. Pre-2018 vintages offset 100% of taxable income and are used first;
    post-2017 vintages are then capped at 80% of what remains."""
    if pre2018_carryforward > 0:
        base = max(0.0, taxable_income_before_nol)
        pre_used = min(pre2018_carryforward, base)
        remaining = base - pre_used
        post_used = min(nol_carryforward, remaining * 0.80)
        used = pre_used + post_used
        taxable_income = max(0.0, taxable_income_before_nol - used)
        new_nol = abs(min(0.0, taxable_income_before_nol))
        return {
            "nol_used": used,
            "pre2018_used": pre_used,
            "post2017_used": post_used,
            "taxable_income": taxable_income,
            "remaining_carryforward": (pre2018_carryforward - pre_used)
                                      + (nol_carryforward - post_used),
            "new_nol_generated": new_nol,
        }
    return _calc_nol_post2017_only(taxable_income_before_nol, nol_carryforward)


def _calc_nol_post2017_only(taxable_income_before_nol: float, nol_carryforward: float) -> dict:
    if taxable_income_before_nol <= 0:
        new_nol = abs(taxable_income_before_nol)
        return {"nol_used": 0.0, "taxable_income": 0.0,
                "new_nol_generated": new_nol, "remaining_carryforward": nol_carryforward}
    limit = taxable_income_before_nol * 0.80
    nol_used = min(nol_carryforward, limit)
    taxable_income = taxable_income_before_nol - nol_used
    return {
        "nol_used": nol_used,
        "taxable_income": taxable_income,
        "remaining_carryforward": nol_carryforward - nol_used,
        "new_nol_generated": 0.0,
    }


# ── CAMT ─────────────────────────────────────────────────────────────────────

def calc_camt(afsi: float, regular_tax: float, avg_afsi_3yr: float) -> dict:
    if avg_afsi_3yr < 1_000_000_000:
        return {"applies": False, "camt": 0.0, "note": "Below $1B AFSI threshold"}
    tentative = afsi * 0.15
    camt = max(0, tentative - regular_tax)
    return {"applies": True, "tentative_minimum_tax": tentative,
            "camt": camt, "regular_tax": regular_tax}


# ── BEAT ─────────────────────────────────────────────────────────────────────

def calc_beat(gross_receipts_3yr_avg: float, base_erosion_payments: float,
              total_deductions: float, regular_tax: float,
              modified_taxable_income: float, year: int = 2025) -> dict:
    if gross_receipts_3yr_avg < 500_000_000:
        return {"applies": False, "beat": 0.0, "note": "Below $500M gross receipts threshold"}
    base_erosion_pct = base_erosion_payments / total_deductions if total_deductions else 0
    if base_erosion_pct < 0.03:
        return {"applies": False, "beat": 0.0,
                "note": f"Base erosion % ({base_erosion_pct:.1%}) below 3% threshold"}
    rate = 0.10 if year <= 2025 else 0.125
    tentative = modified_taxable_income * rate
    beat = max(0, tentative - regular_tax)
    return {"applies": True, "base_erosion_pct": base_erosion_pct,
            "tentative_beat": tentative, "beat": beat, "rate": rate}


# ── Texas Franchise Tax ───────────────────────────────────────────────────────

def calc_texas_franchise(revenue: float, cogs: float, compensation: float) -> dict:
    method_a = revenue * 0.70
    method_b = revenue - cogs
    method_c = revenue - compensation
    method_d = revenue * 0.35
    taxable_margin = min(revenue, max(method_a, min(method_b, method_c, method_d)))
    # EZ computation: 0.331% of revenue (for most manufacturers)
    tax_standard = taxable_margin * 0.01  # 1% standard rate (non-retail)
    tax_ez = revenue * 0.00331
    return {
        "method_a_70pct": method_a,
        "method_b_rev_cogs": method_b,
        "method_c_rev_comp": method_c,
        "method_d_35pct": method_d,
        "taxable_margin": taxable_margin,
        "tax_standard_1pct": tax_standard,
        "tax_ez_0331pct": tax_ez,
        "recommended": min(tax_standard, tax_ez),
    }


# ── Main Calculator ───────────────────────────────────────────────────────────

def calculate_1120(inputs: dict) -> dict:
    # ── Income ────────────────────────────────────────────────────────────────
    gross_revenue = inputs.get("gross_revenue", 0)
    other_income = inputs.get("other_income", 0)
    capital = calc_capital(
        inputs.get("short_term_capital_gain", 0),
        inputs.get("long_term_capital_gain", 0),
        inputs.get("capital_loss_carryforward", 0),
    )
    # Schedule C line 23 (gross dividends and inclusions) is part of income. The DRD is a
    # special deduction taken later at line 29b, never netted against income here.
    dividends_and_inclusions = inputs.get("dividends_and_inclusions",
                                          inputs.get("dividends_received", 0))
    total_income = (gross_revenue + other_income + capital["net_capital_gain"]
                    + dividends_and_inclusions)

    # ── Deductions ────────────────────────────────────────────────────────────
    cogs_raw = inputs.get("cogs", 0)
    unicap_adj = calc_unicap(
        inputs.get("indirect_costs", 0),
        cogs_raw,
        inputs.get("total_inventory_costs", cogs_raw),
    )
    cogs = cogs_raw + unicap_adj

    # Depreciation
    dep_method = inputs.get("depreciation_method", "macrs")
    depreciation = 0.0
    cost_seg_result = None
    if dep_method == "179":
        r = calc_section_179(inputs.get("asset_cost", 0),
                             inputs.get("total_placed_in_service", inputs.get("asset_cost", 0)))
        depreciation = r["deduction"]
    elif dep_method == "bonus":
        r = calc_bonus(inputs.get("asset_cost", 0), inputs.get("tax_year", 2025))
        depreciation = r["deduction"]
    elif dep_method == "macrs":
        r = calc_macrs(inputs.get("asset_cost", 0),
                       inputs.get("macrs_life", 7),
                       inputs.get("year_placed", inputs.get("tax_year", 2025)),
                       inputs.get("tax_year", 2025))
        depreciation = r["deduction"]
    elif dep_method == "cost_seg":
        cost_seg_result = calc_cost_segregation(
            inputs.get("asset_cost", 0),
            inputs.get("year_placed", inputs.get("tax_year", 2025)),
            inputs.get("tax_year", 2025),
        )
        depreciation = cost_seg_result["total_depreciation"]

    # §263A: depreciation on production assets is an indirect production cost. The slice
    # the caller has capitalised leaves the deduction and joins the inventory pool that
    # arrives separately as indirect_costs. §179 expense is excluded by
    # Reg. §1.263A-1(e)(3)(iii) and so is never passed here.
    depreciation_gross = depreciation
    depreciation_capitalized = min(inputs.get("depreciation_capitalized", 0.0), depreciation)
    depreciation -= depreciation_capitalized

    # Interest — §163(j). A None override means "compute ATI", which .get(key, default)
    # would not catch since the key is present.
    _ati_override = inputs.get("ati")
    ati = (_ati_override if _ati_override is not None
           else total_income - cogs - inputs.get("operating_expenses", 0))
    interest_result = calc_163j(
        inputs.get("interest_expense", 0),
        ati,
        inputs.get("interest_carryforward", 0),
        inputs.get("small_business_exempt", False),
    )

    # Officers compensation — §162(m): excess over $1M non-deductible for public cos
    officer_comp = inputs.get("officer_compensation", 0)
    section_162m_disallowed = 0.0
    if inputs.get("is_public", False):
        covered_employees = inputs.get("covered_employees", 1)
        section_162m_disallowed = max(0, officer_comp - 1_000_000 * covered_employees)
    deductible_officer_comp = officer_comp - section_162m_disallowed

    operating_expenses = inputs.get("operating_expenses", 0)

    # §170(b)(2)(C): the 10% base is taxable income computed without the charitable
    # deduction itself, without the special deductions, and without an NOL or capital
    # loss *carryback*. Every other deduction reduces it — including bad debts, which
    # were once missed here and quietly inflated the limit.
    pre_charitable_income = (total_income - cogs - operating_expenses
                             - deductible_officer_comp - depreciation
                             - interest_result["deductible"]
                             - inputs.get("bad_debt_expense", 0))
    charitable = calc_charitable(inputs.get("charitable_contributions", 0),
                                 pre_charitable_income)

    # Special deductions (Schedule C line 24 → page 1 line 29b). Prefer the caller's
    # §246(b)-limited figure; calc_drd alone applies only the flat §243 rate.
    _special = inputs.get("special_deductions")
    if _special is not None:
        drd = {"deduction": _special, "rate": None,
               "label": "Schedule C line 24 — §246(b) limited"}
    else:
        drd = calc_drd(inputs.get("dividends_received", 0),
                       inputs.get("ownership_pct", 0))

    total_deductions = (cogs + operating_expenses + deductible_officer_comp
                        + depreciation + interest_result["deductible"]
                        + charitable["deductible"] + drd["deduction"]
                        + inputs.get("bad_debt_expense", 0))

    # ── Taxable Income ────────────────────────────────────────────────────────
    taxable_before_nol = total_income - total_deductions
    nol = calc_nol(taxable_before_nol, inputs.get("nol_carryforward", 0),
                   inputs.get("pre2018_nol_carryforward", 0))
    taxable_income = nol["taxable_income"]

    # ── Tax ───────────────────────────────────────────────────────────────────
    regular_tax = taxable_income * 0.21

    # Credits
    rd_asc = calc_rd_credit_asc(inputs.get("current_qre", 0),
                                 inputs.get("avg_prior_3yr_qre", 0))
    rd_regular = calc_rd_credit_regular(inputs.get("current_qre", 0),
                                         inputs.get("fixed_base_pct", 0.03),
                                         inputs.get("avg_gross_receipts", gross_revenue))
    # §41 gives the larger of the two methods; §280C(c) then settles the overlap with
    # the §174 deduction before the credit joins the general business credit pool.
    rd_gross = max(rd_asc["credit"], rd_regular["credit"])
    sec280c = calc_280c(rd_gross, inputs.get("elect_reduced_credit", True))
    rd_credit = sec280c["credit"]

    # The foreign tax credit is not part of the general business credit — §901 is its
    # own regime with its own §904 limitation — and it is applied first, so the §38(c)
    # ceiling is measured against what is left.
    ftc = inputs.get("foreign_tax_credit", 0)
    other_credits = inputs.get("other_credits", 0)
    gbc_base = max(0.0, regular_tax - ftc)
    gbc = calc_general_business_credit(
        rd_credit + other_credits, gbc_base,
        carryforwards=inputs.get("gbc_carryforwards", ()),
        tentative_minimum_tax=inputs.get("tentative_minimum_tax", 0.0),
        current_year=inputs.get("tax_year", 0))

    total_credits = min(ftc, regular_tax) + gbc["total_used"]
    tax_after_credits = regular_tax - total_credits

    # CAMT
    camt = calc_camt(inputs.get("afsi", taxable_income),
                     tax_after_credits,
                     inputs.get("avg_afsi_3yr", 0))

    # BEAT
    beat = calc_beat(inputs.get("avg_gross_receipts_3yr", 0),
                     inputs.get("base_erosion_payments", 0),
                     total_deductions,
                     tax_after_credits,
                     inputs.get("modified_taxable_income", taxable_income),
                     inputs.get("tax_year", 2025))

    total_federal_tax = tax_after_credits + camt["camt"] + beat["beat"]

    # ── Texas Franchise Tax ───────────────────────────────────────────────────
    texas = calc_texas_franchise(gross_revenue,
                                  inputs.get("cogs", 0),
                                  inputs.get("total_compensation", officer_comp))

    # ── Payments ──────────────────────────────────────────────────────────────
    estimated_payments = (inputs.get("q1_payment", 0) + inputs.get("q2_payment", 0)
                          + inputs.get("q3_payment", 0) + inputs.get("q4_payment", 0))
    prior_year_overpayment = inputs.get("prior_year_overpayment", 0)
    total_payments = estimated_payments + prior_year_overpayment
    balance_due = total_federal_tax - total_payments

    # ── M-1 Reconciliation ────────────────────────────────────────────────────
    book_income = inputs.get("book_income", taxable_income)
    permanent_diffs = {
        "meals_50pct_disallowed": inputs.get("meals_entertainment", 0) * 0.50,
        "fines_penalties": inputs.get("fines_penalties", 0),
        "162m_disallowed": section_162m_disallowed,
        "lobbying": inputs.get("lobbying_expense", 0),
    }
    temporary_diffs = {
        "depreciation_book_vs_tax": depreciation - inputs.get("book_depreciation", depreciation),
        "bad_debt_reserve": inputs.get("bad_debt_reserve_book", 0) - inputs.get("bad_debt_expense", 0),
        "interest_163j_carryforward": interest_result["excess_carryforward"],
    }
    m1_taxable_income = (book_income
                         + sum(permanent_diffs.values())
                         + sum(temporary_diffs.values()))

    return {
        "income": {
            "gross_revenue": gross_revenue,
            "capital_gains": capital,
            "other_income": other_income,
            "total_income": total_income,
        },
        "deductions": {
            "cogs": cogs,
            "unicap_adjustment": unicap_adj,
            "operating_expenses": operating_expenses,
            "officer_compensation": deductible_officer_comp,
            "section_162m_disallowed": section_162m_disallowed,
            "depreciation": depreciation,
            "depreciation_gross": depreciation_gross,
            "depreciation_capitalized": depreciation_capitalized,
            "cost_seg_detail": cost_seg_result,
            "interest": interest_result,
            "charitable": charitable,
            "drd": drd,
            "bad_debt": inputs.get("bad_debt_expense", 0),
            "total_deductions": total_deductions,
        },
        "taxable_income": {
            "before_nol": taxable_before_nol,
            "nol": nol,
            "taxable_income": taxable_income,
        },
        "tax": {
            "regular_tax": regular_tax,
            "effective_rate": regular_tax / taxable_income if taxable_income > 0 else 0,
            "credits": {
                "rd_asc": rd_asc,
                "rd_regular": rd_regular,
                "rd_credit_used": rd_credit,
                "rd_credit_gross": rd_gross,
                "sec280c": sec280c,
                "foreign_tax_credit": ftc,
                "general_business_credit": gbc,
                "total_credits": total_credits,
            },
            "tax_after_credits": tax_after_credits,
            "camt": camt,
            "beat": beat,
            "total_federal_tax": total_federal_tax,
        },
        "state_tax": {"texas_franchise": texas},
        "payments": {
            "estimated_payments": estimated_payments,
            "prior_year_overpayment": prior_year_overpayment,
            "total_payments": total_payments,
            "balance_due": balance_due,
        },
        "m1_reconciliation": {
            "book_income": book_income,
            "permanent_differences": permanent_diffs,
            "temporary_differences": temporary_diffs,
            "computed_taxable_income": m1_taxable_income,
        },
        "total_tax_burden": total_federal_tax + texas["recommended"],
        "effective_total_rate": ((total_federal_tax + texas["recommended"]) / gross_revenue
                                  if gross_revenue > 0 else 0),
    }
