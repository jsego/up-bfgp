# Integration of a Generalized Planner in the Unified Planning Framework

This repository aims at interfacing the [BFGP++](https://github.com/jsego/bfgp-pp) 
generalized planner into the [Unified Planning](https://github.com/aiplan4eu/unified-planning) 
framework in the context of the AIPlan4EU European project - Grant Agreement #101016442.

## Installation

The code is being developed and tested in an Ubuntu 22.04.2 LTS system.

To install it use the following commands:
1. Install package dependencies
```shell
sudo apt-get -y install cmake g++ make python3 git
```

2. Clone the interface repository
```shell
git clone git@github.com:jsego/up-bfgp.git
```
3. Create a local virtual environment
```shell
cd up-bfgp/
python3 -m venv venv
source venv/bin/activate 
```
4. Clone and install our version of the Unified Planning library
```shell
git clone -b gp-planner git@github.com:jsego/unified-planning.git
```
5. Install the package and its dependencies
```shell
pip install unified-planning/
pip install -r requirements.txt
pip install -e .
```

