# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Provides authentication classes for use with the generated azure-core client."""

from azure.core.credentials import TokenCredential
from azure.core.pipeline import PipelineRequest
from azure.core.pipeline.policies import BearerTokenCredentialPolicy, SansIOHTTPPolicy

from .connection_string import ConnectionString
from .connection_string import HOST_NAME, SHARED_ACCESS_KEY_NAME, SHARED_ACCESS_KEY
from .sastoken import SasToken

__all__ = ["ConnectionStringAuthentication", "AzureIdentityCredentialAdapter"]


class ConnectionStringAuthentication(ConnectionString, SansIOHTTPPolicy):
    """ConnectionString-backed pipeline policy that injects a fresh SAS token as
    the ``Authorization`` header on every outgoing request.

    :param connection_string: The connection string to generate SasToken with
    """

    def __init__(self, connection_string):
        ConnectionString.__init__(self, connection_string)

    @classmethod
    def create_with_parsed_values(cls, host_name, shared_access_key_name, shared_access_key):
        connection_string = (
            HOST_NAME
            + "="
            + host_name
            + ";"
            + SHARED_ACCESS_KEY_NAME
            + "="
            + shared_access_key_name
            + ";"
            + SHARED_ACCESS_KEY
            + "="
            + shared_access_key
        )
        return cls(connection_string)

    def on_request(self, request):
        # type: (PipelineRequest) -> None
        sastoken = SasToken(self[HOST_NAME], self[SHARED_ACCESS_KEY], self[SHARED_ACCESS_KEY_NAME])
        request.http_request.headers["Authorization"] = str(sastoken)


class AzureIdentityCredentialAdapter(BearerTokenCredentialPolicy):
    """Pipeline policy that authenticates requests using any azure-identity
    :class:`~azure.core.credentials.TokenCredential`.

    :param credential: Any azure-identity credential (for example DefaultAzureCredential).
    :param str resource_id: The scope used to acquire tokens. Defaults to the IoT Hub audience.
    """

    def __init__(self, credential, resource_id="https://iothubs.azure.net/.default", **kwargs):
        # type: (TokenCredential, str, ...) -> None
        super().__init__(credential, resource_id, **kwargs)
