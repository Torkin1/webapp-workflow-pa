# webapp-workflow-pa

## Install virtual environment (needs `conda`)

Assuming that the project dir path is specified in the variable `PROJECT_DIR`:

```bash
ENVIRONMENT_PATH=${PROJECT_DIR}/webapp-workflow-pa/src/caballo/domestico/wwsimulator/res
conda env create -f ${ENVIRONMENT_PATH}/environment.yml -p ${ENVIRONMENT_PATH}/.conda/sim-env-dev
```