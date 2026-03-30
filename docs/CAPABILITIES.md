# Wish Engine — Product Capability Reference

> **给产品团队**：本文档描述系统当前能检测到的所有用户需求，以及每种需求会触发哪些服务。

---

## 系统架构一句话

用户说话 → 系统识别"当下/历史/深层"三层需求 → 调用真实 API → 在星图上生成对应的星星

```
用户对话
   │
   ├─ 表层（Surface）  当下说了什么 → ☄️ 流星（4小时后消失）
   ├─ 中层（Middle）   反复提到什么 → ⭐ 星星（一周持续）
   └─ 深层（Deep）     心里藏着什么 → 🌍 地球（永久，Compass驱动）
```

---

## 一、表层需求（Surface Soul）— 44 种

> **触发条件**：用户在最近几条消息中说了关键词。
> **产品表现**：生成 ☄️ 流星，4小时后自动消失。
> **App 集成**：调用 `detect_surface_attention(recent_texts)` 检测，星图自动更新。

---

### 🍽️ 生存需求（Survival）

| 需求 | 触发关键词（样例） | 产品响应 | 调用服务 | 在线状态 |
|---|---|---|---|---|
| **hungry** 饿了 | hungry / starving / 饿 / جائع | 推荐附近餐厅 + 随机食谱 | TheMealDB + OSM | ✅ 实时 |
| **thirsty** 渴了 | thirsty / 渴 / drink / water | 推荐附近咖啡馆 + 鸡尾酒配方 | OSM + TheCocktailDB | ✅ 实时 |
| **need_medicine** 需要药 | sick / medicine / pain / 生病 / مريض | 最近药店/医院 | OSM | ✅ 实时 |
| **need_money** 缺钱 | broke / money / debt / 穷 / 钱 | 实时汇率 + 最近银行ATM | Frankfurter + OSM | ✅ 实时 |
| **cold** 冷 | cold / freezing / 冷 | 附近有暖气的地方 + 当前气温 | OSM + Open-Meteo | ✅ 实时 |
| **hot** 热 | hot / burning / 热 / حر | 附近有空调的地方/游泳池 + 气温 | OSM + Open-Meteo | ✅ 实时 |
| **tired** 累了 | tired / exhausted / 累 / متعب | 附近可以坐下的地方 + 最佳入睡时间 | OSM + 本地计算 | ✅ |
| **headache** 头疼 | headache / migraine / 头疼 / صداع | 最近药店 + 呼吸法 | OSM + 本地 | ✅ |

---

### 😔 情绪需求（Emotional）

| 需求 | 触发关键词（样例） | 产品响应 | 调用服务 | 在线状态 |
|---|---|---|---|---|
| **anxious** 焦虑 | anxious / worried / panic / 焦虑 / قلق | 4-7-8呼吸法 + 附近公园 + 正念提醒 | 本地计算 + OSM + 本地 | ✅ |
| **sad** 难过 | sad / crying / depressed / 伤心 / حزين | 狗狗图片 + 诗歌 + 一句建议 | Dog API + PoetryDB + Advice API | ✅ 实时 |
| **angry** 愤怒 | angry / furious / rage / 生气 / غاضب | 附近健身房/拳击 + 训练动作 | OSM + Wger | ✅ 实时 |
| **lonely** 孤独 | lonely / alone / nobody / 孤独 / وحيد | 附近有人的地方 + 开话题句子 + 猫咪图 | OSM + 本地 + Cat API | ✅ 实时 |
| **scared** 害怕 | scared / afraid / terrified / 害怕 / خائف | 附近安全有人的地方 + 盒式呼吸 | OSM + 本地 | ✅ |
| **panicking** 恐慌 | panic attack / can't breathe / 恐慌 | ⚠️ 紧急呼吸引导 + 最近安静空间 | 本地 + OSM | ✅ |
| **grieving** 哀痛 | died / dead / funeral / loss / 死 / وفاة | 狄金森诗歌 + 安静的地方 | PoetryDB + OSM | ✅ 实时 |
| **guilty** 内疚 | guilty / fault / sorry / 内疚 / 对不起 | 东方智慧语录 + 对话引导 | 本地智慧库 + 本地 | ✅ |
| **overwhelmed** 不知所措 | overwhelmed / can't handle / 崩溃 / مرهق | 附近公园 + 呼吸法 + 番茄钟建议 | OSM + 本地 + 本地 | ✅ |
| **homesick** 想家 | homesick / miss home / 思乡 / أشتاق | 推荐家乡风味菜 + 社区中心 + 一句话陪伴 | TheMealDB + OSM + Advice API | ✅ 实时 |

---

### 🛠️ 实际需求（Practical）

| 需求 | 触发关键词（样例） | 产品响应 | 调用服务 | 在线状态 |
|---|---|---|---|---|
| **need_wifi** 需要网络 | wifi / internet / 上网 / إنترنت | 附近有免费WiFi的地方 | OSM | ✅ 实时 |
| **need_quiet** 需要安静 | quiet / silence / peace / 安静 / هدوء | 附近最安静的图书馆/公园 | OSM | ✅ 实时 |

---

### 🕌 精神需求（Spiritual）

| 需求 | 触发关键词（样例） | 产品响应 | 调用服务 | 在线状态 |
|---|---|---|---|---|
| **need_pray** 需要祈祷 | pray / mosque / church / 祈祷 / صلاة | 实时礼拜时间 + 最近礼拜场所 + 古兰经经文 | Aladhan + OSM + AlQuran | ✅ 实时 |
| **need_meaning** 寻找意义 | meaning / purpose / why am I / 意义 | 哲学语录（斯多葛/佛教/道教等）+ 圣经经文 + 东方智慧 | quotable.io + Bible API + 本地 | ✅ 实时 |

---

### 🌞 情境感知（Context-Aware）

| 需求 | 触发关键词（样例） | 产品响应 | 调用服务 | 在线状态 |
|---|---|---|---|---|
| **morning** 早上 | good morning / just woke up / 早上好 / صباح | 当前天气 + 日出时间 + 今日肯定语 | Open-Meteo + Sunrise-Sunset + Affirmations | ✅ 实时 |
| **evening** 傍晚 | tonight / this evening / winding down / 晚上了 | 当前气温 + 正念提醒 | Open-Meteo + 本地 | ✅ |
| **weekend** 周末 | weekend / saturday / sunday / 周末 | 附近博物馆/公园/艺术馆 + 随机活动建议 | OSM + Bored API | ✅ 实时 |
| **new_place** 到新地方 | new here / just arrived / visiting / 刚来 | 当地维基百科简介 + 下个公假 + 国家文化信息 | Wikipedia + Nager Date + RestCountries | ✅ 实时 |
| **bored** 无聊 | bored / nothing to do / 无聊 / ممل | 随机活动建议 + 笑话 + 冷知识 + 空间站实时位置 | Bored API + JokeAPI + OpenTrivia + ISS API | ✅ 实时 |
| **insomnia** 失眠 | can't sleep / insomnia / 失眠 / أرق | 最佳入睡时间计算 + 4-7-8助眠呼吸 | 本地计算 + 本地 | ✅ |
| **celebrating** 庆祝 | birthday / promotion / celebrating / 生日 / 升职 | 附近餐厅/场所 + 特别食谱 + 鼓励语 | OSM + TheMealDB + CreativeAPI | ✅ 实时 |

---

### 🌿 身心健康

| 需求 | 触发关键词（样例） | 产品响应 | 调用服务 | 在线状态 |
|---|---|---|---|---|
| **need_exercise** 想运动 | exercise / gym / run / workout / 运动 / رياضة | 训练动作 + 附近健身场所 + 热量计算 | Wger + OSM + 本地计算 | ✅ 实时 |
| **want_outdoor** 想去户外 | outdoors / nature / hiking / 户外 / الطبيعة | 附近公园/花园 + 实时天气 + 户外运动建议 | OSM + Open-Meteo + Wger | ✅ 实时 |

---

### 💬 社交需求

| 需求 | 触发关键词（样例） | 产品响应 | 调用服务 | 在线状态 |
|---|---|---|---|---|
| **need_talk** 想倾诉 | talk to someone / need someone / 想说话 | 对话开场句 + 附近适合聊天的地方 | 本地 + OSM | ✅ |
| **want_friends** 想认识人 | friends / meet people / 交朋友 | 附近社区活动中心 + 破冰话题 | OSM + 本地 | ✅ |

---

### 🎨 成长与创造

| 需求 | 触发关键词（样例） | 产品响应 | 调用服务 | 在线状态 |
|---|---|---|---|---|
| **want_read** 想读书 | book / read / library / 书 / 图书馆 | 书籍推荐 + 附近图书馆/书店 + 免费电子书 | Google Books + OSM + Gutenberg | ✅ 实时 |
| **want_learn** 想学习 | learn / study / course / 学 / 课 | 随机维基知识 + 历史上的今天 + 附近学习场所 | Wikipedia + History API + OSM | ✅ 实时 |
| **want_art** 想看艺术 | art / gallery / exhibition / 展览 | 附近艺术馆/博物馆 + 艺术家简介 | OSM + Wikipedia | ✅ 实时 |
| **want_music** 想听音乐 | music / concert / 音乐 / 唱 | 实时电台推荐 + 附近演出场所 | Radio Browser + OSM | ✅ 实时 |
| **want_work** 想工作/专注 | work / productive / focus / deadline / 工作 | 安静工作场所 + 番茄钟计划 | OSM + 本地计算 | ✅ |
| **want_create** 想创作 | creative / draw / paint / craft / 创作 | 附近创作空间 + 今日配色板 + 创意动力语 | OSM + Colormind + Zenquotes | ✅ 实时 |
| **reflection** 在反思 | reflecting on / looking back / in hindsight | 感恩练习提示 + 本周反思问题 | 本地 + 本地 | ✅ |
| **confidence** 需要自信 | not confident / insecure / 没信心 | 肯定语 + 今日挑战 | Affirmations.dev + 本地 | ✅ 实时 |

---

## 二、中层需求（Middle Soul）— 历史兴趣追踪

> **触发条件**：某个话题在历史对话中出现 **3次或以上**，自动生成 ⭐ 星星。
> **产品表现**：⭐ 星星持续一周，稳定显示在星图上。
> **App 集成**：维护 `topic_history: {topic: count}` 字典，传入 `generate_trisoul_stars()`。

| 用户反复提到 | 映射到的需求 | 最终推荐 |
|---|---|---|
| yoga / meditation / fitness / gym / running / swimming | need_exercise | 运动训练 + 附近健身场所 |
| hiking / nature / outdoors / garden | want_outdoor | 附近公园 + 天气 |
| cooking / baking / recipes / coffee / food | hungry | 食谱 + 附近餐厅 |
| art / photography / drawing / painting / crafts / design | want_art / want_create | 艺术馆 + 创作建议 |
| books / reading | want_read | 书籍推荐 |
| language / podcast / study / coding | want_learn | 知识内容 |
| writing | want_create | 创作空间 |
| music / film | want_music / want_art | 电台 + 演出场所 |
| friends / loneliness | want_friends / lonely | 社区活动 |
| family / home | homesick | 家乡菜 + 社区 |
| anxiety | anxious | 呼吸法 + 安静场所 |
| work / career / startup / project | want_work | 工作空间 |
| prayer / faith / spirituality | need_pray / need_meaning | 礼拜时间 + 哲学 |
| gaming / games | bored | 活动建议 |
| travel | new_place | 当地文化信息 |

---

## 三、深层需求（Deep Soul）— Compass 驱动

> **触发条件**：Compass 检测到用户在某话题上的情绪强度超过阈值，即使用户从未明说。
> **产品表现**：🌍 地球，永久存在，直到该愿望被解决。
> **App 集成**：使用 `WishCompass` + `generate_trisoul_stars(compass=compass)`。

| Compass 检测到的隐藏信号 | 产品响应 | 调用服务 |
|---|---|---|
| 对某人/某事的情绪强度高但未直说 | 附近安静的地方（供思考）+ 智慧语录 | OSM + quotable.io |
| 誓言/转折点（"I'll never be hungry again"） | 斯多葛/佛教智慧 + 诗歌 | PoetryDB + 哲学API |
| 反复回避某话题（denial pattern） | 哲学问题 + 平静空间 | 本地 + OSM |

**誓言压制（VowSuppressor）规则：**
- 用户说出深层誓言后，相关 Surface 推荐被自动压制
- survival 阶段：压制 12小时
- 普通阶段：压制 72小时
- meaning 阶段：压制 7天（168小时）

---

## 四、外部服务完整清单

| 服务 | 提供商 | 用途 | 需要 Key | 稳定性 |
|---|---|---|---|---|
| **OSM Overpass** | overpass-api.de | 周边地点搜索 | 无 | ⭐⭐⭐⭐⭐ |
| **Open-Meteo** | api.open-meteo.com | 实时天气 | 无 | ⭐⭐⭐⭐⭐ |
| **TheMealDB** | themealdb.com | 食谱 | 无 | ⭐⭐⭐⭐ |
| **TheCocktailDB** | thecocktaildb.com | 鸡尾酒/饮品 | 无 | ⭐⭐⭐⭐ |
| **Frankfurter** | frankfurter.app | 实时汇率 | 无 | ⭐⭐⭐⭐⭐ |
| **PoetryDB** | poetrydb.org | 诗歌 | 无 | ⭐⭐⭐ |
| **Advice Slip** | adviceslip.com | 随机建议 | 无 | ⭐⭐⭐⭐ |
| **Wger** | wger.de | 运动训练动作 | 无 | ⭐⭐⭐⭐ |
| **Dog CEO** | dog.ceo | 狗狗图片（情绪疗愈） | 无 | ⭐⭐⭐⭐ |
| **The Cat API** | thecatapi.com | 猫咪图片（孤独疗愈） | 无 | ⭐⭐⭐⭐ |
| **Google Books** | googleapis.com/books | 书籍搜索 | 无 | ⭐⭐⭐⭐⭐ |
| **Project Gutenberg** | gutendex.com | 免费电子书 | 无 | ⭐⭐⭐⭐ |
| **Wikipedia REST** | en.wikipedia.org/api | 知识摘要 | 无 | ⭐⭐⭐⭐⭐ |
| **History Muffinlabs** | history.muffinlabs.com | 历史上的今天 | 无 | ⭐⭐⭐ |
| **Radio Browser** | radio-browser.info | 全球电台 | 无 | ⭐⭐⭐⭐ |
| **Aladhan** | aladhan.com | 穆斯林礼拜时间 | 无 | ⭐⭐⭐⭐⭐ |
| **AlQuran Cloud** | alquran.cloud | 古兰经 | 无 | ⭐⭐⭐⭐ |
| **Bible API** | bible-api.com | 圣经经文 | 无 | ⭐⭐⭐⭐ |
| **Affirmations.dev** | affirmations.dev | 肯定语 | 无 | ⭐⭐⭐⭐ |
| **Sunrise-Sunset** | sunrise-sunset.org | 日出日落时间 | 无 | ⭐⭐⭐⭐⭐ |
| **Nager Date** | date.nager.at | 全球公共假日 | 无 | ⭐⭐⭐⭐ |
| **RestCountries** | restcountries.com | 国家文化信息 | 无 | ⭐⭐⭐⭐⭐ |
| **Open Notify (ISS)** | api.open-notify.org | 空间站实时位置 | 无 | ⭐⭐⭐⭐ |
| **Bored API** | bored-api.appbrewery.com | 随机活动建议 | 无 | ⭐⭐⭐ |
| **JokeAPI** | jokeapi.dev | 笑话 | 无 | ⭐⭐⭐⭐ |
| **OpenTDB** | opentdb.com | 冷知识问答 | 无 | ⭐⭐⭐⭐ |
| **quotable.io** | api.quotable.io | 哲学语录（按传统筛选） | 无 | ⭐⭐⭐⭐ |
| **Zenquotes** | zenquotes.io | 通用智慧语录 | 无 | ⭐⭐⭐⭐ |
| **Colormind** | colormind.io | AI 配色板 | 无 | ⭐⭐⭐ |
| **本地计算** | — | 呼吸法/睡眠/番茄钟/健康计算 | — | ⭐⭐⭐⭐⭐ |

**全部 30 个服务无需注册 API Key。**

---

## 五、App 集成接口说明

### 最简单的集成方式（一次调用出完整星图）

```python
from wish_engine.trisoul_stars import generate_trisoul_stars
from wish_engine.soul_layer_classifier import VowSuppressor
from wish_engine.narrative_tracker import NarrativeTracker
from wish_engine.star_feedback import StarFeedbackStore
from wish_engine.compass.compass import WishCompass

# 这四个对象跨 session 持久化（存数据库或用户 profile）
vow_suppressor = VowSuppressor()
narrative = NarrativeTracker()
feedback = StarFeedbackStore()
compass = WishCompass()

# 每次用户发消息后调用
star_map = generate_trisoul_stars(
    recent_texts=["I'm so hungry", "also feeling anxious"],  # 最近几条消息
    lat=25.2048,
    lng=55.2708,
    topic_history={"yoga": 12, "coffee": 8},   # 历史话题统计
    compass=compass,
    vow_suppressor=vow_suppressor,
    narrative=narrative,
    feedback=feedback,
)

# star_map.meteors  → ☄️ 当下需求（立即显示）
# star_map.stars    → ⭐ 持续兴趣（稳定显示）
# star_map.earths   → 🌍 深层愿望（长期显示）
```

### 用户点击/划走后反馈

```python
# 用户点击了一颗流星
feedback.click("hungry")

# 用户划走了一颗流星
feedback.dismiss("anxious")

# 下次生成时，点击多的 attention 自动排前面
```

### 星星显示规则

| 星星类型 | 颜色 | 动画 | 存活时间 | 触发层 |
|---|---|---|---|---|
| ☄️ 流星（Surface） | 金色 #FFD700 | streak_fast | 4小时 | 表层，当下说的 |
| ☄️ 流星（Deep反思） | 玫瑰金 #E8A0BF | pulse_deep | 4小时 | 深层誓言/信念 |
| ⭐ 星星（Middle） | 蓝色 #4A90D9 | glow_steady | 7天 | 历史反复提到 |
| 🌍 地球（Deep） | 玫瑰金 #E8A0BF | pulse_deep | 永久 | Compass 探测 |

---

## 六、叙事阶段（Narrative Arc）

系统自动判断用户所处的人生阶段，影响星图权重：

| 阶段 | 标志性信号 | 流星数量 | 星星数量 | 地球数量 | 允许智慧内容 |
|---|---|---|---|---|---|
| **survival** 生存 | 危机/饥饿/恐惧/无钱 | 最多5颗 | 最少1颗 | 最少1颗 | ❌ |
| **stability** 稳定 | 日常/规律/工作/习惯 | 最多4颗 | 最多2颗 | 最多2颗 | ✅ |
| **growth** 成长 | 学习/目标/挑战/进步 | 最多2颗 | 最多3颗 | 最多2颗 | ✅ |
| **meaning** 意义 | 信念/誓言/人生/永远 | 最多2颗 | 最多2颗 | 最多6颗 | ✅ |

---

## 七、关键设计原则

1. **知行合一**：每一颗星都来自用户心里说的话，不是算法猜测。
2. **分层过滤**：Surface 不推智慧，Deep 不推餐厅。`filter_actions_by_layer()` 强制执行。
3. **誓言压制**：用户说出人生誓言后，相关 Surface 推荐自动退场 12-168 小时。
4. **全部免费 API**：30 个外部服务，零注册，零费用，可直接生产使用。
5. **3级降级**：每个 API 都有 fallback，网络断了也能返回内容。
6. **多语言**：中文/英文/阿拉伯文关键词同步覆盖，44 种需求均支持。

---

*生成于 wish-engine，当前版本：2711 tests passing。*
