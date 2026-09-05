from src.regimes.regime_portfolio_library import main as run_portfolio_library
from src.regimes.regime_transition_decision_engine import main as run_transition_decision
from src.regimes.confidence_weighted_exposure_engine import main as run_confidence_exposure
from src.regimes.dynamic_hedge_overlay_engine import main as run_hedge_overlay
from src.regimes.regime_allocation_switch_engine import main as run_allocation_switch
from src.regimes.portfolio_intelligence_report_generator import main as run_report


def main() -> None:
    print("\n" + "=" * 80)
    print("RUNNING AURUM CHAT 3C — REGIME-AWARE PORTFOLIO INTELLIGENCE")
    print("=" * 80)

    run_portfolio_library()
    run_transition_decision()
    run_confidence_exposure()
    run_hedge_overlay()
    run_allocation_switch()
    run_report()

    print("\n" + "=" * 80)
    print("CHAT 3C COMPLETE")
    print("=" * 80)
    print("Final report:")
    print("results/regime_intelligence/portfolio_intelligence_report.txt")


if __name__ == "__main__":
    main()