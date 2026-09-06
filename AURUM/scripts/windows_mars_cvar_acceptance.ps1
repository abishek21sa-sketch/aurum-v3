$ErrorActionPreference = "Stop"
Write-Host "AURUM MARS-CVaR Windows Acceptance"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$pyCandidate = Join-Path $root ".venv\Scripts\python.exe"
$py = if (Test-Path $pyCandidate) { $pyCandidate } else { "python" }
$env:PYTHONPATH = $root
$acceptanceBase = Join-Path ([System.IO.Path]::GetTempPath()) ("aurum_rc3_pytest_acceptance_ps_{0}" -f ([guid]::NewGuid().ToString("N")))
& $py scripts/mars_cvar_governance_evidence.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py scripts/mars_cvar_walk_forward_evidence.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py scripts/run_mars_cvar_institutional.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py scripts/generate_synthetic_ml_dataset.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py scripts/run_synthetic_ml_validation.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py scripts/run_deployment_preflight.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py scripts/generate_sbom.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py scripts/build_mars_cvar_release_evidence.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py scripts/export_enterprise_evidence.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py scripts/verify_enterprise_release.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py -m pytest -p no:cacheprovider --basetemp $acceptanceBase tests/test_signature_algorithm.py tests/test_mars_cvar_institutional_bridge.py tests/test_mars_cvar_validation.py tests/test_mars_cvar_api_ui.py tests/test_mars_cvar_walk_forward.py tests/test_mars_cvar_product.py tests/test_enterprise_readiness.py tests/test_deployment_preflight.py tests/test_product_frontend.py tests/test_ai_intelligence.py tests/test_governed_controls.py tests/test_external_evidence.py tests/test_synthetic_ml.py tests/test_public_data.py tests/test_release_verifier.py tests/test_evidence_bundle.py tests/test_sbom.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $py -m py_compile src/optimization/signature_algorithm.py src/institutional/mars_cvar_decision_bridge.py src/institutional/mars_cvar_product.py src/institutional/enterprise_readiness.py src/institutional/deployment_preflight.py src/institutional/ai_intelligence.py src/institutional/live_data_contract.py src/institutional/live_data_ingestion.py src/institutional/model_validation.py src/institutional/enterprise_platform.py src/institutional/ai_evaluation.py src/institutional/control_plane.py src/institutional/operations_contract.py src/institutional/external_evidence.py src/institutional/synthetic_ml.py src/institutional/public_data.py src/api/main.py scripts/product_frontend.py scripts/product_runtime.py scripts/ingest_public_data.py scripts/run_deployment_preflight.py scripts/generate_synthetic_ml_dataset.py scripts/run_synthetic_ml_validation.py scripts/verify_enterprise_release.py scripts/export_enterprise_evidence.py scripts/generate_sbom.py dashboard/official_dashboard.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$v2 = Join-Path (Split-Path $root -Parent) "AURUM-v2"
if (Test-Path $v2) {
    Push-Location $v2
    $env:PYTHONPATH = $v2
    & $py -m pytest -p no:cacheprovider --basetemp (Join-Path ([System.IO.Path]::GetTempPath()) ("aurum_v2_rc3_pytest_acceptance_ps_{0}" -f ([guid]::NewGuid().ToString("N")))) tests/test_mars_cvar_engine_bridge.py -q
    $bridgeExit = $LASTEXITCODE
    Pop-Location
    if ($bridgeExit -ne 0) { exit $bridgeExit }
}
Write-Host "MARS_CVAR_WINDOWS_ACCEPTANCE=PASS"
