from requests.auth import HTTPBasicAuth

API_KEY = "96e0cc51-a62e-42ca-acee-910ea7d2a241"
BASE_URL = "https://api.zapper.fi/v2/"
EVM_NETWORKS = ["ethereum", "polygon", "optimism", "gnosis", "binance-smart-chain", "fantom", "avalanche", "arbitrum", "celo", "harmony", "moonriver", "bitcoin", "cronos", "aurora", "evmos"]
AUTH  = HTTPBasicAuth(API_KEY, "")