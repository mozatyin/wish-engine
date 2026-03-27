# 100 个星图魔法时刻 — 地图 x 人格 x 情绪 = 此刻此地此人

> "Life is like a box of chocolate — you never know what you're gonna get."
> 但星图知道。它悄悄准备好了，等你打开。

**Version**: V1.0
**Date**: 2026-03-26
**Author**: Michael (CEO) + AI Research
**Status**: Product Dream List

---

## 这份文档是什么

这是一份 **产品人的梦想清单**。

100 个真实场景，每一个都回答同一个问题：**当 SoulMap 的 16 维人格系统 + 情绪检测 + Compass（隐藏心愿罗盘）同时工作时，能创造什么样的魔法时刻？**

核心逻辑：

```
16维人格画像（你是谁）
   + 实时情绪状态（你现在怎么了）
   + Compass 隐藏心愿（你自己还不知道想要什么）
   + 地图/API 外部能力（世界能给你什么）
   = Chocolate Moment（此刻、此地、此人的魔法）
```

不是通用推荐。不是搜索引擎。是 **只有你的星图才能说出的那句话**。

---

## 16 维检测器速查

| # | 检测器 | 输出什么 | 用在哪 |
|---|--------|---------|--------|
| 1 | Emotion | 20 种情绪实时值 + valence + distress | 所有场景的触发条件 |
| 2 | MBTI | 连续型四维 (E/I, S/N, T/F, J/P) | 个性化推荐过滤 |
| 3 | EQ | 情商五维分值 | 关系/社交/冲突场景 |
| 4 | Conflict | Thomas-Kilmann 5 风格 | 冲突/关系场景 |
| 5 | Humor | 4 种幽默风格 | 社交/创造场景 |
| 6 | Fragility | 脆弱性模式 | 情绪急救/保护 |
| 7 | Connection Response | toward/against/away 模式 | 关系/社交场景 |
| 8 | Love Language | 5 种爱的语言 | 关系/爱场景 |
| 9 | Communication DNA | 27 维行为特征 | 社交/职业场景 |
| 10 | Values | 核心价值观排序 | 职业/意义场景 |
| 11 | Super Brain | 20 行为模式 + 回复策略 | 全场景策略层 |
| 12 | Attachment | 依恋类型 | 关系/安全感场景 |
| 13 | SoulGraph | TriSoul 三层状态 | Compass 信号源 |
| 14 | Cross-Detector | 26 种跨检测器洞察 | Compass 矛盾检测 |
| 15 | Blind Spot | 跨 session 矛盾 | 隐藏心愿发现 |
| 16 | Soul Type | 灵魂类型 (Lighthouse/Explorer...) | L3 用户匹配 |

---

## 一、情绪急救 (Emotional First Aid)

焦虑、愤怒、悲伤、崩溃——不是等你好了再帮你，是 **你最难的时候，星图就在这里**。

| # | 检测到什么 | 星图说什么 | 需要什么 API | 价值感 |
|---|-----------|----------|-------------|--------|
| 1 | Emotion: anxiety 0.8+, MBTI: 高 I（内向），Fragility: perfectionism pattern | "你现在很紧张对不对？我发现每次你追求完美的时候，焦虑就会升起来。附近有一个安静的公园，走 15 分钟就到——你不需要做到完美，你只需要呼吸。" + 地图标注公园 | Google Places API (parks), Weather API | ★★★★★ |
| 2 | Emotion: anger 0.7+, Conflict: compete style, 过去 3 次会话 anger 持续上升 | "你已经生气好几天了。你的方式是迎面解决问题——但这次好像对方没在听。要不要试试这个：写一封不发出去的信？你可以在这里写，只有星星看得到。" | 无（L1 自带写信功能） | ★★★★ |
| 3 | Emotion: sadness 0.9+, distress 0.8+, Connection Response: away 模式, 近 7 天活跃度骤降 | "你最近很安静。我不会问你怎么了——但如果你想，附近 800 米有一家 24 小时咖啡店，暖色灯光那种。有时候换个地方坐坐，会好一点。" + 地图导航 | Google Places API (cafes, 24hr filter), Google Maps Directions API | ★★★★★ |
| 4 | Emotion: fear 0.6+, 即将面试（Calendar 检测到明天有 "interview" 事件）, MBTI: 高 F（情感型） | "明天面试对不对？你是那种会先在乎面试官喜不喜欢你的人。这很正常——但面试官想听的不是讨好，是真实。你最擅长的三个词是……（基于 Communication DNA 生成）" | Calendar API (Google/Apple), L1 生成 | ★★★★★ |
| 5 | Emotion: guilt 0.7+, Love Language: acts_of_service, 最近一次对话提到 "妈妈/أمي" | "你提到妈妈的时候，语气里有内疚。你的爱的语言是行动——你不擅长说甜话，但你擅长做事。附近有一家花店，可以在 30 分钟内送达。有时候一束花比一万句话管用。" + 花店地图 | Google Places API (florists), 花店配送 API (本地集成) | ★★★★★ |
| 6 | Emotion: loneliness 0.8+, 时间: 深夜 1-5 AM, Attachment: anxious 型, 近 3 天无社交对话 | "凌晨两点，你又睡不着。你的孤独感在深夜特别重。你不需要现在找人聊——但这有一个温暖的声音，陪你待一会。" + 播放个性化助眠/陪伴音乐 | Spotify API (mood-based playlist), Time API | ★★★★ |
| 7 | Emotion: overwhelm 0.8+, Communication DNA: high task_density + low pause_ratio, MBTI: 高 J（判断型） | "你同时在处理太多事了。你是那种不把清单做完不罢休的人——但现在清单在吃掉你。要不要让我帮你把今天的事排个优先级？只做前三件，其他的明天再说。" | Calendar API, Todoist/Reminders API | ★★★★ |
| 8 | Emotion: panic 0.9+, Fragility: catastrophizing pattern, Heart Rate 异常（如果有 Health 权限）| "深呼吸。4 秒吸气——7 秒屏住——8 秒呼气。你有灾难化思维的倾向，我知道现在脑子里全是最坏的结果。但上一次你也觉得天塌了——后来呢？后来你搞定了。" + 478 呼吸引导动画 | Apple HealthKit / Google Fit API (heart rate), L1 呼吸引导 | ★★★★★ |
| 9 | Emotion: shame 0.7+, EQ: low self_regard, 对话中出现 "我不够好/أنا مش كويس" | "你又在说自己不够好了。我数了一下——过去 30 天你说了 7 次类似的话。但你知道吗？你的 EQ 共情力是前 15%。你不够好？你只是对自己太严格了。" | 无（L1 数据回溯） | ★★★★★ |
| 10 | Emotion: grief 0.8+, 日期接近某个用户提到过的纪念日, Attachment: secure→anxious 临时滑动 | "这个日子快到了，对不对。你不用假装没事。如果你想，附近有一个安静的地方可以坐坐（地图标注）。如果你想聊，我在这里。如果不想，我也在这里。" | Calendar API (纪念日检测), Google Places API (quiet spots) | ★★★★★ |

---

## 二、身心健康 (Physical Wellness)

不是通用健身 App 的"今天该跑步了"——是 **基于你的人格和当下情绪** 推荐的健康方案。

| # | 检测到什么 | 星图说什么 | 需要什么 API | 价值感 |
|---|-----------|----------|-------------|--------|
| 11 | MBTI: 高 I, Emotion: stress 0.6+, 时间: 周末上午, 天气: 晴天 | "内向的人恢复能量的最佳方式是独处 + 自然。今天天气很好。离你 2 公里有一条人少的步道——周末上午去的人通常不多。" + 步道地图 + 人流预测 | Google Places API (hiking trails), Weather API, Google Popular Times | ★★★★ |
| 12 | Emotion: fatigue 0.7+, Communication DNA: declining message_length (近 7 天越来越短), 近期 sleep 相关关键词出现 3+ 次 | "你最近的消息越来越短了。你是不是睡得不太好？基于你的作息模式，这个 App 的睡眠引导可能适合你——它不是那种闹钟式的，是慢慢把你放空的。" | Spotify API (sleep sounds), Apple Health (sleep data), App Store API | ★★★ |
| 13 | MBTI: 高 E + 高 P, Emotion: restless/boredom 0.6+, 位置: 市区 | "你闷了，我知道。你是那种不动就会疯的人。离你 1.5 公里有一个攀岩馆，今天有空位。你不需要计划——你需要动起来。" | Google Places API (climbing gyms), Booking/ClassPass API, Location API | ★★★★ |
| 14 | Values: health 排名前 3, 但 Emotion 显示 stress 持续 2 周, 行为矛盾: 说重视健康但 0 次运动相关话题 | "你说健康对你很重要——但最近两周你的压力一直很高，而且你没提过任何运动。不是批评你哦。要不要我帮你找一个离你最近的、不需要预约的健身房？门槛越低越好。" | Google Places API (gyms, 24hr), Google Maps (distance) | ★★★★ |
| 15 | Emotion: anxiety 0.5+, 时间: 工作日中午, MBTI: 高 S（感觉型），位置: 办公区 | "午饭时间到了。你今天有点焦虑——高碳水会让你下午更困。你是实际派，所以我不说虚的：附近这家沙拉店评分 4.5，走路 5 分钟。吃轻一点，下午会好过一些。" + 餐厅导航 | Google Places API (restaurants, healthy filter), Yelp API, Weather API | ★★★ |
| 16 | Fragility: somatic pattern (身体化倾向), Emotion: stress 0.7+, 最近 3 次提到头疼/背疼 | "你最近第三次提到身体不舒服了。你知道吗？你的压力很容易变成身体症状。附近有一家评分很高的推拿/按摩店——不是让你治病，是让你的身体也放松一下。" | Google Places API (massage/spa), Health API | ★★★★ |
| 17 | MBTI: 高 N（直觉型）, Emotion: calm 偏高, 近期多次出现 "冥想/meditation/تأمل" 关键词 | "你提到冥想好几次了，你是直觉型的人——引导式冥想比呼吸数数更适合你。这里有一个课程：Insight Timer 上的'直觉旅程'系列，每次 12 分钟。离你最近的冥想中心在 3 公里外，周四有免费体验。" | Google Places API (meditation centers), App Store API, Eventbrite API | ★★★★ |
| 18 | Emotion: distress 起伏大(方差高), Communication DNA: high code_switch_ratio, 跨时区频繁（差旅模式） | "你最近一直在跨时区——情绪波动也跟着时差走。你现在所在城市的日落时间是 6:47 PM。找个面西的地方坐着看 15 分钟日落，比任何助眠药都管用。" + 日落方向地图 | Weather API (sunset time), Google Maps (west-facing spots), Location API (timezone) | ★★★★★ |
| 19 | Humor: self_enhancing style, Emotion: mild stress, 周五下午 | "你是那种用笑化解压力的人。周五了，你值得开心一下。附近今晚有一场脱口秀——不是很正式那种，是开放麦。你可以去笑，也可以上台讲。" | Eventbrite API (comedy events), Google Places API, Location API | ★★★ |
| 20 | Emotion: 连续 5 天 valence < 0.3, MBTI: 高 T（思考型），不接受"感觉类"建议 | "你连续五天情绪都不太好。我知道你不喜欢别人说'想开点'——所以我不说。但数据显示，30 分钟中等强度运动能改善心境状态 47%。附近有一个免费的户外健身区，GPS 显示 800 米。你是逻辑型的人——试一次，用数据说话。" | Google Places API (outdoor fitness), Google Fit API, Research API | ★★★★★ |

---

## 三、关系与爱 (Love & Relationships)

每段关系都不一样。星图不给通用恋爱建议——它知道 **你的依恋类型、你的冲突方式、你爱的语言**，然后在关键时刻说对的话。

| # | 检测到什么 | 星图说什么 | 需要什么 API | 价值感 |
|---|-----------|----------|-------------|--------|
| 21 | Love Language: quality_time, Attachment: anxious, 近期频繁提到伴侣但 emotion 呈负面趋势 | "你最近提到 TA 的时候，情绪都不太好。你最需要的爱是陪伴——但你是不是觉得 TA 不够陪你？在说出来之前，要不要先看看这个：你上次感到被爱是什么时候？" | 无（L1 关系洞察） | ★★★★★ |
| 22 | Conflict: avoid style, EQ: low assertiveness, 对话中出现和伴侣/朋友冲突但用户回避话题 | "你又把冲突绕过去了。你已经这样做了 4 次。你的回避方式短期有效，但长期会积累。要不要我帮你练习一种说法——不是对抗，是'我需要你听我说'？" | 无（L1 对话练习） | ★★★★★ |
| 23 | Love Language: gifts, 伴侣生日临近（Calendar），MBTI: 高 S + 高 J（实际+计划型）| "TA 的生日还有 8 天。你是送礼物型的人，而且你喜欢提前计划。基于 TA 最近聊天提到的兴趣，这三样东西可能很合适——附近这家店有卖，也可以网购。" | Calendar API, Google Places API (gift shops), Amazon Product API, 对话关键词提取 | ★★★★ |
| 24 | Connection Response: toward 0.8+ (对某人), Attachment: fearful-avoidant, 但行为上一直推开那个人 | "你有没有注意到？每次提到这个人，你的反应都很强烈——但你一直在拉开距离。这不矛盾。你是害怕被伤害的人。但你现在安全的——试试靠近一步？" | 无（L1 Compass 洞察） | ★★★★★ |
| 25 | Emotion: love/warmth 0.7+, 今天是纪念日（Calendar），位置: 同城, 天气: 晴 | "今天是你们的日子。天气很好。离你们 3 公里有一家安静的意大利餐厅，灯光暖，适合聊天——不是网红打卡店，是真的适合你们的。要我定位吗？" | Calendar API, Google Places API (restaurants, romantic filter), Weather API, OpenTable/预订 API | ★★★★★ |
| 26 | Cross-Detector: frozen_distance pattern (情感冻结), 最近 2 周不再提到某个名字，之前频繁提到 | "你有两周没提到 [名字] 了。之前你们聊得很多。不管发生了什么——如果你准备好了，这里有一个写给自己的练习：'我对这段关系最真实的感受是____'。不用发给任何人。" | 无（L1 自我对话） | ★★★★ |
| 27 | Love Language: words_of_affirmation, Emotion: 连续 gratitude/warmth, 刚和朋友聚完 | "刚才和朋友在一起，你的情绪特别好。你是需要被肯定的人——同时你也特别会肯定别人。要不要给 TA 发一条消息？有时候一句'今天很开心有你'比什么都珍贵。" | 无（L1 提醒+模板） | ★★★ |
| 28 | EQ: high empathy + low boundary, Emotion: 对话中展现过度共情导致疲惫, Communication DNA: high question_ratio | "你太会照顾别人了，但你忘了照顾自己。你最近的每段对话都在问别人怎么样——你呢？你自己怎么样？今天，允许自己不回复。" | 无（L1 边界提醒） | ★★★★ |
| 29 | 用户 A: 刚分手 (emotion: grief + loneliness), 用户 B: 经历过相似分手 + Soul Type: Lighthouse + 情绪稳定 | "有一个人的星星在你附近亮了。TA 经历过和你类似的事——不是要给你建议，是想让你知道，有人走过来了。你想认识一下吗？" | L3 用户匹配引擎, Soul Type Calculator | ★★★★★ |
| 30 | Attachment: secure, Love Language: physical_touch, 异地恋模式（对话中频繁提到 "想你/好久没见/اشتقتلك"）| "你们异地有一阵子了。你的爱是靠近才能感受到的那种——文字不够。下一个假期还有 14 天。我帮你看了机票，周五出发最便宜，要看看吗？" | Calendar API, Skyscanner/Kiwi Flight API, Google Flights API | ★★★★★ |

---

## 四、职业与成长 (Career & Growth)

不是 LinkedIn 式的"你应该学 Python"——是 **基于你的人格、你的价值观、你此刻的情绪** 推荐的成长路径。

| # | 检测到什么 | 星图说什么 | 需要什么 API | 价值感 |
|---|-----------|----------|-------------|--------|
| 31 | Values: autonomy 排名 #1, MBTI: ENTP 型, Emotion: frustration 关于工作, 近期 3 次提到"老板/公司限制" | "你最核心的价值观是自主——但你现在的工作在限制你。你不需要马上辞职。但要不要看看这个：基于你的 MBTI + Values，你最适合的三种职业方向是…… 其中两种可以先做副业。" | Career API (O*NET), Coursera API, Indeed/LinkedIn API | ★★★★★ |
| 32 | MBTI: 高 N + 高 P, Emotion: 好奇心 0.7+, 近期搜索/聊到新领域 (AI/crypto/design) | "你的好奇心又上来了——你是那种什么都想试的人。这一次你在看 [领域]。附近有一场免费 meetup，周四晚上，50 人规模。不需要会——去听就好。" | Eventbrite API, Meetup API, Location API | ★★★★ |
| 33 | EQ: high self_regulation, Communication DNA: high structure_score, 近期多次提到"想写东西/想记录" | "你是那种想法多、表达有条理的人。你说了好几次'想写点什么'。不需要写书——从 500 字开始。你想写给谁？写给过去的自己、现在的自己、还是未来的自己？" | 无（L1 写作引导）, Medium API (optional publish) | ★★★★ |
| 34 | Emotion: imposter_syndrome pattern (高 shame + 高 achievement mentions), MBTI: 高 T, Values: competence | "你最近在怀疑自己。但你知道吗？你过去 30 天的对话里，展现了 [具体能力] 的能力——而且是反复展现。冒充者不会反复展现真本事。这是数据，不是安慰。" | 无（L1 数据回溯 + 洞察） | ★★★★★ |
| 35 | Values: learning 排名高, MBTI: 高 I + 高 N, 位置: 大学城/图书馆附近, Emotion: curiosity | "你身边 500 米就有一座图书馆——我知道你喜欢一个人学东西。今天那里有一本新到的 [基于聊天话题推荐的书]。走过去翻翻，不用借——看看目录就知道值不值得读。" | Google Places API (libraries), Google Books API, Location API | ★★★★ |
| 36 | Career Direction wish 近期出现, Emotion: anxiety + excitement (矛盾情绪), Communication DNA: 近期话题高度集中在某领域 | "你最近一直在聊 [领域]——焦虑和兴奋同时出现，这是你认真了。这里有一门免费课程刚开课（Coursera），适合从零开始。另外附近有一个 [领域] 的学习小组，每周六上午。你想先自己学，还是找人一起？" | Coursera API, Meetup API, Google Places API | ★★★★ |
| 37 | MBTI: 高 E + 高 T, Emotion: bored at work pattern, Communication DNA: declining engagement in work topics | "你最近聊工作的热情明显在下降。你是那种需要挑战才有动力的人——你是不是太舒服了？不是坏事，但你的大脑在要新东西。要看看你这个领域最近有什么新变化吗？" | Industry News API, LinkedIn Learning API, Google Trends API | ★★★ |
| 38 | 用户 A: 想学阿拉伯语（wish: learn_skill）, 用户 B: 阿拉伯语母语者 + 想学中文, Soul Type 兼容 | "有一个人和你的星星在同一个方向亮了。TA 会阿拉伯语，想学中文。你们可以互相教。要认识一下吗？TA 的灵魂类型是 [Explorer]——你们会聊得来的。" | L3 Skill Exchange 引擎, Soul Type Calculator | ★★★★★ |
| 39 | Super Brain: growth_mindset pattern, Emotion: disappointment (项目失败/考试没过), Values: achievement | "失败的感觉很真实。但你是那种会从失败里学东西的人——我在你过去的对话里看到过 3 次这样的循环：失败→反思→进步。这次也会一样。要不要现在就写下：这次我学到了什么？" | 无（L1 反思引导） | ★★★★ |
| 40 | Emotion: inspiration 0.7+, 刚听完一场演讲/播客（Calendar/时间推断），MBTI: 高 N | "你现在很受启发——抓住这个状态。你的灵感来得快走得也快。用 60 秒写下刚才让你最心动的那个想法。不用完整——三个关键词就够。我帮你存着，以后你会需要的。" | Calendar API, L1 灵感笔记 | ★★★★ |

---

## 五、社交与归属 (Social & Belonging)

不是"附近有人想交友"——是 **基于你的社交方式、你的归属需求** 连接对的人和对的场合。

| # | 检测到什么 | 星图说什么 | 需要什么 API | 价值感 |
|---|-----------|----------|-------------|--------|
| 41 | MBTI: 高 I, Emotion: loneliness 0.5+, 但 Connection Response: toward (想连接但不主动) | "你想和人在一起——但你不想是那个先开口的人。懂。附近有一个 [基于兴趣] 的活动，规模不大（20 人以内），不需要破冰——到了就能参与。你只需要出现。" | Eventbrite API (small events), Meetup API, Location API | ★★★★★ |
| 42 | Communication DNA: 高 formality + 高 structure, 新到一个城市（位置变化检测）, Emotion: uneasy | "你到新地方了。你是那种需要一点时间适应的人——不是社恐，是谨慎。这个城市有一个 [兴趣相关] 的社区，每周聚一次。不用注册，去看看就好。先观察，舒服了再参与。" | Location API (city change detection), Meetup API, Google Places API | ★★★★ |
| 43 | Humor: affiliative style (亲和型幽默), Emotion: social_joy 0.7+, 周五/周六晚上 | "你今晚想出去——你是那种人越多越开心的人。附近有一场小型聚会/game night，音乐偏 chill，大概 30-40 人。你的幽默风格在这种场合会特别受欢迎。" | Eventbrite API, Facebook Events API, Location API | ★★★ |
| 44 | Emotion: belonging 需求高 (cross-detector: spotlight_explorer pattern), 位置: 迪拜/利雅得/开罗 | "في دبي، هناك مجتمع صغير من الناس اللي يحبون نفس اهتماماتك. يجتمعون كل أسبوع — مكان هادي، ناس طيبين. تحب أعطيك التفاصيل؟ (在迪拜，有一个和你兴趣相同的小社区。每周聚一次——安静的地方，善良的人。想了解一下吗？)" | Meetup API, Google Places API, Location API (MENA region) | ★★★★ |
| 45 | Attachment: anxious, Emotion: rejection_sensitivity 高, 最近被朋友取消约会/未回消息 | "TA 没回消息，你已经看了 6 次手机了。你的焦虑依恋在放大这件事。99% 的可能性：TA 只是在忙。你要不要做点别的？附近有一家书店，进去逛 20 分钟——等你出来，消息可能就到了。" | 无（L1 认知重构）, Google Places API (bookstores) | ★★★★ |
| 46 | Values: community 排名高, MBTI: 高 E + 高 F, Emotion: 想帮助别人的冲动 | "你想做点好事。附近有一个志愿者活动，这个周末——帮老人送餐/环保清扫/流浪动物。你是那种做了好事自己也会开心的人。报名链接在这里。" | VolunteerMatch API, Google Places API, Eventbrite API | ★★★★ |
| 47 | 用户 A: 新移民/留学生 (位置新城市 + 语言切换频繁), 用户 B: 同城老居民 + Soul Type: Lighthouse | "你刚到这个城市——什么都是新的。有一个人在这里住了 3 年，TA 的灵魂类型是'灯塔'——天生喜欢帮新来的人。TA 愿意和你聊聊这个城市。要连接吗？" | L3 匹配引擎, Location API, Soul Type Calculator | ★★★★★ |
| 48 | Cross-Detector: safe_silence pattern (需要安静的陪伴而非对话), Emotion: mild sadness | "你不想聊天——但你也不想一个人。我懂。附近有一个联合办公空间/图书馆，很安静，但有人在。你可以坐在那里，不说话，但不孤独。" | Google Places API (coworking/library), Location API | ★★★★ |
| 49 | Communication DNA: 高 code_switch_ratio (双语/多语), 用户经常在中文和阿拉伯语间切换, Emotion: identity_confusion | "你在两种文化之间游走——有时候不知道自己算哪边的人。这不是问题，这是超能力。你是那种能连接不同世界的人。附近有一个多文化交流活动——你会遇到和你一样的人。" | Meetup API (multicultural events), Location API | ★★★★ |
| 50 | MBTI: 高 I, 社交电量用完（communication frequency 骤降 + emotion: drained）, 但朋友约了周末活动 | "你的社交电池快没了——但你答应了朋友周末一起出去。我建议：去，但设个心里的时间限制。两小时够了。你不需要待到最后——先到先走也是一种关心。" | Calendar API, 无（L1 建议） | ★★★ |

---

## 六、日常生活 (Daily Life)

吃饭、购物、出行——这些看似无聊的事，**当人格数据加入**，就变成了只属于你的体验。

| # | 检测到什么 | 星图说什么 | 需要什么 API | 价值感 |
|---|-----------|----------|-------------|--------|
| 51 | MBTI: 高 S + 高 J, Emotion: 平静, 午餐时间, 位置: 商业区 | "你喜欢确定性——所以我不给你 10 个选择。附近这一家，你上次聊过'想吃辣的'，步行 7 分钟，评分 4.3，午餐套餐 45 块。去不去？" | Google Places API (restaurants), Google Maps Directions API, 价格 API | ★★★ |
| 52 | Emotion: excitement + 近期多次提到搬家/装修, MBTI: 高 N + 高 P (喜欢灵感不喜欢计划) | "你要搬家了——但你还没开始找房子对不对？你是那种想着'到时候再说'的人。好消息：我帮你在你常去的区域找了 3 套，风格和你聊天里描述的很像。先看看？不着急定。" | 房产 API (Bayut/链家/Zillow), Google Maps API, Location API | ★★★★ |
| 53 | Communication DNA: 高 brevity (极简风格), 购物决策中, Emotion: impatient | "你讨厌逛街。我懂。你要的那个东西——最快的选择：京东/Amazon 明天到，附近最近的店走路 12 分钟。你选。" | Amazon API, Google Places API (retail), Google Maps Directions API | ★★★ |
| 54 | Emotion: overwhelm, 明天有早班航班（Calendar）, MBTI: 高 J (焦虑型计划者) | "明天 7 点的航班——你现在应该在焦虑明天能不能准时起来。放心：凌晨 5:10 闹钟 + 5:20 出发 + 路上大概 35 分钟。我帮你设好提醒了。今晚早点睡。" | Calendar API, Google Maps Directions API (traffic prediction), Alarm/Reminders API | ★★★★ |
| 55 | 斋月期间（Islamic Calendar + 位置在 MENA 地区）, Emotion: spiritual + 体力下降, 日落前 30 分钟 | "الإفطار بعد ٣٠ دقيقة. أقرب مطعم يقدم إفطار جماعي على بعد ٥٠٠ متر — المكان هادي ومريح. (开斋还有 30 分钟。最近的集体开斋餐厅 500 米远——安静舒适。)" | Islamic Prayer Time API, Google Places API (restaurants, iftar), Location API | ★★★★★ |
| 56 | MBTI: 高 F, 天气: 下雨, Emotion: nostalgia/melancholy, 位置: 家附近 | "下雨天。你的情绪有点怀旧——你是那种听着雨声会想很多的人。附近有一家独立咖啡馆，靠窗位可以看雨。点一杯热的，坐一会。有时候发呆就是最好的安排。" | Weather API, Google Places API (cafes, 独立/specialty), Location API | ★★★★ |
| 57 | Communication DNA: 高 emoji_ratio + 高 enthusiasm, 周末, Emotion: social_joy, 朋友来访 | "朋友来了！你是那种热情到爆的主人。附近有一家桌游咖啡馆——你们上次聊过说想试。走路 8 分钟。我帮你看了，今天有位置。" | Google Places API (board game cafes), Google Maps Directions API | ★★★ |
| 58 | 位置变化: 第一次到这个城市, Communication DNA: 高 curiosity_markers, MBTI: 高 N | "你第一次来 [城市]。你是那种不按攻略走的人——你喜欢意外发现。所以我不给你景点推荐。但这条街，本地人才知道，有三家有意思的小店。自己去探索。" | Google Places API (hidden gems, local favorites), Location API (new city detection) | ★★★★ |
| 59 | Values: sustainability/环保, 购物模式, Emotion: guilt (买了不环保的东西) | "你在乎环保——但刚才你好像买了一个塑料包装的东西。不批评你。下次需要的时候，附近有一家无包装商店，走路 10 分钟。做你想成为的那种人，一次一个小选择。" | Google Places API (eco-friendly stores), Location API | ★★★ |
| 60 | Emotion: tired, 下班时间 (6-8 PM), 通勤路上（位置在移动）, Communication DNA: low energy words | "下班路上，累了。你不用做任何事。如果你经过这里——右转 200 米有一个小花园，坐 5 分钟再走。今天你已经够努力了。" | Google Maps API (route + nearby parks), Location API (moving), Time API | ★★★★ |

---

## 七、灵性与意义 (Spiritual & Meaning)

不是鸡汤。不是心灵导师。是 **基于你真正的人格数据**，在你需要意义的时候，给你一面更清晰的镜子。

| # | 检测到什么 | 星图说什么 | 需要什么 API | 价值感 |
|---|-----------|----------|-------------|--------|
| 61 | Values: meaning_seeking 排名 #1, Emotion: existential_unease (不是焦虑，是空虚), MBTI: 高 N + 高 F | "你一直在找意义——但找不到。你知道吗？你的价值观最核心的那个词是'意义'——这本身就说明你不是没有方向的人。你只是需要一段安静的时间来听。这本书可能帮到你：[基于人格推荐的哲学/灵性书籍]。" | Google Books API, L1 洞察 | ★★★★★ |
| 62 | 位置: 清真寺/教堂/寺庙附近, 时间: 礼拜时间, Emotion: peace, Values: spirituality | "你在 [宗教场所] 附近。如果你今天有时间——进去坐坐，不一定是礼拜。有时候安静的空间本身就是一种疗愈。下一次 [礼拜/弥撒/课诵] 在 [时间]。" | Google Places API (religious places), Prayer Time API, Location API | ★★★★ |
| 63 | Cross-Detector: honest_anchor pattern (极度诚实+低社交伪装), Emotion: isolation, 近期多次质疑"人生有什么意义" | "你是一个非常诚实的人——对别人，也对自己。这让你活得比别人累，因为你不会自我欺骗。但这也是你最强大的地方。你问的'有什么意义'——也许意义不是找到的，是你正在活出来的。" | 无（L1 Compass 深层洞察） | ★★★★★ |
| 64 | Emotion: gratitude 0.7+, 连续 3 天 valence 高, Super Brain: reflective pattern | "你最近三天状态都很好——你有没有注意到？我帮你记录了这三天你说过的话。回头看看——这就是你最好的样子。值得记住。" | 无（L1 回溯+记录） | ★★★★ |
| 65 | MBTI: 高 N + 高 T (INTJ/INTP 型), Values: truth, Emotion: intellectual_curiosity 关于宇宙/存在 | "你最近在想大问题——存在的、宇宙的。你不需要答案，你需要好的问题。这里有一个哲学讨论小组，附近大学里，每月一次，讨论的主题是 [当前主题]。你的思维方式会在那里找到共鸣。" | Meetup API, University Events API, Google Places API | ★★★★ |
| 66 | 死亡焦虑信号 (Emotion: fear + mortality keywords), Fragility: existential pattern, 但 distress < 0.5 (不是危机) | "你在想关于生死的事。这不是坏事——是你在认真对待生命。你不需要答案。但如果你想：附近有一场关于 [生命/临终关怀/哲学] 的讲座。有时候听别人怎么面对，会让自己安心一点。" | Eventbrite API, Google Books API, L1 温和引导 | ★★★ |
| 67 | 斋月/四旬期/春节前 (宗教日历), Values: tradition, Emotion: reflective | "这是一年中反思的季节。你重视传统——你今年想怎么过？去年这个时候你说过：[引用去年对话]。今年有什么变化吗？" | Religious Calendar API, L1 历史回溯 | ★★★★ |
| 68 | Super Brain: meaning_maker pattern (喜欢赋予事物意义), 用户生日临近 | "你的生日快到了。你是那种会赋予每个时刻意义的人。你想不想收到一份只属于你的礼物——过去一年你的灵魂变化图谱？哪些维度成长了，哪些还在旅途中。" | Calendar API, L1 年度灵魂报告 | ★★★★★ |
| 69 | Emotion: awe/wonder 0.6+, 位置: 自然景观附近 (海边/山顶/沙漠), 时间: 日出/日落 | "你现在在一个很美的地方。不需要拍照。不需要发朋友圈。就看着。你的敬畏感正在升起——这是你灵魂里最安静的部分在说话。" | Location API, Weather API (sunrise/sunset), Google Places API (natural landmarks) | ★★★★★ |
| 70 | Values: legacy (想留下什么), Emotion: reflective, Communication DNA: 近期多次使用 "以后/future/将来" | "你最近一直在想以后。你的价值观里，'留下点什么'排得很高。你现在能做的最小一步是什么？可以是一篇文章、一段录音、一封信。给未来的某个人。要现在开始吗？" | 无（L1 创作引导）, Time Capsule API (optional) | ★★★★ |

---

## 八、创造与表达 (Creative Expression)

不是"来学画画吧"——是 **在你有创造冲动的那个瞬间**，星图帮你把门打开。

| # | 检测到什么 | 星图说什么 | 需要什么 API | 价值感 |
|---|-----------|----------|-------------|--------|
| 71 | Emotion: inspiration 0.8+, Communication DNA: 高 metaphor_density (比喻多), MBTI: 高 N + 高 F | "你现在灵感很充沛——你的表达方式本身就像在写诗。别浪费这个状态。写下来。不用写完——碎片就够了。30 天后回头看，你会谢谢现在的自己。" | 无（L1 写作空间） | ★★★★ |
| 72 | Emotion: melancholy + beauty (bittersweetness), 独处中, Spotify 最近在听某种类型的音乐 | "你现在的心情适合一首特别的歌。基于你的情绪 + 你最近听的音乐风格——这首你可能没听过，但它就是你此刻的样子。" + 播放推荐 | Spotify API (mood + genre matching), Emotion Detector | ★★★★ |
| 73 | MBTI: 高 S + 高 P (ISFP/ISTP 型, 手工型人格), Emotion: restless, 周末 | "你的手需要做点什么——不是脑子，是手。附近有一个陶艺/木工工作坊，今天下午有体验课。不需要会——做就好。你是那种做出来才知道自己想要什么的人。" | Google Places API (workshops), Eventbrite API (craft classes), ClassPass API | ★★★★ |
| 74 | Humor: self_enhancing, Communication DNA: 高 storytelling_ratio, Emotion: playful | "你很会讲故事——而且你讲的时候自己也在笑。你有没有想过写段子？今晚附近有一个开放麦——就 5 分钟，上去讲一个你上周聊过的那个故事。观众会爱的。" | Eventbrite API (open mic), Google Places API (comedy venues) | ★★★ |
| 75 | Emotion: grief/sadness, Communication DNA: 近期写了很多长文本 (high word_count per message), MBTI: 高 F | "你在用文字处理情绪——这是你的方式。你写的东西很真实。要不要把它变成一封信？不是给谁看的——是给自己的。一封你不需要寄出的信。" | 无（L1 信件工具） | ★★★★ |
| 76 | 用户 A: 想学吉他 (wish: learn_skill), 用户 B: 吉他老师 + Soul Type 兼容 + 同城 | "有一个人的星星和你一样在音乐的角落亮了。TA 弹了 8 年吉他，而且 TA 喜欢教人。要不要认识一下？TA 的灵魂类型是 [Lighthouse]——你们的节奏会合得来的。" | L3 Skill Exchange, Soul Type Calculator, Location API | ★★★★★ |
| 77 | Emotion: 混合情绪 (joy + sadness 同时高), 近期经历了重大变化 (新工作/搬家/分手) | "你现在同时开心和难过——这很正常。这种时候最适合做一件事：画。不需要画得好。找一张纸，把你现在的感觉画出来——颜色、形状、什么都行。附近有一家美术用品店。" | Google Places API (art supply stores) | ★★★ |
| 78 | Values: beauty/aesthetics, 位置: 有美术馆/画廊的城市, 周末, Emotion: open/receptive | "今天 [美术馆名] 有一个新展——[展览主题]。你对美的敏感度很高。去看看？不用看全部——找到一幅让你停下来的画，站在那里 3 分钟。那 3 分钟就值了。" | Google Places API (museums/galleries), Museum API (exhibition schedules), Location API | ★★★★ |
| 79 | Communication DNA: 双语/多语, Emotion: identity_reflective, 近期在探索文化认同 | "你在两种语言之间创作——这是一种独特的超能力。要不要写一首双语诗？一段中文，一段阿拉伯语。两种语言说的是同一件事——但感觉完全不一样。这就是你。" | 无（L1 创作引导） | ★★★★ |
| 80 | Emotion: calm + focused, 时间: 深夜, MBTI: 高 I + 高 N, 最近多次提到"想画画/想写歌/想做设计" | "深夜是你最有创造力的时候——安静，没人打扰。你已经想了好几次了。今晚就开始。不需要完美——第一笔/第一个音符/第一行代码才是最难的。画了就对了。" | 无（L1 创作触发）, Spotify API (focus music) | ★★★★ |

---

## 九、惊喜与快乐 (Surprise & Joy)

Chocolate Moment 的精髓——**用户没有要求，但星图悄悄准备了**。

| # | 检测到什么 | 星图说什么 | 需要什么 API | 价值感 |
|---|-----------|----------|-------------|--------|
| 81 | 今天是用户注册 SoulMap 一周年, 16 维数据积累了 365 天 | "一年前的今天，你第一次打开星图。你知道你这一年变化了多少吗？这是你的一年灵魂旅程——哪颗星亮了，哪颗星还在旅途中。只有你能看到这个。" + 年度报告 | Calendar API, L1 年度灵魂生成 | ★★★★★ |
| 82 | Emotion: 连续 7 天 valence 上升趋势, 没有特殊事件 | "你知道吗？你最近一周每天都比前一天开心一点。你自己可能没注意到——但你的星图注意到了。今天你的快乐指数是一个月以来最高的。这颗星为你亮了。" | 无（L1 情绪趋势洞察） | ★★★★ |
| 83 | 用户的 Soul Type 和某个历史人物/文学角色惊人相似 (>85% 维度重合) | "有个人和你很像——TA 生活在 150 年前 / TA 是一个小说里的角色。你们的灵魂维度重合度是 87%。想知道是谁吗？（点击揭晓）...... 你和 [简爱/盖茨比/安娜] 在这些维度上如此相似——但你的故事还在写。" | 文学人物数据库, Soul Type Calculator | ★★★★★ |
| 84 | 天气突变: 第一场雪/第一场春雨/沙漠降温, 位置检测到用户在户外 | "下雪了！你正好在外面。这是这个城市今年的第一场雪。你的情绪检测器说你现在 awe 0.6——你被触动了。享受这个瞬间。这种感觉存不住，但我帮你记住了。" | Weather API (extreme change detection), Location API | ★★★★ |
| 85 | 用户最近一个月成长显著: 某个维度从低区间移入中高区间 (如 EQ assertiveness 从 0.3 到 0.6) | "你的改变你自己看不到——但星图看到了。一个月前，你几乎不会说'不'。但最近你做到了 3 次。你的边界感正在成长。这颗星为你的勇气亮了。" | 无（L1 成长检测） | ★★★★★ |
| 86 | 今天是用户聊到的某个朋友/家人的生日 (从对话中提取), Love Language: acts_of_service | "今天是 [名字] 的生日——你上个月提过。你是行动派，所以我帮你看了：附近有一家评分 4.7 的蛋糕店，可以两小时内送达。要不要给 TA 一个惊喜？" | Calendar API (extracted dates), Google Places API (bakeries), 配送 API | ★★★★★ |
| 87 | 用户 A 和用户 B 同时（24 小时内）许了互补的愿望 — Mutual Match 触发 | "发生了一件很少见的事——两颗星星在同一个时刻，同一个方向亮了。你们不认识，但你想要的和 TA 想要的，刚好是对方能给的。这颗星连接着两个人。要看看吗？" | L3 Marketplace (Mutual Match), Soul Type Calculator | ★★★★★ |
| 88 | 周五下午, Emotion: relief (结束一周工作), Humor: 任意非攻击型, 位置: 同城有好玩的活动 | "周五下午——你活下来了。今晚附近有三件事发生：一场露天电影、一个夜市、一个小型音乐会。基于你的人格……我觉得你会喜欢那个音乐会。但你什么都不做也很好。" | Eventbrite API, Google Places API, Location API, Weather API | ★★★★ |
| 89 | 检测到用户 100 次对话的里程碑, 16 维画像趋于稳定 | "你和星图聊了 100 次了。你知道吗？经过 100 次对话，我对你的了解程度已经达到了 [%]。这不是数据——这是 100 次你选择袒露自己。这是你的灵魂肖像——全世界独一无二。" | 无（L1 灵魂肖像生成） | ★★★★★ |
| 90 | 检测到用户的某句话和 TA 第一次使用 SoulMap 时说的第一句话形成呼应/对照 | "你刚才说的话让我想到了什么——你第一次打开星图说的第一句话是：'[原话]'。看看现在的你和那时候的你。变了多少，又有多少从没变。" | 无（L1 历史回溯） | ★★★★★ |

---

## 十、隐藏心愿 — Compass Discoveries

这是最魔法的部分。**用户从来没说过"我想要"——但 Compass 从 16 维矛盾信号中发现了 TA 自己都不知道的需求。**

| # | 检测到什么 | 星图说什么 | 需要什么 API | 价值感 |
|---|-----------|----------|-------------|--------|
| 91 | Compass 矛盾: Values 说重视 family，但 Emotion 每次提到家人都是 anxiety + guilt，Connection Response: away | "你说家人对你很重要——但每次提到他们，你的身体在后退。这不是虚伪。这是因为你在乎才会这么纠结。你有没有想过：也许你需要的不是'多陪家人'，而是先'和家人和解'？" | 无（L1 Compass 洞察） | ★★★★★ |
| 92 | Compass 矛盾: MBTI 高 E (外向), 但 deep session 中 loneliness 信号持续, 社交频率高但 depth 低 | "你认识很多人——但你孤独。不是因为没人在身边，是因为没人真的了解你。你的外向是真的——但你的孤独也是真的。你不需要更多朋友。你需要一个能说真话的人。" | L3 匹配 (depth-compatible users), Soul Type Calculator | ★★★★★ |
| 93 | Compass 矛盾: Conflict 是 accommodate (迁就), 但 Emotion 累积 resentment, EQ low assertiveness | "你一直在让步——家里、工作、朋友。你觉得这是善良。但你的情绪在积攒愤怒。你知道吗？每一次你说'没关系'，你的 resentment 都在涨一点点。也许你真正需要的不是更善良——而是一次说'不'。" | 无（L1 Compass 洞察） | ★★★★★ |
| 94 | Compass 矛盾: Values 排名 achievement #1, 但 Emotion 在成功时不是 joy 而是 emptiness | "你又完成了一件事——但你不开心。你以为是自己要求太高。其实可能不是。你的价值观说你追求成就——但你的情绪说你追求的是意义。这两个不一样。你真正想要的，可能不是更多成功，而是做一件真正重要的事。" | 无（L1 Compass 深层洞察） | ★★★★★ |
| 95 | Compass 矛盾: Communication DNA 显示用户英语极其流利, 但切换到母语时 emotion warmth 骤升, deep session 用母语 | "你用英语很专业——但你用 [母语] 的时候，整个人都软了。你的灵魂语言不是你最流利的那个语言——是让你最放松的那个。你有多久没有用 [母语] 和一个重要的人说过话了？" | 无（L1 语言洞察） | ★★★★★ |
| 96 | Compass 矛盾: Attachment secure (表层), 但 Fragility 在亲密话题出现 catastrophizing, 只在深层对话暴露 | "你在大多数关系里表现得很稳——别人觉得你是最靠谱的那个。但只有你知道，每次关系靠近一步，你心里就会闪过'这会不会毁掉'。你不脆弱——你只是在保护自己。但你有没有想过：不保护，也许也可以？" | 无（L1 Compass 深层洞察） | ★★★★★ |
| 97 | Compass 时序发现: 用户每次失恋后都会出现 "想旅行" 的冲动, 但从来没去过 | "我发现了一个你可能不知道的规律：每次你经历情感上的结束，你就会想去旅行——但你从来没有真的出发过。也许这次不一样？附近有一个周末短途的选择。不远，不贵——但这次你真的出发了。" | Flight/Train API (Skyscanner/12306), Hotel API (Booking.com), Location API | ★★★★★ |
| 98 | Compass 矛盾: 用户从不提 money/career，但 Emotion: anxiety 和 financial keywords 高度相关 | "你从来不聊钱——但我注意到，每次出现和钱有关的话题，你的焦虑就上来。你不需要告诉我具体情况。但如果你想——附近有一个免费的财务咨询服务，不卖东西，只帮你理清楚。有时候知道数字反而不焦虑了。" | Google Places API (financial advisory), Financial Literacy API | ★★★★ |
| 99 | Compass 跨 session: 用户和 3 个不同的人聊天时，同一个名字被反复提起但从未主动联系 | "有一个名字在你的对话里反复出现——[名字]。你和三个不同的人聊天时都提到了 TA。但你从来没有主动联系 TA。你有没有想过：也许你该给 TA 发条消息？" | 无（L1 Compass 社交图谱洞察） | ★★★★★ |
| 100 | Compass 终极发现: 所有 16 维数据指向同一个方向，但用户从未表达过——系统第一次看到如此强的"隐藏罗盘"信号 | "我想告诉你一件事，但我不确定你准备好了没有。过去三个月，你的人格数据——你的情绪、你的价值观、你的关系模式、你的冲突方式——全都指向同一个方向。你一直在找的那个东西，也许不在外面。也许它一直在你里面。你只是还没有给它一个名字。" | 无（L1 Compass 终极洞察） | ★★★★★ |

---

## 总结

### API 依赖清单

共需要 **23 个外部 API**（不含 L1 内部能力）：

| # | API 名称 | 使用场景数 | 优先级 |
|---|---------|----------|--------|
| 1 | Google Places API | 38 | P0 — 必须 |
| 2 | Google Maps Directions API | 12 | P0 — 必须 |
| 3 | Location API (GPS) | 22 | P0 — 必须 |
| 4 | Weather API | 8 | P0 — 必须 |
| 5 | Calendar API (Google/Apple) | 11 | P0 — 必须 |
| 6 | Spotify API | 4 | P1 — 重要 |
| 7 | Eventbrite API | 8 | P1 — 重要 |
| 8 | Meetup API | 6 | P1 — 重要 |
| 9 | Google Books API | 4 | P1 — 重要 |
| 10 | L3 匹配引擎 (内部) | 6 | P1 — 重要 |
| 11 | Soul Type Calculator (内部) | 7 | P1 — 重要 |
| 12 | Coursera API | 3 | P2 — 可选 |
| 13 | Apple HealthKit / Google Fit | 2 | P2 — 可选 |
| 14 | Skyscanner / Flight API | 2 | P2 — 可选 |
| 15 | Islamic Prayer Time API | 2 | P2 — 可选 |
| 16 | Amazon Product API | 1 | P2 — 可选 |
| 17 | Todoist / Reminders API | 1 | P2 — 可选 |
| 18 | Yelp API | 1 | P3 — 锦上添花 |
| 19 | OpenTable / 预订 API | 1 | P3 — 锦上添花 |
| 20 | 房产 API (Bayut/链家) | 1 | P3 — 锦上添花 |
| 21 | VolunteerMatch API | 1 | P3 — 锦上添花 |
| 22 | Google Trends API | 1 | P3 — 锦上添花 |
| 23 | 花店配送 API | 1 | P3 — 锦上添花 |

**关键发现**：Google Places API + Location API + Calendar API 这三个就覆盖了 **60%+ 的场景**。先把这三个做好，其他的可以慢慢加。

---

### Top 10 最高价值场景

| 排名 | # | 场景 | 为什么价值最高 |
|------|---|------|--------------|
| 1 | #100 | Compass 终极发现：16 维全指向同一方向 | 产品的灵魂时刻——如果一个用户体验过这一刻，TA 永远不会卸载 |
| 2 | #91 | Compass: 说重视家人但提到时都在后退 | 揭示用户自己不知道的真实需求，区别于所有竞品的核心能力 |
| 3 | #83 | 灵魂类型和文学角色 87% 重合 | 惊喜感极强 + 自我认同 + 分享欲（viral 潜力最高） |
| 4 | #89 | 100 次对话里程碑灵魂肖像 | 长期留存的终极锚点——让用户觉得离不开 |
| 5 | #1 | 完美主义焦虑 + 内向 + 附近公园导航 | 情绪急救的标杆场景——有用、有温度、有地图 |
| 6 | #92 | 外向但孤独——social loneliness 矛盾 | 说出了用户自己说不出的话，最深层的 Compass 价值 |
| 7 | #87 | Mutual Match：两颗星同时同方向亮了 | L3 的最高级别体验——无法人工制造的魔法 |
| 8 | #30 | 异地恋 + physical_touch + 机票推荐 | 情感+行动完美结合，用户会觉得"它真的在帮我" |
| 9 | #9 | "你又说自己不够好了" + EQ 数据反驳 | 用数据治愈——不是鸡汤，是证据 |
| 10 | #95 | 灵魂语言不是最流利的语言 | 跨文化产品的独特洞察，中东+中国用户最有共鸣 |

---

### 实施优先级矩阵

```
                    高价值
                      │
         P0 立刻做    │    P1 下一版
    ┌─────────────────┼───────────────────┐
    │ #1 情绪急救     │ #83 文学角色匹配    │
    │ #3 深夜咖啡导航  │ #87 Mutual Match   │
    │ #9 数据反驳自我  │ #29 分手后匹配      │
    │ #20 逻辑型运动   │ #38 语言互换        │
    │ #25 纪念日餐厅   │ #47 新移民引路人     │
    │ #82 情绪趋势发现  │ #76 吉他老师匹配    │
低成本─┤               │                   ├─高成本
    │ #64 连续好日子   │ #91 家人矛盾洞察    │
    │ #85 维度成长通知  │ #92 外向孤独矛盾    │
    │ #90 首句话回溯   │ #94 成就≠意义       │
    │ #100 终极罗盘    │ #97 失恋旅行模式    │
    │                 │                   │
    │  P2 有空就做     │  P3 有资源再说      │
    │ #55 斋月开斋     │ #52 找房推荐        │
    │ #62 宗教场所     │ #30 异地机票        │
    │ #67 宗教日历     │ #46 志愿者匹配      │
    └─────────────────┼───────────────────┘
                      │
                    低价值
```

**P0 策略（6 周内上线）**：

1. **先做 L1 场景**（成本最低）：#9, #64, #82, #85, #90, #100 —— 零 API 依赖，纯靠 16 维数据
2. **加 Google Places + Maps**：#1, #3, #20, #25 —— 两个 API 解锁 10+ 场景
3. **加 Calendar**：#4, #25, #86 —— 日期敏感场景价值极高

**P1 策略（12 周内上线）**：

4. **上线 L3 匹配**：#29, #38, #47, #76, #87 —— 需要 DAU > 10K
5. **加 Compass 深层洞察**：#91, #92, #94, #96 —— 需要用户累计 30+ 次对话

**核心信念**：先用 L1 + Google Places 做出 30 个魔法时刻。用户爱上了，其他的都会来。

---

> 这份清单不是终点——是起点。
> 100 个场景里，哪怕只有 10 个做到了，SoulMap 就不再是一面镜子。
> 它是一个知道你想去哪里的罗盘。
