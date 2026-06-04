# aeckit-demo: Engineering-as-Code Workflow Demonstration

This repository provides a hands-on demonstration of the **aeckit** ecosystem, showcasing the unified engineering-as-code workflow. It illustrates how to manage structural parameters, execute compliance checks, and run automated analysis pipelines using the **aeckit-cli** command-line interface.

---

## 1. Key CLI Orchestrator Capabilities

The power of the `aeckit` workflow comes from separating engineering data from execution logic using **aeckit-cli**. The orchestrator provides the following core capabilities:

*   **Single Source of Truth (SSoT):** All building specifications, coordinates, and design parameters reside in a single [project.json](companies/demo/creston-deck/project.json) file. Treating this file as project-level configuration prevents fragmentation and keeps parameters synchronized.
*   **Workflow Orchestration (`flow`):** Instead of manually coordinating scripts, you define ordered pipelines in [workflow.json](companies/demo/creston-deck/workflow.json). The CLI dynamically loads and executes these scripts sequentially, feeding outputs from one script into the input context of the next.
*   **Incremental State Mutation:** Workflow scripts do not modify files directly. Instead, they return a dictionary containing a `building_updates` payload. The CLI safely merges this payload back into the SSoT (`project.json`).
*   **Decoupled Visualization Outputs:** Workflow scripts can generate raw geometric drawings (like arrays of `[x, y, z]` coordinates, edges, meshes, or text labels). In the wider `aeckit` ecosystem, these outputs are rendered by decoupled visualizer extensions (such as `visualizer-vsix` for 3D rendering and `detail-vsix` for 2D parametric detailing), separating engineering math from geometry presentation.
*   **Active Workspace Context (`config`):** A local `.aeckit` configuration file saves the active `--company` and `--project` context, allowing clean command execution without repetitive flags.
*   **Safety Limits (`--dry-run` & `--snapshot`):**
    *   **Dry Run (`--dry-run`):** Simulates calculations and logs results directly to the terminal *without* writing any mutations to `project.json`.
    *   **Snapshot (`--snapshot`):** Automatically backs up the current state of `project.json` into the `history/` directory before mutation, ensuring a full audit trail and easy rollback.

---

## 2. Directory Structure

This demonstration is structured as follows:

```
aeckit-demo/
├── .aeckit                 # Local active context configuration (e.g., demo/creston-deck)
├── LICENSE                 # MIT License details
├── companies/              # Portfolios and project specifications
│   └── demo/               # Company portfolio directory
│       ├── creston-deck/   # Active project directory
│       │   ├── project.json      # SSoT (building specifications and metadata)
│       │   ├── workflow.json     # Workflow pipeline script definitions
│       │   └── reports/          # Flow execution history and reports
│       └── spread-footing/ # Secondary project directory (Spread Footing guidelines)
│           └── notes.md          # Engineering design checklist & requirements
└── scripts/                # Compositional analysis and geoprocessing scripts
    ├── geocode.py                # Uses Census API to resolve address to lat/long
    ├── seismic_hazards.py        # Queries USGS design maps for seismic factors
    ├── roof_weight.py            # Simple interactive weight capture script
    └── helpers/                  # Shared helper scripts
        └── web.py                # Pure Python urllib web client utility
```

---

## 3. Getting Started

Follow these steps to run the demo workflows in your local development environment.

### Prerequisites

*   Python 3.8+ installed.
*   The `aeckit-cli` tool installed. (To install in editable mode for local development, run `pip install -e .` from the `aeckit-cli` directory).

### Step 1: Verify Your Local Context

The repository includes a pre-configured `.aeckit` workspace file that points to the `demo` company and the `creston-deck` project. Check your current active context:

```bash
aeckit config show
```

*Expected output:*
```json
{
  "company": "demo",
  "project": "creston-deck"
}
```

> [!NOTE]
> If you need to set or override the context manually, run:
> `aeckit config set --company demo --project creston-deck`

### Step 2: Inspect Project Data and Workflows

1.  **View Project Data (SSoT):**
    Print the contents of the current `project.json` context:
    ```bash
    aeckit project show
    ```

2.  **List Available Workflows:**
    See all workflows defined in the project's `workflow.json`:
    ```bash
    aeckit workflow list
    ```
    *Expected output:*
    - `get_lat_long`
    - `get_roof_weight`

3.  **Inspect Workflow Steps:**
    View the sequential execution steps of a specific workflow:
    ```bash
    aeckit workflow show --workflow get_lat_long
    ```
    *Expected output:*
    1. `geocode.py`
    2. `seismic_hazards.py`

---

## 4. Running the Workflows

### Workflow A: Geocoding & Seismic Parameters (`get_lat_long`)

This workflow demonstrates automated parameter retrieval. `geocode.py` converts the project's street address into coordinates, which are then passed to `seismic_hazards.py` to query USGS design maps for seismic acceleration factors ($S_s, S_1, S_{DS}$).

1.  **Run in Dry-Run Mode:**
    Simulate the workflow run to verify output without changing the SSoT:
    ```bash
    aeckit flow get_lat_long --dry-run
    ```
    Review the terminal output containing the calculated coordinates and USGS seismic responses.

2.  **Execute and Commit Updates:**
    Run the workflow in commit mode to fetch live values and write them to `project.json`:
    ```bash
    aeckit flow get_lat_long
    ```

3.  **Confirm the Mutation:**
    Verify that `project.json` has been updated with latitude, longitude, and seismic factors:
    ```bash
    aeckit project show
    ```

---

### Workflow B: Interactive Parameter Capture (`get_roof_weight`)

This workflow demonstrates how the CLI handles interactive input during execution. The script `roof_weight.py` prompts the user for building weight parameters and commits the value back to the SSoT.

1.  **Run the Workflow:**
    ```bash
    aeckit flow get_roof_weight
    ```

2.  **Respond to the Prompt:**
    When prompted `How much weight is in the roof (in lbs)?`, enter a numerical value (e.g., `25000`):
    ```
    How much weight is in the roof (in lbs)? 25000
    ```

3.  **Verify the Update:**
    Check that `roof_weight` has been saved under the project metadata:
    ```bash
    aeckit project show
    ```

---

## 5. Compositional Script Architecture

Workflows consist of modular Python scripts placed in the `scripts/` directory. Each script must expose a entrypoint function named after the file. 

The function receives the parsed `project_data` dictionary and returns a dictionary. To update the project's SSoT, the return dictionary must contain a `building_updates` sub-dictionary:

```python
# scripts/geocode.py entrypoint
from helpers.web import make_web_request

def geocode(project_data: dict) -> dict:
    address = project_data.get("address")
    if not address:
        return {"error": "Missing 'address' in project data."}
        
    # Geocoding lookup logic here...
    latitude = 47.507
    longitude = -122.269

    # Return update payload to CLI
    return {
        "analysis_type": "geocoding",
        "latitude": latitude,
        "longitude": longitude,
        "building_updates": {
            "latitude": latitude,
            "longitude": longitude
        }
    }
```

The `aeckit-cli` dynamically handles the loading, execution, safety backups, and state merging of these components.

---

## 6. License

MIT License — see [LICENSE](LICENSE) for details.
