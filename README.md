# Pitfall-Aware Evaluation Framework for Reentrancy Detection

## Overview

This repository contains a research framework designed to support the systematic evaluation of machine-learning-based reentrancy detection tools for Ethereum smart contracts. It investigates how methodological pitfalls in experimental design, dataset construction, labeling, and performance evaluation can influence conclusions about the effectiveness and reliability of these tools.

The framework provides a structured environment for examining the sensitivity of detection results to different evaluation conditions and comparing machine-learning-based detectors with relevant non-machine-learning baselines.

## Research Motivation

The reliability of security evaluation depends not only on a tool's detection capabilities but also on the quality of the evaluation methodology. Dataset selection, label quality, class imbalance, evaluation metrics, and other methodological choices can introduce biases that affect reported performance.

This framework addresses these challenges through a pitfall-aware approach to evaluating reentrancy detection tools. Its objective is to make evaluation assumptions explicit and investigate how changes in experimental conditions may affect the interpretation of detection results.

## Objectives

The main objectives of this framework are to:

* Provide a structured methodology for evaluating reentrancy detection tools.
* Investigate the effects of selected methodological pitfalls on evaluation outcomes.
* Examine the influence of dataset characteristics and labeling assumptions on reported performance.
* Support appropriate evaluation metrics, including those designed for imbalanced classification.
* Facilitate systematic comparisons between machine-learning-based detectors and relevant alternative detection approaches.
* Improve the transparency and reproducibility of experimental evaluations.

## Configuration

The framework uses tool-specific configurations to select the dataset and input format for each execution. The tool to be processed is specified through the required `--tool` command-line argument.

The currently documented tool identifiers are:

| Identifier | Tool      |
| ---------- | --------- |
| `TL1`      | AWDNN     |
| `TL31`     | ReChecker |

Each configuration specifies the dataset location, dataset filename, input type, and bytecode dataset format.

Before running an experiment, update the dataset and tool paths to match your local environment. The current implementation uses Linux-style paths such as `/mnt/f/LISTTOOL/...`, which may need to be adjusted depending on your execution environment.

## Running the Framework

### Prerequisites

Before execution, ensure that the required Python environment, database, metadata services, preprocessing components, test agent, datasets, and detection tools are configured and accessible.

### Execution

Run the entry-point script with the identifier of the tool you want to evaluate:

```bash
python Mainframework.py --tool TL31
```

The supported tool identifiers are defined in `Mainframework`. Users can add or modify identifiers and their corresponding tool configurations, provided that the entry-point script and related components are updated consistently.

Replace `TL31` with the identifier corresponding to your desired tool configuration. Each invocation processes one selected tool configuration.

## Adding or Modifying a Tool Configuration

Tool identifiers and their corresponding configurations are defined in `mainframework`. Users can add new identifiers or modify existing configurations to support different detection tools.

To add or modify a tool configuration:

1. **Update `Mainframework`:** Define the tool identifier and its corresponding dataset configuration.
2. **Configure the dataset:** Specify the dataset path, filename, input type, and bytecode dataset format as required.
3. **Update the entry-point script:** Ensure that the identifier is included in the `choices` list in `parse_args()`. This list must be updated whenever a new identifier is introduced, unless the argument parser is modified to load identifiers directly from `Mainframework`.
4. **Verify compatibility:** Ensure that the preprocessing and testing components support the configuration and that all required dataset paths, tool paths, and dependencies are available.
5. **Run the configuration:** Execute the entry-point script using the corresponding identifier:

   ```bash
   python Mainframework.py --tool YOUR_TOOL_ID
   ```

   Replace `YOUR_TOOL_ID` with the identifier defined in `Mainframework`.

Each invocation processes one selected tool configuration. To process another configuration, run the script again with a different identifier.

**Note:** Defining a new identifier in `Mainframework` does not automatically make the corresponding tool executable. The entry-point script and all dependent components must be configured consistently.


# Experimental Workflow
## Experimental Workflow

The framework follows a sequence of steps to prepare datasets and execute the selected detection tool.

1. **Project initialization:** Create and save the project metadata.
2. **Dataset registration:** Register the selected source-code dataset and its associated bytecode dataset.
3. **Ethereum dataset registration:** Register the Ethereum dataset used by the evaluation workflow.
4. **Tool registration:** Register the configured detection tools and their corresponding paths.
5. **Dataset preprocessing:** Invoke the preprocessing component for the selected dataset.
6. **Test execution:** If preprocessing succeeds, invoke the test agent to execute the evaluation workflow.
7. **Status reporting:** Report the execution status through console messages.

The workflow processes one selected tool configuration per invocation. The successful completion of a registration or preprocessing step does not necessarily guarantee that the detection tool completes execution successfully.

## Repository Structure

The repository contains the components required to configure detection tools, register datasets, preprocess inputs, and execute experiments.

The main components include:

* **`mainframework`**: Defines tool identifiers and their corresponding configurations.
* **`RUN/`**: Contains scripts and resources associated with running the framework.
* **Dataset directories**: Store the datasets and input files required by the detection tools.
* **Tool directories**: Contain or reference the detection tools integrated into the evaluation workflow.
* **Preprocessing and testing components**: Support dataset preparation and test execution.

Dataset and tool locations may depend on the local environment. Update the relevant paths in the configuration before running experiments.

## Reproducibility

To support reproducible experiments, record the following information for each run:

* The selected tool identifier and its configuration.
* The dataset version, location, and input format.
* The relevant preprocessing and execution settings.
* The versions of the detection tools and their dependencies.
* The execution status and generated results.

Keep configuration changes and experimental scripts under version control. Use consistent dataset versions and execution settings when comparing results across tools or experimental conditions.

The framework's reproducibility depends on the availability of the required datasets, dependencies, tool implementations, and execution environment.

## Citation

If you use this framework in your research, please cite the associated publication or research paper.


