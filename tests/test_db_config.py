import certifi

from config import build_mysql_ssl_config


def test_build_mysql_ssl_config_falls_back_to_certifi_bundle():
    ssl_config = build_mysql_ssl_config("")

    assert ssl_config == {"ca": certifi.where()}
