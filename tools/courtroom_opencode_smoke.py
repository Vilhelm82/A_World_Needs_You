#!/usr/bin/env python3
"""Optional REAL model smoke test. Never part of the deterministic test suite.

Requires an already-running managed OpenCode host and externally authenticated
provider. May consume provider usage. Uses synthetic packets, never a real case.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import uuid

import courtroom_v2 as c
from courtroom_opencode import OpenCodeBackend
from courtroom_runtime_config import RuntimeConfig, ModelConfig


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--provider', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--reasoning', help='Supported OpenCode reasoning variant, such as medium or high.')
    args = parser.parse_args(argv)
    handles = []
    backend = None
    try:
        config = RuntimeConfig.load(args.config)
        model = ModelConfig(args.provider, args.model, args.reasoning)
        assignments = {'smoke_A': model, 'smoke_B': model}
        backend = OpenCodeBackend(config, assignments)
        backend.preflight()
        secrets = {who: uuid.uuid4().hex for who in assignments}
        for who in assignments:
            handles.append(backend.create_session(who,
                'You are ' + who + '. Your only knowledge is your own canary in the initial packet.',
                {'identity': who, 'knowledge': [secrets[who]]}))
        c.require(handles[0].session_id != handles[1].session_id, 'Live smoke reused a session.')
        for handle in handles:
            response = backend.send(handle.session_id, {'identity': handle.identity, 'action': 'dialogue',
                'packet': {}, 'task': 'Return JSON with text equal to your own original canary and data equal to {}.'})
            c.require(response['text'] == secrets[handle.identity], 'Live model did not retain its own initial packet.')
            other = 'smoke_B' if handle.identity == 'smoke_A' else 'smoke_A'
            c.require(secrets[other] not in str(response), 'Live smoke received another identity canary.')
        resumed = OpenCodeBackend(config, assignments)
        resumed.preflight()
        for handle in handles:
            c.require(resumed.resume_session(handle.session_id) == handle, 'Live restart did not preserve identity.')
        print('PASS: live OpenCode created, called and resumed two independent model sessions.')
        return 0
    except (c.CourtError, OSError, ValueError, KeyError, TypeError) as exc:
        print('Live OpenCode smoke FAILED (not a deterministic test pass): ' + str(exc), file=sys.stderr)
        return 2
    finally:
        if backend:
            for handle in handles:
                try:
                    backend.close_session(handle.session_id)
                except (c.CourtError, OSError):
                    print('Live smoke cleanup incomplete; retained isolated session.', file=sys.stderr)


if __name__ == '__main__':
    raise SystemExit(main())
