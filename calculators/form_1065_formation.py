"""Contributions to a partnership — §721, §722, §723 and the rules that hang off them.

The headline is that a contribution is tax-free. The examinable content is everything that
survives the non-recognition: the basis carries over, the holding period tacks, the
character of the asset is tainted for a period, and the built-in gain stays attached to the
contributing partner forever under §704(c).

Two traps drive most of the arithmetic here.

**Liability relief is money.** Under §752(b), a liability the partnership assumes is a
deemed cash distribution to the contributing partner, to the extent the partner is no longer
on the hook for it. If that deemed distribution exceeds basis, §721 does not save the
partner — §731(a)(1) produces gain. A contribution can be taxable.

**There are three different capital figures, and they diverge at contribution.** The
partner's outside basis takes the property's *adjusted basis* (§722). The §704(b) book
capital account takes its *fair market value*. The difference between them is the built-in
gain, and §704(c) exists to make sure the contributing partner is the one who eventually
reports it.
"""

# §724 character taints. A partnership cannot launder ordinary income into capital gain by
# routing an asset through a contribution, so the character follows the asset.
TAINTS = {
    "receivable": ("Ordinary — permanently", None,
                   "§724(a): an unrealised receivable keeps ordinary character in the "
                   "partnership's hands for ever, with no expiry."),
    "inventory": ("Ordinary — 5 years", 5,
                  "§724(b): inventory in the contributor's hands produces ordinary income "
                  "if the partnership disposes of it within 5 years of the contribution. "
                  "After 5 years the character follows the partnership's own use."),
    "capital_loss": ("Capital loss — 5 years", 5,
                     "§724(c): a capital asset carrying a built-in loss keeps capital "
                     "character for 5 years, and only to the extent of the loss that "
                     "existed at contribution. Loss beyond that takes the partnership's "
                     "character."),
}

# §1223(1): the holding period of the partnership *interest* tacks only for capital and
# §1231 property. Cash and ordinary-income property start a fresh holding period, so a
# partner who contributes both ends up with a split holding period in one interest.
TACKING_CHARACTERS = {"capital", "1231", "capital_loss"}


def calc_721_contribution(cash=0.0, property_basis=0.0, property_fmv=0.0,
                          liability_assumed=0.0, retained_liability_share=0.0,
                          other_liability_share=0.0, is_investment_company=False):
    """One partner's contribution, run through §721 → §752 → §722 → §723.

    `liability_assumed` is debt encumbering the contributed property that the partnership
    takes on. `retained_liability_share` (0–1) is how much of that same debt still comes
    back to the contributing partner under §752 — a partner with a 40% interest in a
    partnership that assumes their $100k mortgage is relieved of only $60k.
    `other_liability_share` is the partner's share of the partnership's other debts, which
    adds basis without any offsetting relief.

    Order matters: §721(b) gain is measured first, because it raises the basis that the
    liability relief is then tested against.
    """
    # §721(b): non-recognition is switched off where the contribution diversifies holdings
    # into an entity that would be an investment company if incorporated. Gain only —
    # losses stay unrecognised.
    gain_721b = max(0.0, property_fmv - property_basis) if is_investment_company else 0.0

    net_relief = liability_assumed * (1.0 - retained_liability_share)
    basis_in = cash + property_basis + gain_721b

    # §752(b) treats the relief as a distribution of money, and §733 reduces basis by it.
    # Basis cannot go below zero, so the excess is gain under §731(a)(1).
    basis_after_relief = basis_in + other_liability_share - net_relief
    gain_731 = max(0.0, -basis_after_relief)
    outside_basis = max(0.0, basis_after_relief)

    # §723: the partnership takes the transferor's basis, increased by the gain the
    # contribution forced the partner to recognise.
    partnership_basis = property_basis + gain_721b + gain_731
    built_in_gain = property_fmv - partnership_basis if property_fmv else 0.0

    # Reg. §1.704-1(b)(2)(iv)(b): the book capital account takes value, net of debt the
    # partnership assumes. This is the figure Item L reports and M-2 line 2 sums.
    book_capital = cash + property_fmv - liability_assumed
    tax_capital = outside_basis - (liability_assumed * retained_liability_share
                                   + other_liability_share)

    return {
        "gain_721b": gain_721b,
        "gain_731": gain_731,
        "gain_total": gain_721b + gain_731,
        "net_relief": net_relief,
        "outside_basis": outside_basis,
        "partnership_basis": partnership_basis,
        "built_in_gain": built_in_gain,
        "book_capital": book_capital,
        "tax_capital": tax_capital,
    }


def calc_724_taint(character):
    """The character the contributed asset keeps, and for how long."""
    label, years, note = TAINTS.get(
        character,
        ("Follows the partnership's use", None,
         "No §724 taint. Character is determined by how the partnership holds the asset, "
         "not by how the contributor held it."))
    return {"label": label, "years": years, "note": note,
            "tainted": character in TAINTS}


def calc_holding_period(character, has_cash=False):
    """§1223. Two holding periods come out of one contribution and they are not the same.

    The partnership's holding period in the asset always tacks. The partner's holding
    period in the *interest* only tacks for capital and §1231 property."""
    tacks = character in TACKING_CHARACTERS
    return {
        "interest_tacks": tacks,
        "partnership_tacks": True,
        "split": tacks and has_cash,
        "note": ("§1223(1): the interest takes a tacked holding period for the capital or "
                 "§1231 property contributed. Cash contributed at the same time starts a "
                 "fresh period, so the interest has a split holding period."
                 if tacks and has_cash else
                 "§1223(1): the holding period of the interest tacks, because capital or "
                 "§1231 property was contributed." if tacks else
                 "§1223(1) does not tack for cash or ordinary-income property — the "
                 "holding period of the interest begins on the date of contribution. "
                 "§1223(2) still tacks for the partnership's own holding period."),
    }


def calc_disguised_sale(contribution_fmv, distribution, months_apart):
    """§707(a)(2)(B). A contribution followed by a related distribution can be a sale.

    The two-year rule is a presumption running in both directions, not a safe harbour:
    inside two years the transfers are presumed to be a sale unless the facts clearly show
    otherwise; outside two years they are presumed not to be, and the Service carries the
    burden."""
    if distribution <= 0 or contribution_fmv <= 0:
        return {"presumed_sale": False, "within_two_years": months_apart <= 24,
                "sale_proceeds": 0.0, "sale_fraction": 0.0,
                "note": "No distribution to test."}
    within = months_apart <= 24
    fraction = min(1.0, distribution / contribution_fmv)
    return {
        "presumed_sale": within,
        "within_two_years": within,
        "sale_proceeds": distribution,
        "sale_fraction": fraction,
        "note": ("Within two years, so the transfers are presumed to be a sale of "
                 f"{fraction:.0%} of the property and must be disclosed on Form 8275 if "
                 "the partnership takes the contrary position."
                 if within else
                 "More than two years apart, so the transfers are presumed not to be a "
                 "sale — but the presumption is rebuttable and the facts still govern."),
    }


def calc_services_interest(kind, fmv, vested=True):
    """An interest received for services is not a §721 contribution at all — §721 requires
    property, and services are not property.

    A **capital** interest gives the holder a share of liquidation proceeds immediately, so
    it is compensation taxed under §83 at fair market value. A **profits** interest gives
    only a share of future profits and is worth nothing on liquidation the day it is
    granted, which is why Rev. Proc. 93-27 treats it as non-taxable."""
    if kind == "capital":
        return {
            "taxable": True,
            "income": fmv,
            "basis": fmv,
            "note": ("§83: a capital interest received for services is ordinary "
                     "compensation income at fair market value. The partner's basis in the "
                     "interest is the amount included. The partnership deducts or "
                     "capitalises the same amount depending on the service."
                     + ("" if vested else
                        " Unvested and subject to a substantial risk of forfeiture, so "
                        "income is deferred until vesting unless a §83(b) election is made "
                        "within 30 days of the grant.")),
        }
    return {
        "taxable": False,
        "income": 0.0,
        "basis": 0.0,
        "note": ("Rev. Proc. 93-27: a profits interest is generally not taxable on grant, "
                 "because it has no liquidation value on the grant date. The safe harbour "
                 "fails if the interest relates to a substantially certain and predictable "
                 "income stream, if it is disposed of within two years, or if it is an "
                 "interest in a publicly traded partnership."),
    }


def calc_item_n(prior_unrecognized=0.0, current_built_in_gain=0.0, allocated_this_year=0.0):
    """Schedule K-1 Item N — the partner's share of net unrecognised §704(c) gain or loss.

    Built-in gain does not vanish at contribution; it sits against the contributing partner
    until the partnership depreciates or sells the asset, and Item N is the running balance.
    A reverse §704(c) layer from a book-up would also belong here."""
    ending = prior_unrecognized + current_built_in_gain - allocated_this_year
    return {"beginning": prior_unrecognized, "additions": current_built_in_gain,
            "allocated": allocated_this_year, "ending": ending}
