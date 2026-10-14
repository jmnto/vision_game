import unittest
import numpy as np
from game import Campaign, match_detections, render, scene_data, iou, Detector, PHASES, decoy_data

class Stub:
    def __init__(self, predictions): self.predictions=predictions
    def predict(self,*args): return self.predictions

def prediction(label='apple',box=(10,10,60,60),confidence=.9):
    return dict(label=label,box=list(box),confidence=confidence)

class GameTests(unittest.TestCase):
    def test_iou(self):
        self.assertEqual(iou([0,0,10,10],[0,0,10,10]),1)
        self.assertEqual(iou([0,0,10,10],[20,20,30,30]),0)
    def test_wrong_class_duplicate_and_miss(self):
        targets=[dict(id=0,label='apple',box=[10,10,60,60])]
        events=match_detections([prediction(),prediction(confidence=.8),prediction('orange'),prediction(box=(100,100,150,150))],targets)
        self.assertEqual(sum(e['correct'] for e in events),1)
        self.assertEqual(sum(e['points'] for e in events),-20)
    def test_small_overlap_rejected(self):
        event=match_detections([prediction(box=(55,55,80,80))],[dict(id=1,label='apple',box=[10,10,60,60])])[0]
        self.assertFalse(event['correct'])
    def test_harvest_cannot_score_twice_and_disappears(self):
        s=Campaign(); fruit=scene_data(0)[1][0]
        d=Stub([prediction(box=fruit['box'])])
        before=np.asarray(render(0))
        s.scan(d,'test.pt',.5)
        self.assertEqual(s.score,100)
        self.assertIn(0,s.harvested)
        after=np.asarray(render(0,s.harvested))
        self.assertFalse(np.array_equal(before,after))
        self.assertTrue(np.array_equal(after,np.asarray(render(0,{0}))))
        s.scan(d,'test.pt',.5)
        self.assertEqual(s.score,60)
        self.assertEqual(len(s.harvested),1)
    def test_no_prediction_no_points_and_budget(self):
        s=Campaign()
        with self.assertRaises(ValueError): s.advance()
        for _ in range(5): s.scan(Stub([]),'test.pt',.5)
        self.assertTrue(s.done); self.assertEqual(s.score,0)
        with self.assertRaises(ValueError): s.scan(Stub([]),'test.pt',.5)
        s.advance(); self.assertEqual(s.phase,1);self.assertEqual(s.scans,0)
    def test_campaign_completion(self):
        s=Campaign()
        for phase in range(len(PHASES)):
            predictions=[prediction(f['label'],f['box']) for f in scene_data(phase)[1]]
            s.scan(Stub(predictions),'test.pt',.5)
            self.assertTrue(s.done)
            s.advance()
        self.assertTrue(s.finished);self.assertEqual(s.score,sum(p["count"] for p in PHASES)*100)
        self.assertEqual(len(s.reports),len(PHASES))
        with self.assertRaises(ValueError): s.advance()
    def test_decoy_is_penalized_and_never_harvested(self):
        phase=5; s=Campaign(phase=phase); trap=decoy_data(phase)[0]
        before=np.asarray(render(phase))
        result=s.scan(Stub([prediction('apple',trap['box'])]),'test.pt',.5)
        self.assertEqual(result['score'],-40)
        self.assertEqual(result['fooled'],1)
        self.assertEqual(result['events'][0]['reason'],'decoy')
        self.assertEqual(len(s.harvested),0)
        self.assertTrue(np.array_equal(before,np.asarray(render(phase,s.harvested))))
    def test_correct_nonfruit_class_is_ignored(self):
        s=Campaign(phase=7); trap=decoy_data(7)[0]
        r=s.scan(Stub([prediction('sports ball',trap['box'])]),'test.pt',.5)
        self.assertEqual(r['score'],0);self.assertEqual(r['wrong'],0)
        self.assertIsNone(r['precision']);self.assertFalse(r['events'][0]['scored'])
    def test_empty_final_requires_one_scan(self):
        s=Campaign(phase=len(PHASES)-1)
        self.assertFalse(s.done)
        with self.assertRaises(ValueError):s.advance()
        s.scan(Stub([]),'test.pt',.5)
        self.assertTrue(s.done);s.advance()
        self.assertTrue(s.finished);self.assertEqual(s.reports[-1]['wrong'],0)
    def test_combo_records_best_and_resets_on_false_detection(self):
        s=Campaign();fruits=scene_data(0)[1][:3]
        s.scan(Stub([prediction(f['label'],f['box']) for f in fruits]),'test.pt',.5)
        self.assertEqual(s.combo,3);self.assertEqual(s.best_combo,3)
        s.scan(Stub([prediction(box=(0,0,10,10))]),'test.pt',.5)
        self.assertEqual(s.combo,0);self.assertEqual(s.best_combo,3)
    def test_all_annotations_are_inside_frame(self):
        for phase in range(len(PHASES)):
            objects=scene_data(phase)[1]+decoy_data(phase)
            for obj in objects:
                x,y,x2,y2=obj['box']
                self.assertTrue(0<=x<x2<=1200 and 0<=y<y2<=800)
            self.assertEqual(len(scene_data(phase)[1]),PHASES[phase]['count'])
    def test_missing_weights_rejected(self):
        with self.assertRaises(ValueError): Detector().predict(render(0),'../not-a-model.pt',.5)
    def test_failed_inference_does_not_mutate_campaign(self):
        class Failure:
            def predict(self,*args): raise RuntimeError('bad weights')
        s=Campaign()
        with self.assertRaises(RuntimeError): s.scan(Failure(),'bad.pt',.5)
        self.assertEqual(s.score,0);self.assertEqual(s.scans,0);self.assertEqual(s.revision,0)

if __name__=='__main__':unittest.main()
