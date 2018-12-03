# cwlogs-rqid-filter.py
_Ever wanted to filter AWS CloudWatch logs and not only keep the matching events, but also all events that have the same Request ID that the matching event(s)?_

This python3 script prints all log events messages related to a single request (by AWS Request ID) that in any message of any event match a custom python regex pattern.
It works by fetching all events for the period, searching their messages with the custom regex pattern and filtering only events that have the request IDs that have a message matching.

## Usage
The script is mostly intended for interactive usage.
Install the requirements found in requirements.txt (boto3), and perform Credentials configuration (https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html).

```
usage: cwlogs-rqid-filter.py [-h] --group GROUP_NAME --filter FILTER
                             [--streams [STREAM_NAMES [STREAM_NAMES ...]]]
                             [--stream-prefix STREAM_NAME_PREFIX]
                             [--start-ts START_TIMESTAMP] [--start START]
                             [--stop-ts STOP_TIMESTAMP] [--stop STOP]
                             [--limit LIMIT]
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

## Examples

To get all log events of lambda requests that took at least 1000ms, prefixed by ISO8601-formatted timestamps:
`python3 cwlogs-rqid-filter.py  --group /aws/lambda/someLambdaName --start 2018-11-30T05:04:00 --stop 2018-11-30T05:05:00 --filter 'Billed Duration: [0-9]{4,}' --prefix-iso`
