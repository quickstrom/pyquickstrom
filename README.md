# Quickstrom (in Python)

A new Quickstrom based on Specstrom.

## Development Setup

The developer environment is provided by this project's Nix shell.

First, install:

* [Nix](https://nixos.org/download.html)
* [direnv](https://direnv.net/) (make sure to add the shell hook)

Next, set up direnv in the repository:

```shell
echo "use nix" > .envrc
direnv allow .
```

## Check a TodoMVC Implementation

```shell
poetry run quickstrom -Iulib -Icase-studies --log-level=debug check todomvc $TODOMVC_DIR/examples/dojo/index.html --browser=chrome --capture-screenshots
```

## Run Integration Tests

```shell
nix build -f integration-tests/default.nix --option sandbox relaxed
```
