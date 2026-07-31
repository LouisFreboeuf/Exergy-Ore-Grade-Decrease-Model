# Exergy - Ore Grade Decrease Modeling

## Background
This work started by investigating the possibility of measuring the dissipation in LCA using exergy, specifically with the idea of thermodynamic rarity (TheRy), a concept developed by Antonio Valero and Alicia Valero. However, the TheRy model assumes all the dissipated resources go immediately to a concentration of the dead state, which is assumed to take place in a very long time horizon. This is makes it difficult to quantify the short term impact of the life cycle of a product on the aspect of resource use accurately. 


Therefore, the new attempt is to describe the impact of gradual resource dissipation of a product system in terms of exergy. To demonstrate the gradual resource dissipation process, the idea of ore-grade decrease is incorporated. The mathematical equation used to calculated the ERC in the previous work can be applied here to develop characterization factor (CF) for a smaller variation of the ore grade. 

## Setup
The entire LCIA process in this repository runs on [BrightWay2.5](https://learn.brightway.dev/en/latest/content/chapters/BW25/BW25_introduction.html). Check their documentation on how to install the package. <br>
Other libraries to be downloaded: `pubchempy`,`mendeleev`

## Outline
Current work can be separated into 3 parts:
1. Modelling ore-grade decrease: this describes the relationship between the ore-grade and the amount of ore that is extracted (also called tonnage)
2. Corresponding exergy burden added to the future generation due to the change in ore concentration
3. Taking into account the concept of dissipation by considering the ratio between the dissipated resources versus the amount of extracted resources.

![Impact Pathway](/readme_img/Impact-Pathway.png?raw=true&v=2) <br>

The image above illustrates clearly the impact pathway of the target indicator. In order to capture accurately the consequence of mineral dissipation on the reduction of ore-grade, the two driven forces of the mining activity are identified, namely retention and expansion. 
* Retention represents the amount needed to replenish the dissipated resources from the technosphere. 
* Expansion refers to the extra amount that needs to be mined to for the development of the society. <br>

Take note that this indicator will only measure the future burden in terms of exergy for the retention part of the mining activity. Plus, an assumption made here is that the dissipated material will be replaced with the same material during the next life cycle, which means no alternative is considered. 

## 3-step LCIA Process
In brief, the 3-step LCIA calculation includes
1. Find the ore-grade decrease ($\Delta g$) that corresponds to the extraction flow in LCI.
    * unit: mass of metal / mass of ore
2. Find the change in the concentration exergy ($\Delta b_c$) due to the ore-grade decrease ($\Delta g$). This will be the impact factor of the specific element.
    * unit: kJ/kg or MJ/kg
3. There can be 2 final impact scores: multiply the **extraction flows** by the CF from Step#2, we get the overall ore-grade decline caused by the product system; or multiply the **dissipation flows** by the CF from Step#2, we find the amount of ore-grade decline that the dissipative flows are responsible for. 
    * unit: kJ or MJ

### Step 1: Ore-grade decrease modelling
Originally, ore-grade decrease was modelled with the Lasky’s relationship that connects the ore-grade (g) and the tonnage of rocks mined (T). <br>
$$g=a-b\ln(T)$$, <br>
where a and b are constants that differ from mineral to mineral. <br>
The choice of model was updated to the log-logistic distribution in the recent study by Vieira et al. 
#### Original log-logistic distribution, F(x)
$$F(x)=\frac{1}{1+(\frac{x}{a})^{-b}}$$

![Log-Logistic Distribution Curve](readme_img/Log-LogisticDist.drawio.png)

#### Adapted for distribution of ore-grade, H(g)
$$H(g)=1-F(g)=1-\frac{1}{1+(\frac{x}{a})^{-b}}=\frac{1}{1+(\frac{x}{a})^b}$$ <br>
It is expressed in this form in the paper of Vieira: <br>
$$H(g)=\frac{1}{1+e^{\frac{\ln(g)-\alpha}{\beta}}}$$ <br>

##### Derivation 
$$\frac{x}{a}^b$
=e^{\ln(\frac{x}{a})^b}
=e^{b\ln(\frac{x}{a})}
=e^{b(\ln{x}-\ln{a})}$$ <br>
$$ \text{let} \space \alpha=\ln{a}$$
$$ \text{let} \space \beta=\frac{1}{b}$$ <br>
We get:  $$e^{\frac{\ln(g)-\alpha}{\beta}}$$ <br>

To find the cumulative metal tonnage (CMT), we just have to multiply the ore-grade (g), with the ultimate amount of reserve (A): <br>
$$CMT=\frac{A}{1+e^{\frac{\ln(g)-\alpha}{\beta}}}$$, <br>
Here, $\alpha$ represents the natural logarithm of the median ore grade, and $\beta$ is the scale parameter, which tells how spread out is the concentration data from the median, $e^{\alpha}$. <br>
This statistical model better captures the global ore-grade vs. tonnage data. 
![Ore Grade Decrease Representation](/readme_img/Ore-GradeDecrease.drawio.png)

##### Region 1
Region 1 represents the early stage of mining, where most of the ores have high concentration. This is where the independent variable, g, is high, and the dependent variable, CMT, is relatively low. 
##### Region 2
Region 2 has the quickest ore-grade decline, with an almost steep linear relationship between the ore-grade and the CMT. 
##### Region 3
Region 3 is the scenario where the ore grade has become really low and CMT is really high. This models very well the reality of the high effort that needs to be invested in order to get the same amount of 

##### Characterization Factor (CF) Development of Step 1
$$CF_1 = \frac{\partial g}{\partial CMT} = -\frac{A\beta e^{\alpha}}{CMT^2}(\frac{A}{CMT}-1)^{\beta-1}$$ <br>

<font color="red">Possible challenge with this $CF_1$, because the curve is non-linear, therefore the CF is expected to change as the point of reference changes.</font>

### Step 2: Connect ore-grade decrease with exergy
Given calculation of ERC in the framework of TheRy, we can calculate the small extra exergy by considering the starting mine concentration point x_m assumed in the paper of Magdalena and the change in ore grade computed in Part 1. 

![ERCvsSurplusExergy](/readme_img/ERCvsSurplusEx.drawio.png)

$$b_c(x)=-RTº[\ln(x)+\frac{1-x}{x}\ln(1-x)]$$ <br>
$$\text{Change in Concentration Exergy} = \Delta b_c = **CF_2** = b_c(x_{m_{future}})-b_c(x_m)$$ <br>
$$x_{m_{future}} = x_m - CF_1 \times \text{Mass}_{\text{extracted}}$$

### Step 3: Finding the ore-grade decrease due to extraction and dissipation
As of now, the dissipation is thought to be modelled using the yearly dissipation data per year of the extraction data.

$$\text{score}_{\text{total}} = \text{CF}_2 \times \text{Mass}_{\text{extracted}}$$

$$\text{score}_{\text{dissipative}} = \text{CF}_2 \times \text{Mass}_{\text{dissipated}}$$