# Things to be considered in the future development

## Different Scenarios (3 more)
1. I need to provide a sample calculation in terms of DISSIPATION by adjusting the CF-assignment code. 
2. I can try to model the initial ore grade $x_i$ differently by using the assumption in ERC computation. Currently, the first calculation of 500,000 kg of copper cathode is modelled with $x_i$ from the ore-grade vs. tonnage relationship with the constants provided by ReCiPe2016. (Details see the methodology file)
* This means there could be 4 different results ($x_i$ from model/$x_i$ from ERC assumption) * (final mass from input/output flows).

## Integrated workflow
It will be better if I can learn to do lcia with bw just in python without going to the activity browser. I will be able to retreive the elementary flow contribution directly in the same program without going back-and-forth, increasing efficiency and the ease for the others to use my program. 

## Possible Error
The first calculation of the final impact still included the one from "Clay". This is due to the data from PubChem that assigned a chemical formula of $Al_2O_5Si$ to it, but this probably is not considered as an ore deposit; thus, it should not appear in the final impact score. 
