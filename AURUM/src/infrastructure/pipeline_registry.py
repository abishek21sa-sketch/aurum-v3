
PIPELINE_REGISTRY = {
    "infrastructure_smoke_test": [
        {
            "step_name": "storage_validation",
            "module_name": "src.infrastructure.validate_storage_layer",
        },
        {
            "step_name": "runtime_environment_summary",
            "module_name": "src.infrastructure.runtime_environment",
        },
    ],

    "phase1_market_pulse": [
        {
            "step_name": "market_regime_detector",
            "module_name": "src.optimization.market_regime_detector",
        },
        {
            "step_name": "regime_transition_engine",
            "module_name": "src.regimes.regime_transition_engine",
        },
        {
            "step_name": "regime_forecast_engine",
            "module_name": "src.regimes.regime_forecast_engine",
        },
        {
            "step_name": "probabilistic_regime_allocator",
            "module_name": "src.optimization.probabilistic_regime_allocator",
        },
        {
            "step_name": "dynamic_allocation_backtest",
            "module_name": "src.backtesting.dynamic_allocation_backtest",
        },
        {
            "step_name": "dynamic_allocation_transaction_cost",
            "module_name": "src.backtesting.dynamic_allocation_transaction_cost",
        },
        {
            "step_name": "regime_stability_engine",
            "module_name": "src.regimes.regime_stability_engine",
        },
        {
            "step_name": "confidence_adjusted_allocator",
            "module_name": "src.optimization.confidence_adjusted_allocator",
        },
        {
            "step_name": "dynamic_risk_budget_engine",
            "module_name": "src.risk.dynamic_risk_budget_engine",
        },
        {
            "step_name": "portfolio_stress_test_engine",
            "module_name": "src.risk.portfolio_stress_test_engine",
        },
        {
            "step_name": "performance_attribution_engine",
            "module_name": "src.analytics.performance_attribution_engine",
        },
        {
            "step_name": "factor_exposure_engine",
            "module_name": "src.analytics.factor_exposure_engine",
        },
        {
            "step_name": "rolling_factor_exposure_engine",
            "module_name": "src.analytics.rolling_factor_exposure_engine",
        },
        {
            "step_name": "portfolio_health_monitor",
            "module_name": "src.analytics.portfolio_health_monitor",
        },
        {
            "step_name": "monte_carlo_regime_simulator",
            "module_name": "src.forecasting.monte_carlo_regime_simulator",
        },
        {
            "step_name": "executive_summary_engine",
            "module_name": "src.reporting.executive_summary_engine",
        },
    ],
}


def get_pipeline_steps(pipeline_name: str) -> list[dict]:
    if pipeline_name not in PIPELINE_REGISTRY:
        valid = ", ".join(PIPELINE_REGISTRY.keys())
        raise ValueError(f"Unknown pipeline: {pipeline_name}. Valid pipelines: {valid}")

    return PIPELINE_REGISTRY[pipeline_name]


def list_pipelines() -> list[str]:
    return list(PIPELINE_REGISTRY.keys())


if __name__ == "__main__":
    print("AVAILABLE PIPELINES")
    for pipeline in list_pipelines():
        print(f"- {pipeline}")
