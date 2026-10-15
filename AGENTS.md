# AGENTS.md - TinyBrains Ants-Starter 开发与协作指南

本文档为在 `ants-starter` 项目中工作的 AI Agent 和开发者提供完整的项目背景、架构设计、技术约束与开发规范。后续所有开发任务必须遵循本文档中的规则。

---

## 1. 项目概览

`ants-starter` 是 [TinyBrains](https://github.com/Tiny-Brains) 平台下 **Ants（蚂蚁对战）** 比赛的官方入门参赛模板库。

- **竞赛性质**：强化学习与博弈对抗。参赛者提交一个训练好的神经网络策略（ONNX 格式）和输入输出规范清单（manifest.json），参与 TinyBrains 平台天梯（Ladder）系统的自动化对局与评级。
- **项目定位**：开箱即用的参赛模板。包含一份可直接提交的 **nano** 级别基线模型，以及完整的离线对战、行为克隆重训（Behavioral Cloning, BC）和模型导出工作流。
- **提交形式**：计算 `model.onnx` 与 `manifest.json` 的 SHA256 哈希并在平台登记，通过平台返回的一次性 URL 上传这两个文件。

---

## 2. 技术栈与环境依赖

| 层次 | 技术 / 工具 | 说明 |
|---|---|---|
| **平台 CLI** | `tinybrains` (CLI >= 0.5.0) | 核心执行与验证工具，负责准入检查（`check`）、对战仿真与回放渲染。 |
| **模型格式** | ONNX (opset 17, `orion:model@1.0.0`) | 权重以 Float16 存储，运行时 Cast 为 Float32；输入输出基于张量接口。 |
| **训练技术栈** | Python 3.10+ / PyTorch / NumPy | 依赖 `tb-baselines`（位于 `Tiny-Brains/ants` 仓库的 `baselines/` 子目录）。 |
| **游戏引擎** | Ants 游戏卡带 (Cartridge) | 游戏核心逻辑在卡带中，由 `games.toml` 指定 release 与摘要，CLI 自动缓存执行。 |
| **CI / CD** | GitHub Actions (`.github/workflows/check.yml`) | 推送或 PR 时自动运行 CLI 准入测试和自对弈/基线对战。 |

---

## 3. 项目目录与文件职责

```text
ants-starter/
├── .github/workflows/
│   └── check.yml           # CI 配置：安装 tinybrains CLI，运行 check 与 match
├── matches/                # 离线对局测试配置文件
│   ├── self-play.json      # 模型自身对弈 (2p)
│   ├── vs-nano-bc.json     # 与基线 nano-bc 对弈
│   └── vs-nano-bc-max-r.json # 与带记忆的 nano-bc-max-r 对弈
├── models/                 # 平台预置基线对手（供本地对战评测）
│   ├── nano-bc/            # 基础 nano 级别模型
│   ├── micro-bc/           # 蒸馏升级的 micro 级别模型
│   ├── micro-percell/      # 单单元格感知的弱对照组模型
│   └── nano-bc-max-r/      # 带记忆状态（2 个棋盘平面）的高强度 nano 模型
├── card.md                 # 当前交付模型的指标卡片与复现命令
├── games.toml              # 游戏卡带版本固定配置（release、artifacts 与 engine digest）
├── manifest.json           # 平台计算图配置（声明输入适配器 adapter、输出及 shape）
├── metrics.json            # 平台对当前模型的各项静态和性能测量指标
├── model.onnx              # 当前交付的 ONNX 模型权重文件
├── requirements.txt        # Python 依赖声明（引用 Tiny-Brains/ants 下的 baselines）
├── train.py                # 一键重训脚本（采集、训练、导出完整流程）
└── README.md               # 项目使用说明
```

---

## 4. 核心交付物（Four-File Bundle）

根目录下的以下四个文件构成一个严格配套的交付单元：

1. **`model.onnx`**：导出的策略网络。
2. **`manifest.json`**：输入输出契约及 observation -> tensor 的 adapter 表达式。
3. **`metrics.json`**：准入系统评估出的尺寸、参数量、adapter 算力复杂度、最坏推理时延等指标。
4. **`card.md`**：指标总结与复现参数记录。

> **重要规则**：
> 平台将 `model.onnx` 和 `manifest.json` 成对度量。
> 模型所属的 **Weight Class（量级）** 依据 `artifact_bytes + manifest_bytes` 判定。

---

## 5. 核心开发规范与绝对约束

### 5.1 严禁手写 `manifest.json`
- **铁律**：`manifest.json` 必须由导出脚本（如 `tb_baselines.export`）自动生成。
- **原因**：手写极易造成训练时网络见到的特征编码与天梯引擎实际送入的特征编码出现细微偏移。引擎不会崩溃报错，但模型在天梯上的实际胜率会大幅劣化。若需修改特征平面，必须修改训练库中的编码定义并重新导出。

### 5.2 模型量级预算约束 (Weight Classes)
- **nano 级上限**：16,384 字节（16 KB）。当前模型约为 12,280 字节（占上限 75%）。
- **micro 级上限**：65,536 字节（64 KB）。
- 任何超额的模型在 `tinybrains check` 时均会被判定为更高量级或拒绝准入。
- 调优控制手段：通道宽度（width）、卷积层深度（depth）、Float16 参数量。

### 5.3 运行时开销约束
- **推理时延（Deadline）**：每个席位每回合有 1000 ms 的总时间预算。模型单步推理时延不能过长（当前基准约 8 ms，占 0.8%）。
- **Adapter 算力预算**：Adapter 最大操作数上限通常为 1,000,000 ops（当前基准约 229,415 ops）。

### 5.4 记忆机制（Memory Planes）的成本
- 使用 `--memory` 训练时，模型每回合写入 2 个平面（已见食物、已见敌方蚁丘）并在下一回合读取。
- **记忆成本**：每格子额外消耗 2 字节内存。只有当模型级别的空间预算允许时，天梯才接受该机制。

---

## 6. 常用命令与开发工作流

### 6.1 准入检查（Admission Check）
```bash
tinybrains check model.onnx manifest.json
```
*检查模型算子、尺寸量级、adapter 运算预算及最坏情况推理耗时。*

### 6.2 离线对弈测试与回放
```bash
# 运行自对弈
tinybrains matches/self-play.json

# 观看自对弈回放
tinybrains view replays/self-play.json

# 挑战预置基线
tinybrains matches/vs-nano-bc.json
tinybrains matches/vs-nano-bc-max-r.json
```

### 6.3 重新训练与导出
```bash
# 安装训练依赖
pip install -r requirements.txt

# 标准训练（nano 级别，5 个 epoch，耗时约 30 分钟）
python train.py

# 训练更高容量的 micro 级别模型
python train.py --class micro

# 训练带记忆机制的模型
python train.py --memory

# 复用已有采集数据集跳过数据收集阶段
python train.py --skip-collect
```

### 6.4 提交与上传准备
```bash
shasum -a 256 model.onnx manifest.json
```
将这两个哈希值填入 TinyBrains 网站申请上传，然后使用 `curl -T` 或 HTTP `PUT` 将文件传输至获得的一次性 URL。

---

## 7. 踩坑提示与环境诊断 (Troubleshooting)

1. **`tinybrains: connection refused` 或无法下载卡带**：
   - 原因：`tinybrains` 首次运行任何对战或检查时，需根据 `games.toml` 中的配置从 GitHub Releases 下载 `ants-artifacts.tar.gz` 到本地缓存（Linux: `~/.cache/tinybrains/`，macOS: `~/Library/Caches/tinybrains/`）。
   - 处理方式：确保网络可访问 GitHub，或将预下载的卡带文件放置于缓存目录，或配置 `TINYBRAINS_REGISTRY` 指向本地构建产物。
2. **`train.py` 报错 `unrecognized arguments: --repro`**：
   - 原因：`tb-baselines` 处于活跃开发状态，`train.py` 依赖携带 `--repro` 支持的新版基线代码。
   - 处理方式：确保安装最新版 `tb-baselines`，必要时克隆源码本地可编辑安装：`pip install -e <ants-repo>/baselines`。
3. **不要将中间产物加入版本控制**：
   - `data/`（数据集）、`runs/`（权重检查点）、`out/`（导出临时文件）及 `replays/`（对战回放）均已由 `.gitignore` 忽略，切勿强制提交。
