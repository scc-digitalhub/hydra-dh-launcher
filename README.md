# Hydra DigitalHub Launcher

[![license](https://img.shields.io/badge/license-Apache%202.0-blue)](https://github.com/scc-digitalhub/hydra-dh-launcher/LICENSE) ![GitHub Release](https://img.shields.io/github/v/release/scc-digitalhub/hydra-dh-launcher)
![Status](https://img.shields.io/badge/status-stable-gold)


DigitalHub Launcher for Hydra apps uses the [DigitalHub](https://scc-digitalhub.github.io/docs/) platform to launch single tasks. It is expected that the task function is defined as a corresponding `hydra` runtime function. The launcher spawns the execution of the task functions either locally or within the platform, in a batch of parallel jobs.

## Development

See CONTRIBUTING for contribution instructions.

### Build container images

To build the container image, you need to:

Clone the repository and navigate to the `digitalhub-serverless` directory. The build process consists of three main steps:

- Build the processor image (modify the `Makefile` file to change the SERVERLESS_DOCKER_REPO and SERVERLESS_CACHE_REPO variable to your Docker repository, e.g., `docker.io/yourusername`)

```bash
make processor
```

- Build the base image (chooses the Python 3 version from 9, 10, 11 or 12)

```bash
docker build -t python-base-3-<ver> -f ./Dockerfile/Dockerfile-base-3-<ver> .
```

- Build the onbuild image (Modify the `Dockerfile/Dockerfile-onbuild-3-<ver>` file to change the SERVERLESS_DOCKER_REP variable to your Docker repository, e.g., `docker.io/yourusername`)

```bash
docker build -t python-onbuild-3-<ver> -f ./Dockerfile/Dockerfile-onbuild-3-<ver> .
```

- Build the runtime image  (Modify the `Dockerfile/Dockerfile-handler-3-<ver>` file to change the NUCLIO_BASE_IMAGE and NUCLIO_ONBUILD_IMAGE variables that point to the base and onbuild image you just built, e.g., `python-onbuild-3-<ver>`)

```bash

docker build -t python-runtime-3-<ver> -f ./Dockerfile/Dockerfile-handler-3-<ver> --build-arg GIT_TAG=<some-tag> .
```

### Launch container

To run the container, use the following command:

```bash
docker run -e PROJECT_NAME=<project-name> -e RUN_ID=<run-id> python-runtime-3-<ver>
```

Required environment variables:

- `PROJECT`: The name of the project
- `RUN_ID`: The ID of the run to execute

## Security Policy

The current release is the supported version. Security fixes are released together with all other fixes in each new release.

If you discover a security vulnerability in this project, please do not open a public issue.

Instead, report it privately by emailing us at digitalhub@fbk.eu. Include as much detail as possible to help us understand and address the issue quickly and responsibly.

## Contributing

To report a bug or request a feature, please first check the existing issues to avoid duplicates. If none exist, open a new issue with a clear title and a detailed description, including any steps to reproduce if it's a bug.

To contribute code, start by forking the repository. Clone your fork locally and create a new branch for your changes. Make sure your commits follow the [Conventional Commits v1.0](https://www.conventionalcommits.org/en/v1.0.0/) specification to keep history readable and consistent.

Once your changes are ready, push your branch to your fork and open a pull request against the main branch. Be sure to include a summary of what you changed and why. If your pull request addresses an issue, mention it in the description (e.g., “Closes #123”).

Please note that new contributors may be asked to sign a Contributor License Agreement (CLA) before their pull requests can be merged. This helps us ensure compliance with open source licensing standards.

We appreciate contributions and help in improving the project!

## Authors

This project is developed and maintained by **DSLab – Fondazione Bruno Kessler**, with contributions from the open source community. A complete list of contributors is available in the project’s commit history and pull requests.

For questions or inquiries, please contact: [digitalhub@fbk.eu](mailto:digitalhub@fbk.eu)

## Copyright and license

Copyright © 2025 DSLab – Fondazione Bruno Kessler and individual contributors.