"""Tests for the DEFAULT_URLS seed list and its additive seeding contract."""

import importlib.util
import pathlib

import pytest

from app.core.url_validator import validate_url

SEED_PATH = pathlib.Path(__file__).resolve().parents[1] / "seed_user.py"


def _load_seed_module():
    spec = importlib.util.spec_from_file_location("seed_user_under_test", SEED_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


seed = _load_seed_module()
DEFAULT_URLS = seed.DEFAULT_URLS


class TestSeedListIntegrity:
    def test_no_duplicate_urls(self):
        """Duplicates would create two rows polling the same page."""
        urls = [e["url"] for e in DEFAULT_URLS]
        dupes = {u for u in urls if urls.count(u) > 1}
        assert not dupes, f"Duplicate seed URLs: {sorted(dupes)}"

    def test_no_duplicate_names(self):
        names = [e["name"] for e in DEFAULT_URLS]
        dupes = {n for n in names if names.count(n) > 1}
        assert not dupes, f"Duplicate seed names: {sorted(dupes)}"

    def test_every_entry_has_required_fields(self):
        for entry in DEFAULT_URLS:
            assert entry.get("name"), f"missing name: {entry}"
            assert entry.get("url"), f"missing url: {entry}"
            assert isinstance(entry.get("tags"), list), f"bad tags: {entry}"
            assert entry["tags"], f"empty tags: {entry}"

    def test_every_url_passes_validation(self):
        """Entries must satisfy the same validator the API enforces."""
        for entry in DEFAULT_URLS:
            valid, error = validate_url(entry["url"])
            assert valid, f"{entry['url']}: {error}"

    def test_seed_tag_is_not_hardcoded_into_entries(self):
        """The seeder appends SEED_TAG; entries must not pre-declare it."""
        for entry in DEFAULT_URLS:
            assert seed.SEED_TAG not in entry["tags"], entry


class TestPreExistingUrlsPreserved:
    """The PG&E addition must not disturb previously monitored sources."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://openai.com/terms",
            "https://openai.com/policies/privacy-policy/",
            "https://openai.com/policies/business-terms",
            "https://policies.google.com/terms",
            "https://cloud.google.com/terms",
            "https://policies.google.com/privacy",
            "https://www.microsoft.com/en-us/servicesagreement",
            "https://www.anthropic.com/legal/consumer-terms",
            "https://www.anthropic.com/legal/commercial-terms",
            "https://www.anthropic.com/legal/privacy",
            "https://stripe.com/privacy",
            "https://stripe.com/pricing",
        ],
    )
    def test_legacy_url_still_present(self, url):
        assert url in {e["url"] for e in DEFAULT_URLS}


class TestPgeUrls:
    PGE_URLS = [
        "https://www.pge.com/tariffs/en.html",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_E-1.pdf",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/GAS_SCHEDS_G-1.pdf",
        "https://www.pge.com/en/account/service-requests/start-stop-transfer-service.html",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/GAS_SCHEDS_G-NR1.pdf",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/GAS_SCHEDS_G-NR2.pdf",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_B-1.pdf",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_A-1.pdf",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_B-10.pdf",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_E-19.pdf",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_B-20.pdf",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/ELEC_SCHEDS_E-20.pdf",
        "https://www.pge.com/tariffs/assets/pdf/tariffbook/GAS_FORMS_79-716.pdf",
        "https://www.pge.com/en/business-resources/business-customer-service.html",
        "https://www.pge.com/en/privacy-center/disclosure.html",
        "https://myportal.pge.com/saphrportal/rules/TandC.html",
        "https://www.safetyactioncenter.pge.com/terms",
        "https://www.pge.com/en/privacy-center/privacy-policy.html",
    ]

    def test_all_eighteen_pge_urls_present(self):
        present = {e["url"] for e in DEFAULT_URLS}
        missing = [u for u in self.PGE_URLS if u not in present]
        assert not missing, f"Missing PG&E URLs: {missing}"

    def test_pge_entries_are_tagged_pge(self):
        by_url = {e["url"]: e for e in DEFAULT_URLS}
        for url in self.PGE_URLS:
            assert "pge" in by_url[url]["tags"], url

    def test_pdf_entries_carry_pdf_tag(self):
        """The pdf tag lets operators filter sources needing the PDF path."""
        for entry in DEFAULT_URLS:
            if entry["url"].lower().endswith(".pdf"):
                assert "pdf" in entry["tags"], entry["url"]

    def test_pdf_entries_are_detected_by_the_pdf_parser(self):
        from app.core.pdf_parser import looks_like_pdf

        for url in self.PGE_URLS:
            if url.lower().endswith(".pdf"):
                assert looks_like_pdf(url=url), url


class TestMigrationDoesNotDrift:
    """Alembic 0002 holds a frozen copy of the seed list.

    It must never contain a URL that the live list has dropped, otherwise
    running the migration on a fresh database would resurrect stale entries.
    """

    def test_migration_list_is_a_subset_of_the_live_list(self):
        migration_path = (
            SEED_PATH.parent
            / "app"
            / "db"
            / "alembic"
            / "versions"
            / "0002_seed_admin_user_and_default_urls.py"
        )
        spec = importlib.util.spec_from_file_location(
            "migration_0002_under_test", migration_path
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        live = {e["url"] for e in DEFAULT_URLS}
        frozen = {e["url"] for e in migration.DEFAULT_URLS}

        assert frozen <= live, (
            "Alembic 0002 contains URLs absent from seed_user.py: "
            f"{sorted(frozen - live)}"
        )


class TestSeedConstants:
    def test_backend_is_the_polled_one(self):
        """Seeding with a non-polled backend would create dead URLs."""
        assert seed.DEFAULT_BACKEND == "selfhosted"

    def test_interval_is_within_api_bounds(self):
        # The API clamps interval_seconds to [60, 86400]; stay consistent.
        assert 60 <= seed.DEFAULT_INTERVAL_SECONDS <= 86400
