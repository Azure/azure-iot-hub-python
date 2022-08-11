# Tests

The tests in this directory purely cover manually written code. No auto-generated code (i.e. src/azure/iot/hub/protocol) is tested, as it is assumed to be correct, given it is generated from the service API.

These test modules can be run using pytest as such:

```
pytest <name of module>
```

You can also run all tests via the following command:

```
pytest .
```

For more information about pytest, please consult the [pytest documentation](https://docs.pytest.org/)
