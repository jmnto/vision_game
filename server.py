"""Local-only single-process HTTP service; no cloud inference or training needed."""
import argparse
import json
import mimetypes
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from game import ROOT, PHASES, Campaign, Detector, model_files, render, jpeg

sessions={}
lock=threading.Lock()
detector=Detector()

class Handler(BaseHTTPRequestHandler):
    def send(self,data,status=200,kind='application/json'):
        if kind=='application/json': data=json.dumps(data).encode()
        self.send_response(status); self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(data)
    def session(self,token):
        if token not in sessions: raise ValueError('Session expired. Start a new campaign.')
        return sessions[token]
    def do_GET(self):
        parsed=urlparse(self.path); path=parsed.path
        try:
            if path=='/api/config': return self.send(dict(phases=PHASES,models=model_files(),default_model='yolov8n.pt',width=1200,height=800))
            if path=='/api/frame':
                query=parse_qs(parsed.query)
                with lock:
                    s=self.session(query.get('session',[''])[0]); data=jpeg(render(s.phase,s.harvested))
                return self.send(data,kind='image/jpeg')
            if path.startswith('/api/thumbnail/'):
                phase=int(path.rsplit('/',1)[1])
                if not 0<=phase<len(PHASES): raise ValueError('Invalid phase')
                return self.send(jpeg(render(phase).resize((300,200))),kind='image/jpeg')
            if path=='/api/report':
                with lock:
                    s=self.session(parse_qs(parsed.query).get('session',[''])[0])
                    report=dict(summary=s.state(),scans=s.history,scoring={'correct':100,'incorrect':-40,'iou_threshold':.4,'scored_classes':['apple','orange'],'nonfruit_classes':'ignored','combo_bonus':0},scene_type='synthetic photographic composite')
                return self.send(report)
            directory=ROOT/'frontend/dist'
            target=(directory/path.lstrip('/')).resolve()
            if not target.is_relative_to(directory.resolve()): return self.send({'error':'Not found'},404)
            if not target.is_file(): target=directory/'index.html'
            if not target.exists(): return self.send({'error':'Frontend missing. Run npm --prefix frontend install && npm --prefix frontend run build.'},503)
            return self.send(target.read_bytes(),kind=mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        except (ValueError,KeyError) as e: self.send({'error':str(e)},400)
    def do_POST(self):
        # Local browser only; reject cross-site submissions to the inference service.
        origin=self.headers.get('Origin')
        if origin and origin not in (f'http://{self.headers.get("Host")}', 'http://127.0.0.1:5173','http://localhost:5173'):
            return self.send({'error':'Origin not allowed'},403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<=size<=4096: raise ValueError('Request too large')
            body=json.loads(self.rfile.read(size) or b'{}')
            with lock:
                if self.path=='/api/start':
                    expired=[k for k,s in sessions.items() if time.time()-s.last_seen>7200]
                    for k in expired: del sessions[k]
                    if len(sessions)>=32: raise ValueError('Too many active sessions. Restart the server.')
                    old=body.get('session')
                    if old in sessions: del sessions[old]
                    token=secrets.token_urlsafe(24); sessions[token]=Campaign()
                    return self.send({'session':token,**sessions[token].state()})
                s=self.session(body.get('session'))
                if self.path=='/api/scan':
                    if body.get('revision')!=s.revision: raise ValueError('Stale scan request. Reload or start a new campaign.')
                    confidence=float(body.get('confidence',.5))
                    if not .05<=confidence<=.95: raise ValueError('Confidence must be between 0.05 and 0.95.')
                    return self.send(s.scan(detector,body.get('model','yolov8n.pt'),confidence))
                if self.path=='/api/next': return self.send(s.advance())
                return self.send({'error':'Not found'},404)
        except (ValueError,KeyError,TypeError) as e: self.send({'error':str(e)},400)
        except Exception as e:
            print(f'Inference error: {e}',flush=True)
            self.send({'error':f'Inference failed: {e}. Check that the selected weights are a compatible Ultralytics YOLO model.'},500)
    def log_message(self,fmt,*args): pass

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8000); args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'ORCHARD running at http://127.0.0.1:{args.port}',flush=True)
    server.serve_forever()
