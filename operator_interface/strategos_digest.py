from forecast_output.forecast_licenser import filter_licensed_forecasts
from forecast_output.forecast_compressor import compress_forecasts
from forecast_output.strategos_tile_formatter import format_strategos_tile
from forecast_output.strategos_digest_builder import build_digest
from memory.forecast_memory import ForecastMemory
from typing import Optional, List, Dict
from core.path_registry import PATHS
from trust_system.alignment_index import compute_alignment_index
from trust_system.forecast_episode_logger import summarize_episodes
from trust_system.trust_engine import compute_symbolic_attention_score
from trust_system.forecast_licensing_shell import license_forecast
from simulation_engine.simulation_drift_detector import run_simulation_drift_analysis
from trust_system.license_enforcer import annotate_forecasts, filter_licensed, summarize_license_distribution
import os

assert isinstance(PATHS, dict), f"PATHS is not a dict, got {type(PATHS)}"

DIGEST_DIR = PATHS.get("DIGEST_DIR", PATHS["WORLDSTATE_LOG_DIR"])

def group_by_confidence(forecasts: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group forecasts by confidence levels.

    Args:
        forecasts (List[Dict]): List of forecast dictionaries.

    Returns:
        Dict[str, List[Dict]]: Grouped forecasts by confidence levels.
    """
    groups = {"🟢 Trusted": [], "⚠️ Moderate": [], "🔴 Fragile": [], "🔘 Unscored": []}
    for f in forecasts:
        score = f.get("confidence", "unscored")
        if isinstance(score, float):
            if score >= 0.75:
                groups["🟢 Trusted"].append(f)
            elif score >= 0.5:
                groups["⚠️ Moderate"].append(f)
            else:
                groups["🔴 Fragile"].append(f)
        else:
            groups["🔘 Unscored"].append(f)
    # Sort by priority_score, then confidence (descending)
    for label in groups:
        groups[label].sort(key=lambda f: (f.get('priority_score', 0.0), f.get("confidence", 0.0)), reverse=True)
    return groups

def compute_arc_drift(prev_path: str, curr_path: str) -> Dict[str, int]:
    """
    Compute the drift in symbolic arcs between two episode logs.

    Returns:
        Dict[str, int]: Arc label to drift delta.
    """
    try:
        prev = summarize_episodes(prev_path)
        curr = summarize_episodes(curr_path)
    except Exception as e:
        print(f"⚠️ Error summarizing episodes: {e}")
        return {}
    arcs_prev = {k.replace("arc_", ""): v for k, v in prev.items() if k.startswith("arc_")}
    arcs_curr = {k.replace("arc_", ""): v for k, v in curr.items() if k.startswith("arc_")}
    all_keys = set(arcs_prev) | set(arcs_curr)
    return {k: arcs_curr.get(k, 0) - arcs_prev.get(k, 0) for k in all_keys}

def flag_drift_sensitive_forecasts(forecasts: List[Dict], drift_report: Dict, threshold: float = 0.2) -> List[Dict]:
    """
    Flags forecasts if they belong to unstable arcs or drift-prone rule sets.

    Args:
        forecasts (List[Dict])
        drift_report (Dict): Output from run_simulation_drift_analysis()
        threshold (float): Drift cutoff for flagging

    Returns:
        List[Dict]: forecasts updated with 'drift_flag'
    """
    volatile_rules = {r for r, delta in drift_report.get("rule_trigger_delta", {}).items() if abs(delta) > threshold * 10}
    unstable_overlays = {k for k, v in drift_report.get("overlay_drift", {}).items() if v > threshold}

    for fc in forecasts:
        arc = fc.get("arc_label", "unknown")
        rules = fc.get("fired_rules", [])
        overlays = fc.get("forecast", {}).get("symbolic_change", {})

        flagged = False
        if any(r in volatile_rules for r in rules):
            fc["drift_flag"] = "⚠️ Rule Instability"
            flagged = True
        if any(k in unstable_overlays for k in overlays):
            fc["drift_flag"] = "⚠️ Overlay Volatility"
            flagged = True
        if not flagged:
            fc["drift_flag"] = "✅ Stable"
    return forecasts

def generate_strategos_digest(
    memory: ForecastMemory,
    n: int = 5,
    title: Optional[str] = None,
    previous_episode_log: Optional[str] = None,
    current_episode_log: Optional[str] = None,
    previous_trace_path: Optional[str] = None,
    current_trace_path: Optional[str] = None
) -> str:
    """
    Generate a Strategos digest from forecast memory.

    Args:
        memory (ForecastMemory): Forecast memory instance.
        n (int, optional): Number of recent forecasts to include. Defaults to 5.
        title (Optional[str], optional): Title for the digest. Defaults to None.
        previous_episode_log (Optional[str], optional): Path to previous episode log.
        current_episode_log (Optional[str], optional): Path to current episode log.
        previous_trace_path (Optional[str], optional): Path to previous simulation trace.
        current_trace_path (Optional[str], optional): Path to current simulation trace.

    Returns:
        str: Strategos digest as a formatted string.
    """
    raw = memory.get_recent(n + 5)
    try:
        forecasts = filter_licensed_forecasts(raw, strict=True)
    except Exception as e:
        return f"❌ Error filtering licensed forecasts: {e}"

    # --- Trust enforcement logic ---
    original_count = len(forecasts)
    try:
        forecasts = annotate_forecasts(forecasts)
        forecasts = filter_licensed(forecasts)
        licensed_count = len(forecasts)
        drop_rate = round(100 * (1 - licensed_count / max(original_count, 1)), 2)
        license_summary = summarize_license_distribution(forecasts)
    except Exception as e:
        licensed_count = 0
        drop_rate = 100.0
        license_summary = f"❌ License enforcement error: {e}"

    # --- License loss warning logic ---
    digest = {}
    digest["license_loss_percent"] = drop_rate
    digest["warnings"] = []
    if digest.get("license_loss_percent", 0) > 40:
        digest["warnings"].append("🔍 Triggering symbolic audit due to high license loss.")
        # Optionally call symbolic audit system or arc drift scanner here

    # --- Alignment scoring integration ---
    for forecast in forecasts:
        try:
            alignment = compute_alignment_index(forecast)
            forecast["alignment_score"] = alignment.get("alignment_score", 0.0)
        except Exception as e:
            forecast["alignment_score"] = 0.0
            forecast["alignment_error"] = str(e)

    # --- Forecast Licensing Summary ---
    licensed = {"approved": 0, "rejected": 0, "low_alignment": 0}
    for fc in forecasts:
        try:
            license_status = license_forecast(fc)
        except Exception as e:
            license_status = f"❌ Licensing Error: {e}"
        fc["license_status"] = license_status
        if license_status == "✅ Approved":
            licensed["approved"] += 1
        else:
            licensed["rejected"] += 1
            if "Alignment" in license_status:
                licensed["low_alignment"] += 1

    # Optionally sort by alignment_score (top-N)
    forecasts = sorted(forecasts, key=lambda f: f.get("alignment_score", 0), reverse=True)

    groups = group_by_confidence(forecasts)
    header = title or "Strategos Forecast Digest"

    sections = [f"📘 {header}", ""]

    # --- Trust Enforcement Report ---
    sections.append("## 🛡️ Trust Enforcement Report")
    sections.append(f"- Total forecasts: {original_count}")
    sections.append(f"- Approved: {licensed_count}")
    sections.append(f"- Rejected: {original_count - licensed_count}")
    sections.append(f"- License drop rate: {drop_rate:.2f}%")
    if isinstance(license_summary, dict):
        for k, v in license_summary.items():
            sections.append(f"- {k}: {v}")
    else:
        sections.append(str(license_summary))
    if drop_rate > 40:
        sections.append("⚠️ High license loss rate — trust coherence degraded.")
    sections.append("")

    # --- Licensing Summary Markdown Section ---
    sections.append("## ✅ Forecast Licensing Summary")
    sections.append(f"- Approved: {licensed['approved']}")
    sections.append(f"- Rejected: {licensed['rejected']}")
    sections.append(f"- Low Alignment: {licensed['low_alignment']}")
    sections.append("")

    # Arc drift summary
    arc_drift = {}
    if previous_episode_log and current_episode_log and os.path.exists(previous_episode_log) and os.path.exists(current_episode_log):
        arc_drift = compute_arc_drift(previous_episode_log, current_episode_log)
        if arc_drift:
            sections.append("## 🌀 Arc Drift This Cycle")
            for arc, delta in arc_drift.items():
                sign = "+" if delta > 0 else ""
                sections.append(f"- {arc}: {sign}{delta}")
            sections.append("")

    # Simulation drift summary
    drift_report = None
    if previous_trace_path and current_trace_path and os.path.exists(previous_trace_path) and os.path.exists(current_trace_path):
        try:
            drift_report = run_simulation_drift_analysis(previous_trace_path, current_trace_path)
            if "error" in drift_report:
                sections.append(f"⚠️ Simulation drift analysis failed: {drift_report['error']}")
            else:
                sections.append("## 🧪 Simulation Drift Summary")
                for k, v in drift_report.get("overlay_drift", {}).items():
                    sign = "+" if v > 0 else ""
                    sections.append(f"- Overlay Δ {k.capitalize()}: {sign}{v:.3f}")
                if drift_report.get("rule_trigger_delta"):
                    sections.append("- Rule trigger delta:")
                    for rule, delta in drift_report["rule_trigger_delta"].items():
                        sign = "+" if delta > 0 else ""
                        sections.append(f"  - {rule}: {sign}{delta}")
                if drift_report.get("structure_shift") and "turn_diff" in drift_report["structure_shift"]:
                    td = drift_report["structure_shift"]["turn_diff"]
                    sign = "+" if td > 0 else ""
                    sections.append(f"- Turn count changed by: {sign}{td}")
                sections.append("")
        except Exception as e:
            sections.append(f"⚠️ Simulation drift analysis failed: {e}")

    # Flag drift-sensitive forecasts if drift_report is available
    if drift_report and "error" not in drift_report:
        forecasts = flag_drift_sensitive_forecasts(forecasts, drift_report)

    # --- Drift-Flagged Forecasts Section ---
    drifted = [f for f in forecasts if f.get("drift_flag") in {"⚠️ Rule Instability", "⚠️ Overlay Volatility"}]
    if drifted:
        sections.append("## 🔥 Drift-Flagged Forecasts")
        for fc in drifted[:10]:
            sections.append(f"- {fc.get('trace_id', 'unknown')} → {fc['drift_flag']}")
        sections.append("")

    for label in ["🟢 Trusted", "⚠️ Moderate", "🔴 Fragile", "🔘 Unscored"]:
        tiles = groups[label]
        if not tiles:
            continue
        sections.append(f"==== {label} ====")
        for tile in tiles:
            # Display alignment alongside confidence
            conf = tile.get("confidence", "N/A")
            align = tile.get("alignment_score", "N/A")
            drift_flag = tile.get("drift_flag", "")
            # Add attention score if arc_drift is available
            attention = ""
            if arc_drift:
                try:
                    attn_score = compute_symbolic_attention_score(tile, arc_drift)
                    if attn_score > 0.5:
                        attention = f" | ⚡️Attention: {attn_score}"
                    elif attn_score > 0:
                        attention = f" | Attention: {attn_score}"
                except Exception as e:
                    attention = " | ⚠️ Attention Error"
            drift_note = f" | {drift_flag}" if drift_flag and drift_flag != "✅ Stable" else ""
            try:
                tile_str = format_strategos_tile(tile)
            except Exception as e:
                tile_str = f"⚠️ Error formatting tile: {e}"
            sections.append(f"[Conf: {conf} | Align: {align}{attention}{drift_note}]")
            sections.append(tile_str)
        sections.append("")

    # Footer: summary stats
    try:
        ret_scores = [f.get("retrodiction_score", 0.0) for f in forecasts if isinstance(f.get("retrodiction_score"), (float, int))]
        sym_scores = [f.get("symbolic_score", 0.0) for f in forecasts if isinstance(f.get("symbolic_score"), (float, int))]
        avg_r = round(sum(ret_scores) / len(ret_scores), 3) if ret_scores else 0.0
        avg_s = round(sum(sym_scores) / len(sym_scores), 3) if sym_scores else 0.0
        sections.append(f"🎯 Avg Retrodiction Score: {avg_r} | Symbolic Score: {avg_s}")
    except Exception as e:
        sections.append(f"⚠️ Retrodiction stats unavailable: {e}")

    try:
        sparkline = [round(f.get("confidence", 0.0), 2) for f in forecasts]
        sections.append(f"📊 Confidence Sparkline: {sparkline}")
    except Exception as e:
        sections.append(f"⚠️ Sparkline unavailable: {e}")

    try:
        ages = [f.get("age_hours", 0) for f in forecasts]
        if ages:
            avg_age = round(sum(ages) / len(ages), 2)
            oldest = max(ages)
            sections.append(f"🕓 Forecast Age: Avg {avg_age}h | Max: {oldest}h")
    except Exception as e:
        sections.append(f"⚠️ Age stats unavailable: {e}")

    sections.append(f"Total Forecasts: {len(forecasts)}")

    return "\n".join(sections)

def live_digest_ui(memory: ForecastMemory, prompt: str = None, n: int = 10, export_fmt: str = "markdown", template: str = "full"):
    """
    Live UI hook: Build and display strategos digest, optionally filtered by prompt and template.

    Example:
        live_digest_ui(memory, prompt="AI", n=10, export_fmt="markdown", template="short")
    """
    raw = memory.get_recent(n + 10)
    if prompt:
        # Use digest builder's filter for prompt
        try:
            from forecast_output.strategos_digest_builder import filter_forecasts_by_prompt
            raw = filter_forecasts_by_prompt(raw, prompt)
        except Exception as e:
            print(f"⚠️ Error filtering by prompt: {e}")
    try:
        digest = build_digest(raw, fmt=export_fmt, config={"top_n": 3, "actionable_only": False}, template=template)
    except Exception as e:
        digest = f"❌ Error building digest: {e}"
    print(digest)
    return digest

# --- Simple test function for manual validation ---
def _test_digest():
    """Basic test for strategos digest generation."""
    class DummyMemory:
        def get_recent(self, n):
            # Return dummy forecasts
            return [
                {"confidence": 0.8, "alignment_score": 80, "trust_label": "🟢 Trusted", "priority_score": 1, "retrodiction_score": 0.9, "symbolic_score": 0.8, "age_hours": 2},
                {"confidence": 0.6, "alignment_score": 60, "trust_label": "⚠️ Moderate", "priority_score": 0.5, "retrodiction_score": 0.7, "symbolic_score": 0.6, "age_hours": 5},
                {"confidence": 0.4, "alignment_score": 40, "trust_label": "🔴 Fragile", "priority_score": 0.2, "retrodiction_score": 0.5, "symbolic_score": 0.4, "age_hours": 10},
            ]
    print(generate_strategos_digest(DummyMemory(), n=3, title="Test Digest"))

if __name__ == "__main__":
    _test_digest()