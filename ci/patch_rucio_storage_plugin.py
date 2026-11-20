#!/usr/bin/env python3
"""Patch snakemake-storage-plugin-rucio==0.6.0 in place.

Two 0.6.0 bugs break the PanDA Compose integration stack. This script fixes
them wherever the plugin is installed: the CI runner host runs it after
`pip install`, and the worker image runs it at build time (see
ci/worker.Dockerfile).

1. ``--storage-rucio-timeout`` arrives as a CLI *string*, but urllib3
   rejects str timeouts -> cast to int before the rucio Client is built.
2. ``remove()`` raises NotImplementedError. snakemake deletes temp and
   intermediate files through the storage provider, so a raising remove()
   fails the whole run after the task already succeeded -> make it a no-op
   (rucio has no per-replica delete anyway; files remain as provenance).

The plugin version is pinned in CI (RUCIO_STORAGE_PLUGIN_VERSION), so the
anchors below are stable. If a version bump moves them, the assertions fail
loudly at build/install time instead of producing a confusing failure
mid-workflow. Running the script twice is a no-op.
"""

import pathlib

import snakemake_storage_plugin_rucio as plugin

patch_file = pathlib.Path(plugin.__file__)
src = patch_file.read_text()

# 1. int-cast the timeout kwarg before the client is constructed.
client_anchor = "self.client = rucio.client.Client(logger=self.logger, **client_kwargs)"
assert client_anchor in src, "rucio storage plugin: client-construction anchor not found"
if "int(client_kwargs['timeout'])" not in src:
    cast = (
        "client_kwargs['timeout'] = int(client_kwargs['timeout']) "
        "if client_kwargs.get('timeout') is not None else None\n        "
    )
    src = src.replace(client_anchor, cast + client_anchor, 1)
    print("patched: timeout int-cast")

# 2. no-op remove().
remove_anchor = "    def remove(self) -> None:"
assert remove_anchor in src, "rucio storage plugin: remove() anchor not found"
if "no-op for PanDA/CI" not in src:
    src = src.replace(
        remove_anchor,
        remove_anchor
        + "\n        # no-op for PanDA/CI: rucio has no per-replica delete\n"
        + "        return None\n        ",
        1,
    )
    print("patched: remove() no-op")

patch_file.write_text(src)
print("patched rucio storage plugin:", patch_file)
