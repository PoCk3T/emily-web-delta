"""Seed a first admin user and default monitoring URLs.

This script is the source of truth for the monitored URL list and is safe to
re-run. Its contract is deliberately *additive*:

  * URLs in DEFAULT_URLS that do not exist yet are created.
  * URLs that already exist are left alone apart from being tagged as seeded.
    Their interval and schedule are never rewritten, so operator changes made
    through the UI/API survive a re-seed.
  * URLs added manually (not present in DEFAULT_URLS) are never touched or
    removed.

To add new URLs to the deployed system: append entries to DEFAULT_URLS, then
re-run this script on the host (see infra/gcp/DEVOPS_GUIDELINES.md §7).
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

# Add app to path
sys.path.insert(0, "/app")

from app.core.security import hash_password
from app.db.session import async_session_factory, init_db
from app.models.tenant import Tenant
from app.models.url import Url
from app.models.user import User

# Tag applied to every URL managed by this script, so that manually added
# URLs can be distinguished and left untouched.
SEED_TAG = "seeded"

# Default polling cadence for newly seeded URLs (2 hours).
DEFAULT_INTERVAL_SECONDS = 7200

# New URLs have their first check spread across this window so that a large
# batch does not hit every origin at once on the first scheduler tick.
STAGGER_WINDOW_SECONDS = 7200

# Only "selfhosted" URLs are polled by the Celery worker.
DEFAULT_BACKEND = "selfhosted"

# Default URLs to monitor — Terms of Service & Privacy Policies
DEFAULT_URLS = [
    # OpenAI
    {
        "name": "OpenAI Terms of Use",
        "url": "https://openai.com/terms",
        "tags": ["openai", "tos"],
    },
    {
        "name": "OpenAI Privacy Policy",
        "url": "https://openai.com/policies/privacy-policy/",
        "tags": ["openai", "privacy"],
    },
    {
        "name": "OpenAI Business Terms",
        "url": "https://openai.com/policies/business-terms",
        "tags": ["openai", "business", "tos"],
    },
    # Google / Gemini
    {
        "name": "Google Terms of Service",
        "url": "https://policies.google.com/terms",
        "tags": ["google", "gemini", "tos"],
    },
    {
        "name": "Google Cloud Platform Terms of Service",
        "url": "https://cloud.google.com/terms",
        "tags": ["google", "cloud", "business", "tos"],
    },
    {
        "name": "Google Privacy Policy",
        "url": "https://policies.google.com/privacy",
        "tags": ["google", "gemini", "privacy"],
    },
    # Microsoft / Azure
    {
        "name": "Microsoft Services Agreement",
        "url": "https://www.microsoft.com/en-us/servicesagreement",
        "tags": ["microsoft", "tos"],
    },
    {
        "name": "Microsoft Azure Legal Information",
        "url": "https://azure.microsoft.com/en-us/support/legal/subscription-agreement/",
        "tags": ["microsoft", "azure", "business", "tos"],
    },
    # Anthropic
    {
        "name": "Anthropic Terms of Service",
        "url": "https://www.anthropic.com/legal/consumer-terms",
        "tags": ["anthropic", "tos"],
    },
    {
        "name": "Anthropic Commercial Terms of Service",
        "url": "https://www.anthropic.com/legal/commercial-terms",
        "tags": ["anthropic", "business", "tos"],
    },
    {
        "name": "Anthropic Privacy Policy",
        "url": "https://www.anthropic.com/legal/privacy",
        "tags": ["anthropic", "privacy"],
    },
    # Stripe
    {
        "name": "Stripe Privacy Policy",
        "url": "https://stripe.com/privacy",
        "tags": ["stripe", "privacy"],
    },
    # Stripe Pricing - International
    {
        "name": "Stripe Pricing (US)",
        "url": "https://stripe.com/pricing",
        "tags": ["stripe", "pricing", "us"],
    },
    {
        "name": "Stripe Pricing (UK)",
        "url": "https://stripe.com/gb/pricing",
        "tags": ["stripe", "pricing", "gb"],
    },
    {
        "name": "Stripe Pricing (IE)",
        "url": "https://stripe.com/ie/pricing",
        "tags": ["stripe", "pricing", "ie"],
    },
    {
        "name": "Stripe Local Payment Methods (IE)",
        "url": "https://stripe.com/ie/pricing/local-payment-methods",
        "tags": ["stripe", "pricing", "ie", "lpm"],
    },
    {
        "name": "Stripe Pricing (DE)",
        "url": "https://stripe.com/de/pricing",
        "tags": ["stripe", "pricing", "de"],
    },
    {
        "name": "Stripe Local Payment Methods (DE)",
        "url": "https://stripe.com/de/pricing/local-payment-methods",
        "tags": ["stripe", "pricing", "de", "lpm"],
    },
    {
        "name": "Stripe Pricing (SG)",
        "url": "https://stripe.com/en-sg/pricing",
        "tags": ["stripe", "pricing", "sg"],
    },
    {
        "name": "Stripe Pricing (JP)",
        "url": "https://stripe.com/en-jp/pricing",
        "tags": ["stripe", "pricing", "jp"],
    },
    {
        "name": "Stripe Pricing (BR)",
        "url": "https://stripe.com/en-br/pricing",
        "tags": ["stripe", "pricing", "br"],
    },
    {
        "name": "Stripe Connect Pricing (BR)",
        "url": "https://stripe.com/en-br/connect/pricing",
        "tags": ["stripe", "pricing", "br", "connect"],
    },
    {
        "name": "Stripe Pricing (MX)",
        "url": "https://stripe.com/mx/pricing",
        "tags": ["stripe", "pricing", "mx"],
    },
    {
        "name": "Stripe Pricing (EN-MX)",
        "url": "https://stripe.com/en-mx/pricing",
        "tags": ["stripe", "pricing", "mx", "en"],
    },
    {
        "name": "Stripe Local Payment Methods (MX)",
        "url": "https://stripe.com/mx/pricing/local-payment-methods",
        "tags": ["stripe", "pricing", "mx", "lpm"],
    },
    {
        "name": "Stripe Connect Pricing (EN-MX)",
        "url": "https://stripe.com/en-mx/connect/pricing",
        "tags": ["stripe", "pricing", "mx", "connect"],
    },
    {
        "name": "Stripe Pricing (NZ)",
        "url": "https://stripe.com/nz/pricing",
        "tags": ["stripe", "pricing", "nz"],
    },
    {
        "name": "Stripe Pricing (AT)",
        "url": "https://stripe.com/at/pricing",
        "tags": ["stripe", "pricing", "at"],
    },
    {
        "name": "Stripe Pricing (LU)",
        "url": "https://stripe.com/de-lu/pricing",
        "tags": ["stripe", "pricing", "lu"],
    },
    {
        "name": "Stripe Pricing (CH)",
        "url": "https://stripe.com/de-ch/pricing",
        "tags": ["stripe", "pricing", "ch"],
    },
    {
        "name": "Stripe Pricing (AE)",
        "url": "https://stripe.com/ae/pricing",
        "tags": ["stripe", "pricing", "ae"],
    },
    {
        "name": "Stripe Connect Pricing (AE)",
        "url": "https://stripe.com/ae/connect/pricing",
        "tags": ["stripe", "pricing", "ae", "connect"],
    },
    {
        "name": "Stripe Pricing (ES)",
        "url": "https://stripe.com/es/pricing",
        "tags": ["stripe", "pricing", "es"],
    },
    # ─── PG&E — Tariffs, rate schedules, service terms & privacy ───
    # NOTE: most PG&E rate schedules are published as PDFs. They are handled
    # by app/core/pdf_parser.py; the HTML/readability path cannot parse them.
    {
        "name": "PG&E Tariffs Directory",
        "url": "https://www.pge.com/tariffs/en.html",
        "tags": ["pge", "tariffs", "directory"],
    },
    {
        "name": "PG&E Electric Rate Schedule E-1 (Residential Services)",
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_E-1.pdf",
        "tags": ["pge", "tariffs", "electric", "residential", "pdf"],
    },
    {
        "name": "PG&E Gas Rate Schedule G-1 (Residential Service)",
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/GAS_SCHEDS_G-1.pdf",
        "tags": ["pge", "tariffs", "gas", "residential", "pdf"],
    },
    {
        "name": "PG&E Start/Stop/Transfer Service",
        "url": "https://www.pge.com/en/account/service-requests/start-stop-transfer-service.html",
        "tags": ["pge", "service"],
    },
    {
        "name": "PG&E Gas Rate Schedule G-NR1 (Small Commercial)",
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/GAS_SCHEDS_G-NR1.pdf",
        "tags": ["pge", "tariffs", "gas", "commercial", "pdf"],
    },
    {
        "name": "PG&E Gas Rate Schedule G-NR2 (Large Commercial)",
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/GAS_SCHEDS_G-NR2.pdf",
        "tags": ["pge", "tariffs", "gas", "commercial", "pdf"],
    },
    {
        "name": "PG&E Electric Rate Schedule B-1 (Small General Service)",
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_B-1.pdf",
        "tags": ["pge", "tariffs", "electric", "commercial", "pdf"],
    },
    {
        "name": "PG&E Electric Rate Schedule A-1 (Small General Service)",
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_A-1.pdf",
        "tags": ["pge", "tariffs", "electric", "commercial", "pdf"],
    },
    {
        "name": "PG&E Electric Rate Schedule B-10 (Medium General Service)",
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_B-10.pdf",
        "tags": ["pge", "tariffs", "electric", "commercial", "pdf"],
    },
    {
        "name": "PG&E Electric Rate Schedule E-19 (Medium Commercial TOU)",
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_E-19.pdf",
        "tags": ["pge", "tariffs", "electric", "commercial", "pdf"],
    },
    {
        "name": "PG&E Electric Rate Schedule B-20 (Large Commercial Service)",
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_B-20.pdf",
        "tags": ["pge", "tariffs", "electric", "commercial", "pdf"],
    },
    {
        "name": "PG&E Electric Rate Schedule E-20 (Large Commercial Service)",
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_E-20.pdf",
        "tags": ["pge", "tariffs", "electric", "commercial", "pdf"],
    },
    {
        "name": (
            "PG&E Form 79-716: General Terms and Conditions for Extension "
            "& Service Construction"
        ),
        "url": "https://www.pge.com/tariffs/assets/pdf/tariffbook/GAS_FORMS_79-716.pdf",
        "tags": ["pge", "tariffs", "gas", "forms", "tos", "pdf"],
    },
    {
        "name": "PG&E Business Customer Service",
        "url": "https://www.pge.com/en/business-resources/business-customer-service.html",
        "tags": ["pge", "business", "service"],
    },
    {
        "name": "PG&E Website Terms of Use & Disclosure",
        "url": "https://www.pge.com/en/privacy-center/disclosure.html",
        "tags": ["pge", "tos"],
    },
    {
        "name": "PG&E Online Account Terms of Use",
        "url": "https://myportal.pge.com/saphrportal/rules/TandC.html",
        "tags": ["pge", "tos", "account"],
    },
    {
        # Client-rendered SPA: a plain HTTP fetch returns an empty shell, so
        # this must be rendered by CloakBrowser. Without js_required the
        # snapshot would be blank yet hash consistently, hiding all changes.
        "name": "PG&E Safety Action Center Terms of Service",
        "url": "https://www.safetyactioncenter.pge.com/terms",
        "tags": ["pge", "tos", "safety"],
        "js_required": True,
    },
    {
        "name": "PG&E Privacy Policy",
        "url": "https://www.pge.com/en/privacy-center/privacy-policy.html",
        "tags": ["pge", "privacy"],
    },
    # ─────────────────────────────────────────────────────────────────────
    # Largest U.S. banks — retail consumer pricing, fees and disclosures.
    #
    # Tracking `utm_source` query parameters was deliberately dropped from
    # these URLs: they do not change the document served, but they do become
    # part of the stored URL and would make the same page unmatchable if it
    # were ever added again without the parameter.
    # ─────────────────────────────────────────────────────────────────────
    # JPMorgan Chase & Co.
    {
        "name": "Chase Checking Accounts & Pricing",
        "url": "https://personal.chase.com/personal/checking",
        "tags": ["bank", "chase", "jpmorgan", "pricing", "fees"],
    },
    {
        "name": "Chase Personal Disclosures & Interest Rates",
        "url": "https://www.chase.com/digital/disclosures-and-interest-rates-personal",
        "tags": ["bank", "chase", "jpmorgan", "disclosures", "rates"],
    },
    {
        "name": "Chase Additional Banking Services and Fees",
        "url": "https://www.chase.com/content/dam/chase-ux/documents/personal/checking/ABSF-en.pdf",
        "tags": ["bank", "chase", "jpmorgan", "fees", "pdf"],
    },
    # Bank of America Corp.
    {
        "name": "Bank of America Advantage Banking",
        "url": "https://www.bankofamerica.com/deposits/checking/advantage-banking/",
        "tags": ["bank", "bankofamerica", "pricing", "fees"],
    },
    {
        "name": "Bank of America Account Rates & Fees FAQs",
        "url": "https://www.bankofamerica.com/deposits/account-rates-fees-faqs/",
        "tags": ["bank", "bankofamerica", "rates", "fees"],
    },
    {
        "name": "Bank of America Core Checking Clarity Statement",
        "url": (
            "https://www.bankofamerica.com/content/documents/deposits/service/pdf/"
            "docrepo/BofA_CoreChecking_en_ADA.pdf"
        ),
        "tags": ["bank", "bankofamerica", "fees", "pdf"],
    },
    # Citigroup Inc. (Citibank)
    {
        "name": "Citi Simplified Banking Pricing",
        "url": "https://www.citi.com/banking/simplifiedbanking",
        "tags": ["bank", "citi", "citigroup", "pricing", "fees"],
    },
    {
        "name": "Citi Relationship Tiers & Account Comparison",
        "url": "https://www.citi.com/banking/compare-bank-accounts",
        "tags": ["bank", "citi", "citigroup", "pricing", "comparison"],
    },
    {
        # Redirects to the canonical www.citi.com CDN copy; the redirect is
        # followed automatically and the PDF parser handles the result.
        "name": "Citi Consumer Deposit Account Agreement",
        "url": "https://online.citi.com/JRS/popups/ao/CDAA.pdf",
        "tags": ["bank", "citi", "citigroup", "agreement", "fees", "pdf"],
    },
    # Wells Fargo & Co.
    {
        # Redirects to /mobile-online-banking/service-fees/.
        "name": "Wells Fargo Consumer and Business Account Fees",
        "url": "https://www.wellsfargo.com/online-banking/service-fees/",
        "tags": ["bank", "wellsfargo", "fees"],
    },
    {
        "name": "Wells Fargo Consumer Account Fees & Disclosures",
        "url": "https://www.wellsfargo.com/mobile-online-banking/consumer-account-fees/",
        "tags": ["bank", "wellsfargo", "fees", "disclosures"],
    },
    {
        "name": "Wells Fargo Checking Account Comparison",
        "url": "https://www.wellsfargo.com/checking/compare-checking-accounts/",
        "tags": ["bank", "wellsfargo", "pricing", "comparison"],
    },
    # The Goldman Sachs Group, Inc. (Marcus)
    #
    # Marcus fronts these pages with bot protection: a plain httpx fetch is
    # answered with HTTP 403 and a challenge page. CloakBrowser passes the
    # challenge, so js_required is set to forbid the non-JS fallback rather
    # than let a 403 challenge body be stored as if it were the real page.
    {
        "name": "Marcus by Goldman Sachs Savings Options",
        "url": "https://www.marcus.com/us/en/savings",
        "tags": ["bank", "marcus", "goldmansachs", "savings", "rates"],
        "js_required": True,
    },
    {
        "name": "Marcus Accessing Your Money",
        "url": "https://www.marcus.com/us/en/banking-with-us/accessing-your-money",
        "tags": ["bank", "marcus", "goldmansachs", "fees", "transfers"],
        "js_required": True,
    },
    {
        "name": "Marcus Banking FAQs",
        "url": "https://www.marcus.com/us/en/faqs",
        "tags": ["bank", "marcus", "goldmansachs", "faq", "fees"],
        "js_required": True,
    },
    # Morgan Stanley (E*TRADE / Morgan Stanley Private Bank)
    {
        "name": "E*TRADE / Morgan Stanley Private Bank Rates & Fees",
        "url": "https://us.etrade.com/bank/bank-rates",
        "tags": ["bank", "morganstanley", "etrade", "rates", "fees"],
    },
    {
        "name": "E*TRADE Pricing and Rates",
        "url": "https://us.etrade.com/what-we-offer/pricing-and-rates",
        "tags": ["bank", "morganstanley", "etrade", "pricing", "fees"],
    },
    {
        "name": "Morgan Stanley Wealth Management Disclosures",
        "url": "https://www.morganstanley.com/wealth-disclosures/disclosures",
        "tags": ["bank", "morganstanley", "disclosures", "wealth"],
    },
    # U.S. Bancorp (U.S. Bank)
    {
        "name": "U.S. Bank Consumer Pricing Information",
        "url": (
            "https://www.usbank.com/dam/en/documents/pdfs/disclosures/"
            "consumer-pricing-information.pdf"
        ),
        "tags": ["bank", "usbank", "usbancorp", "pricing", "fees", "pdf"],
    },
    {
        "name": "U.S. Bank Smartly Checking",
        "url": "https://www.usbank.com/bank-accounts/checking-accounts/bank-smartly-checking.html",
        "tags": ["bank", "usbank", "usbancorp", "pricing", "fees"],
    },
    {
        "name": "U.S. Bank Smart Rewards",
        "url": "https://www.usbank.com/bank-accounts/checking-accounts/smart-rewards.html",
        "tags": ["bank", "usbank", "usbancorp", "rewards", "fees"],
    },
]


async def seed_user(force_seed=False):
    await init_db()

    async with async_session_factory() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == "emily@lclglaw.com"))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"User {existing.email} already exists (id={existing.id})")
        else:
            # Create tenant first
            tenant = Tenant(
                name="Emily",
                is_active=True,
            )
            db.add(tenant)
            await db.flush()

            # Create user
            user = User(
                email="emily@lclglaw.com",
                name="Admin",
                password_hash=hash_password("emilyadmin123"),
                is_active=True,
                is_superuser=True,
                tenant_id=tenant.id,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            print(f"Created user: {user.email}")
            print(f"Tenant: {tenant.name} (id={tenant.id})")
            print(f"User ID: {user.id}")
            print("Password: emilyadmin123")

        # ─── Seed default URLs (additive, non-destructive) ───
        tenant_result = await db.execute(select(Tenant).where(Tenant.name == "Emily"))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            print("No tenant found — skipping URL seeding")
            return

        # Load every URL, not just this tenant's. URLs created through the API
        # before tenant attachment was fixed have a NULL tenant_id, and the
        # `urls.url` column is globally unique in practice — scoping the
        # lookup to one tenant would re-insert them as duplicates.
        # Materialize once: a Result can only be consumed a single time.
        existing_rows = (await db.execute(select(Url))).scalars().all()
        existing_by_url = {u.url: u for u in existing_rows}

        seeded_rows = [u for u in existing_rows if SEED_TAG in (u.tags or [])]
        manual_rows = [u for u in existing_rows if SEED_TAG not in (u.tags or [])]

        # Detect duplicates inside DEFAULT_URLS itself before touching the DB.
        seen: set[str] = set()
        duplicates = set()
        for entry in DEFAULT_URLS:
            if entry["url"] in seen:
                duplicates.add(entry["url"])
            seen.add(entry["url"])
        if duplicates:
            raise SystemExit(
                "DEFAULT_URLS contains duplicate entries: "
                + ", ".join(sorted(duplicates))
            )

        new_entries = [e for e in DEFAULT_URLS if e["url"] not in existing_by_url]

        # Stagger ONLY the newly added URLs across the window. Deriving the
        # spacing from the full DEFAULT_URLS list (and rewriting next_check on
        # every existing row) used to reshuffle the entire schedule and reset
        # operator interval changes each time a single URL was added.
        now = datetime.now(UTC)
        spacing = (
            STAGGER_WINDOW_SECONDS // len(new_entries) if new_entries else 0
        )

        created_count = 0
        retagged_count = 0

        for idx, entry in enumerate(new_entries):
            db.add(
                Url(
                    tenant_id=tenant.id,
                    name=entry["name"],
                    url=entry["url"],
                    backend=entry.get("backend", DEFAULT_BACKEND),
                    interval_seconds=entry.get(
                        "interval_seconds", DEFAULT_INTERVAL_SECONDS
                    ),
                    enabled=True,
                    js_required=entry.get("js_required", False),
                    tags=list(entry["tags"]) + [SEED_TAG],
                    next_check=now + timedelta(seconds=idx * spacing),
                )
            )
            created_count += 1

        # Existing rows are only ever *tagged*, never rescheduled or retimed.
        for entry in DEFAULT_URLS:
            url = existing_by_url.get(entry["url"])
            if url is not None and SEED_TAG not in (url.tags or []):
                url.tags = list(url.tags or []) + [SEED_TAG]
                db.add(url)
                retagged_count += 1

        if created_count or retagged_count:
            await db.commit()

        print(
            f"\nURL seeding complete:"
            f"\n  defaults defined     : {len(DEFAULT_URLS)}"
            f"\n  created (new)        : {created_count}"
            f"\n  already present      : {len(DEFAULT_URLS) - created_count}"
            f"\n  newly tagged seeded  : {retagged_count}"
            f"\n  previously seeded    : {len(seeded_rows)}"
            f"\n  manual (untouched)   : {len(manual_rows)}"
        )
        if created_count:
            print(
                f"  first checks staggered over "
                f"{spacing * max(created_count - 1, 0) // 60} min"
            )


if __name__ == "__main__":
    asyncio.run(seed_user())

