# Tracking Issues

This document tracks bugs, feature requests, and tasks identified during the spread footing workflow development.

---

## 📋 Issue Status Summary

| ID | Status | Title | Description | Resolution / Target |
|---|---|---|---|---|
| **#1** | ✅ Resolved | `aeckit project show` prints redundant `null` fields | Prints unset fields from `Building` model dump. | Replaced Pydantic models with schema-less native Python dictionaries. |
| **#2** | ✅ Resolved | Add standard load combinations to `aeclib` | Needed to calculate service and ultimate design loads for different failure modes. | Implemented ASD and LRFD combinations (ASCE 7 / IBC) in `aeclib.us.structural.load_combinations`. |
| **#3** | ✅ Resolved | Implement soil bearing capacity verification | First spread footing failure mode to check under service combinations. | Implemented `validate_bearing_pressure` in `aeclib.us.structural.foundations`. |
| **#4** | ✅ Resolved | Implement ACI 318 temperature & shrinkage steel limits | Prescriptive minimum reinforcement limits for concrete slabs/footings. | Implemented `validate_minimum_reinforcement` and shear check helper equations in `aeclib.us.structural.foundations`. |

---

## 🚫 Active Issues

None! All issues have been successfully resolved.

---

## ✅ Resolved Issues

### #1. `aeckit project show` prints redundant `null` fields
*   **Description:** Running `aeckit project show` printed the entire `Building` model dump including all unset/null fields (e.g., `address`, `latitude`, `longitude`, `levels`, `metadata`), cluttering the CLI output.
*   **Root Cause:** In `aeckit-cli/aeckit/cli.py`, the show command validated and serialized Pydantic's structured model, which automatically set default/unset optional properties to `null`.
*   **Resolution:**
    - Refactored `JSONHandler`, `Project`, and `Orchestrator` to load, serialize, and merge data as native Python dictionaries.
    - Deleted `models.py` completely and removed `pydantic` and `aeclib` from the project's dependencies to make the CLI fully schema-less.
    - Updated `aeckit project show` to directly print `p.data` JSON, outputting exactly what is defined in the project configuration without extra null fields.
    - Implemented a standard unit test suite in `tests/` to verify dictionary loader, context manager, AST scanner, and orchestrator workflow runs.

### #2. Add standard load combinations to `aeclib`
*   **Description:** For code-compliant designs, we must evaluate different combinations of dead, live, wind, and seismic loads.
*   **Resolution:** Added `aeclib.us.structural.load_combinations` supporting ASCE 7/IBC ASD and LRFD combinations.

### #3. Implement soil bearing capacity verification
*   **Description:** Verify soil bearing pressures under service loads, accounting for accidental eccentricities.
*   **Resolution:** Implemented bearing capacity checks in `aeclib.us.structural.foundations` and codified design/bearing calculations in `design/footing_bearing.py`.

### #4. Implement ACI 318 temperature & shrinkage minimum reinforcement limits
*   **Description:** Concrete footings must meet minimum reinforcement ratios and shear capacity requirements.
*   **Resolution:** Implemented ACI 318 calculations in `aeclib.us.structural.foundations` and wrote design workflow scripts `design/footing_shear.py` and `design/footing_reinforcement.py` to automate thickness sizing and rebar design.
