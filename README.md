# ants-starter

一个开箱即用、无需修改即可提交的 TinyBrains 参赛模型，以及一条重新训练它的命令。

```sh
brew tap tiny-brains/cli https://github.com/Tiny-Brains/cli    # 仅需执行一次
brew install tiny-brains/cli/tinybrains                         # 仅需执行一次
git clone https://github.com/Tiny-Brains/ants-starter && cd ants-starter

tinybrains check model.onnx manifest.json      # 查看准入检查结果
tinybrains matches/self-play.json              # 自对弈测试，通过真实引擎运行
tinybrains view replays/self-play.json         # 观看回放
python train.py                                # 重新训练：采集、克隆、导出 —— 约耗时半小时
```

该参赛模型属于 **nano** 级别（天梯运行的最小级别），采用与 `models/` 中模型相同的方式训练：由脚本教师策略进行对弈，从其移动轨迹中克隆出一个小型卷积策略；导出时生成 `model.onnx`、描述它的 `manifest.json`、包含平台度量指标的 `metrics.json` 以及记录具体数值的 `card.md`。它是用独立的随机种子训练的，因此具有专属权重，天梯会将其视为全新的参赛作品。

`models/` 包含了 **4 个训练好的对手模型供测试使用**：`nano-bc`、`micro-bc`（将同一教师策略蒸馏至更高一级的 micro 级别的模型）、`micro-percell`（仅能观察单个单元格的弱对照组模型）以及 `nano-bc-max-r` —— **一个带有记忆机制的 nano 模型**：它拥有两个棋盘平面（已看到的食物和已看到的敌方蚁丘），每回合由它写入并在下一回合由运行器传回；该模型从能够读取这些记忆的教师模型克隆而来（敌方蚁丘一旦被发现便持续作为目标）。它是这里最强的 nano 模型。它们是平台在任何地方保留的仅有预训练模型；每个赛季用于对战的基准线（baselines）由管理员选择并上传，可能是这些模型，也可能包含其他模型。

## 包含内容

| 文件                            | 说明                                                                                                                                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model.onnx`                  | 训练好的策略模型。使用 Float16 初始化器，使用时转为 Float32。                                                                                                                         |
| `manifest.json`               | 平台运行计算图的配置声明：声明的输入和输出，以及每个输入对应的**adapter** 表达式（用于将观测数据转换为张量）。自动生成，切勿手动编辑。                                          |
| `metrics.json`, `card.md`   | 平台对该参赛模型的度量指标，以及文本形式的详细数值报告。                                                                                                                              |
| `train.py`                    | 封装为单条命令的完整训练配方，基于[baselines 库](https://github.com/Tiny-Brains/ants/tree/main/baselines)。                                                                            |
| `models/`                     | 4 个训练好的对手模型，每个均包含`model.onnx`、`manifest.json`、`metrics.json` 和 `card.md`：`nano-bc`、`micro-bc`、`micro-percell` 以及带记忆机制的 `nano-bc-max-r`。 |
| `matches/`                    | 3 个对局配置文件：本模型自对弈、对战`models/nano-bc`、对战 `models/nano-bc-max-r`。均在离线状态下运行。                                                                           |
| `games.toml`                  | 游戏卡带来源配置：固定版本（pinned release）的 Ants 卡带，仅需下载一次并通过摘要哈希校验。                                                                                            |
| `.github/workflows/check.yml` | 每次推送时运行`tinybrains check` 和对局测试，防止意外修改 manifest 导致问题，可在产生该修改的提交上及时捕获。                                                                       |

## 前置要求

`tinybrains` —— 如上通过 Homebrew 安装，或从其 [最新发布页面](https://github.com/Tiny-Brains/cli/releases/latest) 下载适用于你平台的归档包 —— 以及克隆本仓库即可：**除本仓库外无需其他仓库，也无需 Rust 工具链**。游戏本身并不在本仓库中，也不在此构建：`games.toml` 通过归档包与引擎的两个摘要哈希固定了 Ants 卡带的特定版本，首次需要它的命令会自动下载至 CLI 缓存（Linux 上为 `~/.cache/tinybrains/`，macOS 上为 `~/Library/Caches/tinybrains/`），若两者摘要不匹配则会拒绝使用。运行 `python train.py` 则额外需要 Python 环境并执行 `pip install -r requirements.txt`（会从 git 安装 baselines 库）。

## 开始使用与自定义

1. **运行对局。** 执行 `tinybrains matches/self-play.json`，然后执行 `tinybrains view replays/self-play.json`。蚂蚁应该开始移动。`matches/vs-nano-bc.json` 用于与 `models/nano-bc` 对战，`matches/vs-nano-bc-max-r.json` 用于与带记忆模型对战；也可以将席位指向 `models/micro-bc` 挑战更强的对手。
   这三场比赛均运行在 `basic-tiny-2p` 地图上，这是发行版附带的 5 张基础地图之一（可通过 `tinybrains maps` 查看）；赛季专用的地图会发布在网站上，对局文件可以通过路径指定地图。如需使用其他地图或更换对手，编辑对局文件即可 —— 手册中的 [match files](https://github.com/Tiny-Brains/web/blob/main/docs/src/models/testing.md#match-files) 章节列出了每个字段的说明。
2. **修改配置并重新训练。** `train.py` 支持 `--class`、`--epochs`、`--seed` 和 `--memory` 参数。其中 `--memory` 会按 `models/nano-bc-max-r` 的方式训练模型：教师策略将每个席位记住的内容读入独立的数据集（`data/teacher-memory.jsonl.gz`），模型据此携带这两个记忆平面。记忆机制本身需要开销：每个棋盘单元格占用 2 字节，只有该级别的空间预算允许时，赛季准入才会接纳它；`tinybrains check` 会打印出具体开销。底层训练方案是 `tb_baselines`，其 [README](https://github.com/Tiny-Brains/ants/tree/main/baselines) 说明了各项旋钮参数测量的指标。宽度（width）、深度（depth）和 float16 是决定模型级别的核心调节因素。不同的编码方式意味着不同的 adapter，而 manifest 是从相同的训练代码中生成的 —— [这是唯一真正关键的测试](https://github.com/Tiny-Brains/ants/tree/main/baselines#the-one-test-that-matters)。
3. **按准入标准进行检查。** 运行 `tinybrains check model.onnx manifest.json`。通过检查是必要条件但非充分条件：你的本地机器无法最终决定模型所属级别。
4. **提交与上传。** 使用 `shasum -a 256 model.onnx manifest.json` 获取两个文件的哈希值，并在网站上提交。提交后将返回 **两个一次性上传 URL**；通过 `PUT` 请求将这两个文件上传，准入系统便会接管后续流程。手册中的 [快速入门（quickstart）](https://github.com/Tiny-Brains/web/blob/main/docs/src/quickstart.md) 提供了详尽说明。

## 核心准则

- **`manifest.json` 必须由程序生成。** 手动编辑会导致训练时见到的编码与天梯运行时使用的编码发生脱节，而且脱节时不会报错：仅仅是最终评分低于训练所承诺的表现。如需修改，请调整 `ants/baselines` 中的 `planes.py` 并重新生成。
- **此处的内容都不是硬编码规则。** 地图、预算和截止时间均来自卡带，并在每次运行时打印；对局配置文件中的 `max_turns` 是唯一的本地覆盖项，用于确保本地对局简短快速。
- **这四个文件必须配套提供。** 模型与其 manifest 作为一对进行哈希与度量 —— 级别（weight class）由工件字节数加上 manifest 字节数共同决定 —— 而 card 和 metrics 则记录了该组合的具体评测数据。

Apache-2.0 协议：详见 [LICENSE](LICENSE)。
