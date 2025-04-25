# URL Health-Check

This program takes a YAML file, checks the health of an endpoint listed in it using a Python script and outputs **unavailable** endpoints.

Endpoints are only considered available if the status code is between 200 and 299 and the endpoint responds in 500 ms or less.

## Installation

Create a virtual environment.

Activate the virtual environment.

For guidance on creating or activating a virtual environment, refer to the [virtual env documentation](https://docs.python.org/3/library/venv.html).

`Python version >= 3.12.3`

`pip install -r requirements.txt`

## Running the Program

`python3 main.py config.yaml <check_cycles>`

`<check_cycles>` is a required integer specifying the total number of health check cycles to perform.

Ensure `check_cycles` is a valid number in base 10 and is positive.
