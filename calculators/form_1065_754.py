"""The §754 election and the basis adjustments it switches on — §743(b), §734(b), §755.

A partnership has two sets of basis. **Outside basis** is what a partner has in the
interest; **inside basis** is what the partnership has in its assets. They start equal and
drift apart the moment an interest is sold for more than the seller's basis, or property
leaves at a capped basis. The §754 election is what pulls them back together.

**§743(b) fixes a transfer.** The buyer paid market value, but without an election the
partnership's basis in its assets does not move — so when the partnership later sells an
asset, the buyer is allocated a share of gain they already paid for. §743(b) steps their
share of inside basis to match the price.

**§734(b) fixes a distribution.** Basis that the §732(a)(2) cap destroyed, or gain the
distributee had to recognise, is put back into the assets the partnership still holds.

**Both adjustments are one-sided in different ways.** A §743(b) adjustment belongs to the
transferee alone and is invisible to every other partner. A §734(b) adjustment belongs to
the partnership as a whole and is shared by everyone.

**The election is sticky and sometimes compulsory.** Once made it binds all future years
until the Service consents to a revocation, which is why a partnership sitting on
depreciated assets thinks carefully first — the adjustment cuts both ways. And §743(d) and
§734(d) make it mandatory where the numbers are large and pointing downward, so it cannot be
used selectively to preserve losses.
"""

ORDINARY = "ordinary"      # unrealised receivables, inventory, other ordinary income assets
CAPITAL = "capital"        # capital assets and §1231 property

SUBSTANTIAL_THRESHOLD = 250_000


def calc_previously_taxed_capital(hypothetical_cash=0.0, tax_loss_allocated=0.0,
                                  tax_gain_allocated=0.0, liability_share=0.0):
    """Reg. §1.743-1(d). The transferee's share of inside basis, built the way the
    regulation builds it rather than by taking a percentage of the balance sheet.

    Imagine the partnership sells everything at value for cash and liquidates. The cash the
    transferee would walk away with, **plus** the tax loss they would be allocated on that
    sale and **minus** the tax gain, is their previously taxed capital. Adding their share
    of liabilities gives their share of inside basis."""
    ptc = hypothetical_cash + tax_loss_allocated - tax_gain_allocated
    return {"previously_taxed_capital": ptc,
            "share_of_inside_basis": ptc + liability_share,
            "liability_share": liability_share}


def calc_743b(outside_basis=0.0, share_of_inside_basis=0.0, election=False,
              substantial_built_in_loss=False):
    """§743(b). Positive where the buyer paid more than their share of inside basis."""
    adjustment = outside_basis - share_of_inside_basis
    applies = election or substantial_built_in_loss
    return {"adjustment": adjustment if applies else 0.0,
            "potential": adjustment,
            "applies": applies,
            "mandatory": substantial_built_in_loss,
            "direction": "increase" if adjustment > 0 else
                         "decrease" if adjustment < 0 else "none"}


def calc_734b(gain_recognised=0.0, loss_recognised=0.0,
              partnership_basis_in_distributed=0.0, distributee_basis=0.0,
              election=False, substantial_basis_reduction=False):
    """§734(b). Two independent sources, and they are allocated differently under §755, so
    they are kept apart here.

    Basis the §732(a)(2) cap destroyed is not gone from the partnership's point of view —
    §734(b) puts it back into the assets that stayed behind. That is the answer to "what
    happens to the basis lost on a distribution": nothing, unless there is an election."""
    from_gain = gain_recognised - loss_recognised
    from_basis = partnership_basis_in_distributed - distributee_basis
    total = from_gain + from_basis
    applies = election or substantial_basis_reduction
    return {"from_gain_or_loss": from_gain if applies else 0.0,
            "from_basis_difference": from_basis if applies else 0.0,
            "adjustment": total if applies else 0.0,
            "potential": total,
            "applies": applies,
            "mandatory": substantial_basis_reduction,
            "direction": "increase" if total > 0 else
                         "decrease" if total < 0 else "none"}


def _spread(amount, assets, pct=1.0):
    """Spread an amount across the assets in one class.

    §755 allocates in proportion to unrealised appreciation and depreciation, so an asset
    whose value already equals its basis takes nothing. Three cases, in order:

    1. The class has a net unrealised gain or loss — allocate in proportion to each asset's
       signed difference, which keeps an appreciated asset and a depreciated one pulling in
       opposite directions.
    2. The differences cancel to nil but individually are not — allocate by magnitude,
       because proportion to a zero total is undefined.
    3. Nothing is unrealised at all — fall back to relative basis, then to an equal split.
    """
    if not assets:
        return {}
    diffs = {a["name"]: (a.get("fmv", 0.0) - a.get("basis", 0.0)) * pct for a in assets}
    signed_total = sum(diffs.values())
    magnitude = sum(abs(v) for v in diffs.values())

    if abs(signed_total) > 0.005:
        return {n: amount * (v / signed_total) for n, v in diffs.items()}
    if magnitude > 0.005:
        return {n: amount * (abs(v) / magnitude) for n, v in diffs.items()}

    bases = {a["name"]: a.get("basis", 0.0) for a in assets}
    total_basis = sum(bases.values())
    if total_basis > 0.005:
        return {n: amount * (b / total_basis) for n, b in bases.items()}
    return {a["name"]: amount / len(assets) for a in assets}


def calc_755_743b(adjustment, assets=(), transferee_pct=1.0):
    """§755 for a §743(b) adjustment.

    Reg. §1.755-1(b): the ordinary income class takes the income, gain or loss the
    transferee would be allocated on a hypothetical sale of the ordinary assets at value.
    The capital gain class takes **the residual** — which is why a §743(b) adjustment can
    be positive overall and still push the capital class downward."""
    ordinary = [a for a in assets if a.get("klass", CAPITAL) == ORDINARY]
    capital = [a for a in assets if a.get("klass", CAPITAL) != ORDINARY]

    to_ordinary = sum((a.get("fmv", 0.0) - a.get("basis", 0.0)) for a in ordinary) * transferee_pct
    to_capital = adjustment - to_ordinary

    alloc = {}
    alloc.update(_spread(to_ordinary, ordinary, transferee_pct))
    alloc.update(_spread(to_capital, capital, transferee_pct))
    return {"to_ordinary": to_ordinary, "to_capital": to_capital,
            "allocations": alloc,
            "capital_is_opposite": adjustment > 0 > to_capital or adjustment < 0 < to_capital}


def calc_755_734b(from_gain_or_loss, from_basis_difference, distributed_class,
                  assets=()):
    """§755 for a §734(b) adjustment. Reg. §1.755-1(c) splits it by source.

    An adjustment arising from **gain or loss recognised** goes only to capital gain
    property, because the gain the distributee recognised was capital. An adjustment
    arising from the **basis of the distributed property** goes to property of the **same
    class** as what went out — ordinary basis is restored to ordinary assets.

    A downward adjustment stops at zero. §755(c) and Reg. §1.755-1(c)(4) do not permit a
    negative basis: a decrease that the class cannot absorb is held in suspense and applied
    when the partnership next acquires property of that class."""
    ordinary = [a for a in assets if a.get("klass", CAPITAL) == ORDINARY]
    capital = [a for a in assets if a.get("klass", CAPITAL) != ORDINARY]

    alloc = {}
    for name, amt in _spread(from_gain_or_loss, capital).items():
        alloc[name] = alloc.get(name, 0.0) + amt
    same_class = ordinary if distributed_class == ORDINARY else capital
    for name, amt in _spread(from_basis_difference, same_class).items():
        alloc[name] = alloc.get(name, 0.0) + amt

    bases = {a["name"]: a.get("basis", 0.0) for a in assets}
    capped, suspended = {}, 0.0
    for name, amt in alloc.items():
        floor = -bases.get(name, 0.0)
        if amt < floor:
            suspended += floor - amt
            amt = floor
        capped[name] = amt

    return {"to_capital_from_gain": from_gain_or_loss,
            "to_same_class_from_basis": from_basis_difference,
            "same_class": distributed_class,
            "allocations": capped,
            "suspended": suspended}


def calc_substantial_built_in_loss(inside_basis=0.0, fmv=0.0, transferee_loss_share=0.0):
    """§743(d). Either test makes the §743(b) adjustment mandatory even with no election.

    The second test came in with the 2017 Act and closed the obvious workaround: a
    partnership whose assets were not loss-making overall could still hand a single
    incoming partner an enormous built-in loss."""
    entity_test = (inside_basis - fmv) > SUBSTANTIAL_THRESHOLD
    transferee_test = transferee_loss_share > SUBSTANTIAL_THRESHOLD
    return {"entity_test": entity_test, "transferee_test": transferee_test,
            "mandatory": entity_test or transferee_test,
            "excess": inside_basis - fmv}


def calc_substantial_basis_reduction(downward_adjustment=0.0):
    """§734(d). A downward §734(b) adjustment over $250,000 is mandatory."""
    amount = max(0.0, -downward_adjustment)
    return {"mandatory": amount > SUBSTANTIAL_THRESHOLD, "amount": amount}
