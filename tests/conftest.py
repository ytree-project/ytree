import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--parallelonly", action="store_true", default=False,
        help="run only parallel tests"
    )
    parser.addoption(
        "--serialonly", action="store_true", default=False,
        help="run only serial tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "parallel: test uses parallelism")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--parallelonly"):
        skip_serial = pytest.mark.skip(reason="only running parallel tests")
        for item in items:
            if "parallel" not in item.keywords:
                item.add_marker(skip_serial)

    if config.getoption("--serialonly"):
        skip_parallel = pytest.mark.skip(reason="only running serial tests")
        for item in items:
            if "parallel" in item.keywords:
                item.add_marker(skip_parallel)
