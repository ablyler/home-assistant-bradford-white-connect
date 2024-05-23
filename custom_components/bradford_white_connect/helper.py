def get_device_property_value(device, property_name):
    """
    Get the value of a property for a given device.

    Args:
        device (Device): The device object.
        property_name (str): The name of the property.

    Returns:
        The value of the property if it exists and has a value attribute, otherwise None.
    """
    # Ensure the property exists
    if property_name in device.properties:
        # Return the value attribute of the property if it is present
        if hasattr(device.properties[property_name], "value"):
            return device.properties[property_name].value

    # Return None if the property does not exist or does not have a value attribute
    return None
