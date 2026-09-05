from src.core.database import SessionLocal
from src.agents.scenario_decision_engine import (
    run_scenario_with_decisions, apply_scenario_decision
)
from src.models.alpha_registry import AlphaSignal
from src.models.hypothesis import Hypothesis
from sqlalchemy import text

def main():
    db = SessionLocal()
    try:
        # Run pandemic scenario — most likely to trigger RESEARCH decisions
        print("Running pandemic scenario to generate RESEARCH triggers...\n")
        results = run_scenario_with_decisions(
            db, scenario_keys=["pandemic_shock", "regional_banking_collapse"]
        )

        research_results = []
        for r in results:
            d = r["decision"]
            action = d.get("decision", "HOLD")
            print(f"  H#{r['hypothesis_number']} | {r['scenario_name'][:35]:<35} "
                  f"→ {action:<12} (confidence {d.get('confidence', 0):.0%})")
            if action == "RESEARCH":
                research_results.append(r)

        if research_results:
            print(f"\n{len(research_results)} RESEARCH decision(s) — applying...")
            for r in research_results:
                alpha = db.query(AlphaSignal).filter_by(
                    id=r["alpha_id"]
                ).first()
                hyp = db.query(Hypothesis).filter_by(
                    hypothesis_number=r["hypothesis_number"]
                ).first()
                applied = apply_scenario_decision(
                    db, alpha, hyp, r["decision"],
                    r["scenario_key"], r["scenario_name"]
                )
                print(f"  Applied: {applied['result']}")
                if applied.get("research_angle"):
                    print(f"  Angle: {applied['research_angle']}")

            # Verify triggers written
            triggers = db.execute(text(
                "SELECT scenario_name, hypothesis_angle, priority, status "
                "FROM research_triggers WHERE status = 'pending'"
            )).fetchall()
            print(f"\nPending research triggers in DB: {len(triggers)}")
            for t in triggers:
                print(f"  [{t.priority}] {t.scenario_name}: {t.hypothesis_angle[:80]}")
        else:
            print("\nNo RESEARCH decisions generated.")
            print("All impacts were within acceptable bounds for these alphas.")
            print("Try running --consume-triggers with a custom observation set.")

    finally:
        db.close

if __name__ == "__main__":
    main()