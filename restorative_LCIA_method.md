# Restorative Perspective LCIA Method: Cumulative Exergy Replacement Cost

## Overview

This document describes the implementation of the **restorative perspective** LCIA method used to assign an **Exergy Replacement Cost (ERC)** to elementary flows in the biosphere database.

The restorative method is implemented as a **direct ERC characterization approach**. Rather than first calculating an ore-grade-decline characterization factor and then translating that result into ERC, the restorative implementation derives the ERC characterization factors directly from the **elemental composition of each elementary flow** and the **Valero rarity / ERC data**.

The method is implemented in the restorative section of the notebook and is applied to both dissipated and input elementary flows according to the selected LCI accounting approach. The resulting Brightway method is registered with the name:

> `Cumulative Exergy Replacement Cost (E)`

with a method description indicating that the objective is to **repurpose all dissipated/input elementary flows as resources**.

The implementation shown in the notebook produced a method containing **2386 characterization-factor entries**. fileciteturn2file0L292-L330

---

## 1. Conceptual Structure of the Restorative Method

The restorative method follows four main operations:

1. **Load the Valero ERC data** and construct an elemental ERC dictionary.
2. **Use the existing elementary-flow composition table** to determine which elements are contained in each biosphere flow.
3. **Calculate an ERC characterization factor for each elementary flow** by applying the Valero ERC values to its elemental composition.
4. **Register the resulting characterization factors as a Brightway LCIA method** and calculate the LCIA score from the characterized inventory.

A key implementation feature is that the restorative calculation **reuses the same `flow_compositions` table already generated for the other LCIA workflow**. Consequently, no new PubChem retrieval is performed at this stage: the composition information required by the restorative calculation is already available. The notebook explicitly states that restorative CFs keep the **stoichiometric compositions** and reuse the existing composition table. fileciteturn1file0L12-L24

---

# Step 1: Extract the Valero ERC Data

## 1.1 Load the Valero input data

The method starts from:

```text
inputs/valero-constants.csv
```

The CSV is read into a dataframe and its columns are assigned as:

| Column | Meaning |
|---|---|
| `name` | Mineral/material name |
| `k(x=xm)` | Valero parameter |
| `MW` | Molecular weight |
| `xm[kg/kg](mineral)` | Metal/mineral mass fraction information |
| `xm[kg/kg](metal)` | Metal/mineral mass fraction information |
| `ERC[MJ/kg]` | Exergy Replacement Cost |
| `E_tot[MJ/kg]` | Total energy |
| `xr[kg/kg](mineral)` | Refining mineral grade |

The restorative implementation specifically extracts the `ERC[MJ/kg]` column as the rarity/ERC value associated with each mapped element. fileciteturn2file0L102-L106

---

## 1.2 Convert Valero mineral names to elemental symbols

The raw Valero names are not always directly expressed as elemental symbols. Therefore, the implementation first cleans the material name and attempts to identify the corresponding element.

For example:

```text
Aluminium - Bauxite (Gibbsite) → Al
Antimony - Stibnite             → Sb
Copper - Chalcopyrite           → Cu
Iron - Hematite                 → Fe
Lithium - Spodumene             → Li
Zinc - Sphalerite               → Zn
```

The procedure:

1. Cleans the raw chemical/material name.
2. Removes mineral-specific qualifiers occurring after hyphens or in parentheses.
3. Removes terminal descriptors such as `ore` or `rock`.
4. Attempts to identify the resulting name as an element.
5. Uses explicit mineral/material mappings for cases that cannot be identified directly.

The notebook contains explicit mappings for minerals such as bauxite, barite, gypsum, chalcopyrite, stibnite, arsenopyrite, monazite, hematite, galena, spodumene, cassiterite, garnierite, ferrocolumbite, sphalerite, cinnabar, and others. fileciteturn2file0L108-L182

---

## 1.3 Build the elemental ERC dictionary

For every successfully mapped Valero entry, the implementation stores:

```text
element symbol → ERC value
```

The resulting dictionary is called:

```python
valero_rarity_data
```

Only entries with both:

- a successfully identified elemental symbol, and
- a non-null `ERC[MJ/kg]`

are retained. Unmapped entries are skipped. In the shown execution, **Fluor-Fluorite** was skipped and the resulting dataset contained **69 Valero rarity entries**. fileciteturn2file0L30-L98

---

## 1.4 Treatment of REE and PGM groups

The Valero dataset contains grouped values for:

- `REE`
- `PGMs (average)`

The implementation propagates these grouped values to individual elements when an individual value is not already present.

### Rare Earth Elements

The following REE symbols are considered:

```text
Sc, Y, La, Ce, Pr, Nd, Pm, Sm, Eu, Gd,
Tb, Dy, Ho, Er, Tm, Yb, Lu
```

If an individual REE is not already present, the generic `REE` value is assigned.

### Platinum Group Metals

The following PGM symbols are considered:

```text
Pt, Pd, Rh, Ru, Ir, Os
```

If an individual PGM value is not already present, the `PGMs (average)` value is assigned.

This creates a complete elemental ERC dictionary suitable for subsequent characterization of the biosphere flows. fileciteturn2file0L207-L220

---

# Step 2: Obtain the Composition of Elementary Flows

## 2.1 Reuse the existing composition table

The restorative method does **not** reconstruct the composition of each biosphere flow independently.

Instead, it takes:

```python
flow_compositions
```

which is the composition table already generated earlier in the workflow.

The restorative implementation explicitly states:

```text
derive ERC CFs from the SAME composition table
computed in the marginalist cell.
No new PubChem fetch — the composition table already covers every flow.
```

Thus, the restorative method uses the elemental composition information already determined for each elementary flow. fileciteturn2file0L254-L284

---

## 2.2 Stoichiometric composition is retained

The restorative calculation calls:

```python
derive_cfs_from_compositions(
    flow_compositions,
    cf_dict=valero_rarity_data,
    cf_calculator=cf_calculator,
    focus=focus,
    apply_ogd=apply_ogd,
    show_progress=True,
)
```

The notebook explicitly comments that:

```text
restorative CFs always keep stoichiometric compositions
```

Therefore, the restorative characterization is based on the elemental composition of the elementary flow rather than replacing that composition with a separate ore-grade-decline weighting during this stage. fileciteturn2file0L268-L284

---

# Step 3: Calculate the ERC Characterization Factors

## 3.1 Apply the Valero ERC values to the flow composition

For each elementary flow, the existing composition information identifies the elements contributing to that flow.

The `cf_calculator` is then used together with:

```python
cf_dict = valero_rarity_data
```

to calculate the ERC-based characterization factor.

Conceptually, for an elementary flow containing several elements, the flow-level characterization factor is obtained from the elemental composition and the corresponding elemental ERC values:

$$
CF_{EF}^{ERC}
=
\sum_{Me}
f_{EF,Me}
\cdot ERC_{Me}
$$

where:

- $CF_{EF}^{ERC}$ is the ERC characterization factor of elementary flow $EF$;
- $f_{EF,Me}$ is the mass fraction of element $Me$ in the elementary flow;
- $ERC_{Me}$ is the Valero ERC value associated with element $Me$.

The notebook itself does not expose the internal implementation of `cf_calculator` in the provided restorative section. Therefore, the equation above describes the calculation implied by the supplied `flow_compositions`, `valero_rarity_data`, and `derive_cfs_from_compositions` workflow; the exact internal implementation of `cf_calculator` is not shown in the supplied source.

---

## 3.2 Resulting flow-level characterization factors

The output of the calculation is:

```python
restorative_method_data
```

together with an auxiliary table:

```python
restorative_extra_info
```

The auxiliary information records, for each flow:

```text
flow_key
name
categories
unit
cleaned_name
formula
mw
cf
composition
grade_source
```

This provides traceability between the original biosphere flow, its chemical information, its elemental composition, and its calculated characterization factor. fileciteturn2file0L271-L284

---

# Step 4: Create the Brightway LCIA Method

## 4.1 Define the method identity

The method is registered using:

```python
restorative_method_name_tuple = (
    "Cumulative Exergy Replacement Cost (E)",
    f"{lci_accounting_approach.capitalize()}",
    f"ERC total: To Repurpose all dissipated/input elementary flows "
    f"as resources applied to {len(valero_rarity_data)} "
    f"with strategy {parameter_code}"
)
```

The method therefore retains the selected LCI accounting approach in its Brightway method identifier.

The shown execution produced:

```text
Cumulative Exergy Replacement Cost (E)
Dissipation-based
ERC total: To Repurpose all dissipated/input elementary flows as resources
applied to 69 with strategy b1iin
```

with **2386 CF entries**. fileciteturn1file1L148-L163

---

## 4.2 Register the method

The method metadata specifies:

```text
unit        = MJ-Eq
description = Exergy Replacement Cost for elementary flows
              based on Valero rarity values and PubChem molecular formulas
source      = inputs/valero-constants.csv and PubChem
version     = 1.0
application = Elementary biosphere flows
```

The characterization factors are then written directly to the Brightway method:

```python
restorative_method_object = bd.Method(restorative_method_name_tuple)
restorative_method_object.register(**restorative_method_metadata)
restorative_method_object.write(restorative_method_data)
```

Thus, the output of the restorative calculation is a standard Brightway LCIA method applicable to elementary biosphere flows. fileciteturn2file0L310-L334

---

# Step 5: Calculate the Restorative LCIA Score

Once the method has been registered, it is used like any other Brightway LCIA method.

For a functional unit:

```python
functional_unit = {
    electricity_activity.key: functional_unit_amount
}
```

the LCA is initialized with:

```python
cerc_E_lca_final = bc.LCA(
    functional_unit,
    method=restorative_method_name_tuple
)
```

The LCI and LCIA are then calculated:

```python
cerc_E_lca_final.lci()
cerc_E_lca_final.lcia()
```

The resulting score is:

```python
cerc_E_lca_final.score
```

The implementation also extracts the characterized elementary-flow contributions and saves them to:

```text
results/CERC_E_{lci_accounting_approach}_{parameter_code}.csv
```

The example execution reported a total LCIA score of:

```text
5.587252100021602 × 10^12
```

and successfully saved a CSV containing **1095 rows**. fileciteturn2file0L342-L404

---

# 6. Interpretation of the Restorative Perspective

The defining feature of this implementation is that the **ERC value is used as the characterization basis for the elementary flows themselves**.

The logic can therefore be represented as:

$$
\text{Elementary flow}
\rightarrow
\text{Elemental composition}
\rightarrow
\text{Elemental ERC values}
\rightarrow
CF_{EF}^{ERC}
\rightarrow
LCIA_{ERC}
$$

The method is therefore designed to express the effort associated with **repurposing dissipated or extracted elementary flows as resources**, using the ERC values contained in the Valero dataset.

In the implementation, the same composition information is retained for the restorative calculation, while the Valero ERC dictionary supplies the resource-rarity/exergy-replacement values. fileciteturn1file0L12-L24

---

# 7. Data and Computational Dependencies

The restorative implementation depends on the following components:

| Component | Role |
|---|---|
| `inputs/valero-constants.csv` | Provides elemental/mineral ERC values and related mineral data |
| `valero_rarity_data` | Dictionary mapping elements to Valero ERC values |
| `flow_compositions` | Existing elemental composition of biosphere elementary flows |
| `cf_calculator` | Performs the characterization-factor calculation |
| `derive_cfs_from_compositions()` | Generates the flow-level ERC characterization factors |
| Brightway `bd.Method` | Registers and stores the LCIA method |
| Brightway `bc.LCA` | Applies the method to an LCI |

The supplied restorative notebook section does not include the internal source code of `cf_calculator` or `derive_cfs_from_compositions()`. Consequently, their internal mathematical operations beyond the documented inputs and outputs are not reconstructed here.

---

# 8. Summary of the Method Construction

The restorative LCIA method can be summarized as follows:

1. **Read Valero constants.**
2. **Extract `ERC[MJ/kg]` values.**
3. **Map Valero mineral/material names to elemental symbols.**
4. **Complete grouped REE and PGM values where required.**
5. **Obtain the existing elemental composition of each biosphere elementary flow.**
6. **Reuse the stoichiometric composition table without performing a new PubChem retrieval.**
7. **Combine the elemental composition with the Valero ERC dictionary through `derive_cfs_from_compositions()` and `cf_calculator`.**
8. **Generate the flow-level ERC characterization factors.**
9. **Register the characterization factors as the Brightway method `Cumulative Exergy Replacement Cost (E)`.**
10. **Apply the method to the LCI to obtain the restorative LCIA score.**
11. **Extract and save elementary-flow contributions for interpretation.**

The essential difference from the marginalist workflow described in the comparison document is therefore that the restorative implementation shown here **starts from the ERC values and the elementary-flow compositions to build the final ERC characterization factors**, rather than documenting an explicit two-stage OGD → ERC translation within this restorative section. The marginalist document explicitly describes that two-stage OGD/ ERC framework. fileciteturn2file1L431-L437

---

# 9. Summary Flowchart

```mermaid
flowchart TD

    subgraph Data["Input data"]
        V[Valero constants CSV]
        B[Biosphere database]
        FC[Existing flow_compositions table]
        P[Existing PubChem-derived chemical information]
    end

    subgraph ERC["1. Build Valero ERC dictionary"]
        V --> VE[Read ERC[MJ/kg]]
        VE --> MAP[Map material/mineral names to element symbols]
        MAP --> GROUP[Complete REE and PGM grouped values]
        GROUP --> DICT[valero_rarity_data]
    end

    subgraph COMP["2. Determine elementary-flow composition"]
        B --> FLOWS[Elementary biosphere flows]
        FLOWS --> FC
        P --> FC
        FC --> COMP_TABLE[Elemental composition of each EF]
    end

    subgraph CF["3. Build restorative characterization factors"]
        DICT --> CALC[derive_cfs_from_compositions]
        COMP_TABLE --> CALC
        CALC --> CF_CALC[cf_calculator]
        CF_CALC --> CF_EF[ERC characterization factor per EF]
    end

    subgraph METHOD["4. Create Brightway LCIA method"]
        CF_EF --> DATA[restorative_method_data]
        DATA --> REGISTER[Register Brightway Method]
        REGISTER --> METHOD_OUT["Cumulative Exergy Replacement Cost (E)"]
    end

    subgraph LCIA["5. Calculate restorative LCIA"]
        LCI[Life Cycle Inventory] --> LCA[Brightway LCA]
        METHOD_OUT --> LCA
        LCA --> SCORE[Restorative LCIA Score]
        LCA --> CONTRIB[Elementary-flow contributions]
        CONTRIB --> CSV[Results CSV]
    end
```

---

## Final methodological chain

$$
\boxed{
\text{Valero ERC data}
+
\text{Elementary-flow composition}
\rightarrow
\text{ERC characterization factors}
\rightarrow
\text{Brightway LCIA method}
\rightarrow
\text{Restorative LCIA score}
}
$$
