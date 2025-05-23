# Module Analysis: `simulation_engine/utils/simulation_trace_viewer.py`

## 1. Module Intent/Purpose

The primary role of the [`simulation_trace_viewer.py`](../../simulation_engine/utils/simulation_trace_viewer.py) module is to provide a command-line utility for loading, inspecting, visualizing, and summarizing simulation trace files. These trace files are expected to be in JSON Lines (`.jsonl`) format, with each line representing an event in the simulation. The module allows users to plot symbolic overlays, specific variables, and symbolic tags over time, as well as generate textual summaries of the trace data.

## 2. Operational Status/Completeness

The module appears to be a functional and relatively complete utility for its defined scope. It handles file loading, provides several plotting options, and can export a basic summary. There are no obvious placeholders (e.g., `TODO` comments) or indications of major unfinished sections within its current feature set. Error handling for file operations and argument parsing is present.

## 3. Implementation Gaps / Unfinished Next Steps

*   **Extensibility:** While functional, the plotting capabilities could be extended (e.g., more customization options for plots, different plot types, statistical summaries on plots).
*   **Advanced Analysis:** The current summary is basic. More advanced analytical features (e.g., event frequency analysis, pattern detection within traces) are not present but could be logical extensions if required.
*   **Interactive Mode:** An interactive mode for exploring traces could be a significant enhancement but is beyond the current script's scope.
*   **No clear signs of deviation:** The module seems to fulfill its role as a standalone trace viewing utility without indications of a larger, unfinished development path it was diverted from.

## 4. Connections & Dependencies

### Direct Project Module Imports
*   None. This module is self-contained in terms of project-specific code dependencies.

### External Library Dependencies
*   [`json`](https://docs.python.org/3/library/json.html): Used for parsing JSON Lines data from the trace file.
*   [`sys`](https://docs.python.org/3/library/sys.html): Used for accessing command-line arguments.
*   [`collections.Counter`](https://docs.python.org/3/library/collections.html#collections.Counter): Used in [`export_summary()`](../../simulation_engine/utils/simulation_trace_viewer.py:46) and [`main()`](../../simulation_engine/utils/simulation_trace_viewer.py:60) to count key occurrences in events.
*   [`matplotlib.pyplot`](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.html): Used for generating plots of trace data.

### Interaction with Other Modules via Shared Data
*   **Input:** Reads simulation trace files, which are assumed to be `.jsonl` files generated by other parts of the simulation engine (e.g., [`simulation_engine/utils/simulation_trace_logger.py`](../../simulation_engine/utils/simulation_trace_logger.py)).
*   **Output:** Can write a textual summary of the trace to a specified output file.

### Input/Output Files
*   **Input:**
    *   A simulation trace file (e.g., `trace.jsonl`), specified as a command-line argument. Each line is a JSON object representing a simulation event.
*   **Output:**
    *   Plots displayed to the screen using `matplotlib`.
    *   A summary text file (e.g., `out.txt`) if the `--export-summary` option is used.

## 5. Function and Class Example Usages

The module is primarily used as a script from the command line.

*   **[`load_trace(filepath)`](../../simulation_engine/utils/simulation_trace_viewer.py:6):**
    *   Loads events from a JSONL trace file.
    *   Usage: `events = list(load_trace("path/to/trace.jsonl"))`

*   **[`plot_trace(events, keys=None)`](../../simulation_engine/utils/simulation_trace_viewer.py:15):**
    *   Plots the values of specified symbolic overlay keys over time. Defaults to `["hope", "despair", "rage", "fatigue"]`.
    *   Called internally when `python simulation_trace_viewer.py <trace.jsonl> --plot` is run.

*   **[`plot_variable(events, var)`](../../simulation_engine/utils/simulation_trace_viewer.py:28):**
    *   Plots the value of a specific variable from the trace events over time.
    *   Called internally when `python simulation_trace_viewer.py <trace.jsonl> --plot-var my_variable` is run.

*   **[`plot_tags(events)`](../../simulation_engine/utils/simulation_trace_viewer.py:37):**
    *   Plots the symbolic tags assigned to events over time.
    *   Called internally when `python simulation_trace_viewer.py <trace.jsonl> --plot-tags` is run.

*   **[`export_summary(events, out_path)`](../../simulation_engine/utils/simulation_trace_viewer.py:46):**
    *   Exports a summary (total events, top keys, first event) to a specified text file.
    *   Called internally when `python simulation_trace_viewer.py <trace.jsonl> --export-summary summary.txt` is run.

*   **[`main()`](../../simulation_engine/utils/simulation_trace_viewer.py:60):**
    *   Parses command-line arguments and orchestrates the loading, plotting, or summarizing of trace data.
    *   Example CLI invocations:
        ```bash
        python simulation_engine/utils/simulation_trace_viewer.py path/to/trace.jsonl
        python simulation_engine/utils/simulation_trace_viewer.py path/to/trace.jsonl --summary
        python simulation_engine/utils/simulation_trace_viewer.py path/to/trace.jsonl --plot
        python simulation_engine/utils/simulation_trace_viewer.py path/to/trace.jsonl --plot-var "temperature"
        python simulation_engine/utils/simulation_trace_viewer.py path/to/trace.jsonl --plot-tags
        python simulation_engine/utils/simulation_trace_viewer.py path/to/trace.jsonl --export-summary output_summary.txt
        ```

## 6. Hardcoding Issues

*   **Default Overlay Keys:** In [`plot_trace()`](../../simulation_engine/utils/simulation_trace_viewer.py:16), the default `overlays` are hardcoded to `["hope", "despair", "rage", "fatigue"]`. While these can be overridden via the `keys` parameter if called programmatically, the CLI `--plot` option does not expose a way to change these defaults.
*   **Default Overlay Value:** In [`plot_trace()`](../../simulation_engine/utils/simulation_trace_viewer.py:17), if an overlay key is missing in an event, its value defaults to `0.5`.
*   **Default Tag Value:** In [`plot_tags()`](../../simulation_engine/utils/simulation_trace_viewer.py:38), if `symbolic_tag` is missing, it defaults to `"N/A"`.
*   **Plot Aesthetics:** Plot titles (e.g., `"Symbolic Overlays Over Time"`), labels (`"Step"`, `"Value"`), and figure sizes (e.g., `figsize=(8, 4)`) are hardcoded.
*   **CLI Argument Strings:** Command-line flags like `"--summary"`, `"--plot"`, etc., are hardcoded strings within the [`main()`](../../simulation_engine/utils/simulation_trace_viewer.py:60) function.

## 7. Coupling Points

*   **Trace File Format:** The module is tightly coupled to the expected structure of the input `.jsonl` trace files. It specifically looks for keys like `"overlays"`, `"variables"`, and `"symbolic_tag"` within the JSON objects. Changes to this trace format would require updates to this viewer.
*   **Matplotlib:** Relies on `matplotlib` for all plotting functionalities.

## 8. Existing Tests

*   No dedicated test file (e.g., `test_simulation_trace_viewer.py`) was found in the `tests/simulation_engine/utils/` directory or other common test locations.
*   This indicates a lack of automated unit or integration tests for this module. Testing would likely involve creating sample trace files and verifying the output of plots (e.g., by saving to image files and comparing, or by checking properties of plot objects) and summary files.

## 9. Module Architecture and Flow

The module is structured as a command-line script:
1.  **Imports:** Standard library modules (`json`, `sys`, `collections`) and `matplotlib.pyplot`.
2.  **Helper Functions:**
    *   [`load_trace()`](../../simulation_engine/utils/simulation_trace_viewer.py:6): Reads and parses the `.jsonl` input file line by line, yielding event dictionaries.
    *   [`plot_trace()`](../../simulation_engine/utils/simulation_trace_viewer.py:15), [`plot_variable()`](../../simulation_engine/utils/simulation_trace_viewer.py:28), [`plot_tags()`](../../simulation_engine/utils/simulation_trace_viewer.py:37): These functions take a list of events and generate specific plots using `matplotlib`.
    *   [`export_summary()`](../../simulation_engine/utils/simulation_trace_viewer.py:46): Writes a textual summary of the events to a file.
3.  **Main Function ([`main()`](../../simulation_engine/utils/simulation_trace_viewer.py:60)):**
    *   Parses command-line arguments using `sys.argv`.
    *   Loads all events from the specified trace file into a list.
    *   Based on the provided arguments, it either:
        *   Prints a summary to the console (`--summary`).
        *   Calls one of the plotting functions (`--plot`, `--plot-var`, `--plot-tags`).
        *   Calls the export summary function (`--export-summary`).
        *   If no specific action is requested, it prints each event to the console.
4.  **Script Execution:** The `if __name__ == "__main__":` block calls the [`main()`](../../simulation_engine/utils/simulation_trace_viewer.py:60) function when the script is run directly.

The primary control flow is determined by the command-line arguments, leading to different processing paths for the loaded trace data.

## 10. Naming Conventions

*   **Functions:** Function names like [`load_trace`](../../simulation_engine/utils/simulation_trace_viewer.py:6), [`plot_trace`](../../simulation_engine/utils/simulation_trace_viewer.py:15), [`export_summary`](../../simulation_engine/utils/simulation_trace_viewer.py:46) are descriptive and follow `snake_case`, which is consistent with PEP 8.
*   **Variables:**
    *   Local variables like `filepath`, `events`, `overlays`, `plot_var` are generally clear.
    *   Short variable names like `f` (for file objects), `e` (for event in loops), `k` (for key in loops), `idx` (for index) are used, which is acceptable in limited scopes.
*   **Constants:** There are no formally defined constants (e.g., uppercase with underscores), but string literals for plot titles, labels, and CLI arguments serve a similar purpose and are directly embedded.
*   **Overall:** The naming is largely consistent and follows Python conventions (PEP 8). There are no obvious AI-generated or highly unconventional naming patterns.