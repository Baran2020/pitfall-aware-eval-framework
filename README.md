##  Pitfall-Aware Evaluation Framework for Reentrancy Detection

## Overview

This repository contains a research framework designed to support the systematic evaluation of machine-learning-based reentrancy detection tools for Ethereum smart contracts. It focuses on investigating how methodological pitfalls in experimental design, dataset construction, labeling, and performance evaluation can influence the conclusions drawn about the effectiveness and reliability of these tools.

The framework provides a structured environment for examining the sensitivity of detection results to different evaluation conditions and for comparing machine-learning-based detectors with relevant non-machine-learning baselines.

## Research Motivation

The reliability of security evaluation depends not only on the detection capabilities of a tool but also on the quality of the evaluation methodology. Dataset selection, label quality, class imbalance, evaluation metrics, and other methodological choices can introduce biases that affect reported performance.

This framework addresses this challenge by providing a pitfall-aware approach to evaluating reentrancy detection tools. Its objective is to make evaluation assumptions explicit and to investigate how changes in experimental conditions may affect the interpretation of detection results.

## Objectives

The main objectives of this framework are to:

* Provide a structured methodology for evaluating reentrancy detection tools.
* Investigate the effects of selected methodological pitfalls on evaluation outcomes.
* Examine the influence of dataset characteristics and labeling assumptions on reported performance.
* Support the use of appropriate evaluation metrics, including metrics designed for imbalanced classification.
* Facilitate systematic comparisons between machine-learning-based detectors and relevant alternative detection approaches.
* Improve the transparency and reproducibility of experimental evaluations.

## Configuration

The framework uses tool-specific configurations to select the dataset and input format associated with each execution. The selected tool is specified through the required --tool command-line argument.

The currently supported identifiers are:

| Identifier | Tool |
|------------|------|
| `TL1`      | AWDNN |
| `TL31`     | ReChecker |


Each configuration specifies the dataset location, dataset filename, input type, and bytecode dataset format.

Before running an experiment, update the dataset and tool paths to match the local environment. The current implementation uses Linux-style paths such as /mnt/f/LISTTOOL/..., which may require adjustment depending on the execution environment.

Running the Framework
