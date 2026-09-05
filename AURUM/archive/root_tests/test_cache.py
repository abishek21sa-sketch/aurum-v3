from src.services.cache_service import set_cache, get_cache


sample_data = {
    "portfolio_beta": 0.27,
    "risk_level": "low",
}


set_cache(
    "aurum:test",
    sample_data,
)

cached = get_cache("aurum:test")

print(cached)