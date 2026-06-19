# Project Setup, CLI Commands, and Missing Components

This document outlines the `aeckit-cli` commands needed to configure the workspace environment and lists the remaining missing components required to fully execute the spread footing design workflow.

---

## 1. Useful `aeckit-cli` Commands

Here is the reference list of CLI commands for establishing and running the workspace environment.

### 1.1 Configuration & Context Management
*   **Show current configuration context:**
    ```bash
    aeckit config show
    ```
*   **Set active company and project defaults:**
    ```bash
    aeckit config set --company demo --project spread-footing
    ```

### 1.2 Resource Management
*   **List all companies:**
    ```bash
    aeckit company list
    ```
*   **Create a new company:**
    ```bash
    aeckit company create --name <company-name>
    ```
*   **List all projects in the active company:**
    ```bash
    aeckit project list
    ```
*   **Show the Single Source of Truth (`project.json`) for the active project:**
    ```bash
    aeckit project show
    ```
*   **Create a new project (under default company):**
    ```bash
    aeckit project create --name spread-footing
    ```

### 1.3 Workflow Management & Execution
*   **List available workflows defined in the active project's `workflow.json`:**
    ```bash
    aeckit workflow list
    ```
*   **Show steps of a specific workflow:**
    ```bash
    aeckit workflow show --workflow design_footing
    ```
*   **Run a workflow (dry-run, safe mode without writing changes):**
    ```bash
    aeckit flow design_footing --dry-run
    ```
*   **Run a workflow (with automatic backup snapshot before execution):**
    ```bash
    aeckit flow design_footing --snapshot
    ```

---

## 2. Resolving the Scaffolding Collision

Because the `companies/demo/spread-footing` directory has already been created to store this documentation, the command `aeckit project create --name spread-footing` will fail with an "already exists" error.

To resolve this and scaffold the files:

### Option A: Manual Setup (Recommended)
Create the missing directory structures and empty configuration files in place:
1. Create directories: `reports/` and `history/`
2. Create `project.json` (root schema)
3. Create `workflow.json` (empty object `{}`)

### Option B: Temporary Renaming
1. Move the `spread-footing` directory out of the way:
   ```bash
   mv companies/demo/spread-footing companies/demo/spread-footing-temp
   ```
2. Scaffold the project using `aeckit-cli`:
   ```bash
   aeckit project create --name spread-footing --company demo
   ```
3. Merge the notes back:
   ```bash
   mv companies/demo/spread-footing-temp/notes companies/demo/spread-footing/
   rm -rf companies/demo/spread-footing-temp
   ```

---

## 3. Checklist of Missing Components

To complete the end-to-end design loop, we must build and configure the following components:

### 3.1 Workspace Configurations
*   [ ] Create [project.json](file:///Users/nguyen/aec-projects/aeckit-org/aeckit-demo/companies/demo/spread-footing/project.json) containing design inputs (loads, material limits, geometry).
*   [ ] Create [workflow.json](file:///Users/nguyen/aec-projects/aeckit-org/aeckit-demo/companies/demo/spread-footing/workflow.json) defining the `design_footing` workflow pipeline steps.
*   [ ] Switch active CLI default project context to `spread-footing`.

### 3.2 Stateless Core Compliance Module (`aeclib`)
We need to implement the structural calculations in the shared `aeclib` engine under `/Users/nguyen/aec-projects/aeclib-org/aeclib/src/aeclib/us/structural/footing/`:
*   [ ] **Soil Bearing Capacity Check:** Compare calculated ASD contact pressure (including eccentrically loaded partial liftoff) against $q_a$.
*   [ ] **One-Way Shear Strength Check:** Verify ACI 318 beam shear capacity ($\phi V_c \ge V_u$) at $d$ from the column face.
*   [ ] **Two-Way Shear Strength Check:** Verify ACI 318 punching shear capacity ($\phi V_c \ge V_u$) at $d/2$ from the column face.
*   [ ] **Flexural Reinforcement Design:** Compute required steel area $A_s$, verify ACI 318 minimum limits ($0.0018 b \cdot h$), and select bar layout.
*   [ ] **Development Length Check:** Ensure bar tension development length ($l_d$) fits in the overhang.
*   [ ] **Unit Tests:** Implement test suite in `/Users/nguyen/aec-projects/aeclib-org/aeclib/tests/us/structural/`.

### 3.3 Compositional Workflow Scripts (in `/Users/nguyen/aec-projects/aeckit-org/aeckit-demo/scripts/`)
*   [ ] `footing_bearing.py`
*   [ ] `footing_shear.py`
*   [ ] `footing_reinforcement.py`
*   [ ] `footing_visualizer.py` (Outputs geometry to `footing.viz.json`)
