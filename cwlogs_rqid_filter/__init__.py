#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import re

import boto3

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel("INFO")

client = boto3.client("logs")

# This pattern matches AWS Request IDs of format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# with 'x's any lowercase 0-9, a-f character
REQUEST_ID_REGEX = re.compile(
    r"(([a-f]|\d){8}-([a-f]|\d){4}-([a-f]|\d){4}-([a-f]|\d){4}-([a-f]|\d){12})"
)


def fetch_events(request_parameters):
    """
    Fetches events from AWS CloudWatch and returns a list of timestamp-sorted events.
    Basically a wrapper around boto3 logs filter_log_events() that takes care of collecting all
    data behind every nextToken.

    Args:
        request_parameters (dict): supported Boto3 logs client filter_log_events() arguments
            {
                'logGroupName': 'xxx',
                'logStreamNames': ['yyy', 'zzz', ...],
                'logStreamNamePrefix': 'xyz',
                'startTime': 123,
                'endTime': 456,
                ...
            }

    Returns:
        list: list of event dicts
    """
    events = []
    next_token = None

    while True:
        if next_token:
            request_parameters["nextToken"] = next_token

        logger.debug("Performing query with parameters: {}".format(request_parameters))
        response = client.filter_log_events(**request_parameters)

        response_events = response["events"]
        logger.debug("Got {} events from this response".format(len(response_events)))

        events += response_events
        next_token = response.get("nextToken")

        if not next_token:
            searched_log_streams = response["searchedLogStreams"]
            searched_log_stream_names = [
                s["logStreamName"] for s in searched_log_streams
            ]
            completely_searched_log_stream_names = [
                s["logStreamName"]
                for s in searched_log_streams
                if s["searchedCompletely"]
            ]

            break

    # Sort events by timestamp
    events = sorted(events, key=lambda x: x["timestamp"])

    logger.debug("Retrieved {} events".format(len(events)))
    logger.debug("Searched log streams {}".format(searched_log_stream_names))
    logger.debug(
        "Completely searched log streams {}".format(
            completely_searched_log_stream_names
        )
    )

    return events


def filter_events(events, filter_regex_pattern):
    """
    Filters events using the provided python regex pattern, and returns not only events that match,
    but also all other events of the same request ID.

    Args:
        events (list): list of events dicts
        filter_regex_pattern (str): string python regex pattern

    Returns:
        list: filtered list of event dicts
    """
    logger.debug("Using filter pattern {}".format(filter_regex_pattern))

    # Build filter regex
    filter_regex = re.compile(filter_regex_pattern)

    # Collect request IDs that match the pattern and write request IDs into events
    matching_request_ids = set()
    for event in events:
        # Collect, strip and replace message
        message = event["message"].strip()
        event["message"] = message

        # Get request ID
        request_id = REQUEST_ID_REGEX.search(message)
        if request_id:
            request_id = request_id.group(0)
        else:
            continue

        event["request_id"] = request_id

        # Match filter pattern
        match = True if filter_regex.search(message) else False

        if match:
            matching_request_ids.add(request_id)

    # Collect events that have a matching request ID
    filtered_events = []
    for event in events:
        if "request_id" in event and event["request_id"] in matching_request_ids:
            filtered_events.append(event)

    logger.debug("Filtered {} events".format(len(filtered_events)))

    return filtered_events
