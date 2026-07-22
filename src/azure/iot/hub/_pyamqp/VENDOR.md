# Vendored `pyamqp`

This directory contains a vendored copy of the pure-Python AMQP implementation
that ships privately as `azure.servicebus._pyamqp` in the
[`Azure/azure-sdk-for-python`](https://github.com/Azure/azure-sdk-for-python)
repository.

`pyamqp` is not published as a standalone PyPI package; vendoring is the
supported way to consume it from outside the SDKs that ship it.

## Provenance

- **Upstream repo:** https://github.com/Azure/azure-sdk-for-python
- **Upstream path:** `sdk/servicebus/azure-servicebus/azure/servicebus/_pyamqp/`
- **Pinned commit:** `42f59593caec801dabfe3d222ddb8561b46b5e72` (tip of `main` at time of fetch)
- **Date copied:** 2026-07-22

## Local modifications

The vendored tree is otherwise byte-identical to upstream at the pinned commit,
with the following exceptions:

1. **`aio/` subtree removed.** This package only performs synchronous C2D
   message sends; the async subtree carried a large maintenance surface and
   required `asyncio` machinery unused by this SDK.
2. **`_message_backcompat.py` removed.** It was unreferenced by any code path
   we import, and it was the only file with a cross-package reference
   (`from ..amqp._amqp_message import ...`, guarded by `TYPE_CHECKING`) — a
   dangling import that would surface under static analysis.

No source edits were made to the remaining files. Internal imports were already
relative (`from .foo import bar`), so no import rewrites were required.

## Why we vendor rather than depend

`pyamqp` lives at a private module path inside `azure-servicebus`
(`azure.servicebus._pyamqp`). Depending on a private module of another SDK is
brittle: upstream is free to reshape or rename it without notice. Vendoring
gives this package a stable, reviewable snapshot that upgrades happen on our
schedule.

## Refresh procedure

To refresh against a newer upstream commit:

1. Choose a target commit SHA on `Azure/azure-sdk-for-python` `main`.
2. Sparse-fetch `sdk/servicebus/azure-servicebus/azure/servicebus/_pyamqp/`
   at that SHA.
3. Replace this directory's contents with the fetched tree.
4. Re-apply the two removals listed under **Local modifications** (`aio/` and
   `_message_backcompat.py`).
5. Update the **Pinned commit** and **Date copied** fields above.
6. Run the test suite and the AMQP-over-WebSocket sample against a real
   IoT Hub to confirm the refresh is safe.
