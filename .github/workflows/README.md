
# Workflows


## Lint and Test
<img src="../../doc/workflows-lint_and_test.drawio.png" width="700" style="margin-bottom: 3%">

Lints and runs both unit and integration tests. 

## Create Release
<img src="../../doc/workflows-create_release.drawio.png" width="700" style="margin-bottom: 3%">

This workflow creates a new release. This is done by generating a new version number, which is used for creating new Github release and making new Docker image. 

When both the Docker image is pushed to Dockerhub the workflow creates a new branch in [base environment repository](https://github.com/Energinet-DataHub/eo-base-environment) with an updated image version in [eo-auth-service.yaml](https://github.com/Energinet-DataHub/eo-base-environment/tree/development/yggdrasil/applications/eo/eo-auth). A pull-request into the development branch is then made. 

# Workflows Triggers
<img src="../../doc/workflows-triggers.drawio.png" width="700" style="margin-bottom: 3%">