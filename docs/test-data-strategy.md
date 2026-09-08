# Test Data & PII Handling Strategy

NexusQA never uses real or real-looking card numbers or personal data anywhere in the codebase, fixtures, or logs.
- Payment simulation uses Stripe's published test card numbers exclusively.
- Synthetic customer data (names, addresses, emails) is generated via Faker.

