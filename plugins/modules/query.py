#!/usr/bin/python

DOCUMENTATION = r'''
---
module: prometheus_query
short_description: Fetches latest metric values from Prometheus
description:
    - This module fetches the latest metric values from Prometheus for a given query and time range.
options:
    prometheus_url:
        description:
            - The URL of the prometheus host
        required: true
        type: str
    queries:
        description:
            - List of Prometheus metric queries to fetch.
        required: true
        type: list
        elements: str
requirements:
    - python >= 3.x
    - requests
author:
    - Colin McNaughton @cloin
examples:
    - name: Fetch metrics from Prometheus
      prometheus_query:
        prometheus_url: 'http://prometheus-server:9090'
        queries:
          - 'rate(http_requests_total[5m])'
          - 'up'
return:
    metrics_data:
        description: A dictionary containing the latest values for the queried metrics.
        returned: always
        type: dict
'''

from ansible.module_utils.basic import AnsibleModule
import time
import requests

PROMETHEUS_QUERY_API = '/api/v1/query'

def fetch_latest_metric_value(query, end_time, prometheus_url):
    params = {'query': query, 'time': end_time}
    try:
        response = requests.get(f"{prometheus_url}{PROMETHEUS_QUERY_API}", params=params)
        response.raise_for_status()
        data = response.json()
        metric_data = data.get('data', {}).get('result', [])
        if metric_data:
            return float(metric_data[0]['value'][1])
        return None
    except requests.RequestException as e:
        raise e

def sanitize_query(query):
    return query.replace(":", "_").replace(".", "_")

def main():
    argument_spec = {
        'prometheus_url': {'type': 'str', 'required': True},
        'queries': {'type': 'list', 'required': True}
    }

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    prometheus_url = module.params['prometheus_url']
    queries = module.params['queries']

    current_time = int(time.time())
    end_time = current_time

    metrics_data = {}

    for query in queries:
        try:
            latest_value = fetch_latest_metric_value(query, end_time, prometheus_url)
            key = sanitize_query(query) if latest_value is not None else query
            metrics_data[key] = latest_value if latest_value is not None else "No data available for the specified time range."
        except Exception as e:
            module.fail_json(msg=str(e))

    module.exit_json(changed=False, metrics_data=metrics_data)

if __name__ == '__main__':
    main()
