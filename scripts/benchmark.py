"""Reproduce a complete real-inference run without opening a browser."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from game import Campaign, Detector, PHASES

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--confidence',type=float,default=.5)
    parser.add_argument('--model',default='yolov8n.pt')
    args=parser.parse_args()
    if not .05<=args.confidence<=.95:parser.error('confidence must be between 0.05 and 0.95')
    campaign=Campaign(); detector=Detector()
    while not campaign.finished:
        while not campaign.done:
            result=campaign.scan(detector,args.model,args.confidence)
            print(f"{campaign.phase+1:02d} | leitura {campaign.scans} | "
                  f"{PHASES[campaign.phase]['short']} | "
                  f"colhidas {result['harvested']}/{result['total']} | "
                  f"saldo {result['delta']:+d}",flush=True)
        campaign.advance()
    print(f"Total: {campaign.score} pontos; {campaign.correct} acertos; "
          f"{campaign.wrong} falsos positivos; {campaign.fooled} confusões com iscas.")
