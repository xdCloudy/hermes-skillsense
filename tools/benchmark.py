"""Reproducible synthetic microbenchmark (not an accuracy guarantee)."""
import random
import statistics
import time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import BM25Index,Document

def main():
    docs=[Document(f"skill-{i}",f"skill {i} workflows topic-{i%31} tools terminal data") for i in range(500)]
    index=BM25Index(docs)
    prompts=["terminal data workflows","tools skill 10","topic-4 workflows","build website and css"]
    timings=[]
    random.seed(43)
    for i in range(2000):
        prompt=random.choice(prompts)
        start=time.perf_counter_ns()
        index.search(prompt,limit=3)
        timings.append((time.perf_counter_ns()-start)/1_000_000)
    values=sorted(timings)
    print(f"Synthetic BM25 microbenchmark: 500 skills, 2000 queries")
    print(f"p50={statistics.median(values):.3f}ms p95={values[int(len(values)*.95)]:.3f}ms "
          f"p99={values[int(len(values)*.99)]:.3f}ms")
    print("This tests the isolated BM25 core, not Hermes end-to-end quality.")
if __name__=="__main__":
    main()
