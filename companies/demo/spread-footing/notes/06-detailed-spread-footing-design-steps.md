# Detailed Spread Footing Design Process

This document traces the actual concrete design and verification steps implemented during our conversation to size and reinforce rectangular spread footings.

---

## Phase 1: Configuring SSoT and Geotechnical Defaults
*   **SSoT Setup:** Configured `project.json` to contain column dimensions ($5.5\text{ in} \times 5.5\text{ in}$ to represent nominal 6x6 wood posts) and loads.
*   **Geotechnical Defaults:** Established standard IBC Table 1806.2 Class 5/6 presumptive defaults for cases where soil properties are not provided:
    *   Allowable bearing capacity $q_a = 1,500\text{ psf}$
    *   Soil unit weight $\gamma_{soil} = 120\text{ pcf}$
*   **Accidental Eccentricity:** Applied an accidental tolerance eccentricity of $e_{acc} = 1.0\text{ inch}$ in both horizontal directions to simulate construction out-of-plumbness for pinned-base columns.
*   **Sizing Constraints:** Configured initial sizing bounds: minimum width $B_{min} = 3.0\text{ ft}$, minimum thickness $T_{min} = 12\text{ in}$, aspect ratio $1.0$, and sizing increments of $0.5\text{ ft}$.

---

## Phase 2: Resolving Load Combinations (`aeclib`)
> [!WARNING] Bottleneck: Missing Load Combinations
> At this point in the workflow, running the `aeckit flow design_footing` command failed because `aeclib` lacked the necessary load combination templates. We had to pause the workflow and implement `aeclib.us.structural.load_combinations` to support ASCE 7-16 Chapter 2 LRFD and ASD templates before proceeding.

*   **Implementation:** Added `aeclib.us.structural.load_combinations` supporting ASCE 7-16 Chapter 2 load combination templates.
*   **Service Level (ASD):** Resolved dead and live vertical load combinations under ASD templates to check soil bearing limits.
*   **Strength Level (LRFD):** Resolved dead and live vertical load combinations under LRFD templates to verify concrete shear and design reinforcement.

---

## Phase 3: Sizing footing base area ($B \times L$)
*   **Script:** [footing_bearing.py](file:///Users/nguyen/aec-projects/aeckit-org/aeckit-demo/scripts/design/footing_bearing.py)
*   **Self-Weight & Overburden:** Computed footing self-weight and soil overburden height $h_{soil} = D_f - T$ using soil and concrete unit weights.
*   **Eccentric Pressure:** Computed peak soil contact pressure under ASD combinations using the two-way eccentricity formula:
    $$q_{max} = \frac{P_{total}}{B \cdot L} \left(1 + \frac{6 e_B}{B} + \frac{6 e_L}{L}\right)$$
*   **Search Loop:** Starting at $B = B_{min}$ (with $L = B \cdot \text{aspect\_ratio}$), the script checks if $q_{max} \le q_a$ across all ASD combinations. It increments $B$ by $0.5\text{ ft}$ until the check passes.

---

## Phase 4: Sizing footing thickness ($T$) for shear capacity
> [!WARNING] Bottleneck: Missing Shear Capacity Equations
> When executing this phase via the CLI, the process halted because `calculate_one_way_shear_capacity` and `calculate_two_way_shear_capacity` did not exist in `aeclib.us.structural.foundations.generic`. We implemented these ACI 318 equations in the library before continuing.

*   **Script:** [footing_shear.py](file:///Users/nguyen/aec-projects/aeckit-org/aeckit-demo/scripts/design/footing_shear.py)
*   **Net Pressure:** Calculated maximum factored net soil bearing pressure ($q_{u,max,net}$) using LRFD load combinations (net column load alone, since soil overburden and self-weight do not produce bending/shear in the footing concrete slab).
*   **Search Loop:** Starting at $T = T_{min}$, the script calculates the effective depth:
    $$d = T - \text{cover} - 0.375\text{ in}$$
    It then verifies two shear criteria:
    1.  **One-Way (Beam) Shear:** Checks critical section at distance $d$ from the column face in both directions:
        $$Vu = q_{u,max,net} \cdot \text{width} \cdot (L_{cantilever} - d)$$
        It compares $Vu$ against the ACI 318 capacity $\phi V_c = 1.5 \sqrt{f'_c} b d$ (using `calculate_one_way_shear_capacity`).
    2.  **Two-Way (Punching) Shear:** Checks critical perimeter $b_0$ at $d/2$ from the column face:
        $$Vu = q_{u,max,net} \cdot (B \cdot L - A_{inside})$$
        It compares $Vu$ against the governing ACI 318 capacity equation (using `calculate_two_way_shear_capacity`).
*   If either shear check fails, the script increments $T$ by $2.0\text{ in}$ and restarts the checks.

---

## Phase 5: Designing bottom reinforcing steel grid
> [!WARNING] Bottleneck: Missing Reinforcement Equations
> Execution of `footing_reinforcement.py` failed because `calculate_required_flexural_steel_area` and `calculate_development_length` were missing from the `aeclib` foundations module. We context-switched to the library to implement these ACI 318 equations to unblock the workflow.

*   **Script:** [footing_reinforcement.py](file:///Users/nguyen/aec-projects/aeckit-org/aeckit-demo/scripts/design/footing_reinforcement.py)
*   **Bending Moment:** Computed governing LRFD factored bending moments at the face of the column in both directions:
    $$M_{u} = q_{u,max,net} \cdot \text{width} \cdot \frac{L_{cantilever}^2}{2}$$
*   **Required Steel Area ($A_{s,req}$):** Solved for $A_{s,req}$ using the ACI 318 flexural design equation (using `calculate_required_flexural_steel_area`).
*   **Shrinkage Reinforcement:** Enforced ACI 318 minimum temperature and shrinkage steel area:
    $$A_{s,min} = 0.0018 \cdot b \cdot T$$
*   **Bar Selection Loop:** For each direction, the script iterates over standard bar sizes (#4 to #8):
    *   Determines bar count $n = \max(4, \lceil A_{s} / a_{b} \rceil)$.
    *   Calculates center-to-center spacing $s$.
    *   Calculates tension development length $l_d$ (using `calculate_development_length`).
    *   Selects the first bar size that meets spacing limits ($3\text{ in} \le s \le 18\text{ in}$) and development length limits ($l_d \le \text{cantilever} - \text{cover}$). If $l_d$ exceeds the available length, it flags that a hook is required.

---

## Phase 6: Geometry Output and Visualization
*   **Script:** [footing_visualizer.py](file:///Users/nguyen/aec-projects/aeckit-org/aeckit-demo/scripts/visualization/footing_visualizer.py)
*   **Visual Elements:** Writes the geometric models to `.viz.json` files containing:
    *   A transparent gray 3D box mesh representing the concrete footing (`opacity: 0.25`).
    *   A semi-transparent amber 3D box mesh representing the wood column (`opacity: 0.75`).
    *   Rebar grids drawn inside the footing: long-direction bars shown as sky blue lines (`#0284c7`) and short-direction bars shown as emerald green lines (`#10b981`).

---

## Phase 7: Workflow Execution Commands (`aeckit-cli`)

Whenever running or reviewing the footing design workflow in `aeckit-demo`, use the following commands.

### 1. Verification & Context Checking
*   **Verify active context defaults (should be set to `demo` and `spread-footing`):**
    ```bash
    aeckit config show
    ```
*   **Set active context defaults (if not already set):**
    ```bash
    aeckit config set --company demo --project spread-footing
    ```
*   **Show the current Single Source of Truth (SSoT) state:**
    ```bash
    aeckit project show
    ```

### 2. Workflow Discovery
*   **List workflows configured in `workflow.json`:**
    ```bash
    aeckit workflow list
    ```
*   **Display steps of the design workflow:**
    ```bash
    aeckit workflow show --workflow design_footing
    ```

### 3. Execution
Since the core math library `aeclib` is located in `/Users/nguyen/aec-projects/aeclib-org/aeclib`, you must prepend the `PYTHONPATH` variable when running workflow executions so Python can locate the modified package source:

*   **Dry Run Execution (checks limits and reports in memory without writing to database):**
    ```bash
    PYTHONPATH=/Users/nguyen/aec-projects/aeclib-org/aeclib/src aeckit flow design_footing --dry-run
    ```
*   **Live Run Execution (writes optimized dimensions, reinforcement parameters, and generates visualizations):**
    ```bash
    PYTHONPATH=/Users/nguyen/aec-projects/aeclib-org/aeclib/src aeckit flow design_footing
    ```

