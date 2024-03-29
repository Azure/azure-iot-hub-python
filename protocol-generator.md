# DPS Service Client

> see https://aka.ms/autorest

## Getting Started

To build the DPS Service Client, simply install AutoRest in Node.js via `npm` (`npm install -g autorest`) and then run:
> `autorest protocol-generator.md`

To see additional help and options, run:
> `autorest --help`

For other options on installation see [Installing Autorest](https://aka.ms/autorest/install) on the AutoRest GitHub page

---

## Configuration

The following are the settings for using this API with AutoRest

```yaml
input-file: service.json

python:
    namespace: protocol
    output-folder: src/azure/iot/hub
    add-credentials: True
```
