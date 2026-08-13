"""Sale of a partnership interest — §741, §751(a), §752(d), §743(b).

§741 is one sentence: gain or loss on the sale of a partnership interest is capital.
§751(a) is the exception that swallows most of the examinable content, and the two traps
around it are what separate a candidate who has read the section from one who has worked
with it.

**The debt is part of the price.** §752(d) puts the seller's share of partnership
liabilities into the amount realised, because the buyer has taken it over. A partner can
sell an interest for no cash at all and still have a large gain.

**Ordinary income is computed first, and the capital number is the residual.** §751(a)
carves out the seller's share of the gain in unrealised receivables and inventory and makes
it ordinary — before §741 sees anything. The consequence people miss is that the residual
can be a capital *loss* on a sale that produced an overall gain, and the two are taxed
separately.

**Inventory does not have to be appreciated on a sale.** The "substantially appreciated"
test lives in §751(b) and applies to disproportionate distributions. For a sale under
§751(a) any inventory item counts. This is the single most common error on the topic.
"""

# §751(c) unrealised receivables reach further than the accounting term. The flush language
# pulls in depreciation recapture that would arise if the partnership sold the asset, so a
# cash-basis partnership with no receivables on its books can still have §751 assets.
HOT_CLASSES = {
    "receivable": "Unrealised receivable — §751(c)",
    "inventory": "Inventory item — §751(d)",
    "recapture": "Depreciation recapture — §751(c) flush language",
}


def calc_amount_realized(cash=0.0, property_fmv=0.0, liabilities_relieved=0.0):
    """§1001 and §752(d). The buyer taking over the seller's share of partnership debt is
    consideration, exactly as an assumption of a mortgage would be on a sale of land."""
    return {"cash": cash, "property": property_fmv, "debt_relief": liabilities_relieved,
            "total": cash + property_fmv + liabilities_relieved}


def calc_751a_ordinary(hot_assets=(), ownership_pct=1.0):
    """The seller's share of the gain sitting in §751 assets.

    Each item contributes its own gain, floored at zero — a receivable standing at a loss
    does not shelter the ordinary income from another one, because §751(a) looks at the
    partner's share of what the partnership would report on a sale of each asset."""
    rows, total = [], 0.0
    for a in hot_assets:
        gain = max(0.0, a.get("fmv", 0.0) - a.get("basis", 0.0))
        cap = a.get("cap")
        if cap is not None:
            gain = min(gain, cap)
        share = gain * ownership_pct
        rows.append({"name": a.get("name", ""), "klass": a.get("klass", "receivable"),
                     "partnership_gain": gain, "partner_share": share})
        total += share
    return {"rows": rows, "ordinary": total}


def calc_sale_of_interest(cash=0.0, property_fmv=0.0, liabilities_relieved=0.0,
                          outside_basis=0.0, hot_assets=(), ownership_pct=1.0,
                          holding_period_months=0):
    """One partner's sale, split into its ordinary and capital halves."""
    ar = calc_amount_realized(cash, property_fmv, liabilities_relieved)
    hot = calc_751a_ordinary(hot_assets, ownership_pct)

    total_gain = ar["total"] - outside_basis
    ordinary = hot["ordinary"]
    capital = total_gain - ordinary
    long_term = holding_period_months > 12

    return {
        "amount_realized": ar,
        "outside_basis": outside_basis,
        "total_gain": total_gain,
        "ordinary_751a": ordinary,
        "capital_741": capital,
        "long_term": long_term,
        "character": ("Long-term capital" if long_term else "Short-term capital")
                     + (" gain" if capital >= 0 else " loss"),
        "hot_rows": hot["rows"],
        # The pattern worth recognising on sight: ordinary income alongside a capital loss,
        # out of a transaction that made money overall.
        "ordinary_with_capital_loss": ordinary > 0 and capital < 0,
        "form_8308_required": ordinary > 0,
    }


def calc_buyer_basis(purchase_price=0.0, liabilities_assumed=0.0):
    """§742 and §1012. The buyer's outside basis is the cost plus the share of partnership
    debt they have stepped into — the mirror of §752(d) on the seller's side."""
    return {"cost": purchase_price, "liabilities": liabilities_assumed,
            "outside_basis": purchase_price + liabilities_assumed}


def calc_743b(buyer_outside_basis=0.0, share_of_inside_basis=0.0, election_in_effect=False,
              substantial_built_in_loss=False):
    """§743(b). Without a §754 election the partnership's basis in its assets does not move
    when an interest changes hands, so the buyer inherits the seller's share of inside basis
    and is taxed again on gain they paid for.

    The election is not always optional: §743(d) makes the adjustment mandatory where the
    partnership has a **substantial built-in loss**, so the rule cannot be used selectively
    to preserve losses."""
    adjustment = buyer_outside_basis - share_of_inside_basis
    applies = election_in_effect or substantial_built_in_loss
    return {
        "adjustment": adjustment if applies else 0.0,
        "potential_adjustment": adjustment,
        "applies": applies,
        "mandatory": substantial_built_in_loss,
        "note": ("§743(b) steps the buyer's share of inside basis up or down to match what "
                 "they paid. The adjustment belongs to that partner alone — it never "
                 "touches the other partners' shares, and §755 governs how it is spread "
                 "across the assets."
                 if applies else
                 "No §754 election and no substantial built-in loss, so inside basis does "
                 "not move. The buyer inherits the seller's share of the partnership's "
                 "basis and will be taxed a second time on gain that was already priced "
                 "into what they paid."),
    }


def calc_704c_transfer(seller_item_n=0.0):
    """Reg. §1.704-3(a)(7). The buyer steps into the seller's §704(c) shoes.

    Built-in gain attaches to the property, not to the person, so selling the interest does
    not wash it away — the balance the seller reported at Item N moves across to the buyer
    and keeps running."""
    return {
        "transferred": seller_item_n,
        "note": ("The §704(c) balance follows the interest. The seller's Item N goes to "
                 "zero and the buyer picks it up at the same figure, still tied to the same "
                 "contributed property."
                 if abs(seller_item_n) > 0.005 else
                 "No §704(c) balance attached to this interest, so nothing transfers."),
    }
