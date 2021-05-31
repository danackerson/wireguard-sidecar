# wireguard-sidecar

## Description

A basic demonstration charm that allows the user to configure a Wireguard instance as a server (prepared to host client connections) or as a client connecting to a single host server instance.

## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests

## Running

Ensure your k8s environment is up and running and connected as a model to your juju controller.

Base64 encode your desired wireguard config file `base64 ../wg0.conf | tr -d '\n'`

charmcraft build

juju deploy ./wireguard-sidecar.charm --config config_file_b64='<b64-result-above>' --resource wireguard-image=cmulk/wireguard-docker:alpine

To verify operations, get the Unit address from `juju status` and connect to the chosen port from a local wireguard client.
