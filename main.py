import yaml
import requests
import time
import json
import os
import tldextract
from collections import defaultdict
from typing import Any

def valid_positive_number(input_str: str) -> bool:
    try:
        number = int(input_str)
        return number > 0
    except ValueError:
        return False


def load_config(file_path: str) -> Any:
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def check_health(endpoint: dict) -> tuple[str, int] | tuple[str, requests.RequestException]:
    HTTP_SUCCESS_CODE_MIN = 200
    HTTP_SUCCESS_CODE_MAX = 299
    MILISECONDS_IN_A_SECOND = 1000
    DECIMAL_PLACES = 2
    TIME_LIMIT_EXCEEDED = 3
    RESPONSE_TIME_THRESHOLD = 500.0

    url = endpoint.get("url")
    method = endpoint.get("method", "GET")
    headers = endpoint.get("headers")
    body = json.loads(endpoint["body"]) if endpoint.get("body") else None

    try:
        response = requests.request(method, url, headers=headers, json=body, timeout=TIME_LIMIT_EXCEEDED)
        elapsed_miliseconds = round(response.elapsed.total_seconds() * MILISECONDS_IN_A_SECOND, DECIMAL_PLACES)

        if elapsed_miliseconds > RESPONSE_TIME_THRESHOLD:
            return ("SLOW", elapsed_miliseconds)
        elif HTTP_SUCCESS_CODE_MIN <= response.status_code <= HTTP_SUCCESS_CODE_MAX and elapsed_miliseconds <= RESPONSE_TIME_THRESHOLD:
            return ("UP", response.status_code)
        else:
            return ("DOWN", response.status_code)
    except requests.RequestException as err:
        return ("DOWN", err)


def monitor_endpoints(file_path: str, check_cycles: int) -> None:
    PERCENTAGE_CONVERSION_FACTOR = 100
    DECIMAL_PLACES = 2

    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})
    config = load_config(file_path)

    if not config:
        raise RuntimeError(f"Error: The YAML file {file_path} is empty.")

    while check_cycles > 0:
        for endpoint in config:
            if "url" not in endpoint:
                print(f"Warning: Skipping this entry {endpoint} because of missing url key in endpoint configuration.")
                continue

            url = endpoint.get("url")
            domain = tldextract.extract(url).registered_domain
            response, response_detail = check_health(endpoint)
            method = endpoint.get("method", "GET")

            if response == "UP":
                domain_stats[domain]["up"] += 1
            elif response == "SLOW":
                print(f"{url} ({method}) is a slow endpoint with a latency of {response_detail} ms")
            elif response == "DOWN" and isinstance(response_detail, requests.RequestException):
                print(f"{url} ({method}) threw an error:\n\n${response_detail}\n")
            else:
                print(f"{url} ({method}) is a down endpoint with a HTTP status code of {response_detail}")
            domain_stats[domain]["total"] += 1

        for domain, stats in domain_stats.items():
            if stats["total"] != 0:
                availability = round(PERCENTAGE_CONVERSION_FACTOR * (stats["up"] / stats["total"]), DECIMAL_PLACES)
                print(f"Domain {domain} has an availability percentage of {availability}% ({stats["up"]}/{stats["total"]})")
            else:
                raise ZeroDivisionError(f"Error: There was no endpoints processed. Please ensure the configuration YAML file contains a url key and name key in atleast one entry.")

        print("---")
        if check_cycles - 1 > 0:
            time.sleep(15)
        domain_stats = defaultdict(lambda: {"up": 0, "total": 0})
        check_cycles -= 1


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Error: Invalid number of arguments. 3 is expected.")
        print("Usage: python main.py <config_file_path.yaml> <check_cycles>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    if not os.path.isfile(config_file):
        print(f"Error: File {config_file} does not exist or is not accessible.")
        sys.exit(1)

    valid_number = valid_positive_number(sys.argv[2])
    if not valid_number:
        print(f"Error: {sys.argv[2]} is not a valid number for <check_cycles>. Please ensure <check_cycles> is greater than 0")
        sys.exit(1)

    check_cycles = int(sys.argv[2])

    try:
        monitor_endpoints(config_file, check_cycles)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")