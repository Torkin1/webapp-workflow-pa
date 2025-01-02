# webapp-workflow-pa

## Install virtual environment (needs `conda`)

Assuming that the project dir full path is specified in the variable `PROJECT_DIR`:

```sh
ENVIRONMENT_DIR=${PROJECT_DIR}
conda env create -f ${ENVIRONMENT_DIR}/environment.yml -p ${ENVIRONMENT_DIR}/.conda/sim-env-dev
```

## Download prng library `DES-Python`

To inflate the submodule(s):

```sh
git submodule update --init --recursive
```

## Launch
### Linux
```sh
export PYTHONPATH=$PYTHONPATH:${PROJECT_DIR}/src
cd ${PROJECT_DIR}/src/caballo/domestico/wwsimulator/
python -m main
```