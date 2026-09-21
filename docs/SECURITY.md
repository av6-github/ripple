# RIPPLE — Security Checklist

## Secrets

- [ ] No secrets in Git
- [ ] No secrets in frontend
- [ ] `.env` ignored
- [ ] CI secrets configured
- [ ] ML service key protected
- [ ] Supabase service role key backend-only

---

# Authentication

- [ ] Supabase JWT verified
- [ ] Token expiry handled
- [ ] Invalid tokens rejected

---

# Authorization

- [ ] Bank routes protected
- [ ] SME routes protected
- [ ] Admin routes protected
- [ ] SME tenant isolation tested
- [ ] Officer-only actions protected

---

# Database

- [ ] RLS enabled
- [ ] RLS tested
- [ ] migrations reviewed
- [ ] service-role usage restricted

---

# Upload Security

- [ ] MIME sniffing
- [ ] file size limit
- [ ] extension validation
- [ ] malicious input considered
- [ ] uploaded content not blindly executed

---

# API

- [ ] CORS restricted
- [ ] rate limiting
- [ ] request validation
- [ ] typed error handling
- [ ] downstream timeout
- [ ] retry policy controlled

---

# ML Service

- [ ] service key required
- [ ] unauthenticated requests rejected
- [ ] model version returned
- [ ] invalid input rejected
- [ ] failure does not fabricate PD

---

# Logging

Never log:

- passwords
- tokens
- API keys
- raw uploaded files
- sensitive financial information
- unnecessary PII

---

# Frontend

- [ ] no backend secret in bundle
- [ ] only public Supabase key exposed
- [ ] protected routes enforced
- [ ] sensitive data not persisted unnecessarily

---

# Deployment

- [ ] environment variables configured
- [ ] production secrets rotated before demo
- [ ] CORS production domain
- [ ] debug mode disabled