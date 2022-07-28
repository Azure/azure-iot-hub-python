# How to release Python

This document details how to do a **manual** release of the Azure IoT Hub service library

## Make a new branch
```cmd
git checkout -b <branch_name>
```

## Bump the version
Increment the `VERSION` constant that is defined in `azure/iot/hub/constant.py`

We use [semantic versioning](https://semver.org/) to version our libraries.

## Build sdist(s) and wheel(s)

**---->Make sure to use Python 3<----**

From the root, generate both the source distribution and the universal wheel. For instance:

```
python setup.py sdist
python setup.py bdist_wheel
```

**NOTE WELL:** These commands **must** be run from within the root

When the commands are run, a `./dist` directory will be created within the root containing both an sdist (`.tar.gz`) and a universal wheel (`.whl`).

e.g.
```
.
+-- azure
    +-- iot
        +-- hub
+-- setup.py
+-- setup.cfg
+-- ...
+-- dist
    +-- azure-iot-hub-<version>.tar.gz
    +-- azure_iot_hub-<version>-py2.py3-none-any.whl
```

**NOTE:** Universal wheel configuration is set in the `setup.cfg`, which is why you don't need to provide it as a command line argument.

## Upload to PyPi
Now, simply upload the contents of the `./dist` directory to PyPi:

```
twine upload ./dist/*
```

You will be prompted for a username and a password. When upload is complete, your package will be live on PyPi and can be installed with pip.

## Merge Branch and Create GitHub Release
With your new package now released, submit a PR on your branch, and merge those version bumps back into master.

Tag the commit into master as `release_YYYY_MM_DD`, and create a release on GitHub following the pattern of previous releases. Make sure to include copies of both the `.tar.gz` and the `.whl` files you generated in the previous step as assets of the release.