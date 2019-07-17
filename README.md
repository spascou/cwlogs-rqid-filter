# cwlogs-rqid-filter.py
_Ever wanted to filter AWS CloudWatch logs and not only keep the matching events, but also all events that have the same Request ID that the matching event(s)?_

This python script fetches all log events messages related to requests (by AWS Request ID) that in any message of any event match a custom python regex pattern.
It fetches all events for the period, searching their messages with the custom regex pattern and filters only events that have the request IDs that have a message matching.

Changes are described in CHANGELOG.md.

## Installation
`pip install cwlogs-rqid-filter`

## Usage
Do not forget to perform AWS Credentials configuration for boto3 beforehand (https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html).

### Console
Install the library as described above, and run it, either with `cwlogs-rqid-filter` or `python -m cwlogs_rqid_filter`


```
    python -m cwlogs_rqid_filter [-h] --group GROUP_NAME --filter FILTER
                                 [--streams [STREAM_NAMES [STREAM_NAMES ...]]]
                                 [--stream-prefix STREAM_NAME_PREFIX]
                                 [--start-ts START_TIMESTAMP] [--start START]
                                 [--stop-ts STOP_TIMESTAMP] [--stop STOP] [--limit LIMIT]
                                 [--prefix-timestamp | --prefix-iso] [--debug]


Filter AWS CloudWatch logs while keeping all events that have the same Request
ID as events that match the filter.

optional arguments:
  -h, --help            show this help message and exit
  --group GROUP_NAME    Log group name
  --filter FILTER       Python regular expression pattern that will match
                        events messages
  --streams [STREAM_NAMES [STREAM_NAMES ...]]
                        Log stream names
  --stream-prefix STREAM_NAME_PREFIX
                        Log stream name prefix
  --start-ts START_TIMESTAMP
                        Start timestamp in milliseconds, UTC timezone
  --start START         Start date and time, ISO8601 format, UTC timezone
  --stop-ts STOP_TIMESTAMP
                        Stop timestamp in milliseconds, UTC timezone
  --stop STOP           Stop date and time, ISO8601 format, UTC timezone
  --limit LIMIT         Event limit count
  --prefix-timestamp    Prefix the logs with event timestamp between
                        parentheses
  --prefix-iso          Prefix the logs with ISO8601 formatted event timestamp
                        between parentheses
  --debug               Print debug information
```

### Script import
```
from cwlogs_rqid_filter import fetch_events, filter_events

# Any parameters set accepted by the Boto3 logs client filter_log_events() function
request_parameters = {
    'logGroupName': 'xxx',
    'logStreamNames': ['yyy', 'zzz', ...],
    'logStreamNamePrefix': 'xyz',
    'startTime': 123,                       # Unix timestamp
    'endTime': 456,                         # Unix timestamp
    ...
}

filter_regex_pattern = r'*'

all_events = fetch_events(request_parameters)
filtered_events = filter_events(all_events, filter_regex_pattern)
```

## Examples
To get all log events of lambda requests that took at least 1000ms, prefixed by ISO8601-formatted timestamps:
`python -m cwlogs_rqid_filter --group /aws/lambda/someLambdaName --start 2018-11-30T05:04:00Z --stop 2018-11-30T05:05:00Z --filter 'Billed Duration: [0-9]{4,}' --prefix-iso`

You can also specify start and stop timestamps in any timezone, formatted following ISO8601: `--start 2018-11-30T14:04:00+09:00 --stop 2018-11-30T14:05:00+09:00`
