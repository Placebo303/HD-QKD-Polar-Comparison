"""CLI for the separately authorized NBLDPC v3 synthetic lane."""
from __future__ import annotations
import argparse
from ..formal_ir import nonbinary_v3_qualification as lane
def main():
    parser=argparse.ArgumentParser();parser.add_argument("action",choices=("plan","execute","verify"));args=parser.parse_args()
    if args.action=="plan":lane.create_plan()
    elif args.action=="execute":lane.run()
    else:print(lane.verify())
if __name__=="__main__":main()
