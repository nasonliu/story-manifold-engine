#!/usr/bin/env python3
import argparse
from novel_pipeline import extract_skeleton

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('text')
    p.add_argument('--title', default='Unknown')
    args = p.parse_args()
    sk = extract_skeleton(args.text, args.title)
    print(sk)
