# Snakemake Executor Plugin: PanDA

[![PyPI version](https://img.shields.io/pypi/v/snakemake-executor-plugin-panda)](https://pypi.org/project/snakemake-executor-plugin-panda/)
[![PyPI downloads](https://img.shields.io/pypi/dm/snakemake-executor-plugin-panda)](https://pypi.org/project/snakemake-executor-plugin-panda/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/pypi/pyversions/snakemake-executor-plugin-panda)](https://pypi.org/project/snakemake-executor-plugin-panda/)

A [Snakemake](https://snakemake.readthedocs.io) executor plugin for submitting jobs to the [PanDA](https://panda-wms.readthedocs.io) (Production and Distributed Analysis) workload management system.

## Installation

Install from PyPI:

```bash
pip install snakemake-executor-plugin-panda
```

## Usage

To run Snakemake with the PanDA executor:

```bash
snakemake --executor panda
```

### Configuration

The plugin supports the following settings:

| Setting | Description | Default |
|---|---|---|
| `pre_script` | Shell commands to run before the Snakemake payload on the worker node | Initializes the EIC environment from CVMFS |

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `PANDA_VO` | Virtual organization | `wlcg` |
| `PANDA_SITE` | PanDA site for job submission | `BNL_PanDA_1` |
| `PANDA_AUTH_VO` | Working group for authentication | `wlcg` |

## Requirements

- Python >= 3.11
- A valid PanDA client configuration (`pandaclient`)
- Access to a PanDA instance and appropriate grid credentials

## Documentation

For more details, see the [Snakemake Plugin Catalog](https://snakemake.github.io/snakemake-plugin-catalog/plugins/executor/panda.html).

## License

This project is licensed under the MIT License — see the [LICENSE.md](LICENSE.md) file for details.
