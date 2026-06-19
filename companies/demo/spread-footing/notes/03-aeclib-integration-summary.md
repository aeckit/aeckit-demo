# Hand-off Summary: Spread Footing Compliance Integration in `aeclib`

This document summarizes the changes made to the core library `aeclib` and outlines the integration context for future refactoring and optimization.

---

## 1. Summary of Changes in `aeclib`
We added stateless building code compliance functions for ACI 318-19 to the structural foundations package in `aeclib` (specifically under `aeclib.us.structural.foundations.generic`):

*   **`calculate_one_way_shear_capacity`**: Calculates the design one-way shear strength ($\phi V_c$) of a concrete member without shear reinforcement.
*   **`calculate_two_way_shear_capacity`**: Calculates the design punching shear strength ($\phi V_c$) using the minimum of the three governing ACI 318-19 formulas, with parameters for column geometries and location categories (interior, edge, corner).
*   **`calculate_required_flexural_steel_area`**: Computes the required reinforcing steel area ($A_s$) for a given factored bending moment ($M_u$) using tension-controlled flexural equations.
*   **`validate_minimum_reinforcement`**: Evaluates whether the reinforcing steel area meets the ACI 318 temperature and shrinkage minimum steel ratio ($A_{s,min} = 0.0018 \cdot b \cdot h$).
*   **`calculate_development_length`**: Calculates the simplified tension development length ($l_d$) for standard US deformed bars (sizes #3–#11), incorporating casting position (top/bottom) and coating factors, subject to the ACI absolute minimum of $12\text{ inches}$.

---

## 2. Why these changes were made (Architectural Context)
1.  **Strict Compliance/Physics Separation**: Per workspace architectural standards, structural physics (concrete self-weight, soil overburden, eccentricity pressures, sizing loops) are written in local project scripts. Prescriptive building code equations, limits, and material check capacities are written in `aeclib`.
2.  **Stateless API Design**: The functions added to `aeclib` accept only raw float/int parameters (rather than nesting under project-specific JSON hierarchies), ensuring they can be reused across different foundation projects, sizing scripts, or higher-level schemas.
3.  **End-to-End Pipeline Support**: These checks allowed the creation of local workflow scripts:
    *   `design/footing_bearing.py` (ASD plan sizing under service loads).
    *   `design/footing_shear.py` (LRFD thickness sizing under one-way and punching shear).
    *   `design/footing_reinforcement.py` (LRFD rebar design and development length checks).

---

## 3. Recommendations for the Next Agent (Reusability & Refactoring)
To further genericize and reuse these functions:
*   **Unify Reinforcement Checks**: The `calculate_development_length` function currently implements the simplified ACI 318-19 method. The next agent could extend this to support the detailed method if confinement factors ($\psi_s$, $c_b$, $K_{tr}$) become available.
*   **Support Column Geometry Types**: The current `calculate_two_way_shear_capacity` assumes a rectangular column pedestal. It can be genericized to accept an equivalent round column parameter or compute critical shear perimeter ($b_0$) for arbitrary polygon shapes.
*   **Pedestal & Dowel Development**: Add a doweled connection development check to transfer compression/tension forces from wood/steel column base plates into the footing.
