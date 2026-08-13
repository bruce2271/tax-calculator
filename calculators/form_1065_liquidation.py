"""Liquidating distributions — §736, §731(a)(2), §732(b), §732(c).

Three things change when a distribution liquidates the interest rather than reducing it,
and each is the opposite of the current-distribution rule.

**Loss becomes possible.** §731(a)(2) allows a loss, but only where nothing comes out
except money, unrealised receivables and inventory. The reason is structural: those are the
only assets whose basis cannot be increased, so they are the only case where basis has
nowhere left to go.

**Basis is substituted, not capped.** §732(b) gives the distributee a basis equal to the
whole of the outside basis less money received. In a current distribution the carryover
basis could only come down; here it can also go **up**, and an increase is allocated first
to appreciated property rather than to depreciated property.

**Payments to a retiring partner split in two.** §736(b) payments buy the partner's share
of partnership property and are a distribution. §736(a) payments are everything else, and
they are ordinary income to the retiring partner and deductible by the partnership. Getting
the split wrong moves money between a capital and an ordinary bucket on both sides at once.
"""

from .form_1065_distributions import HOT, OTHER, _allocate_within_class

# §736(b)(2), as narrowed in 1993. Payments for unrealised receivables, and for goodwill
# that the partnership agreement does not provide for, are pushed out of the property
# bucket and into §736(a) — but only where capital is not a material income-producing
# factor and the retiring partner is a general partner. In a capital-intensive partnership
# both stay in §736(b).
def calc_736_split(total_payment=0.0, receivables_share=0.0, goodwill_share=0.0,
                   other_property_share=0.0, service_partnership=False,
                   general_partner=False, goodwill_in_agreement=False):
    """Split a payment to a retiring partner between §736(b) and §736(a)."""
    carve_out_applies = service_partnership and general_partner

    receivables_736b = 0.0 if carve_out_applies else receivables_share
    goodwill_736b = goodwill_share if (goodwill_in_agreement or not carve_out_applies) else 0.0

    section_736b = other_property_share + receivables_736b + goodwill_736b
    section_736a = max(0.0, total_payment - section_736b)

    reasons = []
    if carve_out_applies and receivables_share:
        reasons.append("Unrealised receivables are §736(a): capital is not a material "
                       "income-producing factor and the retiring partner is a general "
                       "partner, so §736(b)(2)(A) takes them out of the property bucket.")
    if carve_out_applies and goodwill_share and not goodwill_in_agreement:
        reasons.append("Goodwill is §736(a): the partnership agreement does not provide for "
                       "a payment for goodwill, so §736(b)(2)(B) applies.")
    if carve_out_applies and goodwill_share and goodwill_in_agreement:
        reasons.append("Goodwill stays in §736(b) because the partnership agreement "
                       "provides for it — the one drafting decision that moves this money "
                       "from ordinary to capital.")
    if not carve_out_applies and (receivables_share or goodwill_share):
        reasons.append("The §736(b)(2) carve-out does not apply, so receivables and "
                       "goodwill are payments for partnership property. Since 1993 the "
                       "carve-out only reaches a general partner in a partnership where "
                       "capital is not a material income-producing factor.")

    return {
        "section_736b": section_736b,
        "section_736a": section_736a,
        "receivables_736b": receivables_736b,
        "goodwill_736b": goodwill_736b,
        "carve_out_applies": carve_out_applies,
        "reasons": reasons,
    }


def calc_736a_character(determined_by_income=False):
    """§736(a)(1) or (a)(2). Either way the retiring partner has ordinary income; what
    changes is how the partnership gets the deduction."""
    if determined_by_income:
        return {"kind": "distributive share",
                "note": "§736(a)(1): the payment is determined by reference to partnership "
                        "income, so it is a distributive share. It reduces the income "
                        "allocated to the remaining partners rather than being deducted, "
                        "and it keeps the character of the underlying income."}
    return {"kind": "guaranteed payment",
            "note": "§736(a)(2): the payment is not determined by partnership income, so it "
                    "is a guaranteed payment under §707(c). The partnership deducts it at "
                    "page 1 line 10, and the retiring partner reports ordinary income."}


def _allocate_increase(amount, assets):
    """§732(c)(2)(B). A step-up is spread first among properties carrying unrealised
    **appreciation**, in proportion to it and only to the extent of it, and any excess then
    goes in proportion to fair market value.

    Note the mirror: a decrease under §732(c)(3) goes to unrealised *depreciation* first.
    Basis is always pushed towards value from whichever side it is on."""
    out = {a["name"]: float(a["basis"]) for a in assets}
    if not assets or amount <= 0:
        return out

    appreciation = {a["name"]: max(0.0, a.get("fmv", 0.0) - a["basis"]) for a in assets}
    total_app = sum(appreciation.values())
    remaining = amount
    if total_app > 0:
        applied = min(remaining, total_app)
        for name, app in appreciation.items():
            out[name] += applied * (app / total_app)
        remaining -= applied

    if remaining > 0.005:
        fmvs = {a["name"]: a.get("fmv", 0.0) for a in assets}
        total_fmv = sum(fmvs.values())
        if total_fmv > 0:
            for name, v in fmvs.items():
                out[name] += remaining * (v / total_fmv)
        else:
            for name in out:
                out[name] += remaining / len(out)
    return out


def calc_liquidating_distribution(outside_basis=0.0, cash=0.0, marketable_securities=0.0,
                                  liability_relief=0.0, properties=()):
    """§731(a) and §732(b) on a distribution that liquidates the interest."""
    money = cash + marketable_securities + liability_relief
    gain = max(0.0, money - outside_basis)
    # §732(b): the substituted basis is the whole of what is left, so unlike a current
    # distribution nothing is stranded in an interest that no longer exists.
    available = max(0.0, outside_basis - money)

    props = [dict(p) for p in properties]
    hot = [p for p in props if p.get("klass", OTHER) == HOT]
    other = [p for p in props if p.get("klass", OTHER) != HOT]

    # Hot assets never take more than the partnership's basis — they cannot absorb a
    # step-up, which is exactly why a distribution of nothing but money and hot assets can
    # produce a loss.
    hot_alloc, hot_used = _allocate_within_class(hot, available)
    left = available - hot_used

    other_carryover = sum(p["basis"] for p in other)
    if other:
        if left > other_carryover:
            other_alloc = _allocate_increase(left - other_carryover, other)
            other_used = sum(other_alloc.values())
        else:
            other_alloc, other_used = _allocate_within_class(other, max(0.0, left))
    else:
        other_alloc, other_used = {}, 0.0

    allocations = {**hot_alloc, **other_alloc}
    basis_to_property = hot_used + other_used

    # §731(a)(2): a loss only where money, receivables and inventory are all that came out.
    only_money_and_hot = not other
    unabsorbed = max(0.0, available - basis_to_property)
    loss = unabsorbed if only_money_and_hot else 0.0

    return {
        "money": money,
        "gain_731": gain,
        "loss_731": loss,
        "loss_available": only_money_and_hot,
        "basis_available": available,
        "allocations": allocations,
        "basis_to_property": basis_to_property,
        "step_up": max(0.0, basis_to_property - sum(p["basis"] for p in props)),
        "step_down": max(0.0, sum(p["basis"] for p in props) - basis_to_property),
        "unabsorbed": unabsorbed,
    }
