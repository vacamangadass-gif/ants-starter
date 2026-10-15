# micro-bc

micro 级别 Ants 策略模型。

| | |
|---|---|
| 重量级别 (Weight class) | **micro** —— 54,426 / 131,072 字节（占上限的 42%） |
| 参数量 | 24,077（Float16 初始化参数） |
| 网络架构 | `Trunk` 架构，各方向感受野为 **15 个单元格**（空洞率 dilations [1, 2, 4, 8]） |
| 训练方法 | 行为克隆，在 250,000 席位回合上训练 5 个 epoch，保留验证集吻合率 93.8% |
| Adapter 运算量 | 最坏参考情形下 229,415 / 1,000,000 次操作 |
| 推理耗时 | 最坏参考情形下 34.58 ms —— 占单个席位 1000 ms 回合预算的 **3.5%** |
| 算子集 | Cast, Concat, Constant, Conv, Relu, Slice |
| 评测引擎 | `sha256:eead45ca770f5626d1787066bc00522687989101d4bf29ab3ec6ecb712755535` |
| 模型哈希 | `sha256:1e51646a3987eb7844a7cd8e9c3f12f36d2a5d5a678286d856ac1c1be9801268` |
| Manifest 哈希 | `sha256:4085e3b697ca43d90d54ae18510ab88090df8f363dc4e59a5c85edc166aa640b` |

复现命令：

```sh
python -m tb_baselines.collect --seat-turns 250000 --out data/teacher.jsonl.gz
python -m tb_baselines.train.bc --class micro --data data/teacher.jsonl.gz --epochs 5 --out runs/micro-bc
python -m tb_baselines.export --class micro --weights runs/micro-bc/best.pt --out models/micro-bc
```

推理时间是在执行准入检查的具体机器上测量的，**仅用于汇报，绝非准入门槛**：平台本身并未设定算力上限。之所以列出该项，是因为如果计算图开销过大，在实际对局中很容易触碰回合截止时间（turn deadline）；每个席位的份额就是整回合的时间 —— 每个席位每回合调用一次 `model_infer`，各自拥有独立的超时截止时间。

**评测引擎（Measured on）** 是指读取上述指标时所针对的引擎版本，而不是需要严格匹配的固定值。starter 项目实际运行的是其 `games.toml` 中指定的 `engine`，它会随着 ants 的每次发布而更新；上述数值针对此处注明的引擎真实有效，且不会随引擎发布而重复测量，因为引擎变化时模型本身并没有变。如需获取当前最新的指标数值，可通过自行运行 `tinybrains check` 读取。
