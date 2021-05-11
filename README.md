# wireguard-sidecar

## Description

A basic demonstration charm that allows the user to configure a Wireguard instance as a server (prepared to host client connections) or as a client connecting to a single host server instance.

## Usage

TODO: Provide high-level usage, such as required config or relations


## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests
