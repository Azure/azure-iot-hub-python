# Azure IoT Hub — Python SDK codegen

This directory holds the AutoRest configuration used to (re)generate the
`azure.iot.hub.protocol` layer under `src/azure/iot/hub/protocol/` from the
service Swagger at `service.json` in the repository root.

## Requirements

- Node.js + npm (for `autorest`)
- `npm install -g autorest` (or invoke via `npx autorest`)

## Regenerate

From the repository root:

```sh
autorest swagger/README.md --python --use=@autorest/python@6
```

## Config

```yaml
input-file: ../service.json
output-folder: ../src/azure/iot/hub/protocol
namespace: azure.iot.hub.protocol
package-name: azure-iot-hub
package-version: 3.0.0b1
license-header: MICROSOFT_MIT_NO_VERSION
clear-output-folder: true
no-namespace-folders: true
python: true
version-tolerant: false
models-mode: msrest
client-side-validation: false
add-credential: false
```

### Why these flags

- `models-mode: msrest` — emits legacy attribute-map `Model` classes so kwargs-
  based constructors (`Device(**kwargs)`, `SymmetricKey(primary_key=...)`) keep
  the exact call shape the manager classes rely on. The generated
  `_serialization.py` vendors the msrest serializer so there is no runtime
  `msrest` dependency.
- `version-tolerant: false` — version-tolerant mode drops `models.*` classes,
  which we still expose publicly via `azure.iot.hub.models`.
- `add-credential: false` — this SDK constructs its own auth policy
  (`ConnectionStringAuthentication` or `AzureIdentityCredentialAdapter`) and
  passes it via `authentication_policy=...`; AutoRest must not inject one.
- `clear-output-folder: true` — wipes the previous generated tree so removed
  operations/models are not left behind.
- `no-namespace-folders: true` — keeps `azure.iot.hub.protocol` as a leaf
  package rather than nesting into folders that would break the
  `from .protocol.models import Device, ...` imports in the manager files.
