---
source_id: rb-access-v1
tenant_id: 1
version: 1
---

# Access Runbook

## Cannot sign in
1. Confirm the user exists in the identity provider.
2. Check whether the account is locked due to failed attempts.
3. Verify MFA enrollment status.
4. If locked, unlock after identity verification; do not reset the password by default.

## Account locked
1. Ask the user to wait 15 minutes before retrying; lockouts clear automatically.
2. If the lockout persists, verify the user's identity via a secondary channel.
3. Unlock the account and log the action in the audit trail.

## Password reset
1. Direct the user to the self-service password reset flow.
2. If the user lacks access to the reset email, verify identity before resetting manually.
3. Never send a temporary password via unencrypted email.

## MFA issues
1. Confirm the user has the correct MFA device enrolled.
2. If the device is lost, follow the account-recovery procedure with identity verification.
3. Do not disable MFA without manager approval.