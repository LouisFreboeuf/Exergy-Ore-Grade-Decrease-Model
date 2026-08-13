# Rigorous Framework for LCIA Integrating Ore Grade Decline and Exergy Replacement Cost

## Overview

This document presents a two-step methodological framework to translate ore grade decline (OGD) into exergy replacement costs (ERC) for resource depletion assessment. The approach maintains mass balance consistency while enabling sensitivity analysis on the source of initial ore grade ($x_i$).

---

## Step 1: Ore Grade Decline (OGD) Characterization

### 1.1 Pure Metal Ore Grade Decline Factor

The ore grade decline factor for each pure metal ($Me$) is calculated from Vieira et al. (2012):

$$OGD_{Me} = CF1_{Me} = \frac{A \beta e^{\alpha}}{CMT^2} \left( \frac{A}{CMT} - 1 \right)^{\beta - 1}$$

**Inputs:**
- `viera_csv_input_data`: CSV containing $A$, $CMT$, $\alpha$, $\beta$ for each metal

**Output:**
- $OGD_{Me}$: Ore grade decline per kg of pure metal extracted (\% per kg)

---

### 1.2 Determination of Elementary Flow Composition ($f_{EF,Me}$)

The metal composition of elementary flows is determined through a hierarchical approach, prioritized as follows:

#### For Natural Resource Elementary Flows

**Priority 1: Composition Explicitly Stated in Flow Name**
- When the flow name contains explicit metal grades (e.g., "Ni 2.3%, Pt 0.025% in ore"), these values are directly extracted and used as $f_{EF,Me}$.
- This applies to multi-element ore flows where the composition is fully specified.

**Priority 2: Compound Identification via PubChem API**
- When the flow represents a known chemical compound (e.g., "Pyrite", "Bauxite"), the flow name is cleaned to extract the compound name.
- The PubChem API is queried to obtain the molecular formula and molecular weight.
- The metal mass fraction is calculated from the molecular formula:
  $$f_{EF,Me} = \frac{n_i \cdot aw_i}{mw_{compound}}$$
  Where $n_i$ is the number of atoms of metal $i$ in the compound, $aw_i$ is its atomic weight, and $mw_{compound}$ is the molecular weight.

**Priority 3: Pure Metal Assumption**
- If the flow name corresponds to a pure metal (e.g., "Copper, in ground"), then $f_{EF,Me} = 1.0$.
- This is the default assumption when no composition information is available.

**Special Case: Ore Grade Percentage**
- For flows containing a compound with an explicit ore grade (e.g., "TiO2, 95% in rutile"), the ore grade percentage is extracted and applied as an additional factor.
- The final composition becomes: $f_{EF,Me} = \text{ore grade} \times \frac{n_i \cdot aw_i}{mw_{compound}}$

#### For Dissipation Elementary Flows

- Dissipation flows represent emissions of substances to the environment (e.g., "Zinc, ion, to water").
- The PubChem API is used to identify the molecular formula from the cleaned flow name.
- The metal mass fraction is calculated from the molecular formula using the same approach as for compounds in natural resources.
- No ore grade percentage is applied (as dissipation represents pure substance emissions).

**Summary of Composition Determination:**

| Flow Type | Method | Example |
|-----------|--------|---------|
| Multi-element ore | Parse from name | "Ni 2.3%, Pt 0.025%" → $f_{EF,Ni}=0.023$, $f_{EF,Pt}=0.00025$ |
| Compound with ore grade | PubChem API + ore grade | "TiO2, 95% in rutile" → $f_{EF,Ti}=0.95 \times (47.87/79.87)$ |
| Pure compound | PubChem API | "Pyrite" → $f_{EF,Fe}=55.85/119.98$ |
| Pure metal | Assumption | "Copper, in ground" → $f_{EF,Cu}=1.0$ |
| Dissipation | PubChem API | "Zinc, ion, to water" → $f_{EF,Zn}=1.0$ |

---

### 1.3 Elementary Flow Characterization Factor ($CF1_{EF}$)

For each elementary flow (EF) in the biosphere database, the total characterization factor is the weighted sum of the metal-specific contributions:

$$CF1_{EF,Me} = f_{EF,Me} \cdot OGD_{Me}$$

$$CF1_{EF} = \sum_{Me} CF1_{EF,Me} = \sum_{Me} \left( f_{EF,Me} \cdot OGD_{Me} \right)$$

**Where:**
- $f_{EF,Me}$ = Mass fraction of metal $Me$ in elementary flow $EF$ (determined in Section 1.2)
- $CF1_{EF,Me}$ = Metal-specific contribution to the EF's CF

**The composition determination ensures:**
$$\sum_{Me} f_{EF,Me} = 1.0 \text{ (for natural resource flows)}$$
$$\sum_{Me} f_{EF,Me} = 1.0 \text{ (for dissipation flows, representing pure substance)}$$

---

### 1.4 Life Cycle Impact Assessment (LCIA) Score

For a specific functional unit (FU) and life cycle inventory (LCI):

$$LCIA = \sum_{EF} \left( LCI_{amount,EF} \cdot CF1_{EF} \right) = \sum_{EF} \left( LCI_{amount,EF} \cdot \sum_{Me} \left( f_{EF,Me} \cdot OGD_{Me} \right) \right)$$

**Where:**
- $LCI_{amount,EF}$ = Amount of elementary flow $EF$ extracted per functional unit (kg)

**Inputs:**
- `functional_unit`: Defined by the user (e.g., 268 TWh electricity)
- `method_key`: The LCIA method using $CF1_{EF}$

**Output:**
- $LCIA$ = Total ore grade decline for the product system (percentage points)

---

### 1.5 Elementary Flow Contribution to LCIA

The contribution of each elementary flow to the total LCIA score is:

$$\Delta g(LCIA)_{EF} = LCI_{amount,EF} \cdot CF1_{EF}$$

**This represents:** The ore grade decline caused by extracting the amount of EF required for the functional unit.

---

### 1.6 Metal-Specific Contribution to EF's LCIA

To allocate the EF's total LCIA contribution to individual metals:

$$\Delta g(LCIA)_{EF,Me} = \Delta g(LCIA)_{EF} \cdot \frac{CF1_{EF,Me}}{CF1_{EF}}$$

**This ensures:**
$$\sum_{Me} \Delta g(LCIA)_{EF,Me} = \Delta g(LCIA)_{EF}$$

**Interpretation:** $\Delta g(LCIA)_{EF,Me}$ represents the portion of the total ore grade decline for EF that is attributable to metal $Me$.

---

## Step 2: Exergy Replacement Cost (ERC) Translation

### 2.1 Convert to Mineral Grade Decline

The metal-specific ore grade decline must be converted to mineral-specific decline using the metal-to-mineral mass fraction:

$$\Delta g(LCIA)_{EF,Mineral} = \Delta g(LCIA)_{EF,Me} \cdot f_{Mineral,Me}$$

**Where:**
- $f_{Mineral,Me}$ = Mass fraction of metal $Me$ within its host mineral
- Obtained from `valero_csv_input_data`: column `xm[kg/kg](metal)` / column `nxm[kg/kg](mineral)`

**Input:**
- `valero_csv_input_data`: Contains mineral composition data

**Note:** This step is required because ERC is defined at the mineral level, not the metal level.

---

### 2.2 Determine Initial and Final Ore Grades

**Initial ore grade:** $x_{i, EF, Mineral}$

**Data Sources (Sensitivity Analysis):**

| Option | Source | Description |
|--------|--------|-------------|
| **1** | `valero_csv_input_data` | Reference ore grades from Valero |
| **2** | `viera_csv_input_data` | Ore grades from Vieira et al. (2012) |
| **3** | `elementary_flow` | Parsed directly from EF name (e.g., "11% in crude ore") |

**Parameter:**
- `input_for_xi`: Controls which source is used

**Final ore grade:**

$$x_{f, EF, Mineral} = x_{i, EF, Mineral} - \Delta g(LCIA)_{EF,Mineral}$$

**Validation:** Ensure $x_{f, EF, Mineral} > 0$ (otherwise, the grade would become negative).

---

### 2.3 Calculate Exergy Replacement Cost (ERC)

The ERC for a mineral is calculated as:

$$ERC_{EF,Mineral} = \frac{bc(x_f) - bc(x_i)}{bc(x_i) - bc(x_r)} \cdot E(x_f)$$

**Where:**
- $bc(x) = RT \cdot \left[ \ln(x) + \frac{1-x}{x} \cdot \ln(1-x) \right]$
- $R$ = Universal gas constant
- $T$ = Temperature (typically 298.15 K)
- $x_i$ = Initial ore grade
- $x_f$ = Final ore grade
- $x_r$ = Reference ore grade (from `valero_csv_input_data`)
- $E(x_f) = \left( \frac{E_{Valero}}{x_r \cdot 100} \right)^{-0.5}$ (MJ/kg)

**Inputs:**
- `valero_csv_input_data`: Provides $x_r$ and $E_{Valero}$ for each mineral
- Temperature $T$: Standard condition (298.15 K)

**Output:**
- $ERC_{EF,Mineral}$: Exergy replacement cost (MJ/kg mineral)

---

### 2.4 Metal-Specific ERC per Elementary Flow

The mineral ERC is assigned back to the metal:

$$CF2_{EF,Me} = ERC_{EF,Mineral}$$

---

### 2.5 Elementary Flow ERC Characterization Factor

The total characterization factor for the EF (in ERC terms) is:

$$CF2_{EF} = \sum_{Me} \left( f_{EF,Me} \cdot CF2_{EF,Me} \right)$$

**Where:**
- $f_{EF,Me}$ = Same mass fraction used in Step 1.2

---

### 2.6 Final LCIA Score (ERC-based)

$$LCIA_{ERC} = \sum_{EF} \left( LCI_{amount,EF} \cdot CF2_{EF} \right)$$

**This represents:** The total exergy replacement cost for the product system (MJ per functional unit).

---

## Summary of Data Flow

```mermaid
flowchart TD
    subgraph Step1["Step 1: OGD Characterization"]
        Viera[Viera CSV] --> OGD[OGD_Me = CF1_Me]
        EF[Elementary Flow Names] --> Comp[Determine f_EF,Me]
        Comp --> |Priority 1: Parse name| f_parse[Parse from name]
        Comp --> |Priority 2: PubChem API| f_pubchem[Calculate from formula]
        Comp --> |Priority 3: Assumption| f_assume[Assume pure metal]
        PubChem[PubChem API] --> f_pubchem
        f_parse --> f_EF_Me[f_EF,Me]
        f_pubchem --> f_EF_Me
        f_assume --> f_EF_Me
        OGD --> CF1_EF_Me[CF1_EF,Me = f_EF,Me × OGD_Me]
        f_EF_Me --> CF1_EF_Me
        CF1_EF_Me --> CF1_EF[CF1_EF = Σ CF1_EF,Me]
        LCI[LCI amounts] --> LCIA[LCIA = Σ LCI_EF × CF1_EF]
        LCIA --> Δg_EF[Δg_EF = LCI_EF × CF1_EF]
        Δg_EF --> Δg_EF_Me[Δg_EF,Me = Δg_EF × CF1_EF,Me/CF1_EF]
    end

    subgraph Step2["Step 2: ERC Translation"]
        Valero[Valero CSV] --> f_Mineral_Me[f_Mineral,Me]
        Δg_EF_Me --> Δg_Mineral[Δg_Mineral = Δg_EF,Me × f_Mineral,Me]
        
        input_for_xi{input_for_xi} --> |Option 1| xi_Valero[xi from Valero CSV]
        input_for_xi --> |Option 2| xi_Viera[xi from Viera CSV]
        input_for_xi --> |Option 3| xi_EF[xi from EF name]
        
        xi_Valero --> xf[xf = xi - Δg_Mineral]
        xi_Viera --> xf
        xi_EF --> xf
        
        Valero --> xr[xr from Valero CSV]
        Valero --> E_Valero[E_Valero from Valero CSV]
        
        xi --> ERC[ERC = bc(xf)-bc(xi)/bc(xi)-bc(xr) × E(xf)]
        xf --> ERC
        xr --> ERC
        E_Valero --> ERC
        
        ERC --> CF2_EF_Me[CF2_EF,Me = ERC]
        f_EF_Me --> CF2_EF[CF2_EF = Σ f_EF,Me × CF2_EF,Me]
        CF2_EF --> LCIA_ERC[LCIA_ERC = Σ LCI_EF × CF2_EF]
    end
    