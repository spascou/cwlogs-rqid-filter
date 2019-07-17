#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime

import ciso8601

from . import fetch_events, filter_events, logger


def _add_arguments(parser):
    parser.add_argument(
        "--group", dest="group_name", type=str, required=True, help="Log group name"
    )
    parser.add_argument(
        "--filter",
        dest="filter",
        type=str,
        required=True,
        help="Python regular expression pattern that will match events messages",
    )
    parser.add_argument(
        "--streams",
        dest="stream_names",
        type=str,
        nargs="*",
        required=False,
        help="Log stream names",
    )
    parser.add_argument(
        "--stream-prefix",
        dest="stream_name_prefix",
        type=str,
        required=False,
        help="Log stream name prefix",
    )
    parser.add_argument(
        "--start-ts",
        dest="start_timestamp",
        type=int,
        required=False,
        help="Start timestamp in milliseconds, UTC timezone",
    )
    parser.add_argument(
        "--start",
        dest="start",
        type=str,
        required=False,
        help="Start date and time, ISO8601 format, UTC timezone",
    )
    parser.add_argument(
        "--stop-ts",
        dest="stop_timestamp",
        type=int,
        required=False,
        help="Stop timestamp in milliseconds, UTC timezone",
    )
    parser.add_argument(
        "--stop",
        dest="stop",
        type=str,
        required=False,
        help="Stop date and time, ISO8601 format, UTC timezone",
    )
    parser.add_argument(
        "--limit", dest="limit", type=int, required=False, help="Event limit count"
    )
    timestamp_prefix_group = parser.add_mutually_exclusive_group(required=False)
    timestamp_prefix_group.add_argument(
        "--prefix-timestamp",
        dest="prefix_ts",
        action="store_true",
        help="Prefix the logs with event timestamp between parentheses",
    )
    timestamp_prefix_group.add_argument(
        "--prefix-iso",
        dest="prefix_iso",
        action="store_true",
        help="Prefix the logs with ISO8601 formatted event timestamp between parentheses",
    )
    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Print debug information"
    )


def run():
    # Arguments handling
    import argparse

    description = (
        "Filter AWS CloudWatch logs while keeping all events that have the same Request ID as "
        "events that match the filter."
    )
    usage = """
    python -m cwlogs_rqid_filter [-h] --group GROUP_NAME --filter FILTER
                                 [--streams [STREAM_NAMES [STREAM_NAMES ...]]]
                                 [--stream-prefix STREAM_NAME_PREFIX]
                                 [--start-ts START_TIMESTAMP] [--start START]
                                 [--stop-ts STOP_TIMESTAMP] [--stop STOP] [--limit LIMIT]
                                 [--prefix-timestamp | --prefix-iso] [--debug]
    """

    parser = argparse.ArgumentParser(description=description, usage=usage)

    _add_arguments(parser)
    args = parser.parse_args()

    if args.debug:
        logger.setLevel("DEBUG")

    # Build request parameters
    request_parameters = {"logGroupName": args.group_name}
    if args.stream_names:
        request_parameters["logStreamNames"] = args.stream_names
    if args.stream_name_prefix:
        request_parameters["logStreamNamePrefix"] = args.stream_name_prefix
    if args.limit:
        request_parameters["limit"] = args.limit

    if args.start_timestamp:
        request_parameters["startTime"] = args.start_timestamp
    elif args.start:
        request_parameters["startTime"] = int(
            ciso8601.parse_datetime(args.start).timestamp() * 1000
        )

    if args.stop_timestamp:
        request_parameters["endTime"] = args.stop_timestamp
    elif args.stop:
        request_parameters["endTime"] = int(
            ciso8601.parse_datetime(args.stop).timestamp() * 1000
        )

    # Run
    events = fetch_events(request_parameters)
    events = filter_events(events, args.filter)

    # Print events prefixed with their timestamp
    print_pattern = "({}) {}"

    for event in events:
        timestamp = event["timestamp"]

        if args.prefix_ts:
            print(print_pattern.format(timestamp, event["message"]))
        elif args.prefix_iso:
            iso8601_ts = datetime.utcfromtimestamp(timestamp // 1000).replace(
                microsecond=timestamp % 1000 * 1000
            )
            print(print_pattern.format(iso8601_ts, event["message"]))
        else:
            print(event["message"])
