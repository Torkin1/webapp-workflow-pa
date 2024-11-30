# webapp-workflow-pa

## Install virtual environment (needs `conda`)

Assuming that the project dir full path is specified in the variable `PROJECT_DIR`:

```sh
ENVIRONMENT_PATH=${PROJECT_DIR}/src/caballo/domestico/wwsimulator/res
conda env create -f ${ENVIRONMENT_PATH}/environment.yml -p ${ENVIRONMENT_PATH}/.conda/sim-env-dev
```

## Download prng library `DES-Python`

To inflate the submodule(s):

```sh
git submodule update --init --recursive
```