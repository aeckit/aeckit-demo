# Guidance: Automated Engineering Calculation Workflows

This document serves as a complementary guide to the [README.md](file:///Users/nguyen/aec-projects/aeckit-org/aeckit-demo/README.md). It outlines generic guidance, design patterns, and step-by-step phases required to build out automated, code-compliant engineering calculation workflows within the **aeckit** ecosystem.

---

## Problem Statement
In traditional architecture, engineering, and construction (AEC) workflows, structural calculation parameters, code compliance rules, and drafting environments are highly fragmented. Design values (loads, dimensions, materials) are manually transcribed across spreadsheets, design reports, and CAD/BIM software, increasing the risk of data mismatch. Furthermore, compliance calculations are often embedded directly into drafting tools or written as ad-hoc scripts, making them difficult to audit, reuse, or run in headless automated pipelines.

## First Step: Data Modeling & Orchestration Scaffolding
Before writing any verification code or mathematical checks, the first step is to establish the data model. You must explicitly declare the inputs and outputs inside the Single Source of Truth (`project.json`) and configure the sequence of compositional scripts inside the workflow pipeline (`workflow.json`). This ensures that scripts have a predictable contract to read from and write to.

---

## 1. Core Architectural Pillars

All calculation workflows must adhere to the core boundaries of the `aeckit` ecosystem to maintain code safety, modularity, and reusable design:

```
┌────────────────────────────────┐
│   Single Source of Truth       │
│      (project.json)            │
└──────────────┬─────────────────┘
               │ Reads Parameters
               ▼
┌────────────────────────────────┐
│ Compositional Scripts (Python) │ ◄─── Uses ───►  aeclib (Stateless Logic)
└──────────────┬─────────────────┘
               │ Returns building_updates
               ▼
┌────────────────────────────────┐
│  State Merge & Visualization   │
│      (Geometric Draw Files)     │
└────────────────────────────────┘
```

1. **Single Source of Truth (SSoT):** All design inputs, material specifications, and geometry variables must reside within the active project's `project.json` file.
2. **Stateless Compliance Logic (`aeclib`):** Business logic and building code checks must remain stateless. They accept raw primitives, compute compliance status (`PASS`/`FAIL`), and return referenced warnings.
3. **CLI Orchestration (`aeckit-cli`):** Handles environment configurations, runs step-by-step scripts, validates inputs, and merges results back into the SSoT.
4. **Decoupled Visualizations:** Workflows must separate engineering mathematics from geometry presentation. Scripts output generic drawings (vertices, edges, labels, vectors) in a structured format (e.g., `.viz.json` or 2D detail specs) rather than embedding rendering logic.

---

## 2. Standard Workflow Implementation Lifecycle

When establishing a new automated engineering calculation workflow, follow these four phases:

### Phase 1: Define Project Data & Pipelines
Set up the files necessary to specify the parameters and order of operations.
*   **Define SSoT Fields (`project.json`):** Make sure all required input parameters (loads, sizes, materials, coordinates) are defined in the project configuration.
*   **Specify Workflow Pipeline (`workflow.json`):** Configure the sequence of compositional scripts. The output parameters of earlier scripts can serve as inputs to subsequent scripts in the workflow.

### Phase 2: Design Compositional Scripts
Create modular Python scripts in the `scripts/` directory to run via `aeckit-cli flow`.
*   **Input Context Parsing:** Extract the necessary variables from the `project_data` dictionary.
*   **Stateless Execution:** Feed those variables into the generic calculations provided by `aeclib`.
*   **Mutation Payloads:** Design the script to return any modifications to the project parameters under the `building_updates` dictionary key.

### Phase 3: Visual Output Generation
Enable engineering calculations to produce decoupled visual payloads for debugging or detailing.
*   **3D Geometry Preview:** Generate a `.viz.json` file containing raw points/vertices, edges, faces, and labels to visualize force vectors, loading paths, or boundaries.
*   **2D Parametric Detailing:** Output detail sheets specifying structural coordinates and dimensions to allow interactive slider adjustments in the 2D CAD editor.

### Phase 4: Verification & Dry-Runs
*   Run the workflow using `aeckit flow <name> --dry-run` to verify that execution executes cleanly, dependencies are met, and calculation logic passes without mutating the live project file.

---

## 3. Human-Agent Collaborative Workflow Walkthrough

To successfully construct automated calculation workflows, the engineer and the AI agent should collaborate using the following generic step-by-step engineering loop:

### Step 1: Context Retrieval & Domain Discovery
1. **State the Goal:** Identify the engineering design module or component to be automated.
2. **Gather Domain Context:** Work with the AI agent to compile the governing formulas, material limits, and code standards.
3. **Verification:** Inspect the context, engineering formulas, and standards returned by the AI agent against approved design criteria before proceeding.

### Step 2: Establish the Data Model
*   **Declare the Input Schema:** Define the design variables (e.g., sizes, structural parameters, design margins) and external loads (forces, moments) to be saved in the `project.json` SSoT.
*   **Declare the Output Schema:** Define the properties that the script will compute and return to update the SSoT.
*   **Rule - No Abbreviations:** Avoid abbreviations in keys unless necessary or universally understood in the domain (e.g., prefer descriptive names like `width_ft` and `thickness_in` over `B_ft` and `T_in`).

### Step 3: Implement Visual Wireframe Generators
*   Direct the AI agent to write a geometric utility function that maps the SSoT layout parameters to a generic wireframe coordinate structure (e.g., a `.viz.json` file containing drawing lines, faces, or arrows).
*   This provides a visual check of structural clearances and geometry lines in the 3D visualizer before implementing mathematical calculations.

### Step 4: Audit & Extend Core Libraries (The Flywheel Loop)
Identify gaps in the stateless code validation engine (`aeclib`) and implement the foundational formulas there first:
*   **Standard Analysis & Mathematical Formulas:** Ensure foundational scientific, physical, or geometric calculations (e.g., thermal resistance, hydraulic flows, occupancy limits, or force factoring) are represented in the library.
*   **Demand vs. Limit Verifications:** Verify that the library contains methods to compare calculated requirements against maximum or minimum thresholds (e.g., system capacity, flow limits, structural limits, or thermal ratings).
*   **Prescriptive Code Limits:** Ensure static compliance thresholds—such as minimum spatial clearances, maximum heights/widths, material fire/energy ratings, or specific prescriptive design limits defined by local building, zoning, and safety codes—are represented.

### Step 5: Write and Execute the Local Compositional Script
*   Import the generic math and validation checks from `aeclib` into a script within the local `scripts/` directory.
*   Execute the verification workflow via the CLI, using dry-run mode to confirm compliance reports.

---

## 4. Illustrative Example: Spread Footing Module Design (For Reference Only)

To illustrate how this generic human-agent collaborative loop operates in practice, consider the design of a concrete foundation element:

*   **Step 1 (Discovery):** The engineer asks the AI for foundation soil pressure equations and ACI codes. The AI returns the bearing formula and concrete cover codes, which the engineer verifies.
*   **Step 2 (Data Modeling):** The data model in `project.json` represents a building project and stores a set of footing instances nested under the `foundations` key (each specifying dimensions $B, L, T$, concrete cover, and loads).
*   **Step 3 (Visual Prototyping):** The AI generates a utility function that renders the footing geometry as a 3D wireframe box in `.viz.json` to verify spatial orientation.
*   **Step 4 (Core Auditing):** The engineer finds that ACI 318 minimum thickness formulas and foundation cover parameters are missing from `aeclib`. These are written and contributed directly to the `aeclib` codebase.
*   **Step 5 (Local Execution):** A compositional script, `check_footing.py`, is written to load the footing instances from the `foundations` key of `project.json`, evaluate each instance against the new `aeclib` methods, and output individual and combined compliance reports.
