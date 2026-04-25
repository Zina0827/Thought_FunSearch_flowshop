"""Build reproducible PFSP dataset split files from raw benchmark data."""

import os
import random
import argparse


# ======================
# OR-Library parser
# ======================
def parse_orlib_file(path):
    """Parse OR-Library PFSP instances for split-file generation."""
    instances = []

    with open(path, "r") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("instance"):
            name = line.split()[-1]

            i += 1
            while i < len(lines) and len(lines[i].strip().split()) != 2:
                i += 1

            if i >= len(lines):
                break

            n_jobs, n_machines = map(int, lines[i].strip().split())
            i += 1

            proc_times = []
            for _ in range(n_jobs):
                parts = list(map(int, lines[i].strip().split()))
                times = parts[1::2]
                proc_times.append(times)
                i += 1

            instances.append({
                "name": name,
                "proc_times": proc_times
            })

        else:
            i += 1

    return instances


# ======================
# Taillard parser
# ======================
def parse_taillard_file(path):
    """Parse Taillard PFSP instances for split-file generation."""
    instances = []

    with open(path, "r") as f:
        lines = f.readlines()

    i = 0
    instance_id = 0

    while i < len(lines):
        line = lines[i]

        if "number of jobs" in line:
            instance_id += 1

            i += 1
            parts = list(map(int, lines[i].split()))
            n_jobs, n_machines = parts[:2]

            i += 1  # skip "processing times"
            i += 1

            proc_times = []
            for _ in range(n_machines):
                row = list(map(int, lines[i].split()))
                proc_times.append(row)
                i += 1

            # 转置 → job x machine
            proc_times = list(map(list, zip(*proc_times)))

            instances.append({
                "name": f"{os.path.basename(path)}_{instance_id}",
                "proc_times": proc_times
            })

        else:
            i += 1

    return instances


# ======================
# 自动识别 parser
# ======================
def parse_file(path):
    """Dispatch to the supported parser based on file header text."""
    with open(path, "r") as f:
        head = f.read(200)

    if "instance" in head:
        return parse_orlib_file(path)
    elif "number of jobs" in head:
        return parse_taillard_file(path)
    else:
        print(f"[SKIP] Unknown format: {path}")
        return []


# ======================
# 递归读取
# ======================
def load_all_instances(data_dir):
    """Recursively parse all supported ``.txt`` benchmark files in a directory."""
    all_instances = []

    for root, _, files in os.walk(data_dir):
        for fname in files:
            if not fname.endswith(".txt"):
                continue

            path = os.path.join(root, fname)

            try:
                instances = parse_file(path)
                print(f"[INFO] {fname}: {len(instances)} instances")
                all_instances.extend(instances)
            except Exception as e:
                print(f"[WARNING] {fname}: {e}")

    return all_instances


# ======================
# split
# ======================
def split_instances(instances):
    """Shuffle instances and return train, validation, and test partitions."""
    random.shuffle(instances)

    n = len(instances)
    n_train = int(0.7 * n)
    n_val = int(0.15 * n)

    return (
        instances[:n_train],
        instances[n_train:n_train+n_val],
        instances[n_train+n_val:]
    )


def save_split(instances, path):
    """Write one split file containing an instance name per line."""
    with open(path, "w") as f:
        for inst in instances:
            f.write(inst["name"] + "\n")


# ======================
# main
# ======================
def main():
    """Parse CLI arguments and write train/validation/test split files."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--splits_dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.splits_dir, exist_ok=True)

    instances = load_all_instances(args.data_dir)

    print(f"\nTotal instances: {len(instances)}")

    train, val, test = split_instances(instances)

    save_split(train, os.path.join(args.splits_dir, "train.txt"))
    save_split(val, os.path.join(args.splits_dir, "val.txt"))
    save_split(test, os.path.join(args.splits_dir, "test.txt"))

    print("\nDone:")
    print(f"Train: {len(train)}")
    print(f"Val: {len(val)}")
    print(f"Test: {len(test)}")


if __name__ == "__main__":
    main()
