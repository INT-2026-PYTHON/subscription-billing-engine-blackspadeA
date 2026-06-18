"""
Repositories — the ONLY place SQL lives.

Each repository wraps the Database connection and exposes methods that
take/return domain dataclasses (defined in billing_engine/models/).

⚠️ YOU IMPLEMENT every method body marked TODO.
   The signatures, docstrings, and the LedgerRepository's append-only
   guarantee are already in place — do not change them.

Conventions:
  - Always use parameterized queries (`?` placeholders) — NEVER f-string SQL.
  - Money values are persisted as TEXT using `money.to_storage()`.
  - Dates are persisted as ISO strings (`date.isoformat()`).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from billing_engine.db.database import Database
from billing_engine.money import Money
from billing_engine.models import (
    Customer,
    Plan, PricingType, BillingPeriod,
    Subscription, SubscriptionStatus,
    Invoice, InvoiceStatus, InvoiceLineItem, LineItemKind,
    LedgerEntry, LedgerDirection,
)


# ============================================================
# CUSTOMERS
# ============================================================
class CustomerRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, customer: Customer) -> Customer:
        """Insert and return the customer with `id` populated."""
        # TODO Day 2
       cur = self.db.conn.cursor()
        cur.execute(
            "INSERT INTO customers (name, email) VALUES (?, ?)",
            (customer.name, customer.email),
        )
        customer.id = cur.lastrowid
        return customer

    def get(self, customer_id: int) -> Optional[Customer]:
        # TODO Day 2
       cur = self.db.conn.cursor()
        cur.execute("SELECT id, name, email FROM customers WHERE id = ?", (customer_id,))
        row = cur.fetchone()
        if not row:
            return None
        return Customer(id=row[0], name=row[1], email=row[2])

    def find_by_email(self, email: str) -> Optional[Customer]:
        # TODO Day 2
        cur = self.db.conn.cursor()
        cur.execute("SELECT id, name, email FROM customers WHERE email = ?", (email,))
        row = cur.fetchone()
        if not row:
            return None
        return Customer(id=row[0], name=row[1], email=row[2])

    def list_all(self) -> list[Customer]:
        # TODO Day 2
       cur = self.db.conn.cursor()
        cur.execute("SELECT id, name, email FROM customers")
        rows = cur.fetchall()
        return [Customer(id=r[0], name=r[1], email=r[2]) for r in rows]
# ============================================================
# PLANS  +  PLAN TIERS
# ============================================================
class PlanRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, plan: Plan) -> Plan:
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            """INSERT INTO plans (name, pricing_type, amount, currency, billing_period)
               VALUES (?, ?, ?, ?, ?)""",
            (
                plan.name,
                plan.pricing_type.value,
                plan.amount.to_storage(),
                plan.amount.currency,
                plan.billing_period.value,
            ),
        )
        plan.id = cur.lastrowid
        return plan

    def get(self, plan_id: int) -> Optional[Plan]:
        # TODO Day 2.
      cur = self.db.conn.cursor()
        cur.execute(
            "SELECT id, name, pricing_type, amount, currency, billing_period FROM plans WHERE id = ?",
            (plan_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Plan(
            id=row[0],
            name=row[1],
            pricing_type=PricingType(row[2]),
            amount=Money.from_storage(row[3], row[4]),
            billing_period=BillingPeriod(row[5]),
        )

    def list_all(self) -> list[Plan]:
        # TODO Day 2.
         cur = self.db.conn.cursor()
        cur.execute("SELECT id, name, pricing_type, amount, currency, billing_period FROM plans")
        rows = cur.fetchall()
        return [
            Plan(
                id=r[0],
                name=r[1],
                pricing_type=PricingType(r[2]),
                amount=Money.from_storage(r[3], r[4]),
                billing_period=BillingPeriod(r[5]),
            )
            for r in rows
        ]

class PlanTierRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, plan_id: int, from_units: int, to_units: Optional[int], unit_price: Money) -> int:
        """Insert a tier; return new id."""
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            "INSERT INTO plan_tiers (plan_id, from_units, to_units, unit_price) VALUES (?, ?, ?, ?)",
            (plan_id, from_units, to_units, unit_price.to_storage()),
        )
        return cur.lastrowid

    def list_for_plan(self, plan_id: int, currency: str) -> list[tuple[int, Optional[int], Money]]:
        """Return [(from_units, to_units, unit_price)] ordered by from_units.

        Currency is passed in (the plan_tiers table stores only the amount;
        currency lives on the parent plan).
        """
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            "SELECT from_units, to_units, unit_price FROM plan_tiers WHERE plan_id = ? ORDER BY from_units",
            (plan_id,),
        )
        rows = cur.fetchall()
        return [(r[0], r[1], Money.from_storage(r[2], currency)) for r in rows]

# ============================================================
# DISCOUNTS
# ============================================================
class DiscountRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, code: str, discount_type: str, value: str, currency: Optional[str] = None) -> int:
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            "INSERT INTO discounts (code, discount_type, value, currency) VALUES (?, ?, ?, ?)",
            (code, discount_type, value, currency),
        )
        return cur.lastrowid

    def get_by_code(self, code: str) -> Optional[dict]:
        """Return raw row as dict, or None. (Discount has no dataclass yet — we use a dict for now.)"""
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            "SELECT id, code, discount_type, value, currency FROM discounts WHERE code = ?",
            (code,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "code": row[1],
            "discount_type": row[2],
            "value": row[3],
            "currency": row[4],
        }

# ============================================================
# SUBSCRIPTIONS
# ============================================================
class SubscriptionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, subscription: Subscription) -> Subscription:
        # TODO Day 2.
         cur = self.db.conn.cursor()
        cur.execute(
            """INSERT INTO subscriptions
               (customer_id, plan_id, status, current_period_start, current_period_end, trial_end)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                subscription.customer.id,
                subscription.plan.id,
                subscription.status.value,
                subscription.current_period_start.isoformat(),
                subscription.current_period_end.isoformat(),
                subscription.trial_end.isoformat() if subscription.trial_end else None,
            ),
        )
        subscription.id = cur.lastrowid
        return subscription

    def get(self, subscription_id: int) -> Optional[Subscription]:
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            """SELECT id, customer_id, plan_id, status, current_period_start, current_period_end, trial_end
               FROM subscriptions WHERE id = ?""",
            (subscription_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Subscription(
            id=row[0],
            customer_id=row[1],
            plan_id=row[2],
            status=SubscriptionStatus(row[3]),
            current_period_start=date.fromisoformat(row[4]),
            current_period_end=date.fromisoformat(row[5]),
            trial_end=date.fromisoformat(row[6]) if row[6] else None,
        )

    def list_all(self) -> list[Subscription]:
        """All subscriptions, regardless of status. Used by BillingCycle trial scan."""
        # TODO Day 2.
      cur = self.db.conn.cursor()
        cur.execute(
            "SELECT id, customer_id, plan_id, status, current_period_start, current_period_end, trial_end FROM subscriptions"
        )
        rows = cur.fetchall()
        return [
            Subscription(
                id=r[0],
                customer_id=r[1],
                plan_id=r[2],
                status=SubscriptionStatus(r[3]),
                current_period_start=date.fromisoformat(r[4]),
                current_period_end=date.fromisoformat(r[5]),
                trial_end=date.fromisoformat(r[6]) if r[6] else None,
            )
            for r in rows
        ]

    def get_due_for_billing(self, as_of: date) -> list[Subscription]:
        """Subscriptions whose current_period_end <= as_of AND status is ACTIVE.
        (Hint: trial subscriptions whose trial_end <= as_of should also become billable —
         either handle that here or transition them to ACTIVE first in BillingCycle.)
        """
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(            (as_of.isoformat(), SubscriptionStatus.ACTIVE.value),
        )
        rows = cur.fetchall()
        return [
            Subscription(
                id=r[0],
                customer_id=r[1],
                plan_id=r[2],
                status=SubscriptionStatus(r[3]),
                current_period_start=date.fromisoformat(r[4]),
                current_period_end=date.fromisoformat(r[5]),
                trial_end=date.fromisoformat(r[6]) if r[6] else None,
            )
            for r in rows
        ]

    def update_period(self, subscription_id: int, new_start: date, new_end: date) -> None:
        # TODO Day 2.
        cur = self.db.conn.cursor()
        cur.execute(
            (new_start.isoformat(), new_end.isoformat(), subscription_id),
        )
    def update_status(
        self,
        subscription_id: int,
        new_status: SubscriptionStatus,
        past_due_since: Optional[date] = None,
    ) -> None:
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            (new_status.value, past_due_since.isoformat() if past_due_since else None, subscription_id),
        )
    def update_plan(self, subscription_id: int, new_plan_id: int) -> None:
        """Switch the subscription to a different plan (used by upgrade flow)."""
        # TODO Day 4.
        raise NotImplementedError("Day 4: implement SubscriptionRepository.update_plan")


# ============================================================
# USAGE
# ============================================================
class UsageRecordRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, subscription_id: int, metric: str, quantity: int) -> int:
        # TODO Day 2.
        cur = self.db.conn.cursor()
        cur.execute(
            (subscription_id, metric, quantity, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid
       
    def sum_for_period(
        self, subscription_id: int, metric: str, period_start: date, period_end: date
    ) -> int:
        # TODO Day 2: SELECT COALESCE(SUM(quantity), 0) ...
        cur = self.db.conn.cursor()
        cur.execute(
            """SELECT COALESCE(SUM(quantity), 0)
               FROM usage_records
               WHERE subscription_id = ?
                 AND metric = ?
                 AND created_at >= ?
                 AND created_at <= ?""",
            (
                subscription_id,
                metric,
                period_start.isoformat(),
                period_end.isoformat(),
            ),
        )
        return cur.fetchone()[0]
       
# ============================================================
# INVOICES + LINE ITEMS
# ============================================================
class InvoiceRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, invoice: Invoice) -> Invoice:
        """Insert invoice (NOT line items — that's the other repo).

        Must respect the UNIQUE(subscription_id, period_start) constraint.
        If a duplicate is attempted, raise sqlite3.IntegrityError naturally
        (caller is responsible for handling it — this gives idempotency).
        """
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            """INSERT INTO invoices
               (subscription_id, plan_id, period_start, period_end, status, subtotal, total)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                invoice.subscription.id,
                invoice.plan.id,
                invoice.period_start.isoformat(),
                invoice.period_end.isoformat(),
                invoice.status.value,
                invoice.subtotal.to_storage(),
                invoice.total.to_storage(),
            ),
        )
        invoice.id = cur.lastrowid
        return invoice

    def get(self, invoice_id: int) -> Optional[Invoice]:
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            """SELECT id, subscription_id, plan_id, period_start, period_end,
                      status, subtotal, total
               FROM invoices WHERE id = ?""",
            (invoice_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Invoice(
            id=row[0],
            subscription_id=row[1],
            plan_id=row[2],
            period_start=date.fromisoformat(row[3]),
            period_end=date.fromisoformat(row[4]),
            status=InvoiceStatus(row[5]),
            subtotal=Money.from_storage(row[6]),
            total=Money.from_storage(row[7]),
            line_items=[],  # handled separately by InvoiceLineItemRepository
        )

    def count_for_subscription(self, subscription_id: int) -> int:
        """Used by FirstMonthFree discount."""
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM invoices WHERE subscription_id = ?",
            (subscription_id,),
        )
        return cur.fetchone()[0]
       
    def mark_paid(self, invoice_id: int) -> None:
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            "UPDATE invoices SET status = ? WHERE id = ?",
            (InvoiceStatus.PAID.value, invoice_id),
        )

    def mark_failed(self, invoice_id: int) -> None:
        # TODO Day 2.
        cur = self.db.conn.cursor()
        cur.execute(
            "UPDATE invoices SET status = ? WHERE id = ?",
            (InvoiceStatus.PAID.value, invoice_id),
        )
    def set_pdf_path(self, invoice_id: int, path: str) -> None:
        # TODO Day 4.
        raise NotImplementedError("Day 4: implement InvoiceRepository.set_pdf_path")


class InvoiceLineItemRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, line_item: InvoiceLineItem) -> InvoiceLineItem:
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            """INSERT INTO invoice_line_items
               (invoice_id, kind, description, amount)
               VALUES (?, ?, ?, ?)""",
            (
                line_item.invoice_id,
                line_item.kind.value,
                line_item.description,
                line_item.amount.to_storage(),
            ),
        )
        line_item.id = cur.lastrowid
        return line_item

    def list_for_invoice(self, invoice_id: int) -> list[InvoiceLineItem]:
        # TODO Day 2.
       cur = self.db.conn.cursor()
        cur.execute(
            """SELECT id, invoice_id, kind, description, amount
               FROM invoice_line_items
               WHERE invoice_id = ?
               ORDER BY id""",
            (invoice_id,),
        )
        rows = cur.fetchall()
        return [
            InvoiceLineItem(
                id=r[0],
                invoice_id=r[1],
                kind=LineItemKind(r[2]),
                description=r[3],
                amount=Money.from_storage(r[4]),
            )
            for r in rows
        ]

# ============================================================
# LEDGER — APPEND-ONLY (do not implement update/delete)
# ============================================================
class LedgerRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, entry: LedgerEntry) -> LedgerEntry:
        # TODO Day 2.
       
    def add(self, entry: LedgerEntry) -> LedgerEntry:
        """Insert a ledger entry and return it with id populated."""
        cur = self.db.conn.cursor()
        cur.execute(
            """INSERT INTO ledger_entries
               (customer_id, invoice_id, direction, amount, currency, occurred_at, description)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.customer_id,
                entry.invoice_id,
                entry.direction.value,
                entry.amount.to_storage(),
                entry.amount.currency,
                entry.occurred_at.isoformat(),
                entry.description,
            ),
        )
        entry.id = cur.lastrowid
        return entry
       
    def list_for_customer(self, customer_id: int) -> list[LedgerEntry]:
        # TODO Day 2.
               """Return all ledger entries for a given customer, ordered by occurred_at."""
        cur = self.db.conn.cursor()
        cur.execute(
            """SELECT id, customer_id, invoice_id, direction, amount, currency, occurred_at, description
               FROM ledger_entries
               WHERE customer_id = ?
               ORDER BY occurred_at""",
            (customer_id,),
        )
        rows = cur.fetchall()
        return [
            LedgerEntry(
                id=r[0],
                customer_id=r[1],
                invoice_id=r[2],
                direction=LedgerDirection(r[3]),
                amount=Money.from_storage(r[4], r[5]),
                occurred_at=datetime.fromisoformat(r[6]),
                description=r[7],
            )
            for r in rows
        ]

    # ✅ These two methods are intentionally implemented to REJECT — do not override.
    def update(self, *args, **kwargs):
        raise NotImplementedError("Ledger is append-only. Post a reversing entry instead.")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Ledger is append-only. Post a reversing entry instead.")


# ============================================================
# PAYMENT ATTEMPTS
# ============================================================
class PaymentAttemptRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(
        self,
        invoice_id: int,
        attempt_no: int,
        status: str,
        failure_reason: Optional[str],
        next_retry_at: Optional[datetime],
    ) -> int:
        # TODO Day 3.
        """Insert a payment attempt and return its new id."""
        cur = self.db.conn.cursor()
        cur.execute(
            """INSERT INTO payment_attempts
               (invoice_id, attempt_no, status, failure_reason, next_retry_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                invoice_id,
                attempt_no,
                status,
                failure_reason,
                next_retry_at.isoformat() if next_retry_at else None,
            ),
        )
        return cur.lastrowid
       
    def list_for_invoice(self, invoice_id: int) -> list[dict]:
        # TODO Day 3.
        """Return all payment attempts for a given invoice as dicts."""
        cur = self.db.conn.cursor()
        cur.execute(
            """SELECT id, invoice_id, attempt_no, status, failure_reason, next_retry_at
               FROM payment_attempts
               WHERE invoice_id = ?
               ORDER BY attempt_no""",
            (invoice_id,),
        )
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "invoice_id": r[1],
                "attempt_no": r[2],
                "status": r[3],
                "failure_reason": r[4],
                "next_retry_at": r[5],
            }
            for r in rows
        ]
       
    def count_for_invoice(self, invoice_id: int) -> int:
        # TODO Day 3.
       """Return the number of payment attempts for a given invoice."""
        cur = self.db.conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM payment_attempts WHERE invoice_id = ?",
            (invoice_id,),
        )
        return cur.fetchone()[0]
