#!/usr/bin/env python3
"""Start and operate independent courtroom conversations through OpenCode."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

import courtroom_v2 as c
from courtroom_backend import DeterministicBackend
from courtroom_runtime_config import RuntimeConfig
from courtroom_sessions import Orchestrator


COMMANDS = ('backend-check', 'list-models', 'backend-serve', 'start', 'resume', 'turn',
            'rehearse', 'coverage-rule', 'ground', 'amend', 'human', 'control', 'examine', 'deliberate', 'ballots', 'verdict', 'close')
BACKEND_COMMANDS = frozenset({'backend-check', 'list-models', 'backend-serve'})


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=COMMANDS)
    parser.add_argument('--config', type=Path, help='Credential-free runtime JSON; required for OpenCode.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--world', default='courtroom')
    parser.add_argument('--case', type=Path, help='Fully authored case for first start or backend-check.')
    parser.add_argument('--backend', choices=('opencode', 'mock'), default='opencode')
    parser.add_argument('--executable', default='opencode', help='Pinned OpenCode executable for backend-serve.')
    parser.add_argument('--allow-mock', action='store_true', help='Explicitly permit offline scripted testing.')
    parser.add_argument('--script', type=Path, help='Mock response queues; never used for live play.')
    parser.add_argument('--out', type=Path, help='Sealed rehearsed case output; never overwrite an input case.')
    parser.add_argument('--rulings', type=Path, help='Human-authored coverage dispute rulings as JSON.')
    parser.add_argument('--confirm-human-review', action='store_true', help='Confirm these decisions were made by the named human reviewer.')
    parser.add_argument('--reviewer-will-not-play', action='store_true', help='Explicitly confirm the sealed-case reviewer will not play this case.')
    parser.add_argument('--topic', help='Precommitted amendment envelope ID.')
    parser.add_argument('--accept-amended-case', action='store_true', help='Explicitly leave strict fixed-case play for an amended continuation.')
    parser.add_argument('--target', help='Recorded witness answer ID for ground; defaults to the latest heard answer.')
    parser.add_argument('--identity')
    parser.add_argument('--kind')
    parser.add_argument('--audience', nargs='*', default=[])
    parser.add_argument('--event', type=Path)
    parser.add_argument('--witness')
    parser.add_argument('--question')
    parser.add_argument('--purpose', choices=('merits', 'admissibility'), default='merits')
    return parser


def _arguments(args):
    if args.command == 'coverage-rule':
        c.require(args.case is not None and args.rulings is not None and args.out is not None,
                  'coverage-rule requires --case, --rulings and a new --out path.')
        c.require(args.confirm_human_review, 'coverage-rule requires explicit --confirm-human-review.')
        c.require(args.reviewer_will_not_play, 'coverage-rule requires --reviewer-will-not-play; players must not review sealed knowledge.')
        c.require(args.script is None, 'Human review cannot use a model response script.')
        return
    if args.backend == 'opencode':
        c.require(args.config is not None, 'OpenCode requires --config with runtime model assignments.')
        c.require(args.script is None, '--script is available only with the explicit mock backend.')
    else:
        c.require(args.allow_mock, 'Offline testing requires --backend mock --allow-mock.')
        c.require(args.command not in BACKEND_COMMANDS, 'Backend inspection and serving require OpenCode.')
    if args.command == 'turn':
        c.require(args.identity and args.kind, 'turn requires --identity and --kind.')
    elif args.command in {'human', 'control'}:
        c.require(args.event is not None, args.command + ' requires --event JSON.')
    elif args.command == 'examine':
        c.require(args.identity and args.witness, 'examine requires --identity and --witness.')


def _case(args, world):
    if world.exists():
        case = c.read_case(world)
        if args.case is not None:
            supplied = c.validate(c.load(args.case))
            c.require(supplied == case, '--case differs from the immutable committed case; choose another world.')
        return case
    c.require(args.command in {'start', 'backend-check', 'rehearse'} and args.case is not None,
              'World does not exist. Supply a fully authored --case to start or backend-check.')
    return c.validate(c.load(args.case))


def _operate(args, runtime):
    if args.command == 'amend':
        runtime.amend(args.topic, confirmed=args.accept_amended_case)
    elif args.command == 'ground':
        runtime.ground(args.target)
    elif args.command == 'turn':
        runtime.turn(args.identity, args.kind, args.audience)
    elif args.command == 'human':
        runtime.human(c.load(args.event))
    elif args.command == 'control':
        runtime.control(c.load(args.event))
    elif args.command == 'examine':
        runtime.examine(args.identity, args.witness, args.question, purpose=args.purpose)
    elif args.command == 'deliberate':
        runtime.deliberate_round()
    elif args.command == 'ballots':
        runtime.collect_ballots()
    elif args.command == 'verdict':
        runtime.return_verdict()
    elif args.command == 'close':
        runtime.close()


def _check_world_storage(world):
    target = c.safe_path(world, c.AREA) if world.exists() else world.parent
    while not target.exists():
        target = target.parent
    with tempfile.TemporaryFile(dir=target) as probe:
        probe.write(b'courtroom write probe'); probe.flush(); os.fsync(probe.fileno())


def _sealed_case(path, case):
    c.atomic(path,c.encode(case))
    path.chmod(0o600)


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        _arguments(args)
        if args.command == 'coverage-rule':
            from courtroom_rehearsal import apply_rulings, summary
            c.require(not args.out.exists(), 'coverage-rule requires a new --out path.')
            case=c.validate_foundation(c.load(args.case))
            apply_rulings(case,c.load(args.rulings),human_confirmed=args.confirm_human_review,
                          reviewer_will_not_play=args.reviewer_will_not_play)
            _sealed_case(args.out,case)
            print(json.dumps(summary(case['coverage_rehearsal'])))
            c.validate_readiness(case,allow_mock=args.backend=='mock' and args.allow_mock)
            print(json.dumps({'coverage_pass':True}))
            return 0
        if args.backend == 'opencode':
            config = RuntimeConfig.load(args.config)
            if args.command == 'backend-serve':
                from courtroom_opencode_host import serve
                return serve(config, executable=args.executable)
            from courtroom_opencode import OpenCodeBackend
            if args.command == 'list-models':
                backend = OpenCodeBackend(config, {})
                models = [{'provider': provider, 'model': model,
                           'reasoning_levels': list(backend.reasoning_levels[(provider, model)])}
                          for provider, model in sorted(backend.list_models())]
                print(json.dumps({'models': models}, ensure_ascii=False, indent=2))
                return 0

        world = c.world_path(args.root, args.world)
        case = _case(args, world)
        if args.command == 'rehearse':
            from courtroom_rehearsal import rehearse, assignments, summary
            c.validate_foundation(case)
            c.require(args.out is not None and not args.out.exists(), 'rehearse requires a new --out path.')
            c.require(not world.exists(), 'Rehearse an uncommitted case, never a live world.')
            if args.backend == 'opencode':
                backend = OpenCodeBackend(config, assignments(case, config))
                backend.preflight()
            else:
                backend = DeterministicBackend(args.out.parent / 'rehearsal-mock-sessions')
                if args.script:
                    for who, responses in c.load(args.script).items():
                        for response in responses: backend.queue(who, response)
            def checkpoint(report):
                case['coverage_rehearsal']=report
                _sealed_case(args.out,case)
            case['coverage_rehearsal'] = rehearse(case, backend, checkpoint=checkpoint,
                progress=lambda who, counts: print(json.dumps({'witness': who, **counts}), flush=True))
            _sealed_case(args.out,case)
            print(json.dumps({'coverage_complete':True, **summary(case['coverage_rehearsal'])}),flush=True)
            c.validate_readiness(case, allow_mock=args.backend == 'mock')
            print(json.dumps({'coverage_pass': True}))
            return 0
        c.validate_readiness(case, allow_mock=args.backend == 'mock')
        if args.backend == 'opencode':
            backend = OpenCodeBackend(config, config.resolve(case) | config.grounding_assignments(case) | config.amendment_assignments(case))
            report = backend.preflight()
            _check_world_storage(world)
            report['world_runtime_writable'] = True
            if args.command == 'backend-check':
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
                return 0
        # A live server, isolation checks, and every model assignment must pass
        # before committing case storage or creating any identity session.
        if not world.exists():
            world = c.initialise(args.root, args.world, case, allow_mock_rehearsal=args.backend == 'mock')
        if args.backend == 'mock':
            backend = DeterministicBackend(c.safe_path(world, c.AREA / 'mock-sessions'))
            if args.script:
                for identity, responses in c.load(args.script).items():
                    for response in responses:
                        backend.queue(identity, response)
        runtime = Orchestrator.start(world, backend)
        _operate(args, runtime)
        if args.backend == 'mock':
            print('Isolated mock runtime operation completed (not live model play).')
        else:
            print('OpenCode courtroom operation completed.')
        return 0
    except (c.CourtError, OSError, ValueError, KeyError, TypeError) as exc:
        print('Court session error: ' + str(exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print('Courtroom operation interrupted.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
