from src.market_data.market_data_service import MarketDataService


def main():

    print("=" * 80)
    print("AURUM PHASE 6A.2 MARKET DATA LAYER")
    print("=" * 80)

    service = MarketDataService()

    print(
        f"Provider: {service.provider_name()}"
    )

    price = service.get_price("SPY")

    print(
        f"SPY Price: {price:.2f}"
    )

    history = service.get_history(
        "SPY",
        "1mo"
    )

    print(
        f"Rows Retrieved: {len(history)}"
    )

    print("=" * 80)
    print("[PASS] Market Data Layer")
    print("=" * 80)


if __name__ == "__main__":
    main()