# Setting up a development environment

In order to develop the `azure-iot-hub` package, you'll need to set up a Python environment. You can do this with any Python install, however, it is recommended to use a virtual environment (such as [virtualenv](https://pypi.org/project/virtualenv/))

## Creating an editable install
First, you will want to install `azure-iot-hub` from source as an editable install. An editable install allows for changes made to the source to be immediately reflected in your Python environment.

In order to do this, run the following command from the root of the repository:

```
pip install -e .
```

Once you have done this, you will have the package itself installed, as well as all dependencies required to run it. At this point you should be able to run samples.

## Installing testing dependencies

Next, if you'd like to run tests, run the following command from the root

```
pip install -r requirements_test.txt
```

This will install the pytest framework, as well as a handful of extensions that are used in the test code. You should now be able to run tests with pytest. See the [README](./tests/README.md) in the tests directory for more information

## Installing other developer dependencies

Finally, there are some additional tools that are useful for development, such as packaging, static analysis, and automatic code formatting. Once again, from the root, run the following command

```
pip install -r requirements_dev.txt
```

You now will have the ability to release packages (see [RELEASE INSTRUCTIONS](./RELEASE%20INSTRUCTIONS.md) for more information).

To install pre-commit, allowing for automatic static analysis and code formatting, after doing the above, additionally runt he following command:

```
pre-commit install
```
