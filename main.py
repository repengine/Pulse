"""
main.py

Pulse v0.2 execution shell. Initializes simulation state, runs a short simulation loop,
generates foresight forecasts, and prints Strategos Digest summaries.

Author: Pulse v0.2

Usage:
    python main.py [--turns N] [--output FILE]

Options:
    --turns N   Number of simulation turns to run (default: 5)
    --output FILE   Optional output file for digest
"""
import sys
import os
import argparse
import uuid
import json # Import the json module
from datetime import datetime, timezone
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.log_utils import get_logger
logger = get_logger(__name__)

logger.info("🧠 Starting Pulse...")

from core.pulse_config import STARTUP_BANNER

print(STARTUP_BANNER)

from forecast_output.digest_logger import save_digest_to_file
from operator_interface.strategos_digest import generate_strategos_digest
from memory.forecast_memory import ForecastMemory
from simulation_engine.worldstate import WorldState
from simulation_engine.turn_engine import run_turn
from simulation_engine.causal_rules import apply_causal_rules
from forecast_output.forecast_generator import generate_forecast
from forecast_output.pfpa_logger import log_forecast_to_pfpa
from forecast_output.digest_exporter import export_digest, export_digest_json
from forecast_output.strategos_digest_builder import build_digest
from operator_interface.pulse_prompt_logger import log_prompt
from forecast_engine.forecast_regret_engine import analyze_regret, analyze_misses, feedback_loop
from core.pulse_learning_log import log_learning_event
from pipeline.ingestion_service import IngestionService
from core.variable_registry import registry   # shared singleton :contentReference[oaicite:2]{index=2}&#8203;:contentReference[oaicite:3]{index=3}
from core.variable_accessor import set_variable
from iris.iris_utils.historical_data_repair import (
    repair_variable_data,
    simulate_repair,
    get_repair_report,
    repair_multiple_variables,
    revert_to_original,
    compare_versions,
    get_all_versions,
    DEFAULT_REPAIR_STRATEGIES # Import for choices
)


ingester = IngestionService()

#sig_path = ingester.ingest_once()
#for sig in ingester.latest_signals():
 #   set_variable(registry, sig["name"], sig["value"])  # or registry.set()
  #  logger.info(f"Signal ingested: {sig['name']} = {sig['value']}")
def run_pulse_simulation(turns: int = 1):
    """
    Run the main Pulse simulation loop.

    Args:
        turns (int): Number of simulation turns to execute.
    """
    logger.info("\n🌐 Initializing Pulse...\n")
    state = WorldState()
    memory = ForecastMemory()

    for _ in range(turns):
        logger.info(f"\n🔄 Running Turn {state.turn + 1}...")
        # Use a lambda that returns None to satisfy the type
        run_turn(state, rule_fn=lambda s: (apply_causal_rules(s), None)[1])
        try:
            # Always pass a dict to generate_forecast
            state_dict = state.to_dict()
            logger.info(
                "[Forecast Pipeline] After state.to_dict() in main.py: type=%s, keys=%s, sample=%s",
                type(state_dict),
                list(state_dict.keys())[:5],
                {k: state_dict[k] for k in list(state_dict.keys())[:3]}
            )
            forecast = generate_forecast(state_dict)
            
            # Ensure every forecast has a valid trace_id
            if not forecast.get("trace_id") or forecast.get("trace_id") == "None" or forecast.get("trace_id") == "unknown":
                forecast["trace_id"] = str(uuid.uuid4())
                logger.info(f"Assigned new trace_id: {forecast['trace_id']}")

            # Validate numeric fields before storage/further processing
            for field in ['confidence', 'fragility']:
                if field in forecast:
                    try:
                        forecast[field] = float(forecast[field]) if forecast[field] is not None else 0.0
                    except (ValueError, TypeError):
                        logger.warning(f"Type conversion failed for {field}: {forecast[field]}. Using 0.0")
                        forecast[field] = 0.0

            # Enhanced logging and validation before storing forecast in memory
            logger.info("Before storing forecast in memory in main.py")
            logger.info(f"Type of forecast: {type(forecast)}")
            if isinstance(forecast, dict):
                key_fields = ['confidence', 'fragility', 'priority', 'retrodiction_score']
                # Log and validate top-level fields
                for field in key_fields:
                    value = forecast.get(field)
                    logger.info(f"Field '{field}': type={type(value)}, value={value}")
                    if not (isinstance(value, (int, float)) or value is None):
                        logger.warning(f"Field '{field}' is not numeric (type={type(value)}). Attempting conversion.")
                        try:
                            forecast[field] = float(value)
                        except (ValueError, TypeError):
                            logger.warning(f"Failed to convert field '{field}' to float. Defaulting to 0.0.")
                            forecast[field] = 0.0
                # Log and validate nested fields in 'overlays' and 'capital'
                for container in ['overlays', 'capital']:
                    sub = forecast.get(container)
                    if isinstance(sub, dict):
                        for k, v in sub.items():
                            logger.info(f"Field '{container}.{k}': type={type(v)}, value={v}")
                            if not (isinstance(v, (int, float)) or v is None):
                                logger.warning(f"Field '{container}.{k}' is not numeric (type={type(v)}). Attempting conversion.")
                                try:
                                    sub[k] = float(v)
                                except (ValueError, TypeError):
                                    logger.warning(f"Failed to convert field '{container}.{k}' to float. Defaulting to 0.0.")
                                    sub[k] = 0.0

            memory.store(forecast)
            log_forecast_to_pfpa(forecast)
        except Exception as e:
            logger.error(f"❌ Forecast error: {e}")
            log_learning_event("exception", {"error": str(e), "context": "forecast_generation", "timestamp": datetime.now(timezone.utc).isoformat()})
            continue

    digest = generate_strategos_digest(memory, n=min(turns, 5))
    logger.info(digest)
    save_digest_to_file(digest)

# Run post-simulation retrodiction test
try:
    from trust_system.retrodiction_engine import simulate_retrodiction_test
    simulate_retrodiction_test()
    log_learning_event("forecast_scored", {"forecast_id": "retrodiction_test", "score": "success", "timestamp": datetime.now(timezone.utc).isoformat()})
except Exception as e:
    logger.warning(f"⚠️ Retrodiction failed: {e}")
    log_learning_event("exception", {"error": str(e), "context": "retrodiction_test", "timestamp": datetime.now(timezone.utc).isoformat()})
# Strategic trust audit
try:
    from learning.trust_audit import audit_forecasts
    audit_forecasts()
    log_learning_event("symbolic_contradiction", {"details": "audit_success", "timestamp": datetime.now(timezone.utc).isoformat()})
except Exception as e:
    logger.warning(f"⚠️ Audit failed: {e}")
    log_learning_event("exception", {"error": str(e), "context": "trust_audit", "timestamp": datetime.now(timezone.utc).isoformat()})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pulse Simulation and Data Management Engine")
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Simulation command
    simulate_parser = subparsers.add_parser("simulate", help="Run the Pulse simulation")
    simulate_parser.add_argument("--turns", type=int, default=5, help="Number of simulation turns to run")
    simulate_parser.add_argument("--output", type=str, default=None, help="Optional output file for digest")
    simulate_parser.add_argument("--auto-upgrade", action="store_true", help="Automatically generate epistemic upgrade plan after run")

    # Repair command
    repair_parser = subparsers.add_parser("repair", help="Address identified data quality issues")
    repair_parser.add_argument("variable_name", type=str, help="Name of the variable to repair")
    repair_parser.add_argument("--variable-type", type=str, default="raw", choices=list(DEFAULT_REPAIR_STRATEGIES.keys()), help="Type of variable for strategy selection")
    repair_parser.add_argument("--skip-smoothing", action="store_true", help="Skip the smoothing step")
    repair_parser.add_argument("--skip-cross-source", action="store_true", help="Skip cross-source reconciliation")

    # Simulate Repair command
    simulate_repair_parser = subparsers.add_parser("simulate-repair", help="Preview repairs without applying them")
    simulate_repair_parser.add_argument("variable_name", type=str, help="Name of the variable to simulate repairs for")
    simulate_repair_parser.add_argument("--variable-type", type=str, default="raw", choices=list(DEFAULT_REPAIR_STRATEGIES.keys()), help="Type of variable for strategy selection")

    # Repair Report command
    repair_report_parser = subparsers.add_parser("repair-report", help="Generate a report of repairs made")
    repair_report_parser.add_argument("variable_name", type=str, help="Name of the variable")
    repair_report_parser.add_argument("--version", type=str, help="Optional Version ID (if None, gets the latest version)")

    # Revert command
    revert_parser = subparsers.add_parser("revert", help="Revert a variable to its original state")
    revert_parser.add_argument("variable_name", type=str, help="Name of the variable")
    revert_parser.add_argument("--version", type=str, help="Optional Version ID to revert to (if None, reverts to the original)")

    # Compare Versions command
    compare_parser = subparsers.add_parser("compare-versions", help="Compare two versions of a variable")
    compare_parser.add_argument("variable_name", type=str, help="Name of the variable")
    compare_parser.add_argument("version_id1", type=str, help="First version ID")
    compare_parser.add_argument("--version2", type=str, help="Optional Second version ID (if None, uses the latest repaired version)")

    # List Versions command
    versions_parser = subparsers.add_parser("list-versions", help="List all repair versions for a variable")
    versions_parser.add_argument("variable_name", type=str, help="Name of the variable")


    args = parser.parse_args()

    if args.command == "simulate":
        run_pulse_simulation(turns=args.turns)
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write("# Strategos Digest\n\n")
                    f.write(str(generate_strategos_digest(ForecastMemory(), n=min(args.turns, 5))))
                logger.info(f"Digest exported to {args.output}")
            except Exception as e:
                logger.error(f"Failed to export digest: {e}")
                log_learning_event("exception", {"error": str(e), "context": "digest_export", "timestamp": datetime.now(timezone.utc).isoformat()})
        # --- Epistemic Mirror Curriculum Learning ---
        if getattr(args, "auto_upgrade", False):
            try:
                import subprocess
                upgrade_path = "plans/epistemic_upgrade_plan.json"
                batch_path = "logs/strategic_batch_output.jsonl"
                revised_path = "logs/revised_forecasts.jsonl"
                # Step 1: Generate upgrade plan
                subprocess.run([
                    sys.executable, "dev_tools/propose_epistemic_upgrades.py", "--output", upgrade_path
                ], check=True)
                logger.info(f"Epistemic upgrade plan generated at {upgrade_path}")
                # Step 2: Apply upgrade plan to latest batch
                if os.path.exists(batch_path) and os.path.exists(upgrade_path):
                    subprocess.run([
                        sys.executable, "dev_tools/apply_symbolic_upgrades.py",
                        "--batch", batch_path, "--plan", upgrade_path, "--out", revised_path
                    ], check=True)
                    logger.info(f"Applied epistemic upgrade plan to {batch_path}, output: {revised_path}")
                else:
                    logger.warning(f"Batch or upgrade plan not found for application: {batch_path}, {upgrade_path}")
            except Exception as e:
                logger.error(f"Failed to generate/apply epistemic upgrade plan: {e}")

    elif args.command == "repair":
        result = repair_variable_data(
            args.variable_name,
            variable_type=args.variable_type,
            skip_smoothing=args.skip_smoothing,
            skip_cross_source=args.skip_cross_source
        )
        print(json.dumps(result.to_dict(), indent=2))

    elif args.command == "simulate-repair":
        result = simulate_repair(
            args.variable_name,
            variable_type=args.variable_type
        )
        print(json.dumps(result.to_dict(), indent=2))

    elif args.command == "repair-report":
        result = get_repair_report(
            args.variable_name,
            version_id=args.version
        )
        print(json.dumps(result, indent=2))

    elif args.command == "revert":
        result = revert_to_original(
            args.variable_name,
            version_id=args.version
        )
        print(json.dumps(result, indent=2))

    elif args.command == "compare-versions":
        result = compare_versions(
            args.variable_name,
            args.version_id1,
            version_id2=args.version2
        )
        print(json.dumps(result, indent=2))

    elif args.command == "list-versions":
        result = get_all_versions(
            args.variable_name
        )
        print(json.dumps(result, indent=2))

    else:
        # Default action if no command is specified (e.g., just run simulation)
        run_pulse_simulation(turns=args.turns)
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write("# Strategos Digest\n\n")
                    f.write(str(generate_strategos_digest(ForecastMemory(), n=min(args.turns, 5))))
                logger.info(f"Digest exported to {args.output}")
            except Exception as e:
                logger.error(f"Failed to export digest: {e}")
                log_learning_event("exception", {"error": str(e), "context": "digest_export", "timestamp": datetime.now(timezone.utc).isoformat()})
        # --- Epistemic Mirror Curriculum Learning ---
        if getattr(args, "auto_upgrade", False):
            try:
                import subprocess
                upgrade_path = "plans/epistemic_upgrade_plan.json"
                batch_path = "logs/strategic_batch_output.jsonl"
                revised_path = "logs/revised_forecasts.jsonl"
                # Step 1: Generate upgrade plan
                subprocess.run([
                    sys.executable, "dev_tools/propose_epistemic_upgrades.py", "--output", upgrade_path
                ], check=True)
                logger.info(f"Epistemic upgrade plan generated at {upgrade_path}")
                # Step 2: Apply upgrade plan to latest batch
                if os.path.exists(batch_path) and os.path.exists(upgrade_path):
                    subprocess.run([
                        sys.executable, "dev_tools/apply_symbolic_upgrades.py",
                        "--batch", batch_path, "--plan", upgrade_path, "--out", revised_path
                    ], check=True)
                    logger.info(f"Applied epistemic upgrade plan to {batch_path}, output: {revised_path}")
                else:
                    logger.warning(f"Batch or upgrade plan not found for application: {batch_path}, {upgrade_path}")
            except Exception as e:
                logger.error(f"Failed to generate/apply epistemic upgrade plan: {e}")