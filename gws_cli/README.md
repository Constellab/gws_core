# Gws cli 

This sub package is a command line interface for the gws core.

## Dev 

Before testing the cli locally, delete the dist folder and uninstall gws-cli if it is already installed:

```bash
rm -rf gws_cli/dist
pip uninstall gws-cli -y
```

To test the cli locally, you can run the following command from the root of the project:

```bash
python gws_cli/gws_cli/main_cli.py server run
```

## Build 

To build the cli, you can run the following command from the root of the project:

```bash
cd gws_cli
pip install .
```
