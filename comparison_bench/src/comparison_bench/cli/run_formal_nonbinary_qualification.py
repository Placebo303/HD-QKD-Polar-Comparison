"""CLI wrapper for the frozen N3 nonbinary formal qualification lane."""
from __future__ import annotations
import argparse
from pathlib import Path
from ..formal_ir import nonbinary_qualification as lane

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("action", choices=("plan","execute","verify"))
    a=p.parse_args()
    if a.action=="plan": lane.create_plan()
    elif a.action=="execute": lane.run()
    else: print(lane.verify())
if __name__=="__main__": main()
