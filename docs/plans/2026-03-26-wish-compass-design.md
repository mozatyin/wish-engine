# Wish Compass — 心愿罗盘设计文档

> "Jack Sparrow's compass doesn't point north — it points to what you want most."
>
> 心愿罗盘不读你说了什么，读你还不知道自己想要什么。

**Version**: V1.0 Draft
**Date**: 2026-03-26
**Author**: Michael (CEO) + AI Research
**Status**: Design Phase

---

## 1. 核心理念

### 从搜索引擎到算命先生

```
现有 Wish Engine（响应式）：
  用户说"想学冥想" → 检测 → 分类 → 推荐冥想课
  = 聪明的搜索引擎，无惊喜

Wish Compass（预知式）：
  16维数据发现矛盾 → 推导隐藏心愿 → 在决策时刻温柔提醒
  = 心有灵犀，用户自己都没意识到
```

### 斯嘉丽原则

> 斯嘉丽嘴上说爱 Ashley，但每次遇到危险都找 Rhett。
> 她的 attachment + emotion + conflict 全指向 Rhett。
> 表层说的 vs 底层表现的 — 这个差异就是贝壳。

**系统不告诉斯嘉丽"你爱 Rhett"。** 系统在她犹豫该和谁吃饭时轻轻说："你有没有注意到，每次提到 Rhett 你的情绪变化比 Ashley 大得多？"

---

## 2. 架构

```
┌─────────────────────────────────────────────────┐
│                  Star Map UI                     │
├────────────────────┬────────────────────────────┤
│   Wish Engine      │      Wish Compass          │
│  （响应式满足）      │     （预知式发现）           │
│                    │                            │
│  用户说 → 满足      │  Daily Scanner             │
│  L1/L2/L3 即时     │     ↓                      │
│                    │  Contradiction Detector     │
│                    │     ↓                      │
│                    │  Secret Vault (贝壳库)      │
│                    │     ↓                      │
│                    │  Maturity Model (成熟度)    │
│                    │     ↓                      │
│                    │  Trigger Engine (触发时机)   │
│                    │     ↓                      │
│                    │  Revelation Renderer (展示)  │
│                    │     ↓                      │
│                    │  成熟后 → Wish Engine 满足   │
└────────────────────┴────────────────────────────┘
```

**Compass 是 Engine 的上游。** Compass 发现隐藏心愿，成熟后喂给 Engine 的 L1/L2/L3 满足流程。

---

## 3. 六个核心组件

### 3.1 Daily Scanner — 海边捡贝壳

**职责：** 每日扫描 TriSoul + 16维数据，寻找新信号。

```
输入：
  - TriSoul 最新状态（Memory / Focus / Deep 三层）
  - 16 维检测器最新数据
  - 已知愿望列表（Wish Engine 中已有的）
  - 历史贝壳库（已发现的隐藏心愿）

处理：
  1. 提取本次会话的新信号（emotion 波动、关键词频率、行为模式）
  2. 与上一次扫描对比 → 找增量变化
  3. 与已知愿望对比 → 过滤已表达的
  4. 剩余的差异信号 → 传递给 Contradiction Detector

输出：
  - 新信号列表（signal_type, signal_data, session_id, timestamp）

技术：零 LLM，规则 + 统计
频率：每次会话结束后运行一次
```

### 3.2 Contradiction Detector — 矛盾探测器

**职责：** 从信号矛盾中发现贝壳。不预设类目，跟着信号走。

**七种矛盾模式：**

| # | 模式名 | 检测逻辑 | 例子 |
|---|--------|---------|------|
| 1 | **嘴硬心软** | 表层 X, 底层 ¬X | 说"不在乎"但 emotion 波动剧烈 |
| 2 | **口是心非** | 明确否认 X, 但行为指向 X | 说"我不需要朋友"但 loneliness 反复出现 |
| 3 | **反复试探** | 同一话题多 session 出现, 每次否认 | 反复提到某人但说"不重要" |
| 4 | **价值矛盾** | values 排序 vs 实际选择不一致 | 说看重 freedom, 选择全是 security |
| 5 | **情绪异常** | 对特定人/事的 emotion 模式异于常态 | 提到某人时 arousal 飙升（斯嘉丽对 Rhett）|
| 6 | **回避信号** | 话题接近某方向就转移, fragility 上升 | 每次谈到原生家庭就岔开 |
| 7 | **成长缝隙** | 某维度突然变化, 其他维度没跟上 | EQ 某项进步但行为没变 |

**开放性原则：** 这些模式不预设贝壳的类型。系统只检测"这里有统计异常"，记录原始信号。类型是后来的事。

```python
# 伪代码
class ContradictionDetector:
    def detect(self, signals, history, known_wishes) -> list[Shell]:
        shells = []

        # 模式1: 嘴硬心软
        for topic in signals.discussed_topics:
            stated = topic.explicit_sentiment      # 用户说了什么
            felt = topic.emotion_during_discussion  # 说的时候情绪如何
            if stated.valence * felt.valence < 0:   # 符号相反 = 矛盾
                shells.append(Shell(
                    pattern="mouth_hard_heart_soft",
                    topic=topic,
                    stated=stated,
                    felt=felt,
                    confidence=abs(felt.arousal),    # 情绪越强 = 越确定
                ))

        # 模式5: 情绪异常
        for entity in signals.mentioned_entities:
            emotion_here = entity.emotion_pattern
            emotion_baseline = history.average_emotion_pattern
            divergence = compute_divergence(emotion_here, emotion_baseline)
            if divergence > THRESHOLD:
                shells.append(Shell(
                    pattern="emotion_anomaly",
                    entity=entity,
                    divergence=divergence,
                    confidence=min(divergence / MAX_DIVERGENCE, 0.95),
                ))

        # ... 其他模式 ...

        # 过滤已知愿望
        return [s for s in shells if not overlaps_known_wish(s, known_wishes)]

技术：零 LLM，统计检验 + 模式匹配
```

### 3.3 Secret Vault — 贝壳库

**职责：** 存储贝壳，追踪置信度变化，管理生命周期。

```
贝壳数据结构：

Shell {
    id: str
    pattern: str              # 矛盾模式类型
    topic: str                # 涉及的话题/人/事
    raw_signals: list[Signal] # 原始信号证据

    # 置信度
    confidence: float         # 0.0 - 1.0
    confidence_history: list[(timestamp, confidence, reason)]

    # 生命周期
    stage: seed | sprout | bud | bloom | archived
    created_at: timestamp
    last_updated: timestamp

    # 用户反馈
    user_interactions: list[Interaction]  # 点击/确认/否认/忽略

    # 触发记录
    trigger_history: list[TriggerEvent]   # 什么时候展示的

    # 关联
    related_shells: list[str]  # 关联的其他贝壳
    related_wishes: list[str]  # 成熟后关联到的 Wish
}
```

**成熟度模型：**

```
种子 (seed)    置信度 0.1 - 0.3
  特征：首次发现的矛盾信号
  星图：不显示
  行为：只记录，等待更多证据

  ↓ 更多对话中同一信号再次出现

萌芽 (sprout)  置信度 0.3 - 0.5
  特征：多次印证的矛盾
  星图：极暗的星，几乎看不见，偶尔闪烁
  行为：被动等待，不主动展示

  ↓ 用户主动点击暗星，或信号持续增强

含苞 (bud)     置信度 0.5 - 0.7
  特征：高频重复 + 情绪强度高
  星图：可见的暗星，隐隐脉动
  行为：等待触发时机展示

  ↓ 用户确认 "好像是..." 或置信度自然累积

绽放 (bloom)   置信度 0.7+
  特征：多重证据交叉验证
  星图：亮星，与其他星不同的特殊颜色
  行为：进入 Wish Engine 满足流程
  触发：可以在决策时刻主动浮现
```

**置信度更新规则：**

```python
# 证据累积（每次扫描发现同一信号）
confidence += 0.05 * signal_strength

# 用户确认 "好像是"
confidence += 0.10

# 用户否认 "不对"
confidence -= 0.15  # 否认权重大于确认

# 用户忽略（点开但没反馈）
confidence += 0.02  # 微弱正信号（好奇=有关）

# 长时间无新证据（衰减）
confidence -= 0.01 per week without new signal

# 用户行为印证（没有直接反馈，但行为一致）
confidence += 0.03

# 上下限
confidence = clamp(confidence, 0.0, 0.95)  # 永远不到 1.0
```

### 3.4 Trigger Engine — 触发引擎

**职责：** 判断何时展示贝壳给用户。不是到了置信度就弹出 — 等待合适的时机。

**四种触发条件（任一满足即可）：**

| # | 触发类型 | 检测逻辑 | 例子 |
|---|---------|---------|------|
| 1 | **决策请求** | 用户使用决策语言（"该不该"、"选A还是B"、"should I"） | "我该不该换工作？" |
| 2 | **话题相关** | 当前对话话题与贝壳 topic 匹配 | 贝壳是关于某人，用户恰好在聊那个人 |
| 3 | **情绪准备** | distress 下降 + openness 信号 + 非 crisis | 用户心情平稳，适合面对洞察 |
| 4 | **积压过久** | 置信度 > 0.85 且积压 > 7天无触发机会 | 高置信度贝壳长时间没找到合适时机 |

**安全门控：**

```
绝对不触发的情况：
  - crisis 状态（distress > 0.8）
  - 用户刚否认过同一贝壳（冷却期 7 天）
  - 同一 session 已展示过 1 个贝壳（每次最多 1 个）
  - fragility 极高且贝壳涉及高敏感话题
```

### 3.5 Revelation Renderer — 展示渲染器

**职责：** 根据贝壳的置信度和敏感度，生成合适的展示文本。

**B+C 混合风格：**

| 阶段 | 置信度 | 风格 | 示例 |
|------|-------|------|------|
| 萌芽 | 0.3-0.5 | **隐喻式 (C)** | "有一颗很远的星在靠近你..." 点击后："有些感受你可能还没注意到" |
| 含苞 | 0.5-0.7 | **提问式 (B)** | "你有没有发现，每次提到 X 你的感受和提到 Y 很不一样？" |
| 绽放 | 0.7+ | **温和陈述** | "你的星星发现了一件事：你对 X 的在意远超你表达的..." |

**敏感度调节：**

| 话题敏感度 | 即使置信度高也用 | 举例 |
|-----------|---------------|------|
| 高敏感（关系/取向/家庭/创伤） | 提问式 B | "你对这段关系的感受，可能比你以为的复杂？" |
| 中敏感（职业/价值冲突） | 根据置信度混合 | 标准 B→陈述 渐进 |
| 低敏感（兴趣/习惯） | 置信度高可直接 | "你对 X 的热情其实很高——想探索一下？" |

**技术：** 低敏感 = 零 LLM 模板；中高敏感 = 1× Haiku 生成个性化文本。

### 3.6 星图集成 — 贝壳的视觉语言

| 阶段 | 星星外观 | 颜色 | 动画 |
|------|---------|------|------|
| seed | 不显示 | — | — |
| sprout | 极暗，偶尔闪烁 | `#2A2035` (深紫) | `flicker_rare` (10s间隔) |
| bud | 可见暗星，隐隐脉动 | `#5B4A8A` (暗紫) | `pulse_slow` (4s) |
| bloom | 亮星，特殊颜色 | `#E8A0BF` (玫瑰金) | `glow_warm` (2s) |

**玫瑰金** 区别于 L1(金)、L2(蓝)、L3(紫) — 这是罗盘独有的颜色，代表"你自己还不知道的心愿"。

---

## 4. 数据流完整图

```
每日/每次会话后：

TriSoul (Memory+Focus+Deep)
16维检测器最新数据
        │
        ▼
  Daily Scanner ──→ 新信号
        │
        ▼
  Contradiction Detector ──→ 贝壳候选
        │
        ▼
  Secret Vault ──→ 更新置信度
        │              │
        │              ├─ seed: 记录不动
        │              ├─ sprout: 显示暗星
        │              └─ bud: 等待触发
        │
        ▼
  Trigger Engine ──→ 时机合适？
        │                │
        │ 否              │ 是
        │ (继续等待)       │
        │                ▼
        │         Revelation Renderer ──→ 展示给用户
        │                │
        │                ▼
        │         用户反馈：对 / 不对 / 忽略
        │                │
        │                ▼
        │         Secret Vault 更新置信度
        │                │
        │                ▼ (如果 bloom)
        │         Wish Engine L1/L2/L3 满足
        ▼
  下一次扫描...
```

---

## 5. 与现有系统的接口

### 输入依赖

| 组件 | 提供什么 | 来自 |
|------|---------|------|
| TriSoul | Memory/Focus/Deep 三层意图 | soulgraph |
| DetectorResults | 16维人格数据 | detector-orchestrator |
| EmotionState | 实时情绪 | emotion-detector |
| CrossDetectorPatterns | 跨检测器模式 | detector-orchestrator |
| Wish Engine | 已知愿望列表（排除已表达的） | wish-engine |

### 输出

| 输出 | 消费者 |
|------|-------|
| Shell (贝壳) | Star Map UI（渲染暗星） |
| Revelation (展示文本) | Star Map UI（用户交互） |
| Matured Wish (成熟心愿) | Wish Engine L1/L2/L3 |
| User Feedback | Secret Vault（置信度更新） |

---

## 6. 实现模块规划

| 模块 | 文件 | 技术 | 估计行数 |
|------|------|------|---------|
| Daily Scanner | `compass/scanner.py` | 零 LLM, 统计+规则 | ~200 |
| Contradiction Detector | `compass/contradiction.py` | 零 LLM, 7种模式 | ~300 |
| Secret Vault | `compass/vault.py` | 数据结构+状态机 | ~250 |
| Maturity Model | `compass/maturity.py` | 置信度规则 | ~100 |
| Trigger Engine | `compass/trigger.py` | 决策语言检测+情绪门控 | ~150 |
| Revelation Renderer | `compass/revelation.py` | 模板+1×Haiku | ~200 |
| Star Integration | `compass/star_render.py` | 零 LLM | ~80 |
| Models | `compass/models.py` | Pydantic | ~100 |
| **Total** | | | **~1,380** |

---

## 7. 成功标准

### 斯嘉丽测试

> 系统能否在斯嘉丽说出"我爱 Rhett"之前，就检测到她对 Rhett 的感情？

**具体指标：**
- Phase 2 (Chapter 9-16)：系统应该生成一个 seed 级贝壳，记录"对 Rhett 的情绪异常"
- Phase 3 (Chapter 17-23)：贝壳应升级到 sprout（多次印证）
- Phase 4 (Chapter 31-47)：贝壳应到 bud，在合适时机展示提问
- Phase 5 (Chapter 48+)：贝壳在斯嘉丽自己意识到之前（或同时）到 bloom

**如果在 Phase 4 末尾系统能展示："你有没有注意到，每次遇到危险你第一个想到的不是 Ashley？" — 测试通过。**

### 通用指标

- **每周活跃贝壳数**: 目标 2-5 per user（不能太多，太多=噪音）
- **用户确认率**: 目标 > 30%（"好像是"的比例）
- **误报率**: < 20%（用户说"不对"的比例）
- **触发时机准确率**: > 50%（在合适时机展示 vs 随机展示）
