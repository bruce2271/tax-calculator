"""
Form 1065 — partner-level mechanics.

The return itself shows almost none of this. Schedule K-1 reports a partner's
distributive share, but whether that share is *deductible* turns on three separate
limitations applied in a fixed order, and on a basis figure the form never prints.

Everything here is a pure function taking explicit arguments — no Streamlit, no I/O —
so the rules can be tested against worked examples.
"""


# ── §752 — a partner's share of partnership liabilities ──────────────────────

def calc_752_shares(recourse: float = 0.0, nonrecourse: float = 0.0,
                    qualified_nonrecourse: float = 0.0) -> dict:
    """§752. A partner's share of partnership debt is treated as a cash contribution,
    so it *increases* outside basis without the partner paying anything.

    That is why a partnership can push losses out to partners that a corporation cannot:
    debt creates basis here, and never does in a C corporation.

    The three kinds are separated because §465 treats them differently. A partner is at
    risk for recourse debt they are personally liable on, and for qualified nonrecourse
    real estate financing under §465(b)(6) — borrowed from a commercial lender, secured
    by real property, not from a related party. Ordinary nonrecourse debt gives outside
    basis under §752 but no at-risk amount, which is exactly where §704(d) and §465
    diverge."""
    total = recourse + nonrecourse + qualified_nonrecourse
    return {
        "recourse": recourse,
        "nonrecourse": nonrecourse,
        "qualified_nonrecourse": qualified_nonrecourse,
        "total": total,
        # §465(b): recourse and QNRE count; ordinary nonrecourse does not.
        "at_risk_portion": recourse + qualified_nonrecourse,
        "not_at_risk": nonrecourse,
    }


# ── §705 / §722 / §733 — outside basis ───────────────────────────────────────

def calc_outside_basis(beginning: float = 0.0, contributions: float = 0.0,
                       liability_increase: float = 0.0, taxable_income: float = 0.0,
                       tax_exempt_income: float = 0.0, distributions: float = 0.0,
                       liability_decrease: float = 0.0, losses: float = 0.0,
                       nondeductible: float = 0.0) -> dict:
    """§705, with the ordering that Reg. §1.704-1(d)(2) requires.

    The order is not cosmetic. Basis goes up for income first, then down for
    distributions, and only then down for losses. A distribution therefore consumes
    basis that a loss would otherwise have been able to use — so the same facts in a
    different order produce a different deductible loss.

    Basis can never go below zero. A distribution that would take it negative instead
    triggers gain under §731(a); a loss that would take it negative is suspended under
    §704(d) and is returned here rather than applied.

    An increase in the partner's share of liabilities is a deemed contribution under
    §752(a); a decrease is a deemed distribution under §752(b) and is grouped with
    actual distributions because it can trigger the same §731(a) gain."""
    steps = []

    basis = beginning
    steps.append(("Beginning outside basis", beginning, basis))

    for label, amt in (("Contributions (§722)", contributions),
                       ("Increase in share of liabilities (§752(a))", liability_increase),
                       ("Distributive share of taxable income", taxable_income),
                       ("Distributive share of tax-exempt income", tax_exempt_income)):
        if amt:
            basis += amt
            steps.append((label, amt, basis))

    # Distributions come next, and cannot take basis below zero — the excess is gain.
    total_distributions = distributions + liability_decrease
    gain_731a = max(0.0, total_distributions - basis)
    applied_distributions = min(total_distributions, basis)
    if total_distributions:
        basis -= applied_distributions
        steps.append(("Distributions and deemed distributions (§733, §752(b))",
                      -applied_distributions, basis))

    # Nondeductible, non-capitalisable items reduce basis even though they never
    # produce a deduction — fines, the disallowed half of meals, §267 losses.
    if nondeductible:
        applied_nd = min(nondeductible, basis)
        basis -= applied_nd
        steps.append(("Nondeductible, non-capitalisable expenses", -applied_nd, basis))

    # Losses last. Whatever basis cannot absorb is suspended under §704(d).
    allowed_loss = min(losses, basis)
    suspended = losses - allowed_loss
    if losses:
        basis -= allowed_loss
        steps.append(("Losses allowed by basis (§704(d))", -allowed_loss, basis))

    return {"ending_basis": basis, "steps": steps,
            "gain_731a": gain_731a,
            "loss_allowed_by_basis": allowed_loss,
            "loss_suspended_704d": suspended,
            "distributions_applied": applied_distributions}


# ── §704(b) — capital account, the book side ─────────────────────────────────

def calc_capital_account(beginning: float = 0.0, contributions_fmv: float = 0.0,
                         book_income: float = 0.0, distributions_fmv: float = 0.0,
                         book_loss: float = 0.0) -> dict:
    """§704(b) book capital, which answers a different question from outside basis.

    Capital account measures what the partner is economically entitled to — it governs
    who gets what on liquidation. Outside basis measures how much loss the partner may
    deduct and how much of a distribution is tax free.

    Four things make them diverge, and each is worth being able to name:

      * liabilities are in outside basis and never in the capital account
      * contributed property enters the capital account at fair market value and outside
        basis at the contributor's adjusted basis
      * tax-exempt income raises outside basis but not the capital account
      * book depreciation runs off the capital account, tax depreciation off basis

    After a book-up revaluation the two can be far apart, which is how a partner ends up
    with a large positive capital account and no tax basis at all."""
    ending = beginning + contributions_fmv + book_income - distributions_fmv - book_loss
    return {"ending": ending,
            "steps": [("Beginning capital account", beginning),
                      ("Contributions at fair market value", contributions_fmv),
                      ("Share of book income", book_income),
                      ("Distributions at fair market value", -distributions_fmv),
                      ("Share of book loss", -book_loss)]}


# ── §704(d) → §465 → §469 — the loss limitation gauntlet ─────────────────────

def calc_loss_limitations(allocable_loss: float, outside_basis: float,
                          at_risk_amount: float, passive_income: float = 0.0,
                          materially_participates: bool = False) -> dict:
    """Three separate limitations, applied in a fixed order, each on what the previous
    one let through.

    Order matters and is frequently examined:

      §704(d)  Do you have basis? A loss beyond outside basis is suspended until basis
               is restored. Ordinary nonrecourse debt creates basis here.
      §465     Are you at risk? Applied to what §704(d) allowed. Ordinary nonrecourse
               debt does *not* create an at-risk amount, so this is where a partner in
               a leveraged deal usually gets stopped.
      §469     Is the activity passive? Applied to what §465 allowed. A passive loss is
               deductible only against passive income unless the partner materially
               participates.

    Each stage suspends its own excess, and the three suspensions have different
    release conditions — basis restored, amounts placed at risk, passive income earned
    or the activity disposed of. They are therefore tracked separately, never netted.

    Suspended losses keep their original character when they are eventually allowed."""
    after_704d = min(allocable_loss, max(0.0, outside_basis))
    susp_704d = allocable_loss - after_704d

    after_465 = min(after_704d, max(0.0, at_risk_amount))
    susp_465 = after_704d - after_465

    if materially_participates:
        after_469, susp_469 = after_465, 0.0
    else:
        after_469 = min(after_465, max(0.0, passive_income))
        susp_469 = after_465 - after_469

    return {
        "allocable_loss": allocable_loss,
        "after_704d": after_704d, "suspended_704d": susp_704d,
        "after_465": after_465, "suspended_465": susp_465,
        "deductible": after_469, "suspended_469": susp_469,
        "total_suspended": susp_704d + susp_465 + susp_469,
        "steps": [
            ("§704(d) — outside basis", outside_basis, after_704d, susp_704d,
             "Suspended until outside basis is restored"),
            ("§465 — amount at risk", at_risk_amount, after_465, susp_465,
             "Suspended until the partner is at risk for more"),
            ("§469 — passive activity",
             "material participation" if materially_participates else passive_income,
             after_469, susp_469,
             "Released by passive income, or on a fully taxable disposition"),
        ],
    }
