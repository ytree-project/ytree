import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--exclude-slow", action="store_true", default=False,
        help="exclude tests marked as slow"
    )
    parser.addoption(
        "--exclude-serial", action="store_true", default=False,
        help="exclude tests not using parallelism"
    )
    parser.addoption(
        "--exclude-parallel", action="store_true", default=False,
        help="exclude tests using parallelism"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "parallel: test uses parallelism")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--exclude-slow"):
        skip_slow = pytest.mark.skip(reason="excluding tests marked as slow")
        for item in items:
            if getattr(item, "cls", None) is None:
                continue
            if getattr(item.cls, "slow", False):
                item.add_marker(skip_slow)

    if config.getoption("--exclude-serial"):
        skip_serial = pytest.mark.skip(reason="excluding tests not using parallelism")
        for item in items:
            if "parallel" not in item.keywords:
                item.add_marker(skip_serial)

    if config.getoption("--exclude-parallel"):
        skip_parallel = pytest.mark.skip(reason="excluding tests using parallelism")
        for item in items:
            if "parallel" in item.keywords:
                item.add_marker(skip_parallel)
