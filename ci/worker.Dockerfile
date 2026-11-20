# Snakemake worker image for the PanDA Compose integration test.
#
# Built by .github/workflows/panda-compose.yml from the plugin repo checkout,
# so the test exercises the code under review, not the published release. The
# harvester queue's containerImage points at this image (panda-compose
# config/harvester/panda_queues.template.json).
FROM python:3.11-slim

ARG SNAKEMAKE_VERSION=9.27.1
# rucio client wheel must match the server line (RUCIO_TAG in the workflow);
# a 4x client against a 41.x server breaks protocol handling.
ARG RUCIO_CLIENT_VERSION=rucio==41.5.1
ARG RUCIO_STORAGE_PLUGIN_VERSION=snakemake-storage-plugin-rucio==0.6.0

RUN pip install --quiet --no-cache-dir \
      snakemake==${SNAKEMAKE_VERSION} \
      snakemake-executor-plugin-panda \
      ${RUCIO_STORAGE_PLUGIN_VERSION} \
      ${RUCIO_CLIENT_VERSION}

# The PR checkout: overlays the published executor plugin with the code
# under review.
COPY . /plugin
RUN pip install --quiet --no-deps /plugin

# Fix the two pinned-storage-plugin bugs (see the patch script's docstring).
COPY ci/patch_rucio_storage_plugin.py /patch_rucio_storage_plugin.py
RUN python /patch_rucio_storage_plugin.py
