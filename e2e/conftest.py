"""Fixtures. The tests run on the host against a running stack: `make dev`,
then `make e2e`. See helpers.py for E2E_BASE_URL and E2E_COMPOSE."""

import pytest

from helpers import BASE, PageErrors, register


@pytest.fixture(scope="session")
def base_url():
    return BASE


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "viewport": {"width": 1366, "height": 800},
    }


@pytest.fixture
def user():
    return register()


@pytest.fixture
def make_user():
    return register


@pytest.fixture
def errors():
    """Collects page errors; the test fails if any are left at the end."""
    found = PageErrors()
    yield found
    assert not found, "\n".join(found)


@pytest.fixture
def user_page(context, user, errors):
    """A page logged in as a new, set-up user, with errors watched."""
    user.login_context(context)
    page = context.new_page()
    errors.watch(page)
    page.user = user
    return page
