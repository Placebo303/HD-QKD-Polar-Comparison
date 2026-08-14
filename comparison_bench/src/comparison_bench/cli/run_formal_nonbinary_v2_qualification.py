"""CLI for the separately authorized NBLDPC v2 synthetic lane."""
from __future__ import annotations
import argparse
from ..formal_ir import nonbinary_v2_qualification as lane
def main():
 p=argparse.ArgumentParser();p.add_argument("action",choices=("plan","execute","verify"));a=p.parse_args()
 if a.action=="plan": lane.create_plan()
 elif a.action=="execute": lane.run()
 else: print(lane.verify())
if __name__=="__main__":main()
