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
    test_files = [
        'tests/test_signature_algorithm.py',
        'tests/test_mars_cvar_institutional_bridge.py',
        'tests/test_mars_cvar_validation.py',
        'tests/test_mars_cvar_api_ui.py',
        'tests/test_mars_cvar_walk_forward.py',
        'tests/test_mars_cvar_product.py',
        'tests/test_enterprise_readiness.py',
        'tests/test_release_verifier.py',
        'tests/test_evidence_bundle.py',
        'tests/test_sbom.py',
    ]
    for script in ['mars_cvar_governance_evidence.py','mars_cvar_walk_forward_evidence.py','run_mars_cvar_institutional.py']:
        run(py,ROOT/'scripts'/script,env=env)
    run(py,ROOT/'scripts'/'generate_sbom.py',env=env)
    run(py,ROOT/'scripts'/'build_mars_cvar_release_evidence.py',env=env)
    run(py,ROOT/'scripts'/'export_enterprise_evidence.py',env=env)
    run(py,ROOT/'scripts'/'verify_enterprise_release.py',env=env)
    run(py,'-m','pytest','-p','no:cacheprovider','--basetemp',str(acceptance_tmp),*test_files,'-q',env=env)
    run(py,'-m','py_compile','src/optimization/signature_algorithm.py','src/institutional/mars_cvar_decision_bridge.py','src/institutional/mars_cvar_product.py','src/institutional/enterprise_readiness.py','src/api/main.py','scripts/product_adapter.py','scripts/product_runtime.py','scripts/verify_enterprise_release.py','scripts/export_enterprise_evidence.py','scripts/generate_sbom.py','dashboard/official_dashboard.py',env=env)
    v2=ROOT.parent/'AURUM-v2'
    if v2.exists():
        env2={**os.environ,'PYTHONPATH':str(v2)}
        v2_tmp = Path(tempfile.gettempdir()) / f'aurum_v2_rc3_pytest_acceptance_{uuid.uuid4().hex}'
        run(py,'-m','pytest','-p','no:cacheprovider','--basetemp',str(v2_tmp),'tests/test_mars_cvar_engine_bridge.py','-q',cwd=v2,env=env2)
    print('MARS_CVAR_WINDOWS_ACCEPTANCE=PASS')
if __name__=='__main__': main()
