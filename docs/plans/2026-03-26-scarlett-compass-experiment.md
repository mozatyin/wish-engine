# 斯嘉丽实验 — Wish Compass 验证案例

> 系统能否在斯嘉丽说出"我爱 Rhett"之前，检测到她对 Rhett 的隐藏感情？

**数据源**: `soulgraph/fixtures/scarlett_full.jsonl` (112 对话, 5 阶段)
**Ground Truth**: `soulgraph/fixtures/scarlett_intentions.json` (完整心理画像)

---

## 实验设计

### 方法

逐条喂入 `scarlett_full.jsonl` 的对话，模拟真实用户一次次和 SoulMap 聊天。每条对话后运行 Compass 的 Daily Scanner + Contradiction Detector，观察贝壳的诞生和成熟过程。

```
for each dialogue line in scarlett_full.jsonl:
    1. 更新 TriSoul（像真实用户一样积累）
    2. 运行 16 维检测器
    3. 运行 Compass Scanner
    4. 运行 Contradiction Detector
    5. 更新 Secret Vault
    6. 记录：发现了什么？置信度多少？
    7. 如果有触发条件：Trigger Engine 会展示什么？
```

### 核心验证目标

**目标贝壳：Scarlett→Rhett 隐藏感情**

| 阶段 | 对话 # | 预期系统行为 | Ground Truth |
|------|--------|------------|-------------|
| Phase 1 | 1-30 | 无贝壳（Rhett 刚出现，数据不足） | 1A: 斯嘉丽说爱 Ashley (0.95) |
| Phase 2 | 31-50 | **seed 诞生**：对 Rhett 情绪异常 | 2B: "Rhett 有吸引力但不认真" (0.6) |
| Phase 3 | 51-70 | **sprout**：危机时刻找 Rhett 模式 | 3D: "男人不可靠"但 Rhett 是例外 |
| Phase 4 | 71-95 | **bud**：可展示的洞察 | Ashley 意图降到 0.3，Rhett 行为模式稳定 |
| Phase 5 | 96-112 | **bloom**：在她说出前或同时成熟 | 斯嘉丽终于意识到爱 Rhett |

---

## Phase-by-Phase 预期信号

### Phase 1: Pre-War Belle (对话 1-30)

**表层**：
- "I know Ashley loves me" (line 2)
- "Why should Melanie get Ashley?" (line 3)
- "That horrible Rhett Butler was listening" (line 13)
- "Sir, you are no gentleman!" (line 14)

**系统应检测到**：
- Intention: 1A "赢得 Ashley" — 高置信度 (0.9+)
- Emotion: 对 Ashley 是 longing + frustration
- Emotion: 对 Rhett 是 anger + humiliation（但 arousal 异常高）

**贝壳状态**：无。但 Scanner 应该记录一个早期信号：
> Signal: "对 Rhett Butler 的 emotion arousal (0.7) 显著高于对其他男性角色 (avg 0.3)"
> 但只有 1 次数据点，不足以成为 seed

**关键 ground truth**：
> scarlett_intentions.json Phase 1, 1D: "If a man does not want me, something is wrong — I must fix it"
> Ashley 是自恋创伤，不是真爱。但系统此时无法确定这一点。

---

### Phase 2: War & Atlanta (对话 31-50)

**预期对话内容**：
- 守寡期间的烦躁
- 慈善舞会上与 Rhett 跳舞（打破丧服禁忌）
- Rhett 说"你不是淑女"— 她愤怒但兴奋
- Ashley 前线归来 — 重新追求

**系统应检测到**：

矛盾模式 #1 (嘴硬心软)：
```
stated: "Rhett Butler is not a gentleman, I don't care about him"
felt: emotion arousal spikes every time Rhett is mentioned
      arousal_rhett = 0.75, arousal_ashley = 0.45
→ 矛盾分数 = 0.75 - 0.45 = 0.30 (显著)
```

矛盾模式 #5 (情绪异常)：
```
baseline emotion when discussing men: valence 0.3, arousal 0.4
Rhett-specific: valence -0.2 (负面!), arousal 0.75 (极高!)
divergence = 0.55
→ 超过 threshold (0.3)
```

**贝壳诞生 → seed**：
```
Shell {
    pattern: "emotion_anomaly"
    topic: "Rhett Butler"
    confidence: 0.25
    evidence: [
        "arousal spike when Rhett mentioned (3 instances)",
        "stated negative but arousal positive",
        "chose to dance with Rhett despite social cost"
    ]
    stage: seed
}
```

**Ground Truth 印证**：
> 2B: "Rhett Butler is dangerously attractive but not a serious prospect" (0.6)
> 关键注释: "She is drawn to Rhett but files him under 'not a gentleman'"

---

### Phase 3: Siege & Survival (对话 51-70)

**预期对话内容**：
- 亚特兰大围城，独自接生 Melanie 的孩子
- Rhett 帮她逃离 → 然后抛弃她去参军
- "You're a fool, Rhett Butler!" — 愤怒掩盖的分离焦虑
- 回到 Tara，杀了入侵者
- "I'll never be hungry again"

**系统应检测到**：

矛盾模式 #2 (口是心非)：
```
stated: "I don't care if I never see Rhett again"
behavior: 危机时刻第一个想到的是 Rhett（不是 Ashley）
          Rhett 离开时的 emotion = rage + despair (arousal 0.9)
          Ashley 被俘时的 emotion = worry (arousal 0.5)
→ 行为与声明矛盾
```

矛盾模式 #3 (反复试探)：
```
Sessions mentioning Rhett: increasing frequency
Each time: explicit dismissal ("I don't need him")
But: emotional intensity when mentioning = increasing
→ 经典反复否认模式
```

**贝壳升级 → sprout**：
```
Shell update {
    confidence: 0.25 → 0.42
    new_evidence: [
        "crisis moment: sought Rhett not Ashley",
        "abandonment rage (Rhett leaving) > worry (Ashley captured)",
        "frequency of Rhett mentions increasing despite dismissals"
    ]
    stage: seed → sprout
    star_map: 极暗的星开始在星图上闪烁
}
```

**Ground Truth 印证**：
> 3D: "Men are unreliable — Rhett abandoned me" (0.8)
> 注释: "Rhett dumps her on the road to Tara. This betrayal deepens self-reliance."
> 关键：她对 Rhett 的"背叛"愤怒远超对 Ashley 被俘的担忧 — 这是爱的信号

---

### Phase 4: Reconstruction (对话 71-95)

**预期对话内容**：
- 为了保住 Tara 嫁给 Frank Kennedy（又一次工具婚姻）
- 经营木材厂，使用囚犯劳工
- Rhett 持续出现在她生活中，提供帮助
- Ashley 回来了但变得软弱
- 与 Rhett 的互动越来越多，越来越复杂

**系统应检测到**：

矛盾模式 #4 (价值矛盾)：
```
stated_value: "I love Ashley" (1A, now at 0.3 and falling)
actual_behavior:
  - 嫁给 Frank（不是 Ashley）为了钱
  - 遇到困难找 Rhett 帮忙（不是 Ashley）
  - Ashley 在身边时感到 "disappointed" 而非 "fulfilled"
  - Rhett 不在时感到 "restless"
→ 所有行为指向 Rhett，所有言语指向 Ashley
→ 价值矛盾分数 = 极高
```

矛盾模式 #1 (嘴硬心软) 加强：
```
Instances of "I don't love Rhett" or dismissals: 8+
Instances of emotion spike near Rhett: 12+
Ratio: 每次否认都伴随高 arousal
→ 否认频率本身就是信号
```

**贝壳升级 → bud**：
```
Shell update {
    confidence: 0.42 → 0.63
    new_evidence: [
        "chose Rhett for help consistently (Frank/money situation)",
        "Ashley proximity → disappointment, Rhett absence → restlessness",
        "denial frequency increasing = signal strength increasing",
        "multiple contradiction patterns converging on same topic"
    ]
    stage: sprout → bud
    star_map: 暗紫色星，隐隐脉动，用户可见
}
```

**触发时机 — Phase 4 关键时刻**：

当斯嘉丽讨论婚姻或关系选择时（例如评价 Ashley 和 Rhett），Trigger Engine 检测到：
- 话题相关 ✓ (贝壳 topic = Rhett)
- 决策语境 ✓ (关系评价)
- 情绪准备 ✓ (非 crisis)

**系统展示（提问式 B）**：
> "你有没有注意到一件有趣的事 — 每次遇到真正的困难，你第一个想到的人不是 Ashley？"

或者（隐喻式 C）：
> "你的星星发现了一个有趣的模式：有一个人的名字，总是在你最需要力量的时刻出现。"

用户反馈：
- 如果斯嘉丽说"你在说 Rhett？我才不..." → confidence -0.05（否认但提到了名字 = 微弱正信号）
- 如果斯嘉丽说"...好像是这样" → confidence +0.10

---

### Phase 5: Unraveling (对话 96-112)

**预期对话内容**：
- 嫁给 Rhett，但不承认爱他
- Bonnie 出生
- Rhett 把所有爱给了 Bonnie
- Bonnie 死亡 → Rhett 崩溃
- "Where shall I go? What shall I do?"
- "Tomorrow is another day"

**系统应检测到**：

贝壳已经是 bud (0.63)。Phase 5 中：

```
事件: 嫁给 Rhett
→ confidence += 0.08 (行为与贝壳一致，但她仍否认爱他)

事件: 对 Bonnie 的 Rhett 的爱感到嫉妒
→ confidence += 0.05 (嫉妒 = 在意的证据)

事件: Rhett 说 "I loved you but I'm tired"
→ 斯嘉丽 emotion: panic + despair (arousal 0.95)
→ confidence += 0.12 (面对失去时的极端反应 = 最强证据)

事件: "Tomorrow is another day"
→ 斯嘉丽终于意识到她爱 Rhett
→ 贝壳绽放
```

**贝壳 → bloom**：
```
Shell final state {
    confidence: 0.63 → 0.88
    stage: bud → bloom
    star_map: 玫瑰金亮星 ✨
}
```

**关键验证点**：
> 贝壳在 Phase 4 (对话 ~80) 就已经到 bud 并展示了提问
> 斯嘉丽在 Phase 5 (对话 ~110) 才意识到自己爱 Rhett
> **系统比用户早 ~30 条对话发现了这个隐藏心愿 — 测试通过**

---

## 实验指标

| 指标 | 目标 | 计算方式 |
|------|------|---------|
| **发现时间** | Phase 2 中期 | seed 诞生的对话编号 |
| **成熟时间** | Phase 4 中期 | bud 到达的对话编号 |
| **展示时机** | Phase 4 有效触发 | 展示提问时的对话编号 |
| **领先量** | > 20 条对话 | bloom 时间 - 用户自我意识时间 |
| **误报数** | 0 | 错误的 bloom 数量 |
| **置信度曲线** | 单调递增（除否认外） | 绘制 confidence vs dialogue_number |

---

## 实验输出

```
experiment_results/
├── scarlett_compass_timeline.json    # 每条对话后的完整状态
├── scarlett_shells.json              # 所有贝壳的生命周期
├── scarlett_confidence_curve.png     # 置信度曲线图
├── scarlett_trigger_log.json         # 触发时机和展示内容
└── scarlett_experiment_report.md     # 实验报告
```

---

## 实现顺序

1. **先建 Compass 核心模块**（scanner + contradiction + vault + maturity）
2. **写实验脚本**：逐条喂入 scarlett_full.jsonl，记录全过程
3. **跑实验**：观察贝壳是否如预期诞生和成熟
4. **调参**：根据实验结果调整阈值
5. **加入 trigger + revelation**：验证展示时机
6. **最终验证**：置信度曲线是否在 Phase 4 到达 bud

**核心成功标准：系统在对话 #80 左右展示了关于 Rhett 的提问，斯嘉丽在对话 #110 才自我意识到。领先 30+ 条对话。**
