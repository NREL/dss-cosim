# Distribution system co-simulation with OpenDSS and DER controls

A sample co-simulation framework using HELICS with federates for a distribution network 
in OpenDSS and DER controllers.

### Installation

Using Anaconda or conda:
 1. Create a conda environment with HELICS:
    ```
    cd <main path>/DSS_cosim
    conda env create
    ```
    
Without using conda:
 1. Install HELICS:
   `conda install -c gmlc-tdc helics=2.2` 
 2. Install helics-cli:
    `pip install git+https://github.com/GMLC-TDC/helics-cli.git@python-master#egg=helics-cli`
 3. Install OpenDSS-wrapper (and OpenDSSDirect.py):
    `pip install git+https://github.com/NREL/OpenDSS-wrapper#egg=OpenDSS-wrapper`

### Usage

To run the co-simulation:
 1. CD to the co-simulation directory: `cd <main path>/DSS_cosim`
 2. Run the command: `helics run --path runner.json`

By default, results files are saved to `<main path>/results/`
