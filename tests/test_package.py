import price_pack_copilot
import price_pack_copilot.services


def test_packages_import_without_starting_servers() -> None:
    assert price_pack_copilot.__doc__
    assert price_pack_copilot.services.__doc__
