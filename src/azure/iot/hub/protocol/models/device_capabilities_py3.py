# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class DeviceCapabilities(Model):
    """The status of capabilities enabled on the device.

    :param iot_edge: The property that determines if the device is an edge
     device or not.
    :type iot_edge: bool
    """

    _attribute_map = {"iot_edge": {"key": "iotEdge", "type": "bool"}}

    def __init__(self, *, iot_edge: bool = None, **kwargs) -> None:
        super(DeviceCapabilities, self).__init__(**kwargs)
        self.iot_edge = iot_edge