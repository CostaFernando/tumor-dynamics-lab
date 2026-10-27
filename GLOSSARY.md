# Tumor Dynamics Lab

A research workbench for forecasting changes in tumor populations during treatment and recovery.

## Language

**Lineage**:
A group of cells sharing an experimentally identified ancestry. A lineage can contain multiple cell states.
_Avoid_: Cell state, cell type as synonyms for lineage

**Cell state**:
A description of a cell's measured biological characteristics, initially focused on gene expression. A state can occur across multiple lineages.
_Avoid_: Lineage as a synonym

**Observed proportion**:
A group's fraction of the cells observed in a specified sample. An increase in this fraction does not establish an increase in absolute abundance.
_Avoid_: Absolute abundance, growth as synonyms

**Absolute abundance**:
The number of cells in a defined population, distinct from the fraction captured in a sample.
_Avoid_: Observed proportion as a synonym

**Forecast**:
A prediction of later observations using only information available at a specified cutoff, within a supported experimental setting.
_Avoid_: Hypothetical treatment simulation as a synonym

**Forecasting cutoff**:
The latest observation time whose measurements may inform a forecast.

**Baseline predictor**:
A simple forecasting method used as a reference for assessing whether more complex methods improve prediction.

**Last observed composition**:
A baseline prediction that preserves the latest observed lineage proportions at future times.

**Trend extrapolation**:
A baseline prediction that extends earlier changes in relative composition while preserving valid proportions.

**Synthetic dataset**:
Artificially generated observations used for demonstrations and controlled tests. Performance on them does not establish biological validity.

**Culture**:
An experimental cell population maintained under a defined treatment history and sampled over time. Separate cultures are not automatically biologically independent.

**Treatment schedule**:
The timing of treatment exposure and withdrawal for a culture, including treatment identity and dose when known.

**Non-detection**:
No cells from a particular lineage were observed in a sample. This does not establish that the lineage is absent from the culture.
_Avoid_: Extinction as a synonym

**Unknown ancestry**:
The category of observed cells whose lineage could not be identified. It is not itself a biological lineage.

**Experiment snapshot**:
A fixed version of experimental observations and their associated metadata used as a research input.

**Forecast run**:
A recorded forecasting attempt defined by its experiment snapshot, culture, cutoff, method and settings, together with its outcome.

**Evaluation observation**:
A later measurement withheld from a predictor and used to assess its forecast.

**Previously unseen lineage**:
A lineage identified in an evaluation observation but absent from all input observations available to the predictor. Its ancestry is identified, unlike cells categorized as unknown ancestry.

**Total variation distance**:
Half the sum of absolute differences between predicted and observed proportions over the same exhaustive categories. It ranges from zero for identical compositions to one for disjoint compositions.

**Target time**:
A later sampling time for which a forecast is made and compared with a held-out observation.
