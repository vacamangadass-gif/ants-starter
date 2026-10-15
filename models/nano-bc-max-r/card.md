# nano-bc-max-r

nano 级别 Ants 策略模型。

| | |
|---|---|
| 重量级别 (Weight class) | **nano** —— 13,735 / 16,384 字节（占上限的 84%） |
| 参数量 | 3,170（Float16 初始化参数） |
| 网络架构 | `Trunk + max memory`，各方向感受野为 **15 个单元格**（空洞率 dilations [1, 2, 4, 8]） |
| 训练方法 | 基于带记忆教师标签的行为克隆，通过 `Max` 算子维护 `planes.MEMORY`，在 250,000 席位回合上训练 5 个 epoch，保留验证集吻合率 81.8% |
| Adapter 运算量 | 最坏参考情形下 208,423 / 1,000,000 次操作 |
| 推理耗时 | 最坏参考情形下 11.91 ms —— 占单个席位 1000 ms 回合预算的 **1.2%** |
| 算子集 | Cast, Concat, Constant, Conv, Gather, Max, Relu, Slice |
| 评测引擎 | `sha256:8ebceb4a67ce8656f4eab53bd389905c1b9aecd4dcdc6576086d5baf31709554` |
| 模型哈希 | `sha256:0765a4e242750e982d7268f829f2b1eb9d2fc082ea40a2bd273d25e369e0794d` |
| Manifest 哈希 | `sha256:e4641e8f6fa3d7da8bb65b998f1d33840e164c0c2e1768677437a64ff37256e7` |
| 记忆开销 (Memory) | `2` 个 `i8` 平面（已见食物 food_seen、已见敌方蚁丘 hill_foe_seen），每单元格 2 字节：在最大地图上需 29,760 字节。赛季的对应级别必须允许该开销；`check` 通过链式连续 202 个观测验证了状态往返传递回路 |

复现命令：

```sh
python -m tb_baselines.collect --remember --seat-turns 250000 --out data/teacher-memory.jsonl.gz
python -m tb_baselines.train.bc --class nano --memory --data data/teacher-memory.jsonl.gz --epochs 5 --out runs/nano-bc-max-r
python -m tb_baselines.export --class nano --weights runs/nano-bc-max-r/best.pt --out models/nano-bc-max-r
```

推理时间是在执行准入检查的具体机器上测量的，**仅用于汇报，绝非准入门槛**：平台本身并未设定算力上限。之所以列出该项，是因为如果计算图开销过大，在实际对局中很容易触碰回合截止时间（turn deadline）；每个席位的份额就是整回合的时间 —— 每个席位每回合调用一次 `model_infer`，各自拥有独立的超时截止时间。

**评测引擎（Measured on）** 是指读取上述指标时所针对的引擎版本，而不是需要严格匹配的固定值。starter 项目实际运行的是其 `games.toml` 中指定的 `engine`，它会随着 ants 的每次发布而更新；上述数值针对此处注明的引擎真实有效，且不会随引擎发布而重复测量，因为引擎变化时模型本身并没有变。如需获取当前最新的指标数值，可通过自行运行 `tinybrains check` 读取。
