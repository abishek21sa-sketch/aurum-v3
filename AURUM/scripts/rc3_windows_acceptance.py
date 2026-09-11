from __future__ import annotations
import os, subprocess, sys, tempfile, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(*args, cwd=ROOT, env=None):
    print('RUNNING:', ' '.join(map(str,args)), flush=True)
    subprocess.run([str(a) for a in args], cwd=cwd, env=env, check=True)

def main():
    py=sys.executable
    env={**os.environ,'PYTHONPATH':str(ROOT)}
    # Keep pytest's disposable workspace off synced/protected folders such as OneDrive.
    acceptance_tmp = Path(tempfile.gettempdir()) / f'aurum_rc3_pytest_acceptance_{uuid.uuid4().hex}'
    # Discover every tests/test_*.py rather than hand-listing them: a hardcoded list here
    # previously left 6 real test files (test_anomaly_detector, test_market_stream,
    # test_python314_regime_compat, test_regimes, test_research_operations, test_signals)
    # silently unrun by this acceptance gate since whoever wrote the list didn't update it
    # when those files were added -- they all pass once collected (verified locally after
    # fixing the unrelated src/ namespace-package issue below).
    test_files = sorted(str(p.relative_to(ROOT)).replace('\\', '/') for p in (ROOT / 'tests').glob('test_*.py'))
    for script in ['mars_cvar_governance_evidence.py','mars_cvar_walk_forward_evidence.py','run_mars_cvar_institutional.py','generate_synthetic_ml_dataset.py','run_synthetic_ml_validation.py','run_deployment_preflight.py']:
        run(py,ROOT/'scripts'/script,env=env)
    run(py,ROOT/'scripts'/'generate_sbom.py',env=env)
    run(py,ROOT/'scripts'/'build_mars_cvar_release_evidence.py',env=env)
    run(py,ROOT/'scripts'/'export_enterprise_evidence.py',env=env)
    run(py,ROOT/'scripts'/'verify_enterprise_release.py',env=env)
    run(py,'-m','pytest','-p','no:cacheprovider','--basetemp',str(acceptance_tmp),*test_files,'-q',env=env)
    run(py,'-m','py_compile','src/optimization/signature_algorithm.py','src/institutional/mars_cvar_decision_bridge.py','src/institutional/mars_cvar_product.py','src/institutional/enterprise_readiness.py','src/institutional/deployment_preflight.py','src/institutional/ai_intelligence.py','src/institutional/live_data_contract.py','src/institutional/live_data_ingestion.py','src/institutional/public_data.py','src/institutional/model_validation.py','src/institutional/enterprise_platform.py','src/institutional/ai_evaluation.py','src/institutional/control_plane.py','src/institutional/operations_contract.py','src/institutional/external_evidence.py','src/institutional/synthetic_ml.py','src/api/main.py','scripts/product_adapter.py','scripts/product_runtime.py','scripts/product_frontend.py','scripts/ingest_public_data.py','scripts/run_deployment_preflight.py','scripts/generate_synthetic_ml_dataset.py','scripts/run_synthetic_ml_validation.py','scripts/verify_enterprise_release.py','scripts/export_enterprise_evidence.py','scripts/generate_sbom.py','dashboard/official_dashboard.py',env=env)
    v2=ROOT.parent/'AURUM-v2'
    if v2.exists():
        env2={**os.environ,'PYTHONPATH':str(v2)}
        v2_tmp = Path(tempfile.gettempdir()) / f'aurum_v2_rc3_pytest_acceptance_{uuid.uuid4().hex}'
        run(py,'-m','pytest','-p','no:cacheprovider','--basetemp',str(v2_tmp),'tests/test_mars_cvar_engine_bridge.py','-q',cwd=v2,env=env2)
    print('MARS_CVAR_WINDOWS_ACCEPTANCE=PASS')
if __name__=='__main__': main()
