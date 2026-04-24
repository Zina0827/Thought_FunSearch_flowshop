import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 读取完整对比表
df = pd.read_csv("results/tables/full_comparison.csv")

# ── 1. 运行时间对比柱状图 ──
# 基准算法的运行时间可以从 baseline_results.csv 中获取，但你之前跑出的 baseline_test_real.csv
# 并没有记录时间。我们需要重新从 raw 数据中读取测试实例并记录运行时。
# 这里我写一个简单的时间采集脚本，直接用 build_schedule 模拟。
from core.parser import load_instances_from_dir
from core.scheduler import build_schedule
from core.makespan import compute_makespan
from heuristics.random_rule import RandomPriority
from heuristics.spt import SPTPriority
from heuristics.lpt import LPTPriority
from heuristics.neh import neh_sequence
from llm.sandbox import load_priority_function
import json, time

# 加载实例
all_inst = load_instances_from_dir("data/raw")
with open("data/splits/test.txt") as f:
    test_names = {line.strip() for line in f}
test_instances = [inst for inst in all_inst if inst["name"] in test_names]

# 定义算法和它们的评估函数
def run_random(proc):
    start = time.time()
    priority = RandomPriority(seed=42)
    seq = build_schedule(proc, priority, maximize=True)
    _ = compute_makespan(seq, proc)
    return time.time() - start

def run_spt(proc):
    start = time.time()
    priority = SPTPriority()
    seq = build_schedule(proc, priority, maximize=True)
    _ = compute_makespan(seq, proc)
    return time.time() - start

def run_lpt(proc):
    start = time.time()
    priority = LPTPriority()
    seq = build_schedule(proc, priority, maximize=True)
    _ = compute_makespan(seq, proc)
    return time.time() - start

def run_neh(proc):
    start = time.time()
    seq = neh_sequence(proc)
    _ = compute_makespan(seq, proc)
    return time.time() - start

# 加载 FunSearch 最优程序
with open("results/logs/direct/direct_population.json") as f:
    code_direct = max(json.load(f), key=lambda c: c["score"])["code"]
fn_direct = load_priority_function(code_direct)

with open("results/logs/thought/thought_population.json") as f:
    code_thought = max(json.load(f), key=lambda c: c["score"])["code"]
fn_thought = load_priority_function(code_thought)

def run_direct(proc):
    start = time.time()
    seq = build_schedule(proc, fn_direct, maximize=True)
    _ = compute_makespan(seq, proc)
    return time.time() - start

def run_thought(proc):
    start = time.time()
    seq = build_schedule(proc, fn_thought, maximize=True)
    _ = compute_makespan(seq, proc)
    return time.time() - start

# 收集平均时间
algo_names = ["Random", "SPT", "LPT", "NEH", "Direct FunSearch", "Thought FunSearch"]
runners = [run_random, run_spt, run_lpt, run_neh, run_direct, run_thought]
avg_times = []
for name, func in zip(algo_names, runners):
    times = []
    for inst in test_instances:
        proc = inst["proc_times"]
        t = func(proc)
        times.append(t)
    avg_times.append(np.mean(times))
    print(f"{name}: avg time = {avg_times[-1]:.5f} s")

# 画运行时间图
plt.figure(figsize=(10,6))
bars = plt.bar(algo_names, avg_times, color=["gray","gray","gray","gray","steelblue","darkorange"])
plt.ylabel("Average Runtime per Instance (seconds)")
plt.title("Runtime Comparison of Heuristics")
for b, v in zip(bars, avg_times):
    plt.text(b.get_x()+b.get_width()/2, v+0.0001, f"{v:.5f}s", ha="center", fontsize=8, rotation=0)
plt.yscale("log")  # 对数坐标，因为 Thought 可能慢很多
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("results/figures/runtime_comparison.png", dpi=150)
plt.show()

# ── 2. 按规模分组柱状图 ──
# 用实例名判断规模：包含 "500" 是大规模，"100" 是中规模，其余为小规模
def get_scale(name):
    if "500" in name: return "Large (500 j)"
    if "100" in name: return "Medium (100 j)"
    return "Small (<100 j)"

df["Scale"] = df["instance"].apply(get_scale)

# 分组计算平均
grouped = df.groupby("Scale")[algos].mean()
print("\n按规模分组平均 makespan：")
print(grouped)

# 画分组柱状图
grouped.plot(kind="bar", figsize=(12,6), color=["gray","gray","gray","gray","steelblue","darkorange"])
plt.ylabel("Average Makespan")
plt.title("Average Makespan by Problem Scale")
plt.xticks(rotation=0)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("results/figures/makespan_by_scale.png", dpi=150)
plt.show()

print("\n额外图表已保存至 results/figures/")