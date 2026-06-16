"""
VATCalculator — single-rate VAT (e.g. 19% in Germany).
"""

from decimal import Decimal

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext, TaxBreakdown


class VATCalculator(TaxCalculator):
    def __init__(self, rate: Decimal) -> None:
        # TODO Day 1
        #   - Validate 0 <= rate <= 1.
        #   - Reject float.
        #   - Store on self.
         if not isinstance(rate, Decimal):
            raise TypeError("VAT rate must be a Decimal, not float")

        if rate < Decimal("0") or rate > Decimal("1"):
            raise ValueError("VAT rate must be between 0 and 1")

        self.rate = rate

    def apply(self, taxable: Money, context: TaxContext) -> TaxBreakdown:
        # TODO Day 1
        #   - vat = taxable * self.rate
        #   - Return TaxBreakdown with one component (f"VAT {percent}%", vat) and total = vat.
        #   - Tip: format the rate as a percentage cleanly.
        vat_amount = taxable.amount * self.rate
        currency = taxable.currency

        percent_str = f"{(self.rate * 100):.0f}%"

        components = [(f"VAT {percent_str}", Money(vat_amount, currency))]
        total = Money(vat_amount, currency)

        return TaxBreakdown(components=components, total=total)
