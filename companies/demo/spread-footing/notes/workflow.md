# Spread Footing Workflow Progress Log

This document records the design progression, key decisions, and upcoming tasks for the automated spread footing design workflow.

---

## 1. Accomplishments (Session Log)

### 1.1 Project Scaffolding & Context
*   **Workflow Integration:** Reviewed the architectural boundaries and guidelines in `system_architecture.md` and `WORKFLOW_GUIDANCE.md`.
*   **Pipeline Scaffolding:** Configured the `design_footing` workflow sequence in `workflow.json` and switched the active CLI default context to `spread-footing`.
*   **Issue Tracking:** Set up `tracking-issues.md` to log bugs and coordinate resolution tasks.

### 1.2 Data Model Improvements
*   **Building-Level Hierarchy:** Configured `project.json` to organize footing instances under a nested `foundations.spread_footings.instances` structure.
*   **Shared Attributes:** Consolidated `materials` and `geotechnical` properties at the parent level to avoid duplication across individual instances.
*   **"No Abbreviations" Standard:** Added rules in `contributing.md` and `WORKFLOW_GUIDANCE.md` to avoid key abbreviations. Renamed abbreviated variables in `project.json` and `01-required-scripts.md` to full descriptive names (e.g., `width_ft`, `thickness_in`, `concrete_strength_psi`).

### 1.3 Geometry Preview & Formatting
*   **3D Geometry Preview:** Generated a Three.js-compatible wireframe model for footing `SF-1` at `visualizations/SF-1.viz.json`.
*   **Subfolder Structure:** Established the convention that all output wireframes reside in the `visualizations/` subdirectory.
*   **Formatting Prevention:** Resolved the IDE auto-formatting issue (splitting coordinate arrays into vertical lists) by globally associating `*.viz.json` with the `jsonc` language and disabling format-on-save for it.

### 1.4 Code Reset
*   **Clean Slate:** Reverted initial draft math checks in `aeclib` (bearing, shear, flexure) to keep the repository clean while coordinating planning and documentation.

---

## 2. Key Decisions & Technical Discoveries

### 2.1 Default Presumptive Geotechnical Values
Through technical review of building codes, we identified the following standard engineering defaults when geotechnical data is unknown:
*   **Allowable Soil Bearing Capacity:** Default to **$1,500\text{ psf}$** per *IBC Table 1806.2* (Class 5/6 soils: clays, silts, sand mixtures).
*   **Soil Unit Weight:** Default to **$120\text{ pcf}$** for gravity calculations.

### 2.2 Column Base Moments & Minimum Eccentricity
*   **Pinned-Base Columns:** Standard gravity posts/columns transferring loads to spread footings are assumed to be pinned, meaning we do not input external bending moments ($M_x = 0, M_y = 0$).
*   **Minimum Eccentricity (Accidental):** To account for construction tolerances, out-of-plumbness, and loading eccentricities, the calculations will programmatically apply a minimum eccentricity of $e_{min} = 1.0\text{ inch}$ (or similar prescriptive ratio) in both horizontal directions during bearing capacity and shear checks.

### 2.3 Architectural Scope: aeclib vs. Local Scripts
*   **aeclib Scope (Building Code Rules):** Contains only stateless prescriptive legal limits, constants, and compliance checks (e.g. load combinations, allowable soil tables, minimum reinforcement ratios).
*   **Local Scripts Scope (Engineering Logic):** Performs physical structural calculations (like concrete overburden weight, corner pressures, eccentricity calculations) and the sizing optimization loop based on user-defined constraints.

---

## 3. Pending Task Checklist

### 3.1 Core Compliance Library (`aeclib`)
*   [x] **Presumptive Defaults Lookup:** Expose default soil values (IBC Table 1806.2).
*   [x] **Load Combinations:** Calculate ASCE 7 / IBC ASD and LRFD combinations.
*   [ ] **Minimum Temperature & Shrinkage Reinforcement:** Implement ratio-based verification ($A_{s,min} = 0.0018 b \cdot h$).
*   [ ] **Development Length lookup/checks:** Prescriptive equations for deformed bar development length $l_d$.
*   [ ] **Prescriptive Shear Equations:** Verify capacity equations ($\phi V_c$ limits) are in `aeclib`.
*   [ ] **Unit Tests:** Implement tests in `tests/us/structural/test_load_combinations.py` and other test files.

### 3.2 Compositional Workflow Scripts (in `aeckit-demo/scripts/`)
*   [ ] `footing_bearing.py` (Iterates and sizes the footing base based on ASD bearing checks, applying minimum eccentricity).
*   [ ] `footing_shear.py` (Factored LRFD punching and beam shear thickness check).
*   [ ] `footing_reinforcement.py` (Designs flexural reinforcement, checks ACI temperature/shrinkage minimums, and checks development length).
*   [x] `footing_visualizer.py` (Outputs geometry to `visualizations/{footing_id}.viz.json`).
