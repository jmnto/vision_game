"""ORCHARD: deterministic image scenes, real YOLO inference, server-owned scoring."""
from __future__ import annotations
import io
import json
import os
import time
from pathlib import Path
from dataclasses import dataclass, field
from functools import lru_cache
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent
os.environ.setdefault('YOLO_CONFIG_DIR', str(ROOT / '.runtime'))
os.environ.setdefault('YOLO_OFFLINE', 'true')
WIDTH, HEIGHT = 1200, 800
MAX_SCANS = 5
PHASES = [
    dict(name='Bom dia, pomar!', short='Bom dia, pomar', description='Maçãs ao sol. Café para você, pixels para o robô.', light='Manhã clara', fruit='apple', count=8, decoys=[]),
    dict(name='Laranja é o novo desafio', short='Cítricos', description='Mudou a fruta. O robô continua sem saber fazer suco.', light='Sol aberto', fruit='orange', count=9, decoys=[]),
    dict(name='Cadê a maçã?', short='Esconde-esconde', description='Frutas pequenas e folhas na frente. Não vale culpar a salada.', light='Sombra das folhas', fruit='apple', count=12, decoys=[]),
    dict(name='Hora extra no pomar', short='Luz baixa', description='Pouca luz e ruído no sensor. O robô esqueceu os óculos.', light='Fim de tarde', fruit='orange', count=10, decoys=[]),
    dict(name='Salada de algoritmos', short='Tudo misturado', description='Maçãs e laranjas juntas. Aqui comparar as duas é obrigatório.', light='Luz variável', fruit='mixed', count=14, decoys=[]),
    dict(name='O pomar de plástico', short='Frutas de mentira', description='Maçãs decorativas entre frutas reais. Procure a emenda: plástico não vira torta.', light='Vitrine rural', fruit='apple', count=6, decoys=['plastic','plastic','wax','plastic']),
    dict(name='Natal fora de época', short='Natal no pomar', description='Bolinhas de Natal e velas de laranja invadiram os galhos. Não colha a decoração!', light='Festa no sítio', fruit='mixed', count=6, decoys=['bauble','bauble','plastic','wax']),
    dict(name='A liga das laranjas', short='Pomar esportivo', description='Bolas de basquete e velas entre laranjas. Cesta de frutas ou cesta de três pontos?', light='Tarde esportiva', fruit='orange', count=8, decoys=['ball','wax','ball','plastic']),
    dict(name='A feira dos impostores', short='Impostores', description='Folhas, sombra e quatro tipos de isca. O robô pediu adicional de insalubridade.', light='Sombra traiçoeira', fruit='mixed', count=8, decoys=['plastic','wax','bauble','ball','plastic','wax']),
    dict(name='A grande pegadinha', short='Só decoração!', description='Nenhuma fruta de verdade! Faça uma leitura sem tentar colher nada. Saber se abster também é inteligência.', light='Pegadinha final', fruit='mixed', count=0, decoys=['plastic','wax','plastic','wax','bauble','ball']),
]
DECOY_NAMES = {'plastic':'maçã de plástico','wax':'vela de laranja','bauble':'bolinha de Natal','ball':'bola de basquete'}
FRUIT_LABELS = {'apple', 'orange'}

@lru_cache(maxsize=2)
def sprite(label):
    sheet = Image.open(ROOT / 'assets/fruits.png').convert('RGBA')
    w,h = sheet.size
    im = sheet.crop((0 if label == 'apple' else w//2, 0, w//2 if label == 'apple' else w, h))
    # Trim transparent padding. Alpha is supplied by the generated asset.
    alpha = im.getchannel('A')
    box = alpha.point(lambda x: 255 if x > 220 else 0).getbbox()
    return im.crop(box)

@lru_cache(maxsize=len(PHASES))
def scene_data(phase):
    base = Image.open(ROOT/'assets/orchard.png').convert('RGB').resize((WIDTH, HEIGHT))
    if phase in (1,3): base = ImageOps.mirror(base)
    if phase == 2: base = base.crop((80,20,1100,700)).resize((WIDTH,HEIGHT))
    if phase == 4: base = base.crop((0,0,1120,747)).resize((WIDTH,HEIGHT))
    # Hand-authored attachment locations; labels come from scene construction, never YOLO.
    positions = [(160,155,116),(385,245,130),(585,145,94),(1030,215,110),
                 (900,400,87),(280,440,122),(510,490,98),(1080,535,94),
                 (730,300,70),(420,105,77),(670,550,72),(140,580,88),
                 (975,95,68),(760,130,65)]
    fruits=[]
    for i,(x,y,size) in enumerate(positions[:PHASES[phase]['count']]):
        label = PHASES[phase]['fruit']
        if label == 'mixed': label = 'apple' if i%2 == 0 else 'orange'
        if phase == 2: size=int(size*.48)
        if phase == 3: size=int(size*.60)
        if phase in (1,3): x=WIDTH-x
        fruit=sprite(label).copy()
        fruit.thumbnail((size,size))
        fruit=fruit.rotate((i%5-2)*6,Image.Resampling.BICUBIC,expand=True)
        bbox=fruit.getchannel('A').point(lambda a: 255 if a>180 else 0).getbbox()
        fruit=fruit.crop(bbox)
        x,y=int(x-fruit.width/2),int(y-fruit.height/2)
        fruits.append(dict(id=i,label=label,box=[x,y,x+fruit.width,y+fruit.height],sprite=fruit))
    return base, fruits

@lru_cache(maxsize=4)
def decoy_sprite(kind):
    sheet=Image.open(ROOT/'assets/decoys.png').convert('RGBA')
    w,h=sheet.size
    col,row={'plastic':(0,0),'wax':(1,0),'bauble':(0,1),'ball':(1,1)}[kind]
    tile=sheet.crop((col*w//2,row*h//2,(col+1)*w//2,(row+1)*h//2))
    bounds=tile.getchannel('A').point(lambda a:255 if a>180 else 0).getbbox()
    if bounds is None: raise ValueError('Missing decoy sprite')
    return tile.crop(bounds)

@lru_cache(maxsize=len(PHASES))
def decoy_data(phase):
    slots=[(725,190,150),(720,470,130),(170,650,125),(430,650,120),(945,630,125),(1040,100,130)]
    result=[]
    for i,kind in enumerate(PHASES[phase]['decoys']):
        x,y,size=slots[i]
        asset=decoy_sprite(kind).copy();asset.thumbnail((size,size))
        x,y=int(x-asset.width/2),int(y-asset.height/2)
        result.append(dict(id=i,kind=kind,name=DECOY_NAMES[kind],box=[x,y,x+asset.width,y+asset.height],sprite=asset))
    return result

def render(phase, harvested=()):
    base, fruits=scene_data(phase)
    frame=base.copy()
    for f in fruits:
        if f['id'] in harvested: continue
        x,y,x2,y2=f['box']
        frame.paste(f['sprite'],(x,y),f['sprite'])
        if phase == 2 and f['id']%2 == 0:
            # A foreground strip restores the actual foliage over the fruit.
            cut=y+int((y2-y)*.42)
            foliage=base.crop((x,y,x2,cut))
            rgb=np.asarray(foliage).astype(float)
            mask=Image.fromarray(np.uint8((rgb[:,:,1]>rgb[:,:,0]*.9)&(rgb[:,:,1]>rgb[:,:,2]*1.12))*255)
            frame.paste(foliage,(x,y),mask)
    for decoy in decoy_data(phase):
        frame.paste(decoy['sprite'],tuple(decoy['box'][:2]),decoy['sprite'])
    if phase in (2,8): frame=ImageEnhance.Brightness(frame).enhance(.72)
    if phase == 3:
        arr=np.asarray(frame).astype(float)*np.array([.42,.33,.25])
        arr+=np.random.default_rng(42).normal(0,8,arr.shape)
        frame=Image.fromarray(np.clip(arr,0,255).astype('uint8'))
    if phase == 4: frame=ImageEnhance.Color(frame).enhance(.82)
    return frame

def jpeg(frame):
    out=io.BytesIO(); frame.save(out,format='JPEG',quality=93); return out.getvalue()

def iou(a,b):
    intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    union=max(0,a[2]-a[0])*max(0,a[3]-a[1])+max(0,b[2]-b[0])*max(0,b[3]-b[1])-intersection
    return intersection/union if union else 0

def match_detections(predictions, targets, threshold=.4, decoys=()):
    """Confidence-ordered, class-aware, one-to-one matching. Duplicates are errors."""
    available={f['id']:f for f in targets}
    events=[]
    for pred in sorted(predictions,key=lambda p:p['confidence'],reverse=True):
        if pred['label'] not in FRUIT_LABELS:
            events.append({**pred,'correct':False,'scored':False,'fruit_id':None,'points':0,'iou':0,'reason':'ignored'})
            continue
        candidates=[(iou(pred['box'],f['box']),k) for k,f in available.items() if pred['label']==f['label']]
        overlap,match=max(candidates,default=(0,None))
        good=match is not None and overlap>=threshold
        trap=max(decoys,key=lambda d:iou(pred['box'],d['box']),default=None)
        fooled=not good and trap is not None and iou(pred['box'],trap['box'])>=threshold
        events.append({**pred,'correct':good,'scored':True,'fruit_id':match if good else None,'points':100 if good else -40,'iou':round(overlap,3),'reason':'harvest' if good else 'decoy' if fooled else 'false_detection','decoy':trap['name'] if fooled else None})
        if good: del available[match]
    return events

def model_files():
    return sorted(p.name for p in (ROOT/'models').glob('*.pt') if p.is_file() and not p.is_symlink())

class Detector:
    def __init__(self): self.name=None; self.model=None; self.signature=None
    def predict(self,frame,name,confidence):
        if name not in model_files(): raise ValueError('Select an existing .pt file inside models/.')
        stat=(ROOT/'models'/name).stat()
        signature=(name,stat.st_mtime_ns,stat.st_size)
        if signature!=self.signature:
            from ultralytics import YOLO
            model=YOLO(str(ROOT/'models'/name),task='detect')
            if model.task not in ('detect','segment'): raise ValueError('Use a YOLO detection or segmentation checkpoint.')
            self.model=model; self.name=name; self.signature=signature
        mapping_path=ROOT/'models'/f'{Path(name).stem}.json'
        mapping=json.loads(mapping_path.read_text()) if mapping_path.exists() else {}
        if not isinstance(mapping,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in mapping.items()):
            raise ValueError('Class aliases must be a JSON object of string-to-string mappings.')
        # PIL RGB input: Ultralytics handles the conversion internally.
        result=self.model.predict(source=frame,conf=confidence,imgsz=960,device='cpu',verbose=False)[0]
        predictions=[]
        for box in result.boxes:
            label=str(result.names[int(box.cls.item())]).lower().strip()
            label=mapping.get(label,label)
            label={'apples':'apple','oranges':'orange'}.get(label,label)
            predictions.append(dict(label=label,confidence=round(float(box.conf.item()),4),box=[round(float(v),1) for v in box.xyxy[0].tolist()]))
        return predictions

@dataclass
class Campaign:
    phase:int=0
    score:int=0
    harvested:set=field(default_factory=set)
    scans:int=0
    correct:int=0
    wrong:int=0
    history:list=field(default_factory=list)
    reports:list=field(default_factory=list)
    finished:bool=False
    revision:int=0
    combo:int=0
    best_combo:int=0
    fooled:int=0
    last_seen:float=field(default_factory=time.time)

    @property
    def done(self): return self.scans>=MAX_SCANS or (self.scans>0 and len(self.harvested)==PHASES[self.phase]['count'])
    def state(self):
        self.last_seen=time.time()
        return dict(phase=self.phase,phase_count=len(PHASES),combo=self.combo,best_combo=self.best_combo,fooled=self.fooled,decoys=len(PHASES[self.phase]['decoys']),score=self.score,harvested=len(self.harvested),total=PHASES[self.phase]['count'],scans=self.scans,max_scans=MAX_SCANS,correct=self.correct,wrong=self.wrong,precision=round(100*self.correct/(self.correct+self.wrong),1) if self.correct+self.wrong else None,done=self.done,finished=self.finished,revision=self.revision,events=self.history[-1]['events'] if self.history else [],reports=self.reports)
    def scan(self,detector,model,confidence):
        if self.done or self.finished: raise ValueError('This phase has ended. Continue to the next phase.')
        start=time.perf_counter()
        predictions=detector.predict(render(self.phase,self.harvested),model,confidence)
        remaining=[f for f in scene_data(self.phase)[1] if f['id'] not in self.harvested]
        events=match_detections(predictions,remaining,decoys=decoy_data(self.phase))
        for e in events:
            self.score+=e['points']
            if e['correct']:
                self.harvested.add(e['fruit_id']); self.correct+=1; self.combo+=1
                self.best_combo=max(self.best_combo,self.combo)
            elif e['scored']:
                self.wrong+=1; self.combo=0
                if e['reason']=='decoy': self.fooled+=1
        self.scans+=1; self.revision+=1
        self.history.append(dict(phase=self.phase+1,scan=self.scans,model=model,confidence=confidence,latency_ms=round((time.perf_counter()-start)*1000),events=events,combo=self.combo))
        return {**self.state(),'latency_ms':self.history[-1]['latency_ms'],'delta':sum(e['points'] for e in events)}
    def advance(self):
        if not self.done or self.finished: raise ValueError('Finish the current phase before continuing.')
        self.reports.append(dict(phase=self.phase+1,name=PHASES[self.phase]['short'],harvested=len(self.harvested),total=PHASES[self.phase]['count'],scans=self.scans,wrong=sum(not e['correct'] and e['scored'] for scan in self.history if scan['phase']==self.phase+1 for e in scan['events'])))
        if self.phase==len(PHASES)-1: self.finished=True
        else: self.phase+=1; self.harvested=set(); self.scans=0
        self.revision+=1
        return self.state()
