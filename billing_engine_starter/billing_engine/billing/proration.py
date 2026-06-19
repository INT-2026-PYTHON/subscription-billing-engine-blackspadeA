"""
Proration — Day 4 stretch.

Mid-cycle plan change: customer is on Plan A from period_start to period_end,
but on `switch_date` they upgrade (or downgrade) to Plan B.

Day-count proration:
    total_days     = (period_end - period_start).days
    used_days      = (switch_date - period_start).days
    remaining_days = total_days - used_days

    credit = old_price * (remaining_days / total_days)
    charge = new_price * (remaining_days / total_days)

Tax MUST be recalculated on BOTH legs (reverse-tax on the credit,
fresh tax on the new charge). Tax is NOT prorated linearly — the tax
on a proration credit/charge is just `tax_calc.apply(credit_or_charge)`.

The two legs are returned as TAX-INCLUSIVE Money values for the
PRORATION_CREDIT (negative) and PRORATION_CHARGE (positive) line items.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext


@dataclass(frozen=True)
class ProrationResult:
    credit_amount: Money     # always returned as a POSITIVE Money; caller negates for line item
    charge_amount: Money     # always positive
    credit_tax: Money        # tax that was on the credit
    charge_tax: Money        # tax that is on the new charge


def compute_proration(
    old_plan_price: Money,
    new_plan_price: Money,
    period_start: date,
    period_end: date,
    switch_date: date,
    tax_calc: TaxCalculator,
    tax_context: TaxContext,
) -> ProrationResult:
    """Pure function. STRETCH — implement only after Days 1+2 are green."""
    # TODO Day 4
   total_days = (period_end - period_start).days
    used_days = (switch_date - period_start).days
    remaining_days = total_days - used_days

    if total_days <= 0 or remaining_days <= 0:
        # No proration needed
        return ProrationResult(
            credit_amount=Money(0, old_plan_price.currency),
            charge_amount=Money(0, new_plan_price.currency),
            credit_tax=Money(0, old_plan_price.currency),
            charge_tax=Money(0, new_plan_price.currency),
        )

    # Fraction of the period remaining
    fraction = Decimal(remaining_days) / Decimal(total_days)

    # Compute amounts
    credit_amount = Money(old_plan_price.amount * fraction, old_plan_price.currency)
    charge_amount = Money(new_plan_price.amount * fraction, new_plan_price.currency)

    # Compute taxes separately (not prorated linearly)
    credit_tax = tax_calc.apply(credit_amount, tax_context)
    charge_tax = tax_calc.apply(charge_amount, tax_context)

    return ProrationResult(
        credit_amount=credit_amount,
        charge_amount=charge_amount,
        credit_tax=credit_tax,
        charge_tax=charge_tax,
    )
