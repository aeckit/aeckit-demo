# Spread Footing Workflow Progress & Resolution Summary

This document outlines the design history, initial unknowns, and the step-by-step resolution process implemented during the development of the automated spread footing design workflow.

---

## 1. Initial Unknowns and Challenges
At the start of the design implementation, we faced several technical and architectural unknowns:
*   **Architectural Separation (Where does logic live?):** We had to align on the *Flywheel Effect*—determining what calculations belong in the core shared library (`aeclib`) and what belongs in local workflow scripts.
*   **Geotechnical Defaults:** We needed to establish what presumptive soil properties to fall back on if soil profiles were not provided in the project database.
*   **Accidental Eccentricities:** We had to determine how to model construction and loading tolerances for pinned columns without input moments.
*   **CLI Data Serialization Clutter:** The initial CLI structure outputted large chunks of empty/null fields due to Pydantic model validation.
*   **Scaffolding Collisions:** The directory structure already contained documentation files, which would cause automatic CLI project creators to error out.

---

## 2. Step-by-Step Resolutions

### Step 1: Scaffolding and Directory Setup
*   **Action:** Bypassed automated scaffolding errors by manually creating the database files (`project.json`) and workflow definition (`workflow.json`) in place, avoiding any loss of documentation notes.

### Step 2: Refactoring CLI Data Model (Schema-less)
*   **Action:** Removed Pydantic and `aeclib` CLI dependencies. Re-engineered the database handlers to load and save native Python dictionaries.
*   **Outcome:** Eliminated all redundant `null` fields in CLI outputs and simplified data merging between workflow scripts.

### Step 3: Aligning Geotechnical and Structural Assumptions
*   **Action:** Codified industry standard defaults:
    *   Presumptive soil allowable bearing capacity = **$1,500\text{ psf}$** (IBC Table 1806.2 Class 5/6 soils).
    *   Presumptive soil unit weight = **$120\text{ pcf}$**.
    *   Accidental eccentricity = **$1.0\text{ inch}$** in both directions to simulate construction tolerances.
    *   Column dimensions = **$5.5\text{ in} \times 5.5\text{ in}$** (nominal 6x6 wood posts).

### Step 4: Library Load Combination Implementation
*   **Action:** Added `aeclib.us.structural.load_combinations` to evaluate dead, live, and environmental loads under standard ASCE 7/IBC templates (ASD for soil bearing, LRFD for concrete sizing).

### Step 5: Adding ACI 318 Concrete Checks to `aeclib`
*   **Action:** Added stateless calculation functions to `aeclib.us.structural.foundations` for one-way shear, two-way punching shear, required flexural steel area, minimum reinforcement verification ($A_{s,min} = 0.0018 b \cdot h$), and tension development length ($l_d$).
*   **Outcome:** Upgraded the core library to perform standard concrete checks cleanly without hardcoded project assumptions.

### Step 6: Coding local scripts & running the pipeline
*   **Action:** Created the final set of workflow scripts (`footing_bearing.py`, `footing_shear.py`, `footing_reinforcement.py`, and `footing_visualizer.py`), updated script path prefixes in `workflow.json` to match the reorganized `scripts/design/` and `scripts/visualization/` layout, and successfully executed the workflow.
*   **Outcome:** Verified end-to-end execution, producing completed 3D visualizations and successfully writing the optimized footing dimensions and reinforcement profiles back to the database.
