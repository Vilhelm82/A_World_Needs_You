"""Trusted adapter boundary. Role sessions must have no ambient tools or shared memory.

Adapters may share transport/model weights, never conversation history, agent memory,
retrieval stores or tools that reach other identities. Handles must refer to actual
independent contexts, not aliases of one conversation. This contract is trusted code;
remote infrastructure claims require provider/adapter review, not a capability flag alone.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from copy import deepcopy
from pathlib import Path
import uuid
import courtroom_v2 as c


@dataclass(frozen=True)
class Capabilities:
    independent_contexts: bool = True
    persistent_contexts: bool = True
    no_ambient_access: bool = True
    safe_resume: bool = True


@dataclass(frozen=True)
class Session:
    session_id: str
    context_id: str
    identity: str


class SessionUnavailable(Exception):
    """No safe resumption possible. Rebuild this identity alone from allowed history."""


class Backend(ABC):
    capabilities = Capabilities(False, False, False, False)
    backend_id: str
    mock = False

    def healthcheck(self) -> dict:
        raise c.CourtError('Backend does not expose a health check.')

    def list_models(self) -> set[tuple[str, str]]:
        raise c.CourtError('Backend does not expose a configured model catalog.')

    @abstractmethod
    def create_session(self, identity: str, system_prompt: str, initial_packet: dict, model_config=None) -> Session: ...
    @abstractmethod
    def send(self, session_id: str, request: dict) -> dict: ...
    @abstractmethod
    def close_session(self, session_id: str) -> None: ...
    @abstractmethod
    def resume_session(self, session_id: str) -> Session: ...


class DeterministicBackend(Backend):
    """Durable isolated conversations for tests/demos; does not simulate legal reasoning.

Scripts are queued per identity by tests only. Unscripted turns fail instead of
inventing testimony. Every conversation is an independent on-disk object. No shared
history, model, network, retrieval, callable tools or access to the court's case file.
"""
    capabilities = Capabilities()
    mock = True

    def __init__(self, directory: Path):
        self.directory = Path(directory).absolute()
        c.require(not any(p.is_symlink() for p in [self.directory,*self.directory.parents]), 'Backend directory cannot contain symlinks.')
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.backend_id = 'deterministic-v1:' + str(self.directory)
        self.scripts: dict[str,list[dict]] = {}

    def _path(self, sid):
        c.require(isinstance(sid,str) and len(sid)==32 and all(x in '0123456789abcdef' for x in sid), 'Invalid session handle.')
        return c.safe_path(self.directory, Path(sid+'.json'))

    def healthcheck(self):
        return {'healthy': True, 'mock': True}

    def list_models(self):
        return set()

    def create_session(self, identity, system_prompt, initial_packet, model_config=None):
        sid=uuid.uuid4().hex
        handle=Session(sid,sid,identity)
        c.atomic(self._path(sid),c.encode({'handle':asdict(handle),'closed':False,
            'history':[{'system':system_prompt,'packet':deepcopy(initial_packet)}]}))
        return handle

    def resume_session(self, session_id):
        try: data=c.load(self._path(session_id))
        except FileNotFoundError as exc: raise SessionUnavailable(session_id) from exc
        if data['closed']: raise SessionUnavailable(session_id)
        return Session(**data['handle'])

    def send(self, session_id, request):
        handle=self.resume_session(session_id)
        c.require(request['identity']==handle.identity,'Request identity does not own this session.')
        queue=self.scripts.get(handle.identity,[])
        c.require(bool(queue),'Deterministic backend has no scripted response; no live model is configured.')
        response=deepcopy(queue.pop(0))
        data=c.load(self._path(session_id))
        data['history'].append({'request':deepcopy(request),'response':response})
        c.atomic(self._path(session_id),c.encode(data))
        return response

    def close_session(self, session_id):
        try: data=c.load(self._path(session_id))
        except FileNotFoundError: return
        data['closed']=True;c.atomic(self._path(session_id),c.encode(data))

    def inspect(self, session_id):
        return deepcopy(c.load(self._path(session_id))['history'])

    def queue(self, identity, response):
        self.scripts.setdefault(identity,[]).append(deepcopy(response))

    def lose(self, session_id):
        self._path(session_id).unlink()
