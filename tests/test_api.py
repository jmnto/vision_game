import io
import json
import unittest
from unittest.mock import patch
import server

class ApiTests(unittest.TestCase):
    def setUp(self): server.sessions.clear()
    def request(self,path,body,origin=None):
        handler=object.__new__(server.Handler)
        encoded=json.dumps(body).encode()
        handler.path=path
        handler.headers={'Content-Length':str(len(encoded)),'Host':'127.0.0.1:8000'}
        if origin:handler.headers['Origin']=origin
        handler.rfile=io.BytesIO(encoded)
        output=[]
        handler.send=lambda data,status=200,kind=None:output.append((status,data))
        handler.do_POST()
        return output[0]
    def test_start_and_invalid_session(self):
        status,data=self.request('/api/start',{})
        self.assertEqual(status,200);self.assertEqual(data['score'],0)
        self.assertIn(data['session'],server.sessions)
        self.assertEqual(self.request('/api/scan',{'session':'invalid'})[0],400)
    def test_stale_revision_and_invalid_confidence(self):
        _,data=self.request('/api/start',{})
        body={'session':data['session'],'revision':99,'confidence':.5}
        self.assertEqual(self.request('/api/scan',body)[0],400)
        body.update(revision=0,confidence=2)
        self.assertEqual(self.request('/api/scan',body)[0],400)
        self.assertEqual(server.sessions[data['session']].scans,0)
    def test_http_scan_updates_state_and_rejects_replay(self):
        _,data=self.request('/api/start',{})
        body={'session':data['session'],'revision':0,'confidence':.5}
        with patch.object(server.detector,'predict',return_value=[]):
            status,scan=self.request('/api/scan',body)
        self.assertEqual(status,200);self.assertEqual(scan['scans'],1)
        self.assertEqual(self.request('/api/scan',body)[0],400)
    def test_reset_replaces_session(self):
        _,data=self.request('/api/start',{})
        _,new=self.request('/api/start',{'session':data['session']})
        self.assertNotIn(data['session'],server.sessions)
        self.assertIn(new['session'],server.sessions)
    def test_foreign_origin_rejected(self):
        self.assertEqual(self.request('/api/start',{},'https://example.com')[0],403)

if __name__=='__main__':unittest.main()
