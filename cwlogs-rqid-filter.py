#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retrieve and filter AWS CloudWatch logs while keeping all events that contain the same Request ID as
events that match the filter.
"""

import boto3
import logging
import re
import dateutil.parser
from datetime import datetime, timezone

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel('INFO')

client = boto3.client('logs')

# This pattern matches AWS Request IDs of format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# with 'x's any lowercase 0-9, a-f character
REQUEST_ID_REGEX = re.compile(
    r'(([a-f]|\d){8}-([a-f]|\d){4}-([a-f]|\d){4}-([a-f]|\d){4}-([a-f]|\d){12})')


def fetch_events(request_parameters):
    """
    Fetches events from AWS CloudWatch and returns a list of timestamp-sorted events.
    Basically a wrapper around boto3 logs filter_log_events() that takes care of collecting all
    data behind every nextToken.

    Args:
        request_parameters (dict): supported filter_log_events() arguments
            {
                'logGroupName': 'xxx',
                'logStreamNames': ['yyy', 'zzz', ...],
                'logStreamNamePrefix': 'xyz',
                'startTime': 123,
                'endTime': 456,
                'limit': 678
            }

    Returns:
        list: list of event dicts
    """
    events = []
    next_token = None

    while True:
        if next_token:
            request_parameters['nextToken'] = next_token

        logger.debug('Performing query with parameters: {}'.format(request_parameters))
        response = client.filter_log_events(**request_parameters)

        response_events = response['events']
        logger.debug('Got {} events from this response'.format(len(response_events)))

        events += response_events
        next_token = response.get('nextToken')

        if not next_token:
            searched_log_streams = response['searchedLogStreams']
            searched_log_stream_names = [s['logStreamName'] for s in searched_log_streams]
            completely_searched_log_stream_names = [
                s['logStreamName'] for s in searched_log_streams if s['searchedCompletely']]

            break

    # Sort events by timestamp
    events = sorted(events, key=lambda x: x['timestamp'])

    logger.debug('Retrieved {} events'.format(len(events)))
    logger.debug('Searched log streams {}'.format(searched_log_stream_names))
    logger.debug('Completely searched log streams {}'.format(completely_searched_log_stream_names))

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
    logger.debug('Using filter pattern {}'.format(filter_regex_pattern))

    # Build filter regex
    filter_regex = re.compile(filter_regex_pattern)

    # Collect request IDs that match the pattern and write request IDs into events
    matching_request_ids = set()
    for event in events:
        # Collect, strip and replace message
        message = event['message'].strip()
        event['message'] = message

        # Get request ID
        request_id = REQUEST_ID_REGEX.search(message).group(0)
        event['request_id'] = request_id

        # Match filter pattern
        match = True if filter_regex.search(message) else False

        if match:
            matching_request_ids.add(request_id)

    # Collect events that have a matching request ID
    filtered_events = []
    for event in events:
        if event['request_id'] in matching_request_ids:
            filtered_events.append(event)

    logger.debug('Filtered {} events'.format(len(filtered_events)))

    return filtered_events


def _add_arguments(parser):
    parser.add_argument(
        '--group', dest='group_name', type=str, required=True,
        help='Log group name'
    )
    parser.add_argument(
        '--filter', dest='filter', type=str, required=True,
        help='Python regular expression pattern that will match events messages'
    )
    parser.add_argument(
        '--streams', dest='stream_names', type=str, nargs='*', required=False,
        help='Log stream names'
    )
    parser.add_argument(
        '--stream-prefix', dest='stream_name_prefix', type=str, required=False,
        help='Log stream name prefix'
    )
    parser.add_argument(
        '--start-ts', dest='start_timestamp', type=int, required=False,
        help='Start timestamp in milliseconds, UTC timezone'
    )
    parser.add_argument(
        '--start', dest='start', type=str, required=False,
        help='Start date and time, ISO8601 format, UTC timezone'
    )
    parser.add_argument(
        '--stop-ts', dest='stop_timestamp', type=int, required=False,
        help='Stop timestamp in milliseconds, UTC timezone'
    )
    parser.add_argument(
        '--stop', dest='stop', type=str, required=False,
        help='Stop date and time, ISO8601 format, UTC timezone'
    )
    parser.add_argument(
        '--limit', dest='limit', type=int, required=False,
        help='Event limit count'
    )
    timestamp_prefix_group = parser.add_mutually_exclusive_group(required=False)
    timestamp_prefix_group.add_argument(
        '--prefix-timestamp', dest='prefix_ts', action='store_true',
        help='Prefix the logs with event timestamp between parentheses'
    )
    timestamp_prefix_group.add_argument(
        '--prefix-iso', dest='prefix_iso', action='store_true',
        help='Prefix the logs with ISO8601 formatted event timestamp between parentheses'
    )
    parser.add_argument(
        '--debug', dest='debug', action='store_true',
        help='Print debug information'
    )


if __name__ == '__main__':
    # Arguments handling
    import argparse
    description = (
        'Filter AWS CloudWatch logs while keeping all events that have the same Request ID as '
        'events that match the filter.'
    )
    parser = argparse.ArgumentParser(description=description)
    _add_arguments(parser)
    args = parser.parse_args()

    if args.debug:
        logger.setLevel('DEBUG')

    # Build request parameters
    request_parameters = {'logGroupName': args.group_name}
    if args.stream_names:
        request_parameters['logStreamNames'] = args.stream_names
    if args.stream_name_prefix:
        request_parameters['logStreamNamePrefix'] = args.stream_name_prefix
    if args.limit:
        request_parameters['limit'] = args.limit

    if args.start_timestamp:
        request_parameters['startTime'] = args.start_timestamp
    elif args.start:
        request_parameters['startTime'] = int(
            dateutil.parser.parse(args.start).replace(tzinfo=timezone.utc).timestamp() * 1000)

    if args.stop_timestamp:
        request_parameters['endTime'] = args.stop_timestamp
    elif args.stop:
        request_parameters['endTime'] = int(
            dateutil.parser.parse(args.stop).replace(tzinfo=timezone.utc).timestamp() * 1000)

    # Run
    events = fetch_events(request_parameters)
    events = filter_events(events, args.filter)

    # Print events prefixed with their timestamp
    print_pattern = '({}) {}'

    for event in events:
        timestamp = event['timestamp']

        if args.prefix_ts:
            print(print_pattern.format(timestamp, event['message']))
        elif args.prefix_iso:
            iso8601_ts = (
                datetime.utcfromtimestamp(timestamp//1000)
                .replace(microsecond=timestamp % 1000 * 1000))
            print(print_pattern.format(iso8601_ts, event['message']))
        else:
            print(event['message'])
