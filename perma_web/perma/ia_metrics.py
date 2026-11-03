"""
Structured log lines for Internet Archive pipeline metrics.

Each call writes one line of compact JSON, and nothing else, to the process's
real stdout via the `perma.ia_metrics` logger (configured in settings LOGGING:
bare-message formatter, handler on sys.__stdout__, no propagation). CloudWatch
metric filters in lil-terraform read these lines; the field names are the
contract in perma's IA review notes (09-ia-metrics-contract.md), so change them
only together with those filters.
"""
import json
import logging

logger = logging.getLogger('perma.ia_metrics')


def emit(event, **fields):
    logger.info(json.dumps({'ia_metrics': 1, 'event': event, **fields}, separators=(',', ':')))


def flow(kind, n=1, item=None, **fields):
    """
    One ia_flow event: something happened `n` times, optionally to one IA item.
    """
    if item:
        fields['item'] = item
    emit('ia_flow', kind=kind, n=n, **fields)


def state(**fields):
    """
    One ia_state event: a snapshot of the pipeline, taken once per upload producer run.
    """
    emit('ia_state', **fields)
