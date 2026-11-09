---
slug: h-issuer-cert-notbefore
track: harness
priority: P2
---
# issuer.py key: backdate notBefore so a WSL clock step cannot invalidate the gate cert



## alert 72 fault 332 (×1, first 2026-11-09T05:50:33+00:00)
gate flake: fork-tools TokenLogin.test_sign_in_opens_a_session... failed with curl (60) 'certificate is not yet valid' on the 2nd sign_in after the 1st passed with the same cert (gate-3d07ad7cca94.log); issuer.py key makes the self-signed cert with notBefore=now (openssl 3.0 req has no -not_before), so a WSL clock step back mid-gate invalidates it; passes 3/3 on rerun. Fix: backdate notBefore in issuer.py key.
