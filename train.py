#!/usr/bin/env python3
"""只需一条命令，即可按照平台基准模型的训练方式重新训练本参赛模型。

    pip install -r requirements.txt
    python train.py                    # 采集数据（约9分钟），训练 nano 模型 5 个 epoch（约20分钟），导出
    python train.py --class micro      # 相同的训练流程，但采用更高预算的 micro 级别
    python train.py --skip-collect     # 跳过采集，复用先前运行生成的 data/teacher.jsonl.gz
    python train.py --epochs 10 --seed 3
    python train.py --memory           # 相同的流程，但携带记忆机制：对应 models/nano-bc-max-r 的方案

在 Apple Silicon GPU 上训练 nano 级别大约耗时半小时，大部分时间花在 5 个 epoch 的训练上；在 CPU 上耗时会更长。

该脚本会在当前目录下生成 model.onnx、manifest.json、metrics.json 和 card.md 并替换现有自带文件，
同时在执行过程中打印平台的各项评测结论：尺寸指标、所归属的量级类别、adapter 最坏情况下的操作数以及推理耗时。

`--memory` 对应带记忆的基准模型 `models/nano-bc-max-r` 的训练配方：
教师策略在对战中读取各席位所记忆的信息（`collect --remember`，敌方蚁丘一经发现便始终作为目标）并写入独立的数据集
`data/teacher-memory.jsonl.gz`；策略模型则携带两个平面，并在回合交替时通过 `Max` 算子持续保留状态（`bc --memory`），
这些状态在每回合由运行器传回。训练输出保存在 `runs/<class>-bc-max-r`：包含行为克隆（BC）、`Max` 记忆机制以及带记忆教师的标注。
每个棋盘单元格启用记忆需额外消耗 2 字节内存，只有当赛季的对应级别预算允许该开销时才会被准入接纳。

本脚本背后的所有底层实现均来自 tb_baselines（github.com/Tiny-Brains/ants 仓库下的 baselines/）：
包含脚本规则教师策略、分别渲染为 NumPy 数组和 manifest adapter 的 7 平面特征编码、行为克隆算法，
以及内置运行 `tinybrains check` 的导出工具。本脚本仅仅是将这三条命令与当前仓库的路径串联在一起，
以确保其执行流程与基准模型的构建配方严格保持一致，杜绝任何实现漂移。
执行导出步骤时需要 PATH 中包含 `tinybrains` 命令（或通过 $TINYBRAINS 环境变量指定）：README.md 中说明了其安装来源。
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHIPPED = ["model.onnx", "manifest.json", "metrics.json", "card.md"]


def run(*module_and_args: str) -> None:
    cmd = [sys.executable, "-m", *module_and_args]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=HERE)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--class", dest="cls", default="nano", help="the weight class to aim at (default nano)")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--seed", type=int, default=7,
                    help="default 7, so a retrain has weights of its own; the shipped entry was "
                         "trained with seed 1, as card.md says")
    ap.add_argument("--seat-turns", type=int, default=250_000, help="how much of the teacher to collect")
    ap.add_argument("--memory", action="store_true",
                    help="carry a memory: the remembering teacher's dataset and a model that keeps "
                         "two planes by Max, as models/nano-bc-max-r was trained")
    ap.add_argument("--skip-collect", action="store_true",
                    help="reuse the dataset (data/teacher.jsonl.gz, or data/teacher-memory.jsonl.gz "
                         "with --memory)")
    a = ap.parse_args()

    if not (os.environ.get("TINYBRAINS") or shutil.which("tinybrains")):
        sys.exit("train.py: `tinybrains` is not on PATH (or named by $TINYBRAINS); the export "
                 "needs it. See README.md.")

    # The two recipes differ in three places: the teacher remembers, the dataset is its own file
    # (a row carries the state its seat remembered, and `bc --memory` refuses a dataset without
    # it), and the model carries the memory. Everything else is the same command.
    data = HERE / "data" / ("teacher-memory.jsonl.gz" if a.memory else "teacher.jsonl.gz")
    if a.skip_collect and not data.exists():
        sys.exit(f"train.py: --skip-collect, but {data} is not there")
    if not a.skip_collect:
        run("tb_baselines.collect", "--seat-turns", str(a.seat_turns), "--out", str(data),
            *(["--remember"] if a.memory else []))

    runs = HERE / "runs" / (f"{a.cls}-bc-max-r" if a.memory else a.cls) # 设置输出路径，如果带 memory 则加上-max-r后缀
    run("tb_baselines.train.bc", "--class", a.cls, "--epochs", str(a.epochs), "--seed", str(a.seed),
        "--data", str(data), "--out", str(runs), *(["--memory"] if a.memory else [])) # 核心训练指令，

    # The card names the entry after the export directory, and says how it was made from the
    # method string: the last epoch's held-out agreement comes off the run's own history.
    history = json.loads((runs / "history.json").read_text()) # 读取训练历史，包含每个 epoch 的指标
    agreement = history["epochs"][-1]["val_acc"] # 获取最后一轮验证集的准确率
    labels = ("behaviour cloning on the remembering teacher's labels, with `planes.MEMORY` kept by "
              "`Max`, " if a.memory else "behaviour cloning, ")
    method = (f"{labels}{a.epochs} epochs over {a.seat_turns:,} seat-turns, "
              f"{agreement:.1%} held-out agreement, seed {a.seed}") # 组合训练信息
    repro = shlex.join(["python", "train.py", *(["--memory"] if a.memory else []), "--class", a.cls,
                        "--epochs", str(a.epochs), "--seed", str(a.seed),
                        "--seat-turns", str(a.seat_turns)])
    out = HERE / "out" / HERE.name
    run("tb_baselines.export", "--class", a.cls, "--weights", str(runs / "best.pt"), "--out", str(out),
        "--method", method, "--repro", repro) # 格式转换，pt换成ONNX格式，存到 out 里

    for name in SHIPPED:
        shutil.copyfile(out / name, HERE / name) # 把 out 里的文件复制到 HERE 目录
    print(f"\nWrote {', '.join(SHIPPED)} into {HERE}. Next: `tinybrains matches/self-play.json`, then "
          "take the two hashes with `shasum -a 256 model.onnx manifest.json`, submit them on the site, "
          "and PUT the two files to the upload URLs the submission answers with.")


if __name__ == "__main__":
    main()
