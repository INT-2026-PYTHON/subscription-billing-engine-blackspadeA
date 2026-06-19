"""
CLI entrypoint.

Subcommands to implement (Day 4):
    billing init                              -- create / migrate the DB
    billing customer add <name> <email> <country> [--state CODE]
    billing plan list
    billing subscribe <customer_id> <plan_id> [--trial-days N] [--discount CODE]
    billing bill run [--date YYYY-MM-DD]
    billing invoice show <invoice_id>          -- prints PLAIN TEXT invoice
    billing upgrade <subscription_id> <new_plan_id> [--date YYYY-MM-DD]   (STRETCH)
    billing demo                              -- run the scripted scenario

Use argparse with subparsers. Keep each subcommand handler in its own function.

PDF rendering is OUT OF SCOPE for the core project — `invoice show` should
print a clean PLAIN-TEXT invoice (see helper `format_invoice_text` below).
PDF generation is BONUS: see `billing_engine/pdf/renderer.py`.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from billing_engine.models import Invoice


def format_invoice_text(invoice: Invoice, customer_name: str, plan_name: str) -> str:
    """Render an invoice as a plain-text receipt. Pure function — easy to test."""
    # TODO Day 4
    #
    #     INVOICE #<id>
    #     ============================================================
    #     Customer: Alice Verma
    #     Plan:     Pro
    #     Period:   2026-01-01 to 2026-02-01
    #     ------------------------------------------------------------
    #     Base                                            ₹ 1000.00
    #     Discount (10%)                                  ₹  -100.00
    #     CGST (9%)                                       ₹    81.00
    #     SGST (9%)                                       ₹    81.00
    #     ------------------------------------------------------------
    #     TOTAL                                           ₹  1062.00
    #     Status: ISSUED
    #
    # Use invoice.line_items, invoice.total, invoice.status, invoice.period_start/end.
    raise NotImplementedError("Day 4: implement format_invoice_text")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="billing", description="Subscription Billing CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # TODO Day 4
     subscribe = sub.add_parser("subscribe", help="create subscription")
    sub.add_parser("init", help="initialize the database")
     cust_add = sub.add_parser("customer", help="customer operations")
    cust_sub = cust_add.add_subparsers(dest="subcmd", required=True)
    cust_add_cmd = cust_sub.add_parser("add", help="add a customer")
    cust_add_cmd.add_argument("name")
    cust_add_cmd.add_argument("email")
    cust_add_cmd.add_argument("country")
    cust_add_cmd.add_argument("--state")
    sub.add_parser("demo", help="run the demo scenario")
    # TODO Day 4
    subscribe.add_argument("customer_id", type=int)
    subscribe.add_argument("plan_id", type=int)
    subscribe.add_argument("--trial-days", type=int)
    subscribe.add_argument("--discount")

    # bill run
    bill = sub.add_parser("bill", help="billing operations")
    bill_sub = bill.add_subparsers(dest="subcmd", required=True)
    bill_run = bill_sub.add_parser("run", help="run billing cycle")
    bill_run.add_argument("--date", type=str)

    # invoice show
    inv = sub.add_parser("invoice", help="invoice operations")
    inv_sub = inv.add_subparsers(dest="subcmd", required=True)
    inv_show = inv_sub.add_parser("show", help="show invoice")
    inv_show.add_argument("invoice_id", type=int)

    # upgrade (stretch)
    upgrade = sub.add_parser("upgrade", help="upgrade subscription")
    upgrade.add_argument("subscription_id", type=int)
    upgrade.add_argument("new_plan_id", type=int)
    upgrade.add_argument("--date", type=str)

    # demo
    sub.add_parser("demo", help="run the demo scenario")

    args = parser.parse_args(argv)

    # Dispatch
    if args.cmd == "init":
        return handle_init()
    elif args.cmd == "customer" and args.subcmd == "add":
        return handle_customer_add(args)
    elif args.cmd == "plan" and args.subcmd == "list":
        return handle_plan_list()
    elif args.cmd == "subscribe":
        return handle_subscribe(args)
    elif args.cmd == "bill" and args.subcmd == "run":
        return handle_bill_run(args)
    elif args.cmd == "invoice" and args.subcmd == "show":
        return handle_invoice_show(args)
    elif args.cmd == "upgrade":
        return handle_upgrade(args)
    elif args.cmd == "demo":
        return run_demo()
    else:
        print(f"Unknown command {args.cmd}", file=sys.stderr)
        return 2

def run_demo() -> int:
    """Scripted end-to-end scenario for the `demo` subcommand.

    Should mirror `tests/test_demo_scenario.py::TestEndToEndScenario::test_full_lifecycle`
    and print a human-readable summary to stdout.
    """
    # TODO Day 4
def handle_invoice_show(args) -> int:
    invoice = invoice_repo.get(args.invoice_id)
    if not invoice:
        print("Invoice not found", file=sys.stderr)
        return 1
    customer = customer_repo.get(invoice.subscription.customer_id)
    plan = plan_repo.get(invoice.plan_id)
    print(format_invoice_text(invoice, customer.name, plan.name))
    return 0
