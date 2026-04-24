import json, os, csv, pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon

from core.parser import load_instances_from_dir
from core.evaluator import evaluate_priority_function
from llm.sandbox import load_priority_function

# ── 1. 加载测试实例 ──────────────────────────────────
print("加载实例...")
all_instances = load_instances_from_dir("data/raw")

with open("data/splits/test.txt") as f:
    test_names = {line.strip() for line in f}

test_instances = [inst for inst in all_instances if inst["name"] in test_names]
print(f"测试实例数: {len(test_instances)}")

# ── 2. 提取最优程序 ──────────────────────────────────
def load_best_code(pop_file):
    with open(pop_file) as f:
        pop = json.load(f)
    # 选择 score 最高的候选 (makespan 越小 score 越大)
    best = max(pop, key=lambda c: c["score"])
    print(f'从 {pop_file} 提取最优程序, score={best["score"]:.1f}')
    return best["code"]

code_direct = load_best_code("results/logs/direct/direct_population.json")
code_thought = load_best_code("results/logs/thought/thought_population.json")

# ── 3. 加载为可调用函数 ──────────────────────────────
fn_direct = load_priority_function(code_direct)
fn_thought = load_priority_function(code_thought)

# ── 4. 在测试集上评估 ────────────────────────────────
print("\n评估 Direct FunSearch ...")
summary_direct = evaluate_priority_function(
    "direct_funsearch", test_instances, fn_direct, maximize=True
)

print("评估 Thought-Augmented FunSearch ...")
summary_thought = evaluate_priority_function(
    "thought_funsearch", test_instances, fn_thought, maximize=True
)

# ── 5. 保存 CSV ──────────────────────────────────────
os.makedirs("results/tables", exist_ok=True)

def save_csv(summary, filename):
    with open(filename, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["instance","method","sequence","makespan","runtime_sec","reference","gap_percent"])
        w.writeheader()
        for r in summary.results:
            w.writerow(r.to_dict())
    print(f"已保存 {filename}")

save_csv(summary_direct, "results/tables/direct_test_24.csv")
save_csv(summary_thought, "results/tables/thought_test_24.csv")

# ── 6. 合并 & 对比 ───────────────────────────────────
baseline = pd.read_csv("results/tables/baseline_test_real.csv")

df_d = pd.read_csv("results/tables/direct_test_24.csv")[["instance","makespan"]].rename(
    columns={"makespan": "Direct_FunSearch"}
)
df_t = pd.read_csv("results/tables/thought_test_24.csv")[["instance","makespan"]].rename(
    columns={"makespan": "Thought_FunSearch"}
)

df_all = baseline.merge(df_d, on="instance").merge(df_t, on="instance")
df_all.to_csv("results/tables/full_comparison.csv", index=False)
print(f"\n合并后实例数: {len(df_all)}")
print(df_all.head())

# 汇总统计
algos = ["random","spt","lpt","neh","Direct_FunSearch","Thought_FunSearch"]
print("\n===== 汇总统计 =====")
print(df_all[algos].describe().T[["mean","50%","min","max"]])

# ── 7. 柱状图 ────────────────────────────────────────
avg = df_all[algos].mean()
plt.figure(figsize=(10,6))
bars = plt.bar(algos, avg.values,
               color=["gray","gray","gray","gray","steelblue","darkorange"])
plt.ylabel("Average Makespan")
plt.title("Heuristics Comparison on 24 Test Instances")
for b, v in zip(bars, avg.values):
    plt.text(b.get_x()+b.get_width()/2, v+5, f"{v:.0f}", ha="center", fontsize=9)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
os.makedirs("results/figures", exist_ok=True)
plt.savefig("results/figures/avg_makespan.png", dpi=150)
plt.show()

# ── 8. 箱线图 ────────────────────────────────────────
plt.figure(figsize=(12,6))
df_all[algos].boxplot()
plt.ylabel("Makespan")
plt.title("Makespan Distribution")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("results/figures/boxplot.png", dpi=150)
plt.show()

# ── 9. Wilcoxon 检验 ─────────────────────────────────
stat, p = wilcoxon(df_all["Thought_FunSearch"], df_all["neh"])
print(f"\nWilcoxon Thought vs NEH: stat={stat:.2f}, p={p:.4f}")
print("✅ 显著" if p < 0.05 else "⚠️ 不显著")

stat_d, p_d = wilcoxon(df_all["Direct_FunSearch"], df_all["neh"])
print(f"Wilcoxon Direct vs NEH: stat={stat_d:.2f}, p={p_d:.4f}")
print("✅ 显著" if p_d < 0.05 else "⚠️ 不显著")

stat_td, p_td = wilcoxon(df_all["Thought_FunSearch"], df_all["Direct_FunSearch"])
print(f"Wilcoxon Thought vs Direct: stat={stat_td:.2f}, p={p_td:.4f}")
print("✅ 显著" if p_td < 0.05 else "⚠️ 不显著")

print("\n🎉 完成！图表在 results/figures/，对比表在 results/tables/full_comparison.csv")