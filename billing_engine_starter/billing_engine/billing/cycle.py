"""
BillingCycle — finds due subscriptions, generates invoices, posts ledger DEBITs,
advances the subscription period. Must be IDEMPOTENT (safe to run twice).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

from billing_engine.db import (
    Database,
    CustomerRepository, PlanRepository, SubscriptionRepository,
    UsageRecordRepository, InvoiceRepository, InvoiceLineItemRepository,
    LedgerRepository,
)
from billing_engine.models import Subscription


@dataclass
class BillingResult:
    invoices_created: int
    invoices_skipped_duplicate: int
    trials_activated: int


class BillingCycle:
    """Day-3 deliverable. Day-4 stretch: add `upgrade_subscription(...)`."""

    def __init__(
        self,
        db: Database,
        customer_repo: CustomerRepository,
        plan_repo: PlanRepository,
        subscription_repo: SubscriptionRepository,
        usage_repo: UsageRecordRepository,
        invoice_repo: InvoiceRepository,
        line_item_repo: InvoiceLineItemRepository,
        ledger_repo: LedgerRepository,
        strategy_factory: Callable,    # given a Plan, returns a PricingStrategy
        discount_factory: Callable,    # given a discount_id or None, returns a Discount or None
        tax_factory: Callable,         # given a Customer, returns (TaxCalculator, TaxContext)
    ) -> None:
        self.db = db
        self.customer_repo = customer_repo
        self.plan_repo = plan_repo
        self.subscription_repo = subscription_repo
        self.usage_repo = usage_repo
        self.invoice_repo = invoice_repo
        self.line_item_repo = line_item_repo
        self.ledger_repo = ledger_repo
        self.strategy_factory = strategy_factory
        self.discount_factory = discount_factory
        self.tax_factory = tax_factory

    # --------------------------------------------------------
    def run(self, as_of: date) -> BillingResult:
        """Bill all subscriptions whose current period ends on or before `as_of`."""
        # TODO Day 3
        invoices_created = 0
        invoices_skipped_duplicate = 0
        trials_activated = 0

        # 1. Find subscriptions due for billing
        due_subs = self.subscription_repo.get_due_for_billing(as_of)

        for sub in due_subs:
            plan = self.plan_repo.get(sub.plan_id)
            customer = self.customer_repo.get(sub.customer_id)

            # Activate trial if needed
            if sub.status == SubscriptionStatus.TRIALING and sub.trial_end and sub.trial_end <= as_of:
                self.subscription_repo.update_status(sub.id, SubscriptionStatus.ACTIVE)
                trials_activated += 1

            # Pricing strategy
            strategy = self.strategy_factory(plan)

            # Discount (if any)
            discount = self.discount_factory(getattr(sub, "discount_id", None))

            # Tax calculator/context
            tax_calc, tax_ctx = self.tax_factory(customer)

            # Usage quantity (if usage-based plan)
            usage_quantity = self.usage_repo.sum_for_period(
                sub.id, metric="api_calls",  # example metric
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
            )

            # Build invoice (pure function)
            invoice_count = self.invoice_repo.count_for_subscription(sub.id)
            invoice = build_invoice(
                subscription=sub,
                plan=plan,
                strategy=strategy,
                discount=discount,
                tax_calc=tax_calc,
                tax_context=tax_ctx,
                usage_quantity=usage_quantity,
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                invoice_count_so_far=invoice_count,
            )

            # 2. Persist invoice (idempotent: duplicates skipped)
            try:
                invoice = self.invoice_repo.add(invoice)
                invoices_created += 1
            except sqlite3.IntegrityError:
                invoices_skipped_duplicate += 1
                continue

            # 3. Persist line items
            for li in invoice.line_items:
                li.invoice_id = invoice.id
                self.line_item_repo.add(li)

            # 4. Post ledger DEBIT
            self.ledger_repo.add(
                LedgerEntry(
                    id=None,
                    customer_id=sub.customer_id,
                    invoice_id=invoice.id,
                    direction=LedgerDirection.DEBIT,
                    amount=invoice.total,
                    occurred_at=as_of,
                    description=f"Invoice {invoice.id} for subscription {sub.id}",
                )
            )

            # 5. Advance subscription period
            self.subscription_repo.update_period(
                sub.id,
                new_start=sub.current_period_end,
                new_end=sub.current_period_end + plan.billing_period.delta(),
            )

        return BillingResult(
            invoices_created=invoices_created,
            invoices_skipped_duplicate=invoices_skipped_duplicate,
            trials_activated=trials_activated,
        )
            
    # --------------------------------------------------------
    def upgrade_subscription(self, subscription_id: int, new_plan_id: int, switch_date: date) -> None:
        """Mid-cycle upgrade — Day 4 stretch."""
        # TODO Day 4
        raise NotImplementedError("Day 4: implement BillingCycle.upgrade_subscription")
