"""Current (non-liquidating) distributions — §731, §732, §733, §735, §737.

A current distribution is normally tax-free, for the same reason a contribution is: the
partner has not cashed out, only moved assets across a line that tax law mostly ignores.
What is examined is the small set of circumstances where that breaks down.

**Only money produces gain, and only above basis.** §731(a)(1). Property never does,
however far its value exceeds its basis — the partner simply takes a lower basis in it.

**Loss is impossible on a current distribution.** §731(a)(2) allows loss only in
liquidation, and even then only where nothing but money, receivables and inventory comes
out. A current distribution that leaves the partner with basis still in the interest cannot
produce a loss, because the basis has somewhere to go.

**Basis is capped, never stepped up.** §732(a)(2) limits the basis of distributed property
to what is left of the partner's outside basis after money. In a current distribution the
carryover basis can only come down.

**Two seven-year rules pull contributed property back.** §704(c)(1)(B) catches the
contributed property going out to somebody else; §737 catches other property coming back to
the contributor. Both exist to stop a partnership being used to swap appreciated assets
tax-free, and both draw down the same net §704(c) balance the K-1 reports at Item N.
"""

HOT = "hot"     # unrealised receivables and inventory — §751(a) assets
OTHER = "other"


def _allocate_within_class(props, available):
    """§732(c). Spread a shortfall across the properties in one class.

    The order is deliberate and is the part people get wrong. A required decrease goes
    **first to properties carrying unrealised depreciation**, in proportion to that
    depreciation and only to the extent of it — the theory being that basis in excess of
    value is the least useful basis to keep. Only what is left over is then spread in
    proportion to the remaining bases."""
    total_basis = sum(p["basis"] for p in props)
    if not props:
        return {}, 0.0
    if available >= total_basis:
        return {p["name"]: p["basis"] for p in props}, total_basis

    decrease = total_basis - available
    out = {p["name"]: float(p["basis"]) for p in props}

    # Step one: unrealised depreciation.
    depreciation = {p["name"]: max(0.0, p["basis"] - p.get("fmv", p["basis"]))
                    for p in props}
    total_dep = sum(depreciation.values())
    if total_dep > 0:
        applied = min(decrease, total_dep)
        for name, dep in depreciation.items():
            out[name] -= applied * (dep / total_dep)
        decrease -= applied

    # Step two: whatever remains, in proportion to the bases still standing.
    if decrease > 0.005:
        remaining_total = sum(out.values())
        if remaining_total > 0:
            for name in out:
                out[name] -= decrease * (out[name] / remaining_total)
        decrease = 0.0

    # Rounding only. The proportional step cannot overshoot — the decrease left after the
    # depreciation step is always within the bases still standing — so this is float dust,
    # not a real allocation rule.
    return {k: round(v, 2) + 0.0 for k, v in out.items()}, available


def calc_current_distribution(outside_basis, cash=0.0, marketable_securities=0.0,
                              liability_relief=0.0, properties=(),
                              net_precontribution_gain=0.0, seven_year_property=False):
    """One partner's current distribution, in the order the Code applies.

    `properties` is a sequence of dicts with `name`, `basis`, `fmv` and `klass`
    (`"hot"` for unrealised receivables and inventory, `"other"` for everything else).
    `seven_year_property` says the partner contributed appreciated property within the last
    seven years, which is what switches §737 on.
    """
    # §731(c) puts marketable securities on the money side, and §752(b) does the same for a
    # reduction in the partner's share of debt. Neither is "property" for §732.
    money = cash + marketable_securities + liability_relief

    gain_731 = max(0.0, money - outside_basis)
    basis_after_money = max(0.0, outside_basis - money)

    props = [dict(p) for p in properties]
    fmv_property = sum(p.get("fmv", 0.0) for p in props)

    # §737: other property coming back to a partner who contributed appreciated property
    # within seven years. The gain is the lesser of the net pre-contribution gain still
    # outstanding and the value received over basis. §737(c)(1) then adds it to basis
    # *before* §732 runs, so the property can absorb more.
    gain_737 = 0.0
    if seven_year_property and net_precontribution_gain > 0 and props:
        gain_737 = min(net_precontribution_gain,
                       max(0.0, fmv_property - basis_after_money))
    basis_for_property = basis_after_money + gain_737

    # §732(a): carryover basis, capped at what is left. Hot assets are served first,
    # because §751 assets keep their ordinary character and the Code will not let a partner
    # push basis away from them.
    hot = [p for p in props if p.get("klass", OTHER) == HOT]
    other = [p for p in props if p.get("klass", OTHER) != HOT]

    hot_alloc, hot_used = _allocate_within_class(hot, basis_for_property)
    left = basis_for_property - hot_used
    other_alloc, other_used = _allocate_within_class(other, max(0.0, left))

    allocations = {**hot_alloc, **other_alloc}
    basis_to_property = hot_used + other_used

    # §733: outside basis comes down by the money and by the basis the property took. It
    # cannot go below zero, and the cap in §732(a)(2) is what guarantees that.
    ending_basis = max(0.0, basis_for_property - basis_to_property)

    carryover_total = sum(p["basis"] for p in props)
    return {
        "money": money,
        "gain_731": gain_731,
        "gain_737": gain_737,
        "gain_total": gain_731 + gain_737,
        "basis_after_money": basis_after_money,
        "basis_for_property": basis_for_property,
        "allocations": allocations,
        "basis_to_property": basis_to_property,
        "basis_lost": max(0.0, carryover_total - basis_to_property),
        "ending_basis": ending_basis,
        "fmv_property": fmv_property,
        "loss_recognised": 0.0,     # §731(a)(2) — never on a current distribution
    }


def calc_704c_1b(built_in_gain_remaining, distributed_to_another_partner,
                 years_since_contribution):
    """§704(c)(1)(B). The contributed property itself goes out to a different partner.

    The contributor is treated as if the partnership sold it at value on that date, and
    recognises the built-in gain that was still attached. Seven years, and the clock runs
    from the contribution."""
    within = years_since_contribution < 7
    triggered = bool(distributed_to_another_partner) and within and built_in_gain_remaining != 0
    return {
        "triggered": triggered,
        "gain": built_in_gain_remaining if triggered else 0.0,
        "within_seven_years": within,
        "note": ("The contributed property was distributed to another partner inside the "
                 "seven-year window, so the contributor recognises the built-in gain that "
                 "was still riding on it. Outside basis and the partnership's basis in the "
                 "property both rise by that amount."
                 if triggered else
                 "Outside the seven-year window, so §704(c)(1)(B) does not apply and the "
                 "built-in gain simply disappears."
                 if not within else
                 "§704(c)(1)(B) is not triggered — the property did not go to another "
                 "partner, or no built-in gain remains."),
    }


def calc_735_character(klass, years_held_by_partner):
    """§735. The character taint that survives the distribution, mirroring §724 on the way
    in. Note the asymmetry: receivables are ordinary for ever, inventory for five years."""
    if klass == "receivable":
        return {"label": "Ordinary — permanently", "years": None, "tainted": True,
                "note": "§735(a)(1): an unrealised receivable distributed by a partnership "
                        "produces ordinary income whenever the partner disposes of it, "
                        "with no expiry."}
    if klass == "inventory":
        return {"label": "Ordinary — 5 years", "years": 5,
                "tainted": years_held_by_partner < 5,
                "note": "§735(a)(2): inventory keeps ordinary character for five years from "
                        "the distribution. After that the character follows the partner's "
                        "own use, so a partner holding it as an investment can get capital "
                        "treatment by waiting."}
    return {"label": "Follows the partner's use", "years": None, "tainted": False,
            "note": "No §735 taint. §735(b) still tacks the partnership's holding period "
                    "onto the partner's."}


def calc_751b_flag(hot_before_pct, hot_after_pct):
    """§751(b) — a disproportionate distribution.

    Where a distribution shifts a partner's interest in hot assets, the shift is torn out
    and treated as a taxable exchange between the partner and the partnership. This reports
    whether the shift exists; measuring it requires valuing every §751 asset, which is a
    separate exercise."""
    shift = hot_after_pct - hot_before_pct
    return {
        "disproportionate": abs(shift) > 0.0001,
        "shift": shift,
        "note": ("The partner's interest in unrealised receivables and substantially "
                 "appreciated inventory changed, so §751(b) recharacterises the shift as a "
                 "taxable exchange at fair market value — outside §731 and §732 entirely. "
                 "The exchange has to be valued asset by asset."
                 if abs(shift) > 0.0001 else
                 "The distribution is proportionate in hot assets, so §751(b) does not "
                 "disturb the §731 and §732 result."),
    }
