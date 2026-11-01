from pathlib import Path
import unittest,hashlib,re,json
R=Path(__file__).resolve().parents[1]
D=R/'deploy-v0610'
class StaffDiagnosticsV0610(unittest.TestCase):
 def test_opt_in_not_normal(self):
  for game in ('Alice2000','Alice2011-VorpalFix'):
   base=(D/game/'RUN_A3D_WINDOWS.cmd').read_text()
   diag=(D/game/'RUN_A3D_STAFF_DIAGNOSTIC_WINDOWS.cmd').read_text()
   self.assertIn('A3D_LOG=0',base)
   self.assertIn('A3D_LOG=1',diag)
   self.assertIn('A3D_STAFF_DIAG=1',diag)
 def test_markers_are_optional(self):
  for game in ('Alice2000','Alice2011-VorpalFix'):
   for state in ('GOOD','BAD'):
    self.assertIn('A3D_STAFF_'+state+'.flag',(D/game/f'MARK_STAFF_{state}_WINDOWS.cmd').read_text())
    self.assertIn('A3D_STAFF_'+state+'.flag',(D/game/f'MARK_STAFF_{state}_WINE.sh').read_text())
 def test_pcm_and_queue_invariant(self):
  P=json.loads((R/'config/game_profiles_v069.json').read_text())
  for game,cfg in P.items():
   self.assertEqual(cfg['queue_headers'],6)
   self.assertEqual(cfg['subblocks'],1)
  self.assertEqual(P['Alice2000']['render_snapshot'],1)
  self.assertEqual(P['Alice2011-VorpalFix']['render_snapshot'],0)
  self.assertEqual(P['QuakeIII-117']['render_snapshot'],1)
 def test_dll_identical_all_games(self):
  for dll in ('a3dapi.dll','a3d.dll'):
   self.assertEqual(len({hashlib.sha256((D/game/dll).read_bytes()).hexdigest() for game in ('Alice2000','Alice2011-VorpalFix','QuakeIII-117')}),1)
 def test_memory_events_and_log_limit(self):
  src=(R/'win32/staff_diag.inc').read_text()
  core=(R/'win32/a3dapi.c').read_text()
  self.assertIn('STAFF_TRACE_CAP 4096u',src)
  self.assertIn('A3D_STAFF_DIAG',src)
  self.assertIn('A3D_LOG_LIMIT_BYTES (1024u*1024u)',core)
 def test_source_events(self):
  src=(R/'win32/source_probe.inc').read_text()
  renderer=(R/'win32/stream_winmm.inc').read_text()
  for event in ('STAFF_EVENT_PLAY','STAFF_EVENT_STOP','STAFF_EVENT_REJECT','STAFF_EVENT_GAIN','STAFF_EVENT_PRIO'):
   self.assertTrue(event in src or event in renderer,event)
  self.assertIn('staff_dump();',renderer)
if __name__=='__main__':unittest.main()
