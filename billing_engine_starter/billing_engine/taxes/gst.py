"""
GSTCalculator — Indian Goods & Services Tax.

The rule:
    - If customer_state == seller_state (or seller_state is "")  =>  intra-state
        -> charge CGST + SGST (split equally, e.g. 9% + 9% = 18%)
    - Else  =>  inter-state
        -> charge IGST (e.g. 18%)

Customers without a state code default to IGST (safe choice).
"""

from decimal import Decimal

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext, TaxBreakdown


class GSTCalculator(TaxCalculator):
    def __init__(self, cgst: Decimal, sgst: Decimal, igst: Decimal) -> None:
        # TODO Day 1
        #   - Validate each rate is Decimal in [0, 1].
        #   - Validate cgst + sgst == igst (sanity check on Indian GST setup).
        #   - Store on self.
        for rate in (cgst, sgst, igst):
            if not isinstance(rate, Decimal):
                raise TypeError("GST rates must be Decimal")
            if rate < Decimal("0") or rate > Decimal("1"):
                raise ValueError("GST rates must be between 0 and 1")

     if cgst + sgst != igst:
            raise ValueError("CGST + SGST must equal IGST")

        self.cgst = cgst
        self.sgst = sgst
        self.igst = igst

    def apply(self, taxable: Money, context: TaxContext) -> TaxBreakdown:
        # TODO Day 1
        #   - Decide intra vs inter-state from context.
        #     intra = bool(context.customer_state) and context.customer_state == context.seller_state
        #   - If intra: components = [("CGST X%", taxable*cgst), ("SGST Y%", taxable*sgst)], total = sum
        #   - Else:     components = [("IGST Z%", taxable*igst)],                            total = igst leg
        intra = bool(context.customer_state) and (
            context.customer_state == context.seller_state or not context.seller_state
        )

        components = []
        total = 0
        currency = taxable.currency

        if intra:
            cgst_amount = taxable.amount * self.cgst
            sgst_amount = taxable.amount * self.sgst
            components.append((f"CGST {self.cgst*100}%", Money(cgst_amount, currency)))
            components.append((f"SGST {self.sgst*100}%", Money(sgst_amount, currency)))
            total = cgst_amount + sgst_amount
        else:
            igst_amount = taxable.amount * self.igst
            components.append((f"IGST {self.igst*100}%", Money(igst_amount, currency)))
            total = igst_amount

        return TaxBreakdown(
            components=components,
            total=Money(total, currency)
        )
