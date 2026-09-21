"""Deterministic controller tests. No LLM, network, real legal assessment or spoilers."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("courtroom", ROOT / "tools/courtroom.py")
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)
PUBLIC = ["player", "opponent", "bench"]

def event(kind, actor="engine", text="Recorded test event.", audience=None, **data):
    return {"type": kind, "actor": actor, "text": text, "audience": PUBLIC if audience is None else audience, "data": data}

class CourtroomTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Only the new template/module resources; no pre-existing user worlds are read.
        for rel in ["templates/courtroom-charter.md", "modules/courtroom/procedure.md", "modules/courtroom/authorities.md", "modules/courtroom/.sealed/case-001.json.zlib.b64"]:
            dest = self.root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((ROOT / rel).read_bytes())
        self.world = c.initialise(self.root, "trial-test")
    def tearDown(self):
        self.tmp.cleanup()
    def add(self, value):
        return c.record(self.world, value)
    def phase(self, target):
        current = c.verify(self.world)["phase"]
        for p in c.PHASES[c.PHASES.index(current)+1:c.PHASES.index(target)+1]:
            self.add(event("phase", to=p))
    def ask(self, actor="opponent", witness="W1"):
        self.phase("evidence")
        return self.add(event("question", actor, "Did you make this entry?", PUBLIC+[witness], witness=witness))[0]
    def answer(self, actor="opponent", witness="W1"):
        self.ask(actor, witness)
        self.add(event("pass", "player" if actor == "opponent" else "opponent"))
        return self.add(event("answer", witness, "Yes.", PUBLIC+[witness]))[0]
    def admit(self, key="E02", status="admitted", uses=None):
        return self.add(event("ruling", "bench", document=key, effect="document", status=status, uses=["truth"] if uses is None else uses, rule="P5"))
    def judgment(self, refs=None, proved=False, award=0):
        self.phase("judgment")
        return event("judgment", "bench", "Reasons grounded in the available record.", findings=[{"issue":"I1", "finding":"proved" if proved else "not_proved", "reason":"Test only; no legal finding claimed.", "refs":refs or []}, {"issue":"I2", "finding":"proved" if proved else "not_reached", "reason":"Test only.", "refs":refs or []}], award_aud=award)
    def test_initial_structure_and_counts(self):
        self.assertEqual(c.verify(self.world)["status"], "PASS")
        seed=c.read_case(self.world)
        self.assertEqual(sum(d["kind"]=="exhibit" for d in seed["documents"].values()),10)
        self.assertEqual(sum(d["kind"]=="statement" for d in seed["documents"].values()),4)
    def test_seed_pinned(self):
        self.assertEqual(c.digest(c.source_seed(self.root)), c.SEED_SHA256)
    def test_init_idempotent(self):
        self.add(event("private", "player", "Private theory", ["player"]))
        self.assertEqual(c.initialise(self.root, "trial-test"),self.world)
        self.assertEqual(c.verify(self.world)["events"],1)
    def test_existing_unrelated_world_not_overwritten(self):
        p=self.root/'worlds/other'; p.mkdir(); (p/'keep.txt').write_text('original')
        with self.assertRaises((OSError,c.CourtError)):
            c.initialise(self.root,'other')
        self.assertEqual((p/'keep.txt').read_text(),'original')
    def test_path_traversal_rejected(self):
        for name in ('../outside','a/b','/tmp/x','UPPER',''):
            with self.subTest(name=name), self.assertRaises(c.CourtError): c.world_path(self.root,name)
    def test_source_tamper_rejected(self):
        p=self.root/'modules/courtroom/.sealed/case-001.json.zlib.b64'; p.write_text('notbase64')
        with self.assertRaises((ValueError,c.CourtError)): c.initialise(self.root,'second')
    def test_case_base_tamper_detected(self):
        p=self.world/c.CASE/'case-base.json'; p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(c.CourtError): c.verify(self.world)
    def test_document_tamper_detected(self):
        (self.world/c.PUBLIC/'documents/E02.md').write_text('replacement')
        with self.assertRaises(c.CourtError): c.verify(self.world)
    def test_role_packet_tamper_detected(self):
        (self.world/c.CASE/'role-packets/initial-W1.json').write_text('{}')
        with self.assertRaises(c.CourtError): c.verify(self.world)
    def test_rule_tamper_detected(self):
        (self.world/'canon/procedure.md').write_text('changed standard')
        with self.assertRaises(c.CourtError): c.verify(self.world)
    def test_charter_is_player_mutable(self):
        p=self.world/'charter.md'; p.write_text(p.read_text()+'\nMore compact dialogue.\n')
        self.assertEqual(c.verify(self.world)['status'],'PASS')
    def test_private_strategy_isolated(self):
        marker='PRIVATE_STRATEGY_TEST_81732'
        self.add(event('private','player',marker,['player']))
        for role in c.ROLES-{'player'}:
            self.assertNotIn(marker,json.dumps(c.packet(self.world,role)))
        self.assertIn(marker,json.dumps(c.packet(self.world,'player')))
    def test_sealed_note_never_exported(self):
        e=event('dialogue','solicitor','Public text.',PUBLIC); e['private_note']='SEALED_NOTE_TEST_92467'; self.add(e)
        for role in c.ROLES:
            self.assertNotIn(e['private_note'],json.dumps(c.packet(self.world,role)))
    def test_bench_has_no_truth_or_privileged_instructions(self):
        p=c.packet(self.world,'bench')
        self.assertEqual(set(p['documents']),{'E01'})
        self.assertNotIn('truth',p)
        private=c.read_case(self.world)['roles']['player']['private_instructions']
        self.assertNotIn(private,json.dumps(p))
    def test_witnesses_do_not_share_unheard_testimony(self):
        self.add(event('dialogue','W1','UNHEARD_WITNESS_MARKER',PUBLIC+['W1']))
        self.assertNotIn('UNHEARD_WITNESS_MARKER',json.dumps(c.packet(self.world,'W2')))
    def test_document_show_is_role_local(self):
        self.add(event('show','player','Shown E09.',['player','W4'],document='E09',to='W4'))
        self.assertIn('E09',c.packet(self.world,'W4')['documents'])
        self.assertNotIn('E09',c.packet(self.world,'W1')['documents'])
    def test_opponent_question_waits_for_player(self):
        self.ask()
        with self.assertRaises(c.CourtError): self.add(event('answer','W1',audience=PUBLIC+['W1']))
        self.add(event('pass','player')); self.add(event('answer','W1',audience=PUBLIC+['W1']))
        self.assertIsNone(c.replay(c.read_case(self.world),c.read_events(self.world))['pending'])
    def test_player_question_gives_opponent_same_right(self):
        self.ask('player')
        with self.assertRaises(c.CourtError): self.add(event('answer','W1',audience=PUBLIC+['W1']))
        self.add(event('pass','opponent')); self.add(event('answer','W1',audience=PUBLIC+['W1']))
    def test_objection_holds_answer(self):
        self.ask(); self.add(event('objection','player',rule='P4'))
        with self.assertRaises(c.CourtError): self.add(event('answer','W1',audience=PUBLIC+['W1']))
        self.add(event('ruling','bench',effect='objection',rule='P4',result='overruled'))
        self.add(event('answer','W1',audience=PUBLIC+['W1']))
    def test_sustained_question_cannot_be_answered(self):
        self.ask(); self.add(event('objection','player',rule='P4'))
        self.add(event('ruling','bench',effect='objection',rule='P4',result='sustained'))
        with self.assertRaises(c.CourtError): self.add(event('answer','W1',audience=PUBLIC+['W1']))
    def test_wrong_witness_cannot_answer(self):
        self.ask(); self.add(event('pass','player'))
        with self.assertRaises(c.CourtError): self.add(event('answer','W2',audience=PUBLIC+['W2']))
    def test_wrong_actor_cannot_pass(self):
        self.ask()
        with self.assertRaises(c.CourtError): self.add(event('pass','opponent'))
    def test_no_magic_rule(self):
        with self.assertRaises(c.CourtError): self.add(event('ruling','bench',effect='procedure',rule='P999'))
    def test_unknown_exhibit_rejected(self):
        with self.assertRaises(c.CourtError): self.admit('E999')
    def test_excluded_exhibit_not_in_bench_packet(self):
        self.admit('E02'); self.admit('E02','excluded',[])
        self.assertNotIn('E02',c.packet(self.world,'bench')['documents'])
    def test_marked_exhibit_only_for_admissibility(self):
        self.admit('E02','marked',[]); p=c.packet(self.world,'bench')
        self.assertNotIn('E02',p['documents']); self.assertIn('E02',p['admissibility_only'])
    def test_limited_admission_cannot_support_truth(self):
        self.admit('E02','limited',['notice'])
        j=self.judgment([{'id':'E02','use':'truth'}],True,1)
        with self.assertRaises(c.CourtError): self.add(j)
    def test_unknown_record_reference_rejected(self):
        j=self.judgment([{'id':'T9999','use':'truth'}],True,1)
        with self.assertRaises(c.CourtError): self.add(j)
    def test_submission_is_not_evidence(self):
        t=self.add(event('submission','player','An unsupported allegation.'))[0]
        j=self.judgment([{'id':t,'use':'truth'}],True,1)
        with self.assertRaises(c.CourtError): self.add(j)
    def test_private_statement_is_not_evidence(self):
        t=self.add(event('private','player','Private assertion.',['player']))[0]
        j=self.judgment([{'id':t,'use':'truth'}],True,1)
        with self.assertRaises(c.CourtError): self.add(j)
    def test_proved_finding_needs_references(self):
        j=self.judgment([],True,1)
        with self.assertRaises(c.CourtError): self.add(j)
    def test_award_requires_required_findings(self):
        j=self.judgment([],False,1)
        with self.assertRaises(c.CourtError): self.add(j)
    def test_excluded_testimony_cannot_support_judgment(self):
        t=self.answer(); self.add(event('ruling','bench',effect='testimony',turn=t,uses=[],rule='P6'))
        j=self.judgment([{'id':t,'use':'truth'}],True,1)
        with self.assertRaises(c.CourtError): self.add(j)
    def test_batch_rejection_is_atomic(self):
        before=(self.world/c.CASE/'events.jsonl').read_bytes()
        with self.assertRaises(c.CourtError): self.add([event('private','player','X',['player']),event('ruling','player',effect='procedure',rule='P4')])
        self.assertEqual(before,(self.world/c.CASE/'events.jsonl').read_bytes())
    def test_log_tamper_detected(self):
        self.add(event('dialogue','solicitor','ORIGINAL'))
        p=self.world/c.CASE/'events.jsonl'; p.write_text(p.read_text().replace('ORIGINAL','MODIFIED'))
        with self.assertRaises(c.CourtError): c.verify(self.world)
    def test_exact_wording_preserved(self):
        text='I said "approved access", not "approved the charge".\nThat is my answer.'
        self.add(event('dialogue','W1',text,PUBLIC+['W1']))
        self.assertIn(text,(self.world/c.PUBLIC/'transcript.md').read_text())
    def test_resume_restores_projections_not_facts(self):
        self.ask(); before=(self.world/c.CASE/'case-base.json').read_bytes()
        (self.world/c.CASE/'live.json').write_text('{}')
        with self.assertRaises(c.CourtError): c.verify(self.world)
        c.resume(self.world)
        self.assertEqual(before,(self.world/c.CASE/'case-base.json').read_bytes())
        self.assertEqual(c.packet(self.world,'player')['pending']['waiting'],['player'])
    def test_erratum_invalidates_reliance_without_rewriting_history(self):
        t=self.answer(); original=(self.world/c.CASE/'case-base.json').read_bytes()
        self.add(event('erratum','engine','Engine correction.',PUBLIC+['W1'],target=t,replacement='Corrected wording.'))
        self.assertTrue(c.packet(self.world,'player')['assessment_paused'])
        self.assertEqual(original,(self.world/c.CASE/'case-base.json').read_bytes())
        self.add(event('repair','engine','Reopened the opportunity to ask again.',reopen='evidence'))
        j=self.judgment([{'id':t,'use':'truth'}],True,1)
        with self.assertRaises(c.CourtError): self.add(j)
    def test_gap_blocks_judgment(self):
        j=self.judgment(); self.add(event('gap','engine','Material authoring gap.'))
        with self.assertRaises(c.CourtError): self.add(j)
    def test_live_case_cannot_unseal(self):
        with self.assertRaises(c.CourtError): c.unseal(self.world,True)
    def test_unseal_requires_confirmed_closed_case(self):
        self.add(self.judgment()); self.phase('closed')
        with self.assertRaises(c.CourtError): c.unseal(self.world,False)
        dest=c.unseal(self.world,True)
        self.assertTrue(dest.exists()); self.assertTrue(c.packet(self.world,'player')['informed_replay'])
    def test_judgment_snapshot_is_record_only(self):
        self.add(self.judgment())
        p=c.load(self.world/c.CASE/'adjudication.json')
        self.assertNotIn('truth',p)
        self.assertEqual(set(p['documents']),{'E01'})
    def test_unilateral_assertion_is_not_a_stipulation(self):
        with self.assertRaises(c.CourtError): self.add(event('stipulation','player','I assert this is agreed.'))
    def test_repair_removes_superseded_judgment_snapshot(self):
        self.add(self.judgment())
        self.add(event('gap','engine','An openly recorded review issue.'))
        self.add(event('repair','engine','Reopened evidence without changing the past.',reopen='evidence'))
        self.assertFalse((self.world/c.CASE/'adjudication.json').exists())
        self.assertEqual(c.verify(self.world)['status'],'PASS')
    def test_judgment_snapshot_tamper_detected(self):
        self.add(self.judgment())
        (self.world/c.CASE/'adjudication.json').write_text('{}')
        with self.assertRaises(c.CourtError): c.verify(self.world)
        self.assertEqual(c.resume(self.world)['status'],'PASS')
    def test_phase_cannot_skip_to_verdict(self):
        with self.assertRaises(c.CourtError): self.add(event('phase',to='judgment'))
    def test_unknown_event_fields_rejected(self):
        e=event('dialogue'); e['invented_history']='forbidden'
        with self.assertRaises(c.CourtError): self.add(e)

if __name__ == '__main__':
    unittest.main()
