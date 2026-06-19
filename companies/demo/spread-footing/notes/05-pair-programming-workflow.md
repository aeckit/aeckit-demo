# Iterative, Multi-Repository Pair Programming Workflow

This document explains and diagrams the collaborative development loop used during this project. It outlines how a developer and an AI assistant interact across multiple scopes—core code compliance, local script executions, and extension-level user interfaces.

---

## 1. Explanation of the Workflow

Our workflow represents a **Multi-Tiered Iterative Development Cycle** across three separate code repositories/projects:
1.  **`aeclib` (Shared Core Engine):** Stateless, input-driven building code mathematics and parameters (e.g. ACI 318 limits, ASCE 7 load combinations).
2.  **`aeckit-demo` (Local Workspace):** Physical design scripts (`footing_shear.py`, etc.), pipeline workflows, and the JSON Single Source of Truth (SSoT).
3.  **`visualizer-vsix` (IDE Tooling):** Custom 3D rendering engine, UI controls (Node Size slider), and VS Code integration commands.

### The Collaboration Pattern
*   **User Directs Intent & Constraints:** You establish the architectural boundaries (the *Flywheel Effect*), provide design assumptions (nominal 6x6 columns, accidental eccentricity), reorganize workspaces, and audit UI features (e.g. JSON split view panel, concrete mesh transparency).
*   **Assistant Coordinates Cross-Repository Execution:** The AI acts as the execution agent, writing logic in the core library, designing workflow scripts in the local workspace, compiling the extension front-end, and documenting outcomes in tracking issues.
*   **Continuous SSoT Integration:** We verify the designs using dry-run tests and live runs, which automatically update `project.json` and generate THREE.js `.viz.json` files for real-time visualization.

---

## 2. Diagram of the Conversation & Development Loop

The interaction model below represents our conversation loop in a generic sense:

```mermaid
graph TD
    %% Roles
    User([User: Directs & Audits])
    Agent[Agent: Executes & Integrates]
    
    %% Repos/Scopes
    AECLIB[(aeclib: Core Engine)]
    AECKIT_DEMO[(aeckit-demo: SSoT & Scripts)]
    VSIX[(visualizer-vsix: Webview UI & Extension)]
    
    %% Interactions
    User -->|"1. Dictates design criteria & files layout"| Agent
    Agent -->|"2. Implements stateless building code"| AECLIB
    Agent -->|"3. Writes physical sizing scripts"| AECKIT_DEMO
    Agent -->|"4. Adds transparent 3D faces & UI slider"| VSIX
    
    %% Execution Cycle
    AECKIT_DEMO -->|"5. Run flow"| AECLIB
    AECLIB -->|"6. Compute code limits"| AECKIT_DEMO
    AECKIT_DEMO -->|"7. Save SSoT & generate viz.json"| VSIX
    
    %% Feedback Loop
    VSIX -->|"8. Audited by"| User
    User -->|"9. Request UI refinements (slider, json side-panel)"| Agent
```

### Detailed Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Agent
    participant aeclib as Core Library (aeclib)
    participant Workspace as Workspace (aeckit-demo)
    participant Visualizer as IDE Tooling (visualizer-vsix)
    
    User->>Agent: Acknowledge reorganization / request sizing script
    Agent->>aeclib: Update ACI 318 equations (shear, rebar area, ld)
    Agent->>Workspace: Create footing_shear.py & footing_reinforcement.py
    Agent->>Workspace: Run flow (combines aeclib & local scripts)
    Workspace->>Workspace: Update project.json (SSoT) & generate viz.json
    User->>Agent: Request transparent meshes and node size control
    Agent->>Visualizer: Update webview (faces, opacity, nodeSizeMultiplier)
    Agent->>Visualizer: Compile & package VSIX
    User->>Visualizer: Install VSIX & audit 3D view
    User->>Agent: Fix JSON side-panel routing & remove JSON nodeSize properties
    Agent->>Visualizer: Update extension.ts (openWith) & simplify WireframeRenderer
    Agent->>Visualizer: Repackage VSIX
```

---

## 3. Generalized Workflow Steps

In a generic sense, this multi-repo pair programming workflow consists of the following sequential phases:

1.  **Scope Alignment & Parameterization:** The developer establishes the goal, designs the database schema (SSoT layout in `project.json`), and aligns on building code requirements vs. physical calculations.
2.  **Core Library Implementation (`aeclib`):** Stateless compliance equations, prescriptive constants, and load combination logic are implemented in the shared core engine to ensure reusability.
3.  **Local Sizing & SSoT Scripting (`aeckit-demo`):** Sizing calculations (such as concrete weight, trapezoidal pressure, and sizing search iterations) are codified in local workspace scripts. These scripts read SSoT inputs, apply the core `aeclib` capacity equations, and return optimized results.
4.  **SSoT Database Update:** Running the design workflow executes the local scripts in sequence, updating the Centralized JSON SSoT with derived dimensions and reinforcement schedules.
5.  **Geometry Rendering Output:** A local visualizer script reads the finalized SSoT data and outputs wireframe coordinates and face meshes to a `.viz.json` file.
6.  **Tooling & Webview Upgrades (`visualizer-vsix`):** The custom 3D editor extension is updated to support rendering of transparent faces (using custom Three.js `BufferGeometry`), draw rebar grids, integrate correct VS Code side-panel text editing views, and introduce interactive UI controls (like the Node Size slider).
7.  **Schema Refinement:** Presentation/rendering properties (like individual `nodeSize` settings) are migrated from the engineering database to the UI toolbar controls to maintain SSoT data purity.

