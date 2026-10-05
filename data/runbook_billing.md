---
source_id: rb-billing-v1
tenant_id: 1
version: 1
---

# Billing Runbook

## Invoice total is wrong
1. Compare the invoice line items to the original order record.
2. Check for duplicate charges on the same billing period.
3. Verify tax and discount rules were applied for the customer's region.
4. If a discrepancy is confirmed, escalate to the billing owner; do not issue refunds automatically.

## Duplicate charge
1. Identify both charge IDs and their timestamps.
2. Confirm the charges are for the same service period.
3. Mark the duplicate for reversal through the billing system; do not reverse manually.
4. Notify the customer within one business day.

## Tax or discount mismatch
1. Verify the customer's billing region and tax profile.
2. Confirm any active promotions were applied correctly.
3. If the discount was missed, issue a corrected invoice through the standard flow.

## Refund requests
1. Refund requests are out of scope for the automated copilot.
2. Route to the billing owner with the customer's account ID and invoice number.
3. Do not promise a refund on behalf of the company.