# ants-starter

nano 级别 Ants 策略模型。

| | |
|---|---|
| 重量级别 (Weight class) | **nano** —— 12,280 / 16,384 字节（占上限的 75%） |
| 参数量 | 3,006（Float16 初始化参数） |
| 网络架构 | `Trunk` 架构，各方向感受野为 **15 个单元格**（空洞率 dilations [1, 2, 4, 8]） |
| 训练方法 | 行为克隆，在 250,000 席位回合上训练 5 个 epoch，保留验证集吻合率 85.8%，随机种子 1 |
| Adapter 运算量 | 最坏参考情形下 229,415 / 1,000,000 次操作 |
| 推理耗时 | 最坏参考情形下 8.08 ms —— 占单个席位 1000 ms 回合预算的 **0.8%** |
| 算子集 | Cast, Concat, Constant, Conv, Relu, Slice |
| 评测引擎 | `sha256:eead45ca770f5626d1787066bc00522687989101d4bf29ab3ec6ecb712755535` |
| 模型哈希 | `sha256:17f9dfb7cd6bb1a4746cd5960a05765916bc775f5a37c9900ded0daac0a12f3a` |
| Manifest 哈希 | `sha256:58425bd6ee6a0cc7bd529c04eb36d62a09ff7e29f5ad38b3f06cb300f94c1db4` |

复现命令：

```sh
python train.py --class nano --epochs 5 --seed 1 --seat-turns 250000
```

推理时间是在执行准入检查的具体机器上测量的，**仅用于汇报，绝非准入门槛**：平台本身并未设定算力上限。之所以列出该项，是因为如果计算图开销过大，在实际对局中很容易触碰回合截止时间（turn deadline）；每个席位的份额就是整回合的时间 —— 每个席位每回合调用一次 `model_infer`，各自拥有独立的超时截止时间。
