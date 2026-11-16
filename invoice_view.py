"""
Hermes - Invoice document rendering.

Builds a clean, print-ready HTML invoice from the joined invoice+job row,
with the quote breakdown as line items. The owner opens /invoices/{id}
in a browser and prints/saves as PDF (browser print-to-PDF, no extra deps).
"""

import html

DISPATCH_FEE = 75.0
TAX_RATE = 0.05


def render_invoice_html(inv: dict) -> str:
    e = html.escape
    inv_id = inv.get("id", 0)
    total = float(inv.get("total") or 0)
    paid_amount = float(inv.get("paid_amount") or 0)
    paid = inv.get("status") == "paid"
    balance = max(total - paid_amount, 0.0)

    job_ref = inv.get("job_ref") or f"JOB-{inv.get('job_id')}"
    service = inv.get("service_type") or "Home service"
    created = (inv.get("created_at") or "")[:10]

    # Reconstruct the breakdown exactly as quote_agent did (total includes GST):
    # pre-tax subtotal = total / 1.05; labor = subtotal - dispatch fee.
    subtotal = round(total / (1 + TAX_RATE), 2)
    tax = round(total - subtotal, 2)
    labor_cost = round(subtotal - DISPATCH_FEE, 2)

    status_badge = "PAID" if paid else "SENT"

    # Build conditional rows as plain strings BEFORE the f-string template
    # (f-strings on Python 3.11 cannot nest double quotes in expressions).
    paid_row = (
        f"<tr><td>Amount paid</td><td class='num'>-${paid_amount:.2f}</td></tr>"
        if paid_amount else "")
    balance_row = (
        f"<tr class='grand'><td>Balance</td><td class='num'>${balance:.2f}</td></tr>"
        if not paid else "")
    payment_note = "" if paid else """
  <div class="paid-note">
    Payment can be arranged by phone at (778) 909-4293.
    Thank you for your business.
  </div>"""

    name = e(inv.get("customer_name") or "Customer")
    address = e(inv.get("customer_address") or "")
    phone = e(inv.get("customer_phone") or "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Invoice #{inv_id} — Comox Valley Home Services</title>
<style>
  body {{ font-family: system-ui, sans-serif; color:#111; margin:0; padding:40px; }}
  .head {{ display:flex; justify-content:space-between; align-items:flex-start;
           border-bottom:2px solid #111; padding-bottom:16px; }}
  .co h1 {{ font-size:20px; margin:0; }}
  .co p {{ margin:2px 0; color:#444; font-size:13px; }}
  .doc-title {{ text-align:right; }}
  .doc-title h2 {{ font-size:26px; margin:0; }}
  .doc-title .badge {{ display:inline-block; margin-top:8px; padding:4px 14px;
    border-radius:999px; font-size:13px; font-weight:700; }}
  .badge.paid {{ background:#22c55e; color:#fff; }}
  .badge.sent {{ background:#3b82f6; color:#fff; }}
  .bill {{ display:flex; justify-content:space-between; margin:24px 0; }}
  .bill .to {{ font-size:14px; }}
  .bill .to b {{ display:block; margin-bottom:4px; }}
  table {{ width:100%; border-collapse:collapse; font-size:14px; }}
  th, td {{ padding:10px 12px; border-bottom:1px solid #ddd; text-align:left; }}
  th {{ background:#f4f4f4; }}
  .num {{ text-align:right; }}
  .total td {{ border-top:2px solid #111; font-weight:700; font-size:15px; }}
  .grand td {{ border-top:2px solid #111; font-weight:800; font-size:18px; }}
  .paid-note {{ margin-top:20px; padding:10px 14px; border-radius:8px;
    background:#f0fdf4; border:1px solid #86efac; font-size:14px; }}
  .foot {{ margin-top:40px; font-size:12px; color:#555; border-top:1px solid #ccc; padding-top:12px; }}
  @media print {{ body {{ padding:0; }} }}
</style>
</head>
<body>
  <div class="head">
    <div class="co">
      <h1>Comox Valley Home Services</h1>
      <p>Comox Valley, BC &nbsp;•&nbsp; (778) 909-4293</p>
      <p>GST #12345 6789 RT001</p>
    </div>
    <div class="doc-title">
      <h2>INVOICE</h2>
      <p>#{inv_id} &nbsp;•&nbsp; {created}</p>
      <span class="badge { 'paid' if paid else 'sent' }">{status_badge}</span>
    </div>
  </div>

  <div class="bill">
    <div class="to">
      <b>Bill to</b>
      {name}<br>
      {address}<br>
      {phone}
    </div>
    <div class="to">
      <b>Work order</b>
      {e(job_ref)}<br>
      {e(service.capitalize())}
    </div>
  </div>

  <table>
    <tr><th>Description</th><th class="num">Amount</th></tr>
    <tr><td>Labor — {e(service)} (diagnosis, parts installation, &amp; service call)</td>
        <td class="num">${labor_cost:.2f}</td></tr>
    <tr><td>Dispatch &amp; admin fee</td><td class="num">${DISPATCH_FEE:.2f}</td></tr>
    <tr class="total"><td>Subtotal</td><td class="num">${subtotal:.2f}</td></tr>
    <tr><td>GST ({TAX_RATE:.0%})</td><td class="num">${tax:.2f}</td></tr>
    <tr class="grand"><td>Total due</td><td class="num">${total:.2f}</td></tr>
    {paid_row}
    {balance_row}
  </table>

  {payment_note}

  <div class="foot">
    Invoice #{inv_id} • Comox Valley Home Services • Questions? Call (778) 909-4293
  </div>
</body>
</html>"""
