"""Parse PFSP benchmark files and dataset split definitions."""

import os


# =========================
# OR-Library parser
# =========================
def parse_orlib_file(path):
    """Parse one OR-Library PFSP text file into instance dictionaries."""
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
                times = parts[1::2]  # (machine, time)
                proc_times.append(times)
                i += 1

            instances.append({
                "name": name,
                "n_jobs": n_jobs,
                "n_machines": n_machines,
                "proc_times": proc_times
            })

        else:
            i += 1

    return instances


# =========================
# Taillard parser
# =========================
def parse_taillard_file(path):
    """Parse a Taillard PFSP text file into job-by-machine instances."""
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

            # 转换为 job x machine
            proc_times = list(map(list, zip(*proc_times)))

            instances.append({
                "name": f"{os.path.basename(path)}_{instance_id}",
                "n_jobs": n_jobs,
                "n_machines": n_machines,
                "proc_times": proc_times
            })

        else:
            i += 1

    return instances


# =========================
# Simple parser（兜底）
# =========================
def parse_simple_instance(path):
    """Parse the fallback plain matrix format used by small local examples."""
    with open(path, "r") as f:
        lines = f.readlines()

    rows = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        try:
            row = [int(x) for x in line.split()]
            if len(row) > 0:
                rows.append(row)
        except:
            continue

    if len(rows) == 0 or len(rows[0]) < 2:
        raise ValueError(f"Invalid simple format: {path}")

    n_jobs, n_machines = rows[0][:2]
    proc_times = rows[1:1+n_jobs]

    return [{
        "name": os.path.basename(path).replace(".txt", ""),
        "n_jobs": n_jobs,
        "n_machines": n_machines,
        "proc_times": proc_times
    }]


# =========================
# 自动识别 parser
# =========================
def load_instances_from_file(path, format_hint=None):
    """Infer a supported PFSP file format and return parsed instances."""
    try:
        with open(path, "r") as f:
            head = f.read(300)

        if "instance" in head:
            return parse_orlib_file(path)

        elif "number of jobs" in head:
            return parse_taillard_file(path)

        else:
            # The simple parser is intentionally last: it accepts many numeric
            # files, so trying it earlier could misread structured benchmarks.
            return parse_simple_instance(path)

    except Exception as e:
        # One malformed benchmark should not stop batch experiments over a whole
        # directory; the warning keeps the skipped file visible in logs.
        print(f"[WARNING] Skipping {path}: {e}")
        return []


# =========================
# 递归读取目录
# =========================
def load_instances_from_dir(raw_dir, format_hint=None):
    """Recursively load all ``.txt`` PFSP instances under ``raw_dir``."""
    instances = []

    for root, _, files in os.walk(raw_dir):
        for fname in files:
            if not fname.endswith(".txt"):
                continue

            path = os.path.join(root, fname)

            file_instances = load_instances_from_file(path, format_hint)
            print(f"[INFO] {fname}: {len(file_instances)} instances")

            instances.extend(file_instances)

    print(f"\nTotal instances loaded: {len(instances)}")
    return instances


# =========================
# split loader（供 experiments 用）
# =========================
def load_dataset_splits(raw_dir, splits_dir, format_hint=None):
    """Load all raw instances and return train/val/test lists by split files."""
    all_instances = load_instances_from_dir(raw_dir, format_hint)

    # Split files store stable names instead of serialized instances so raw data can
    # be refreshed without rewriting the train/validation/test definitions.
    name_to_instance = {inst["name"]: inst for inst in all_instances}

    def load_split(file):
        """Load one split-name file and resolve names to parsed instances."""
        path = os.path.join(splits_dir, file)
        if not os.path.exists(path):
            return []

        with open(path, "r") as f:
            names = [line.strip() for line in f]

        return [name_to_instance[n] for n in names if n in name_to_instance]

    return {
        "train": load_split("train.txt"),
        "val": load_split("val.txt"),
        "test": load_split("test.txt"),
    }
