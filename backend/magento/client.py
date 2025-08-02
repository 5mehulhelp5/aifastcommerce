# client.py

from utils import common
from .magento_oauth_client import MagentoOAuthClient

def get_magento_client():
    env_vars = common.get_required_env_vars([
        "MAGENTO_BASE_URL",
        "MAGENTO_CONSUMER_KEY",
        "MAGENTO_CONSUMER_SECRET",
        "MAGENTO_ACCESS_TOKEN",
        "MAGENTO_ACCESS_TOKEN_SECRET",
        "MAGENTO_VERIFY_SSL"
    ])

    return MagentoOAuthClient(
        base_url=env_vars["MAGENTO_BASE_URL"],
        consumer_key=env_vars["MAGENTO_CONSUMER_KEY"],
        consumer_secret=env_vars["MAGENTO_CONSUMER_SECRET"],
        access_token=env_vars["MAGENTO_ACCESS_TOKEN"],
        access_token_secret=env_vars["MAGENTO_ACCESS_TOKEN_SECRET"],
        verify_ssl=env_vars["MAGENTO_VERIFY_SSL"].lower() != "false"
    )

