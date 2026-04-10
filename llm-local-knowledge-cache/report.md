# LLM 本地知识缓存系统调研报告
> **主题**: LLM 本地知识缓存系统设计 — 通过本地验证知识库减少 LLM 幻觉  
> **日期**: 2026-04-10  
> **范围**: 2025-04 ~ 2026-04  
> **调研项目数**: 27  

---

## 目录


### 判定机制

1. [Adaptive RAG](#adaptive-rag) — research  
2. [CRAG (Corrective RAG)](#crag-corrective-rag) — research  
3. [FLARE](#flare) — research  
4. [RouteRAG](#routerag) — research  
5. [Rowen](#rowen) — research  
6. [SKR / SeaKR](#skr--seakr) — research  
7. [Self-RAG](#self-rag) — research  

### 缓存工程

8. [Amazon Bedrock Verified Semantic Cache](#amazon-bedrock-verified-semantic-cache) — production-ready  
9. [Bifrost](#bifrost) — early-stage  
10. [GPTCache](#gptcache) — early-stage  
11. [Krites (Apple)](#krites-apple) — research  
12. [语义缓存方案对比 (Redis / LangChain / 轻量方案)](#语义缓存方案对比-redis--langchain--轻量方案) — production-ready  
13. [Upstash Semantic Cache](#upstash-semantic-cache) — production-ready  

### MCP生态

14. [ConPort (Context Portal)](#conport-context-portal) — early-stage  
15. [MCP 知识服务架构](#mcp-知识服务架构) — production-ready  
16. [Mem0](#mem0) — production-ready  
17. [Zep / Graphiti](#zep--graphiti) — production-ready  
18. [bigmemory/.pipeline/ 现有架构](#bigmemorypipeline-现有架构) — production-ready  
19. [txtai MCP Server](#txtai-mcp-server) — production-ready  

### 验证核查

20. [AFEV](#afev) — research  
21. [MiniCheck](#minicheck) — production-ready  
22. [RAGLens / SAE-based](#raglens--sae-based) — research  
23. [SAFE (Google DeepMind)](#safe-google-deepmind) — research  

### 架构范式

24. [A-RAG (Agentic RAG)](#a-rag-agentic-rag) — research  
25. [Anthropic Contextual Retrieval](#anthropic-contextual-retrieval) — production-ready  
26. [Domain-Grounded Tiered Retrieval](#domain-grounded-tiered-retrieval) — research  
27. [Microsoft GraphRAG](#microsoft-graphrag) — production-ready  

---

## 详细调研结果


---

## 判定机制

### Adaptive RAG

#### 基本信息

**name**: Adaptive RAG

**category**: 判定机制

**source**: https://arxiv.org/abs/2403.14403

**maturity**: research

#### 核心机制

**architecture**: Adaptive-RAG 在标准 RAG 管线前插入一个轻量查询复杂度分类器（T5-Large，770M 参数），将输入查询路由到三类策略：
(A) 无检索（参数化直接回答）、
(B) 单步检索（one-shot RAG）、
(C) 多步迭代检索（iterative RAG）。
分类器通过自动化标注生成训练标签——对各策略实际运行结果和数据集归纳偏差（单跳/多跳）进行采样，共使用 6 个数据集各 400 条查询训练。
推理时分类器仅增加极小额外延迟（<100ms），而多步迭代策略平均耗时 27 秒，无检索仅 0.35 秒，路由节省显著。


**retrieval_trigger**: rl-learned — 通过训练得到的 T5-Large 分类器根据查询复杂度（单跳/多跳/无需检索）动态路由，等价于学习得到的策略；非固定规则，而是从数据中习得的判定函数。

**verification_method**: none — Adaptive-RAG 本身不含验证机制，专注于检索策略的路由决策；验证质量依赖下游 RAG 系统。

**cache_tier_strategy**: none — 不涉及缓存机制。

#### 技术特性

**knowledge_source_types**: 开放域问答语料库（Wikipedia 等），复用下游 RAG 系统的知识源；知识源类型由路由后的具体 RAG 策略决定

**retrieval_method**: 复用下游检索器（论文实验中使用 BM25 和稠密检索），分类器本身不直接检索

**hallucination_mitigation**: 通过避免对简单查询进行不必要的检索（减少知识冲突来源），并对复杂查询启用多步迭代检索（提升事实覆盖度），间接降低幻觉率。核心贡献是'用对策略'而非引入新的验证机制。

**offline_capability**: hybrid — 分类器可本地运行（T5-Large 开源），下游 RAG 系统的离线能力取决于具体配置

**local_model_support**: 支持 — T5-Large 分类器完全开源可本地部署；下游 LM 支持 FLAN-T5 等开源模型

**embedding_strategy**: standard — 分类器使用标准文本分类，不涉及 embedding；下游检索策略根据配置而定

#### 实用性评估

**setup_complexity**: low — 仅需部署 T5-Large 分类器（约 3GB），接入已有 RAG 管线；GitHub 代码已开源（starsuzi/Adaptive-RAG）

**token_cost**: 降低 — 对简单查询路由到无检索策略，节省检索 + 上下文 token；对复杂查询使用多步迭代，质量更高但成本也更高；整体 token 消耗低于始终多步检索策略

**latency**: 秒级 — 分类器延迟 <100ms 可忽略；端到端延迟由路由策略决定：无检索 0.35s，单步 3.08s，多步 27.18s

**dqn10_fit**: 契合度较高。
T5-Large 分类器可以学习识别 DQN/强化学习领域的查询复杂度：简单定义类查询无检索直答，多跳推理类查询触发迭代检索。
集成到 MCP 工具链较简单，仅需在现有 RAG 调用前插入分类路由层。
bigmemory/.pipeline/ 数据可作为分类器的领域适配训练集（少量标注即可）。
对单人科研工作流的主要价值：大幅节省在简单查询上的检索开销。


#### 科研适配

**domain_adaptability**: 强 — 分类器可在少量领域数据上微调，适配强化学习/DQN 专域查询复杂度分布

**incremental_update**: 支持 — 知识库更新由下游 RAG 系统处理；分类器可在新领域数据上增量微调

**citation_traceability**: source-link — 依赖下游 RAG 系统的溯源能力；分类器本身不提供溯源

**temporal_awareness**: static — 无时间感知；知识时效性由下游检索库决定

**provenance_tracking**: source-link — 溯源能力由下游 RAG 系统决定

**memory_consolidation**: manual — 分类器和检索库均需人工维护


### CRAG (Corrective RAG)

#### 基本信息

**name**: CRAG (Corrective RAG)

**category**: 判定机制

**source**: https://arxiv.org/abs/2401.15884

**maturity**: research

#### 核心机制

**architecture**: CRAG 在标准 RAG 管线后插入三级纠错模块：
(1) 检索评估器——基于 T5 微调的轻量模型（0.77B 参数），对每个「问题-文档」对打置信度分；

(2) 动作触发器——依据分数阈值选择三种动作：高置信 Correct（精炼文档）、低置信 Incorrect（丢弃，改用网络搜索）、中间 Ambiguous（结合两者）；

(3) 知识精炼算法——分解-重组算法将文档切分为条带（strip），逐条评估相关性后重组，去除无关段落噪声。
网络搜索路径通过 ChatGPT 重写查询、调用 Google API，优先纳入 Wikipedia 结果后同样经过精炼算法处理。


**retrieval_trigger**: confidence-based — 检索评估器的置信度分数驱动触发逻辑：高于上阈值进行精炼式使用，低于下阈值触发网络搜索替代，介于两者之间则混合两路结果。

**verification_method**: retrieval-based — 检索评估器在事实上是一个相关性验证器，对检索结果进行可靠性评分后决定是否接受；分解-重组算法进一步在段落内部做细粒度可靠性过滤。

**cache_tier_strategy**: none — CRAG 专注于检索纠错而非缓存。

#### 技术特性

**knowledge_source_types**: 本地检索库（论文实验中用 Wikipedia）+ 网络实时搜索（Google API）；低置信时自动切换到网络来源

**retrieval_method**: 向量语义检索（本地库）+ 网络关键词检索（Google API）混合；精炼后使用相关性评估器二次过滤

**hallucination_mitigation**: 核心机制：不使用低置信检索结果（宁可丢弃再搜索），避免低质量上下文引导模型产生错误事实；
分解-重组算法去除文档内无关条带，防止无关信息污染生成。
评估器在 PopQA 上准确率 84.3%，远超 ChatGPT 评估基线（58-64.7%），保证纠错决策本身的可靠性。


**offline_capability**: hybrid — 本地检索路径可离线运行；Incorrect 触发时需要在线 Google API；Ambiguous 路径两者兼用

**local_model_support**: 支持 — T5-based 评估器可本地部署；生成器可换用本地 LLM；但网络搜索路径依赖外部 API

**embedding_strategy**: standard — 使用标准向量检索；评估器使用 T5 分类而非 embedding 相似度

#### 实用性评估

**setup_complexity**: medium — 需要微调 T5 评估器（论文提供 PopQA 微调权重）、配置 Google API、搭建本地检索库；三级动作逻辑实现中等复杂度

**token_cost**: 增加 — 分解-重组步骤需要额外 LLM 调用进行条带相关性评估；Ambiguous 路径双路检索增加上下文 token；但精炼后的上下文比原始文档更精简，生成阶段 token 可能减少

**latency**: 秒级 — 本地评估器 <500ms；精炼算法逐条带评估增加 1-3 秒；网络搜索路径额外增加 1-5 秒；总延迟 2-10 秒

**dqn10_fit**: 契合度中等。
CRAG 的核心价值在于'不相信低质量检索结果'，适合 DQN10 场景中处理过时或无关的论文检索结果。
可将 T5 评估器替换为对强化学习文献相关性评分的轻量分类器。
网络搜索路径与 MCP 的 WebSearch 工具可直接对接。
主要限制：网络搜索触发路径增加延迟且依赖外部 API；
评估器需要领域标注数据微调。


#### 科研适配

**domain_adaptability**: 中等 — 评估器在 PopQA 上微调，迁移到强化学习领域需要新的标注数据；精炼算法与领域无关

**incremental_update**: 支持 — 本地检索库可增量更新；评估器定期重训以适应新领域文献

**citation_traceability**: chunk-level — 分解-重组算法精确到文档条带级别，可追溯哪些条带被保留使用

**temporal_awareness**: static — 无时间感知；网络搜索路径天然获取最新信息

**provenance_tracking**: chunk-level — 精炼算法保留了具体使用的段落条带，可追溯到子文档级别

**memory_consolidation**: manual — 无自动整合机制


### FLARE

#### 基本信息

**name**: FLARE

**category**: 判定机制

**source**: https://arxiv.org/abs/2305.06983

**maturity**: research

#### 核心机制

**architecture**: FLARE（Forward-Looking Active REtrieval）是主动检索的早期代表性工作。
核心思路：生成长文本时，模型先临时生成下一句话（前瞻预测），若该句中任意 token 的概率低于阈值 θ（StrategyQA 用 0.4，其余用 0.8），则以该临时句为查询触发检索，用检索结果重新生成该句。
存在两个变体：FLARE-direct（直接用临时句作检索查询）和 FLARE-instruct（指令 LM 生成隐式检索查询）。
整体是一个迭代检索-生成循环，直到生成完整输出。


**retrieval_trigger**: confidence-based — 以 token 级概率为置信度信号：若临时生成句中任意 token 概率 p < θ，触发检索（θ 值因任务调参，0.4-0.8）；高置信度则直接接受临时句继续生成，无需检索。

**verification_method**: none — FLARE 本身无显式验证机制；置信度阈值是代理指标，不等于真实的事实验证；检索后直接重新生成，未核验检索结果可靠性。

**cache_tier_strategy**: none — 不涉及缓存机制。

#### 技术特性

**knowledge_source_types**: Wikipedia 段落集（论文实验主要用 DPR 检索 Wikipedia）；原则上支持任何可以向量化的文本知识库

**retrieval_method**: 向量语义检索（论文使用 BM25 和 DPR），前瞻句直接作为检索查询

**hallucination_mitigation**: 检测低置信度 token 作为模型不确定性的代理信号，在生成低置信段落时主动引入外部知识修正，避免模型在不确定时'胡乱生成'高概率但错误的词。相比始终检索，减少了高置信区段引入无关上下文导致的间接幻觉。

**offline_capability**: full-local — 所有组件（LM + 检索库 + 检索器）均可本地部署，无需在线 API

**local_model_support**: 支持 — 论文使用 GPT-3.5-turbo-instruct，但机制本身兼容任何可输出 token 概率的语言模型（包括开源 LM）

**embedding_strategy**: standard — 使用标准 BM25 或 DPR 向量检索，前瞻句作为自然语言查询直接检索

#### 实用性评估

**setup_complexity**: medium — 需要获取 token 级概率输出（某些闭源 API 不支持）、配置检索库和检索器、实现迭代生成循环；代码已开源（jzbjyb/FLARE）

**token_cost**: 增加 — 每次触发检索都生成一次临时句（额外 token），检索后重新生成该段落（重复消耗），多轮迭代累积成本显著高于单次检索

**latency**: 秒级 — 每次前瞻预测 + 检索 + 重生成约 1-3 秒；长文本生成中可能触发多次检索，总延迟随文本长度和触发频率线性增长，分钟级长文本任务延迟显著

**dqn10_fit**: 契合度中等偏低。
FLARE 的置信度触发机制理论上适合 DQN10 的'不确定时才检索'需求，但实际集成有以下障碍：
(1) 需要 token 级概率输出，Claude API 不提供该接口；

(2) 论文验证场景是长文本生成（WikiAsp/ASQA），与 DQN10 的短 QA 场景匹配度有限；

(3) 迭代生成-检索-重生成的循环实现复杂度较高。
建议参考其核心思想（前瞻+置信度触发）而非直接集成。


#### 科研适配

**domain_adaptability**: 强 — 触发机制与领域无关，只要 LM 能输出 token 概率；领域知识存入检索库即可适配

**incremental_update**: 支持 — 检索库可增量更新，无需重训 LM

**citation_traceability**: source-link — 检索时可记录使用的段落来源，但原始实现未强制要求引用追踪

**temporal_awareness**: static — 无时间感知，依赖检索库的更新频率

**provenance_tracking**: source-link — 可记录每次检索使用的段落链接，但未精确到 chunk 级

**memory_consolidation**: manual — 检索库需人工维护

#### 待核实字段

- token概率接口在当前MCP工具链中的可行性


### RouteRAG

#### 基本信息

**name**: RouteRAG

**category**: 判定机制

**source**: https://arxiv.org/abs/2512.09487

**maturity**: research

#### 核心机制

**architecture**: RouteRAG 将 RAG 重新定义为一个马尔可夫决策过程，用强化学习端到端学习统一的检索路由策略。
系统以 Qwen2.5-3B/7B-Instruct 为 backbone，通过两阶段 RL 训练：
(1) 第一阶段仅优化回答准确率（EM 奖励）；

(2) 第二阶段加入检索效率奖励（R_efficiency = 
(t_avg - t)/T，惩罚超出平均检索次数的轨迹），平衡准确率与检索成本。
模型在生成时自主选择四类动作：推理（内部推理步骤）、文本检索（`<search>` + `[passage]`）、图谱检索（`<search>` + `[graph]`）、输出答案（`<answer>`）。
图谱检索使用 HippoRAG 2 构建的知识图谱，文本检索使用标准稠密检索器。


**retrieval_trigger**: rl-learned — 通过强化学习端到端习得路由策略，模型学习在何时推理、何时检索文本、何时检索图谱、何时给出答案；策略由任务奖励和效率奖励共同塑造，而非人工设计的启发式规则。

**verification_method**: none — RouteRAG 不含显式事实验证步骤；检索结果直接注入生成上下文，依赖 RL 训练学习利用可靠证据。

**cache_tier_strategy**: none — 不涉及缓存机制。

#### 技术特性

**knowledge_source_types**: 非结构化文本（段落检索）+ 结构化知识图谱（HippoRAG 2 构建），是目前少数同时支持文本和图谱两类知识源的自适应 RAG 方法

**retrieval_method**: 混合 — 文本检索（稠密向量检索）+ 图谱遍历（HippoRAG 2），RL 策略动态选择使用哪种检索方式

**hallucination_mitigation**: RL 训练使模型学习在知识不足时才检索（避免检索过少导致的幻觉），同时通过效率奖励防止过度检索引入噪声；图谱检索对多跳推理提供更结构化的事实支撑，减少复杂推理链中的幻觉累积。

**offline_capability**: full-local — 所有组件（Qwen2.5 LM + 文本检索器 + HippoRAG 2 图谱）可本地部署

**local_model_support**: 支持 — 基于开源 Qwen2.5-3B/7B-Instruct，完全可本地部署；图谱构建使用 HippoRAG 2（开源）

**embedding_strategy**: standard — 文本检索使用标准稠密向量；图谱检索基于实体关系结构

#### 实用性评估

**setup_complexity**: high — 需要：
(1) 构建 HippoRAG 2 知识图谱（计算密集）；

(2) RL 训练流程（两阶段，10k HotpotQA 查询）；

(3) 部署 Qwen2.5 开源模型。
端到端从零构建工作量大，但可复用预训练的 RouteRAG 权重

**token_cost**: 降低（相对始终检索） — RL 训练的效率奖励促使模型减少不必要检索；与始终多步检索相比，检索次数更少；但比无检索 baseline 多消耗图谱/文本检索的上下文 token

**latency**: 秒级 — 文本检索约 500ms-1s；图谱检索取决于图谱规模，通常 1-5s；多步推理累积延迟较高

**dqn10_fit**: 契合度中等。
RouteRAG 的文本+图谱双路检索思路对 DQN10 有参考价值（bigmemory 可作为文本库，.pipeline/ 知识图谱可作为图谱库），但实际集成障碍较大：
(1) 需要重新在 DQN 领域数据上做 RL 训练；

(2) HippoRAG 2 图谱构建需要大量计算；

(3) 依赖开源 LM 而非当前 Claude MCP 架构。
建议参考其双路检索架构设计，实现层面选择更轻量方案。


#### 科研适配

**domain_adaptability**: 中等 — RL 训练在 HotpotQA 上完成，迁移到强化学习/DQN 领域需要重新收集领域训练数据并重训路由策略

**incremental_update**: 有限 — 图谱需要重构（代价高）；文本检索库可增量更新；RL 策略需定期重训以适应新数据分布

**citation_traceability**: source-link — 检索动作可记录使用的文本段落或图谱实体来源

**temporal_awareness**: static — 无时间感知；知识时效性依赖检索库和图谱的更新频率

**provenance_tracking**: source-link — 记录检索动作关联的来源（段落链接或图谱节点），未精确到声明级

**memory_consolidation**: manual — 图谱和文本库均需人工维护，图谱更新代价尤其高

#### 待核实字段

- 领域迁移后的具体性能下降幅度


### Rowen

#### 基本信息

**name**: Rowen

**category**: 判定机制

**source**: https://arxiv.org/abs/2402.10612

**maturity**: research

#### 核心机制

**architecture**: Rowen（Retrieve Only When It Needs）受神经科学启发，模拟人脑在内部思考与外部感知之间动态切换的机制。
核心模块：一致性不确定性估计器——对输入查询，生成语义等价的多语言翻译版本（或调用多个不同 LLM），分别获取响应，计算响应之间的语义不一致程度作为不确定性分数。
不确定性超过阈值时，触发外部检索补充事实；
不确定性低时，直接使用模型参数化知识作答。
检索后将外部信息注入生成过程，并再次用一致性模块评估最终输出可靠性。
发表于 SIGIR-AP 2025。


**retrieval_trigger**: confidence-based — 通过跨语言/跨模型响应一致性作为不确定性代理指标：高一致性=模型已知=直接作答；
低一致性=模型不确定=触发检索。
与 FLARE 的 token 概率方案相比，该方案无需访问 token 概率，适用于黑盒 LLM。


**verification_method**: consistency-check — 跨语言/跨模型一致性检查是核心验证机制：语义等价问题在不同语言或不同模型下的响应不一致，说明模型对该问题知识不稳定，需要外部检索验证。

**cache_tier_strategy**: none — 不涉及缓存机制。

#### 技术特性

**knowledge_source_types**: 通用外部知识库（支持 Wikipedia 等文本检索源）；检索源类型与不确定性估计机制独立

**retrieval_method**: 向量语义检索（论文实验中使用标准检索器，检索查询由原始问题或改写后的问题构成）

**hallucination_mitigation**: 双层防御：
(1) 内部幻觉——对模型参数化知识不稳定的问题强制检索外部事实，避免模型在不确定时'自信作答'；

(2) 外部幻觉——通过一致性检验评估检索增强后的输出可靠性，防止引入错误外部信息。
在 TruthfulQA 上 GPT-Judge 得分 59.34%，比 SOTA baseline +16.74%。


**offline_capability**: hybrid — 一致性估计可使用本地 LLM（多模型模式）或调用在线 API（多语言模式）；检索库可本地部署

**local_model_support**: 支持（多模型模式）— 使用多个本地模型进行一致性估计，无需访问内部状态，适用于黑盒 LLM；单模型多语言模式可完全在线或本地运行

**embedding_strategy**: standard — 检索阶段使用标准语义检索

#### 实用性评估

**setup_complexity**: medium — 需要配置多语言翻译接口或多模型调用端点、计算语义一致性（如 BERTScore 或 LLM 判断）、阈值调参；相比 SeaKR 无需访问内部状态，实现相对简洁

**token_cost**: 增加 — 多语言翻译+多次生成增加额外 token 消耗（通常生成 2-3 种语言版本）；但仅对不确定问题触发检索，总体 token 消耗低于始终检索策略

**latency**: 秒级 — 多语言翻译+多次生成约 2-5 秒；一致性计算约 500ms；检索约 1-2 秒；总延迟 3-8 秒

**dqn10_fit**: 契合度较高。
Rowen 的跨语言/跨模型一致性方案不依赖内部状态访问，可与当前 MCP+Claude 架构兼容：通过调用 Claude 的多次翻译生成并计算语义一致性，判断是否触发 bigmemory/.pipeline/ 检索。
实际集成要点：
(1) 设计一致性计算函数（使用 BERTScore 或请求 LLM 打分）；

(2) 阈值在 DQN 领域查询上校准；

(3) 与 MCP WebSearch 对接检索路径。
是当前最适合 DQN10 实际部署的判定机制之一。


#### 科研适配

**domain_adaptability**: 强 — 一致性估计机制与领域无关；适配新领域只需在领域查询上校准不确定性阈值

**incremental_update**: 支持 — 检索库可增量更新；一致性模型无需重训

**citation_traceability**: source-link — 可记录触发检索时使用的外部来源

**temporal_awareness**: static — 无时间感知；检索库更新频率决定时效性

**provenance_tracking**: source-link — 记录检索使用的来源链接

**memory_consolidation**: manual — 无自动整合机制

#### 待核实字段

- 具体语义一致性计算实现细节
- StrategyQA与其他数据集对比数值


### SKR / SeaKR

#### 基本信息

**name**: SKR / SeaKR

**category**: 判定机制

**source**: https://arxiv.org/abs/2310.05002 (SKR) / https://arxiv.org/abs/2406.19215 (SeaKR)

**maturity**: research

#### 核心机制

**architecture**: SKR（Self-Knowledge guided Retrieval，2023）：LLM 参考历史已见问题，通过对比输入问题与已知/未知问题集合的相似度，判断自身是否'已知'该问题，已知则直接回答，未知则触发检索。
依赖外部问题标注集作为自知识参照。
SeaKR（Self-Aware Knowledge Retrieval，2024，清华大学）：更深层的自知识方案，从 LLM 内部隐藏状态（EOS token 的隐层表征）提取不确定性信号，无需外部标注集。
具体做法：对同一问题多次采样（k=20）生成，提取每次 EOS token 的隐层向量，计算 Gram 矩阵行列式作为不确定性分数；
高不确定性触发检索；
检索后对多段落按'哪段使不确定性降低最多'重排序；
复杂任务中对'直接回答 vs 综合推理'两种策略选择不确定性更低者。


**retrieval_trigger**: self-knowledge — SKR 依赖外部历史问题集对比判断是否已知；SeaKR 利用 LLM 内部激活状态评估自知识不确定性，两者均属于 LLM 自评是否已知后决定是否检索，是对'何时检索'判定机制的精细化实现。

**verification_method**: consistency-check — SeaKR 通过多次采样内部状态的一致性（Gram 矩阵行列式）衡量不确定性，本质是内部一致性检查，而非外部事实验证；SKR 无显式验证机制。

**cache_tier_strategy**: none — 两者均不涉及缓存机制。

#### 技术特性

**knowledge_source_types**: 通用开放域语料库（Wikipedia 等）；SeaKR 对知识源类型无特殊要求

**retrieval_method**: 向量语义检索（SeaKR 使用标准 DPR/BM25 检索，再基于不确定性分数对段落重排序）

**hallucination_mitigation**: SKR：对 LLM 已知的问题避免引入检索噪声（减少知识冲突），对未知问题补充外部知识；SeaKR：不确定性驱动的检索减少'自信但错误'的幻觉，重排序机制选择真正有助于降低不确定性的段落，过滤无关或矛盾检索结果。

**offline_capability**: full-local — SeaKR 完全依赖开源 LM 内部状态，无需外部 API；SKR 需要维护历史问题集，也可离线运行

**local_model_support**: SeaKR 仅支持开源 LM（需访问内部隐藏状态）；SKR 理论上支持任何 LLM（通过 prompt 形式询问自知识），但实验在 InstructGPT/ChatGPT 上验证

**embedding_strategy**: standard — 检索阶段使用标准向量检索；SeaKR 的不确定性估计来自内部状态而非 embedding

#### 实用性评估

**setup_complexity**: SeaKR: high — 需要访问开源 LM 内部隐藏状态（需本地部署），多次采样（k=20）计算 Gram 矩阵，需要一定的工程实现；SKR: low — 仅需维护历史问题集和 prompt 设计

**token_cost**: SeaKR: 增加 — k=20 次采样用于不确定性估计（但可并行，通过 vLLM 缓解）；SKR: 基本不变，仅增加少量 prompt token

**latency**: SeaKR: 秒级 — k=20 并行采样通过 vLLM 约 500ms-2s；检索和重排序额外增加 1-3s；SKR: 毫秒级到秒级（取决于历史集检索速度）

**dqn10_fit**: SeaKR 与 DQN10 需求契合度较高，但有重要限制：SeaKR 依赖开源 LM（需访问隐层）且需要 GPU 本地部署，与 DQN10 当前 MCP+Claude API 架构不兼容；
SKR 更轻量但判定精度不如 SeaKR。
建议：参考 SeaKR 的不确定性重排序思想，结合 Rowen 的跨模型一致性方案（无需访问内部状态）作为替代实现。


#### 科研适配

**domain_adaptability**: SeaKR: 强 — 不确定性估计机制与领域无关；SKR: 中等 — 需要领域内已标注的已知/未知问题集

**incremental_update**: 支持 — 检索库可增量更新；SeaKR 模型不需重训；SKR 需更新历史问题集

**citation_traceability**: source-link — 可记录触发检索时使用的段落来源；重排序后的段落溯源更可靠

**temporal_awareness**: static — 无时间感知

**provenance_tracking**: source-link — 记录检索段落来源链接，未精确到声明级

**memory_consolidation**: manual — 历史问题集（SKR）和检索库均需人工维护

#### 待核实字段

- SKR具体benchmark数值


### Self-RAG

#### 基本信息

**name**: Self-RAG

**category**: 判定机制

**source**: https://arxiv.org/abs/2310.11511

**maturity**: research

#### 核心机制

**architecture**: Self-RAG 训练单个语言模型，使其能够自主决定何时检索、如何利用检索结果并评估自身输出质量。
系统由三个组件构成：生成器 LM（ℳ）、检索器（ℛ）和离线评判模型（𝒞）。
评判模型利用 GPT-4 生成反思 token 的监督数据，再训练生成器在推理时内联输出四类特殊 token（Retrieve/IsRel/IsSup/IsUse），实现检索决策与质量评估的端到端一体化。
推理时，模型并行处理多个候选段落，通过反思 token 自评后选取最优输出。


**retrieval_trigger**: confidence-based — 模型通过生成 Retrieve token（yes/no/continue）主动决定是否触发检索，而非固定规则；
触发后由 IsRel token 判断段落相关性，IsSup token 评估生成内容是否被段落支撑（fully/partially/no support），IsUse token 对输出整体质量打分（1-5 分），四类 token 协同控制检索深度与输出选择。


**verification_method**: consistency-check — IsSup token 在生成阶段实时核查每段输出是否有段落级文献支撑，本质是基于检索证据的内联一致性验证；IsRel 验证段落与问题的相关性；IsUse 从整体效用角度评估最终回复质量。

**cache_tier_strategy**: none — Self-RAG 不涉及缓存机制，专注于检索决策与自我评估。

#### 技术特性

**knowledge_source_types**: 大规模段落集合（默认 Contriever-MS MARCO 检索库）；特定任务中补充网络搜索结果；支持 PDF 型文献数据库（离线索引）

**retrieval_method**: 向量语义检索（Contriever-MS MARCO 密集检索器）

**hallucination_mitigation**: 通过 IsSup 反思 token 在生成过程中实时检测每个输出段是否有段落支撑，未支撑的段落被标记为 'no support' 并触发重生成或丢弃；
IsUse token 从整体质量角度过滤低质量输出。
整个机制无需外部验证器，幻觉抑制内嵌于语言模型自身的生成过程中。


**offline_capability**: hybrid — 需要本地检索库（可离线索引），但评判模型训练依赖 GPT-4 生成监督数据；推理阶段可配置为仅使用本地段落集，无需在线 API

**local_model_support**: 支持 — Self-RAG 开源 7B/13B 模型可本地部署，检索器 Contriever 也可本地运行；不依赖商业 API 推理

**embedding_strategy**: standard — 使用 Contriever-MS MARCO 标准密集向量检索

#### 实用性评估

**setup_complexity**: medium — 需要部署开源 LM（7B/13B）、配置 Contriever 检索器和段落索引，涉及模型微调或加载预训练 Self-RAG 权重；但代码和模型均已开源

**token_cost**: 增加 — 反思 token（Retrieve/IsRel/IsSup/IsUse）本身占用额外 token；
并行处理多段落时输入 token 增加数倍；
与始终检索 baseline 相比，自适应不检索可节省部分 token，整体成本视查询分布而定

**latency**: 秒级 — 检索器查询 + 多段落并行生成 + 反思 token 评估，单次查询通常 1-5 秒；并行候选段落数（默认 top-k）影响延迟

**dqn10_fit**: 契合度中等。
Self-RAG 的自适应检索决策机制与 DQN10 '仅在需要时检索' 的设计目标高度吻合，可作为判定机制的参考范式。
实际集成难点在于：
(1) 需要本地部署 7B+ 开源 LM 作为生成器；

(2) bigmemory/.pipeline/ 需转为 Contriever 可检索的段落索引；

(3) MCP 工具链需要适配 Self-RAG 的特殊 token 生成逻辑。
对单人科研场景，资源消耗偏高，建议作为架构参考而非直接部署。


#### 科研适配

**domain_adaptability**: 强 — 强化学习/DQN 相关文献可直接索引为段落集；反思 token 机制与领域无关，适用于专业领域 QA

**incremental_update**: 支持 — 检索库（段落索引）可增量添加新论文/实验记录，生成器模型无需重训；但新领域若显著偏离训练分布，反思 token 准确性可能下降

**citation_traceability**: 支持 — IsRel/IsSup token 标记了哪些段落被实际使用，可追溯到具体检索段落；但精度到段落级而非原子声明级

**temporal_awareness**: static — 无内置时间戳机制；检索库更新频率决定知识时效性

**provenance_tracking**: chunk-level — IsSup token 关联到具体段落（chunk），可追溯到段落级文献来源

**memory_consolidation**: manual — 段落索引需人工维护和更新，无自动去重或合并机制

#### 待核实字段

- benchmark_comparison中部分细节
- integration_effort具体工作量估算



---

## 缓存工程

### Amazon Bedrock Verified Semantic Cache

#### 基本信息

**name**: Amazon Bedrock Verified Semantic Cache

**category**: 缓存工程

**source**: https://aws.amazon.com/blogs/machine-learning/reducing-hallucinations-in-llm-agents-with-a-verified-semantic-cache-using-amazon-bedrock-knowledge-bases/

**maturity**: production-ready

#### 核心机制

**architecture**: Amazon Bedrock Verified Semantic Cache 在用户与 Amazon Bedrock Agents 之间插入一个'只读语义缓存中间层'，存储人工策划和验证的标准 Q&A 对（知识库形式）。
三级匹配路由：
(1) 强匹配（>80% 相似度）——直接返回验证答案，完全绕过 LLM；

(2) 部分匹配（60-80%）——将匹配的验证答案作为 few-shot 示例注入 LLM 上下文，引导生成相似风格的正确响应；

(3) 低匹配（<60%）——回退标准 LLM 处理流程。
技术实现：使用 Amazon Titan Text Embeddings v2 生成 embedding，Amazon Bedrock Knowledge Bases Retrieve API 进行相似度搜索，Claude Sonnet v1 作为生成模型，CloudFormation 一键部署基础设施（SageMaker notebook 环境）。


**retrieval_trigger**: confidence-based — 相似度分数（>80%/>60%/<60%）驱动三级路由决策；命中时返回缓存（类语义缓存），部分命中时引导 LLM，未命中时正常处理。

**verification_method**: none — 缓存内容本身经人工策划验证（curated & verified），系统层面无在线事实验证机制；验证工作在缓存构建阶段完成（离线）。

**cache_tier_strategy**: three-tier — 强匹配直返（>80%）/ 部分匹配 few-shot 引导（60-80%）/ 低匹配回退 LLM（<60%）；三级设计是本方案的核心创新，其中 60-80% 的部分匹配 few-shot 机制在同类产品中较罕见。

#### 技术特性

**knowledge_source_types**: 人工策划的验证 Q&A 对（Bedrock Knowledge Bases 管理）；不直接支持 PDF/代码等原始文档的直接缓存

**retrieval_method**: 向量语义检索 — Amazon Bedrock Knowledge Bases Retrieve API + Amazon Titan Text Embeddings v2

**hallucination_mitigation**: 三层机制协同减少幻觉：
(1) 强命中完全绕过 LLM 生成，使用已验证答案，幻觉率为零；

(2) 部分命中用验证答案作为 few-shot 示例，约束 LLM 输出方向，显著减少偏离事实的响应；

(3) 低命中回退标准流程（幻觉风险与无缓存相同）。
整体上，对高频已知问题实现了幻觉减少，对新问题保持正常能力。


**offline_capability**: cloud-only — 完全依赖 AWS 生态（Bedrock/Knowledge Bases/CloudFormation/SageMaker），无本地部署选项

**local_model_support**: 不支持 — 绑定 Amazon Bedrock 托管模型（Claude Sonnet v1 + Titan Embeddings），不支持本地 LLM

**embedding_strategy**: standard — 使用 Amazon Titan Text Embeddings v2 进行标准 embedding

#### 实用性评估

**setup_complexity**: medium — 需要：AWS 账号（Bedrock 访问权限）、CloudFormation 部署（sagemaker_notebook.yaml）、执行 verified_semantic_cache.ipynb 初始化；
但 AWS 提供完整 sample code（aws-samples 仓库）；
对 AWS 有经验的用户约 1-3 天可部署

**token_cost**: 降低 — 强命中（>80%）完全绕过 LLM，token 为零；部分命中（60-80%）用 few-shot 引导，可能略增加上下文 token 但避免完整推理；整体对高频已知问题的 token 消耗显著下降

**latency**: 毫秒级（强命中）/ 秒级（部分匹配+LLM 引导）/ 正常 LLM 延迟（低匹配）— 强命中仅需 Knowledge Bases 检索（<200ms）；AWS 基础设施延迟取决于区域配置

**dqn10_fit**: 契合度中等偏低，主要受 AWS 锁定制约。
架构设计理念（三级分层缓存）对 DQN10 有强参考价值。
实际集成障碍：
(1) 完全绑定 AWS 生态，DQN10 当前架构（MCP + Claude API）需要大幅改造；

(2) 人工策划 Q&A 集构建需要显著人工成本；

(3) 云端处理科研数据有数据主权顾虑。
建议：参考三级分层设计思路，在 DQN10 本地架构中实现类似逻辑（强命中→精确匹配、部分命中→few-shot 注入、低命中→正常检索）。


#### 科研适配

**domain_adaptability**: 强（架构层面）/ 有限（实现层面）— 三级路由逻辑与领域无关；但 AWS Bedrock 锁定限制了自由适配

**incremental_update**: 支持 — Bedrock Knowledge Bases 支持动态添加新的验证 Q&A 对；增量更新无需重建整个知识库

**citation_traceability**: source-link — 返回的答案来自策划知识库，可追溯到具体 Q&A 条目；无 chunk 级或声明级追踪

**temporal_awareness**: static — 知识库内容无自动时间感知；需人工维护更新频率

**provenance_tracking**: source-link — 强命中返回的答案可追溯到知识库条目

**memory_consolidation**: manual — 策划知识库需人工维护、审核和更新

#### 待核实字段

- 具体token节省率和延迟改善的定量数据
- 与GPTCache/Upstash等开源方案的直接对比benchmark


### Bifrost

#### 基本信息

**name**: Bifrost

**category**: 缓存工程

**source**: https://github.com/maximhq/bifrost

**maturity**: early-stage

#### 核心机制

**architecture**: Bifrost 是用 Go 编写的开源 AI 网关，提供统一的 OpenAI 兼容 API 接入 15+ LLM 提供商（OpenAI/Anthropic/AWS Bedrock/Google Vertex/Azure/Mistral/Ollama 等）。
采用模块化分层架构：Core 层（提供商集成/请求路由）、Framework 层（配置/日志/向量存储数据持久化）、Transport 层（HTTP 网关/API 接口）、Plugin 系统（可扩展中间件）、Web UI（配置与监控仪表板）。
双层缓存机制：精确哈希缓存（完全相同请求直返）+ 语义向量缓存（识别语义等价提示）。
提供三种部署方式：HTTP Gateway（NPX/Docker 秒级启动）、Go SDK（库集成）、Drop-in 替换（仅改 URL）。


**retrieval_trigger**: none — Bifrost 是 AI 网关而非 RAG 系统；'触发检索'对应缓存未命中时路由到 LLM 提供商，不涉及知识库检索。

**verification_method**: none — 无事实验证机制；缓存命中基于哈希精确匹配或向量相似度，不验证响应的事实性。

**cache_tier_strategy**: dual-layer — 第一层：精确哈希匹配（完全相同请求，O(1) 查找）；第二层：向量语义缓存（语义等价提示，向量相似度搜索）。精确层优先，未命中则查语义层，两层均未命中才调用 LLM。

#### 技术特性

**knowledge_source_types**: 缓存 LLM API 响应；作为网关可代理任何 LLM 提供商的请求；不直接管理外部知识库

**retrieval_method**: 精确哈希 + 向量语义检索双模式；向量存储后端由 Framework 层管理（具体向量数据库实现待确认）

**hallucination_mitigation**: 间接效果 — 复用缓存响应减少随机幻觉；主要价值是成本和延迟优化，非幻觉减少。语义缓存命中时返回之前验证过的响应，对高频相似问题提供一致性输出。

**offline_capability**: hybrid — 本地 Ollama 作为 LLM 提供商时可离线运行；向量缓存可本地部署；云端 LLM 提供商需联网

**local_model_support**: 支持 — 内置 Ollama 提供商集成，支持本地 LLM；go 实现支持自定义提供商扩展

**embedding_strategy**: standard — 语义缓存使用标准 embedding；具体 embedding 方案可通过插件配置

#### 实用性评估

**setup_complexity**: low — HTTP 网关模式：npx @maximhq/bifrost 或 Docker 一行命令启动；Drop-in 模式：仅改 API endpoint URL；Go SDK 模式需编写代码

**token_cost**: 降低 — 精确缓存命中：零 token 消耗；语义缓存命中：零 token 消耗；双层缓存最大化命中率；声称成本优化显著（具体数字取决于请求重复率）

**latency**: 微秒级（精确缓存命中）/ 毫秒级（语义缓存命中）/ 正常 LLM 延迟（未命中）— 官方压测：5000 RPS 下仅增加 11 微秒网关开销（t3.xlarge），100% 请求成功率；声称比 LiteLLM 快 50x

**dqn10_fit**: 契合度中等偏低。
Bifrost 主要价值是企业级多提供商 LLM 网关，对 DQN10 单人科研场景偏重。
具体评估：
(1) 若 DQN10 需要同时使用多个 LLM 提供商（Claude + OpenAI + 本地 Ollama），Bifrost 网关可统一管理；

(2) 双层缓存对高频 LLM 调用（如实验中的大量相似推理请求）有成本节省；

(3) 对单人使用场景，引入网关层增加了不必要的系统复杂度；
建议在 DQN10 实验 LLM 调用量显著增加时再考虑。


#### 科研适配

**domain_adaptability**: 强 — 作为通用 AI 网关，与领域无关

**incremental_update**: 支持 — 缓存自动增量写入；新 LLM 提供商通过插件扩展

**citation_traceability**: none — 网关层不提供来源追踪

**temporal_awareness**: static — 无时间感知；缓存内容随 TTL 过期

**provenance_tracking**: none — 无溯源功能

**memory_consolidation**: auto-dedup — 精确哈希天然去重；语义缓存通过相似度隐式去重

#### 待核实字段

- 语义缓存向量后端的具体实现细节
- 50x vs LiteLLM的详细测试条件
- 向量缓存的假阳性率


### GPTCache

#### 基本信息

**name**: GPTCache

**category**: 缓存工程

**source**: https://github.com/zilliztech/GPTCache

**maturity**: early-stage

#### 核心机制

**architecture**: GPTCache 是 Zilliz 开源的 Python 语义缓存库，为 LLM API 调用提供语义级缓存层。
核心流程：
(1) 将输入查询通过 Embedding Generator 转换为向量；

(2) 在 Vector Store 中检索语义相似的历史查询；

(3) 若相似度超过阈值，直接返回缓存响应；

(4) 否则调用 LLM 并将新响应写入缓存。
四大模块：LLM Adapter（适配 OpenAI/LangChain/Llama.cpp/Dolly）、Embedding Generator（支持 OpenAI/ONNX/HuggingFace/Cohere/SentenceTransformers）、Cache Storage（SQLite/DuckDB/PostgreSQL/MySQL 等）、Vector Store（Milvus/FAISS/Zilliz Cloud/Milvus Lite）。
支持 Docker server 模式实现语言无关接入。


**retrieval_trigger**: none — GPTCache 是语义缓存系统而非 RAG 系统，'触发检索'对应缓存未命中时调用 LLM，缓存命中时直接返回；无主动检索知识库的逻辑。

**verification_method**: none — 缓存命中基于向量相似度阈值，无事实验证机制；缓存的响应质量取决于初次 LLM 生成的质量。

**cache_tier_strategy**: single-tier — 单层语义缓存：Embedding 相似度检索 + 阈值判断，命中则返回缓存响应；无多级分层策略。

#### 技术特性

**knowledge_source_types**: 缓存已验证的 LLM 响应（问题-答案对）；不支持外部文档/PDF 等知识源的直接索引

**retrieval_method**: 向量语义检索 — 输入查询 embedding 与缓存查询 embedding 进行余弦相似度搜索；支持 FAISS（本地）和 Milvus（分布式）

**hallucination_mitigation**: 间接减少幻觉：对高频相似问题复用已验证的历史 LLM 响应，避免同一问题的多次随机生成导致答案不一致；但不对缓存内容本身的事实性进行验证。

**offline_capability**: full-local — SQLite + FAISS + 本地 embedding 模型（ONNX/SentenceTransformers）可实现完全离线运行

**local_model_support**: 支持 — 支持 Llama.cpp、本地 HuggingFace/ONNX embedding 模型；可完全脱离云端 API 运行

**embedding_strategy**: standard — 支持多种标准 embedding 方案（OpenAI text-embedding、SentenceTransformers、fastText 等），默认使用 OpenAI Embedding API

#### 实用性评估

**setup_complexity**: low — pip install gptcache 即可；基础依赖最小化，扩展组件按需自动加载；提供 LangChain/LlamaIndex 预集成接口

**token_cost**: 降低 — 缓存命中时完全跳过 LLM 调用，token 消耗为零；声称可降低 API 成本最多 10 倍（取决于查询重复率）

**latency**: 毫秒级（命中）/ 正常 LLM 延迟（未命中） — embedding 计算约 50-200ms，向量检索约 10-100ms；命中时总延迟从秒级降至毫秒级（声称 100x 速度提升）

**dqn10_fit**: 契合度中等。
GPTCache 可作为 DQN10 MCP 工具链的语义缓存层，缓存对同类问题的 LLM 响应（如'DQN 的 Q 值更新公式是什么'类型的重复查询）。
主要价值：减少对重复问题的 API 调用成本。
主要限制：
(1) 缓存的是 LLM 响应而非知识库内容，无法替代 bigmemory/.pipeline/ 的作用；

(2) 新增 API 对新 LLM 的支持已停止，需使用通用 get/set API；

(3) 假阳性（相似但不同含义的问题命中缓存）在专业科研场景风险较高。


#### 科研适配

**domain_adaptability**: 强 — 语义缓存与领域无关，可缓存任何领域的 LLM 响应

**incremental_update**: 支持 — 缓存自动增量写入新的 LLM 响应；支持 TTL（Time-To-Live）策略控制过期

**citation_traceability**: none — 缓存响应不包含原始来源追踪；返回的是历史 LLM 输出而非文档引用

**temporal_awareness**: static — 缓存内容无时间感知；过时的缓存响应可能返回过时知识，需依赖 TTL 机制定期清除

**provenance_tracking**: none — 不提供来源追踪功能

**memory_consolidation**: auto-dedup — 向量相似度检索天然实现去重（相似问题复用缓存）；但不自动合并或整合知识内容

#### 待核实字段

- 实际生产环境的假阳性率数据


### Krites (Apple)

#### 基本信息

**name**: Krites (Apple)

**category**: 缓存工程

**source**: https://arxiv.org/abs/2602.13165

**maturity**: research

#### 核心机制

**architecture**: Krites 是 Apple 提出的异步验证语义缓存系统，专为分层 LLM 架构（小模型快速响应 + 大模型高精度后备）设计。
三层架构：
(1) 强命中层（Strong-hit）——输入提示与静态缓存中的已验证答案相似度高于阈值，直接同步返回缓存响应，零额外延迟；

(2) 灰区异步验证层（Grey-zone Async Verification）——相似度略低于阈值（灰区）时，不阻塞请求、立即返回当前最优响应，同时在后台异步调用 LLM Judge 判断缓存响应是否适用于该新提示；

(3) 动态缓存写入层（Dynamic Cache Write）——LLM Judge 验证通过的灰区匹配被写入动态缓存，供未来语义相近的提示命中。
核心创新：通过异步验证解耦命中判断与响应延迟，既保持关键路径低延迟，又渐进式扩大缓存覆盖范围。


**retrieval_trigger**: none — Krites 是纯缓存系统，触发逻辑为相似度阈值判断，不涉及主动知识检索。

**verification_method**: none — 验证机制针对缓存响应的适用性（LLM Judge 判断灰区匹配是否可接受），而非事实正确性验证；但 LLM Judge 本质是在做语义一致性检查。

**cache_tier_strategy**: async-verified — Krites 的核心创新：强命中直返（同步）+ 灰区异步 LLM 验证 + 动态缓存写入，相比传统单层或双层方案，通过异步验证大幅提升缓存覆盖率而不牺牲响应延迟。

#### 技术特性

**knowledge_source_types**: 静态策划的已验证问答对（curated static cache）；不支持外部文档知识库

**retrieval_method**: 向量语义检索 — 输入 embedding 与静态缓存 embedding 进行相似度搜索；灰区阈值区间内启动异步 LLM Judge

**hallucination_mitigation**: 通过复用已策划验证（curated & verified）的答案，直接绕过 LLM 生成步骤，对高频已知问题实现零幻觉；灰区验证通过 LLM Judge 过滤不适合的缓存复用，防止语义相似但答案不同的问题引入错误响应。

**offline_capability**: hybrid — 静态缓存和向量检索可本地运行；LLM Judge（灰区异步验证）依赖 LLM 调用（可配置本地或云端）

**local_model_support**: 支持 — LLM Judge 可配置使用本地 LLM；核心相似度检索完全本地化

**embedding_strategy**: standard — 使用标准 embedding 进行相似度检索，论文未说明特定 embedding 模型

#### 实用性评估

**setup_complexity**: high — 需要：(1) 构建和维护静态策划验证答案集；(2) 实现异步 LLM Judge 验证流程；(3) 动态缓存写入机制；相比普通语义缓存复杂度显著更高

**token_cost**: 降低 — 强命中直接绕过 LLM，token 消耗为零；灰区验证使用轻量 LLM Judge（成本低于完整 LLM 推理）；覆盖率提升 136%-290% 意味着更多请求无需完整 LLM 处理

**latency**: 毫秒级（强命中）/ 正常延迟（灰区和未命中）— 强命中：仅向量检索延迟（<50ms）；灰区：异步验证不阻塞当前请求，用户无感知；未命中：正常 LLM 延迟

**dqn10_fit**: 契合度较高，但实现成本高。
对 DQN10 的价值：
(1) 可为高频 DQN 问题（算法定义/公式/经典结论）建立静态策划答案集，强命中直返；

(2) 灰区异步验证适合 DQN10 中问法多样但答案相同的问题；

(3) 异步验证避免了验证过程阻塞用户响应。
主要门槛：需要构建和维护高质量静态答案集（人工成本），以及实现异步验证流程（工程成本）。
对单人科研场景，实现复杂度偏高，建议参考设计思路结合简化实现。


#### 科研适配

**domain_adaptability**: 强 — 架构与领域无关；只需为 DQN/强化学习领域准备策划答案集

**incremental_update**: 支持 — 动态缓存层自动写入经验证的新问答对；静态层需人工策划和审核

**citation_traceability**: none — 缓存系统不追踪来源

**temporal_awareness**: static — 静态缓存层无时间感知；动态缓存层随使用渐进式扩展

**provenance_tracking**: none — 无溯源功能

**memory_consolidation**: auto-dedup — 动态缓存写入时通过相似度检索隐式实现去重

#### 待核实字段

- 论文仿真到实际生产的性能差距
- LLM Judge具体使用的模型规格


### 语义缓存方案对比 (Redis / LangChain / 轻量方案)

#### 基本信息

**name**: 语义缓存方案对比 (Redis / LangChain / 轻量方案)

**category**: 缓存工程

**source**: 综合对比 — Redis 官方文档 / LangChain 文档 / Upstash 文档

**maturity**: production-ready

#### 核心机制

**architecture**: 本条目横向对比三类语义缓存方案。

(1) Redis Semantic Cache（RedisSemanticCache）：依托 Redis Vector Sets（2025 年春季发布的 LangCache 服务）或 Redis Stack，将查询 embedding 存入 Redis 向量索引，命中时返回缓存响应。
支持精确匹配（RedisCache，MD5 哈希）和语义匹配（RedisSemanticCache，余弦相似度）双模式，生产级高可用。

(2) LangChain Cache 抽象层：LangChain 提供统一 Cache 接口，支持 InMemoryCache、SQLiteCache、RedisCache、RedisSemanticCache、GPTCache 等多种后端，通过 `set_llm_cache
()` 一行配置切换；
本质是缓存后端的适配器，自身不实现存储。

(3) 轻量方案（Upstash Semantic Cache、FAISS+SQLite 自建）：无服务器架构（Upstash）或纯本地（FAISS）；
适合低成本个人/小团队场景。


**retrieval_trigger**: none — 所有方案均为缓存触发逻辑（相似度阈值判断命中/未命中），非主动知识检索触发。

**verification_method**: none — 语义缓存方案均不包含事实验证机制；命中质量取决于缓存内容的事实性。

**cache_tier_strategy**: dual-layer — Redis 方案可组合精确哈希（RedisCache）+ 向量相似度（RedisSemanticCache）实现双层缓存；
LangChain 通过叠加多个 Cache 后端实现；
单独的 GPTCache/Upstash 为单层；
Redis LangCache（2025）提供托管式单层语义缓存。


#### 技术特性

**knowledge_source_types**: 缓存 LLM 响应（问题-答案对）；部分方案支持将知识文档预存为 embedding 但主要用途仍是响应缓存

**retrieval_method**: 向量语义检索 — 所有方案均使用 embedding 相似度搜索；Redis 使用内置向量搜索；FAISS 使用近似最近邻

**hallucination_mitigation**: 间接效果 — 复用已验证的历史响应避免同一问题的随机幻觉；但均不主动核验缓存内容的事实性。

**offline_capability**: Redis: hybrid（Redis Stack 可本地部署，托管版需联网）；
LangChain: full-local（SQLiteCache/InMemoryCache 完全离线）；
Upstash: cloud-only（Serverless）

**local_model_support**: Redis: 支持本地 embedding 模型（通过 langchain-redis 配置）；LangChain: 支持（embedding 可配置任意本地模型）；Upstash: 内置 embedding，无需配置外部模型

**embedding_strategy**: standard — 所有方案默认使用标准 embedding；Upstash 内置 embedding 生成，其他方案支持自定义 embedding 模型

#### 实用性评估

**setup_complexity**: Redis Semantic Cache: medium（需要 Redis Stack 或 Upstash Redis）；
LangChain Cache: low（set_llm_cache 一行配置）；
Upstash: low（Serverless 免配置）；
FAISS 自建: medium

**token_cost**: 降低 — 所有方案缓存命中时完全跳过 LLM 调用；Redis 官方案例显示语义缓存速度提升 5.22x；实际 token 节省比例取决于查询重复率

**latency**: Redis Semantic Cache: 毫秒级命中（10-50ms 向量搜索）；LangChain InMemoryCache: 微秒级；Upstash: 20-100ms（网络 RTT）；FAISS 本地: 1-10ms

**dqn10_fit**: 对 DQN10 的实用价值：LangChain Cache 抽象层是最低成本的集成方案——当前 MCP 工具链若使用 LangChain 封装，可一行代码启用 SQLiteCache 本地语义缓存，缓存对重复 DQN 问题（公式/概念/算法步骤）的 LLM 响应。
Redis Semantic Cache 适合需要多用户共享缓存的场景（当前单人科研暂无此需求）。
Upstash 免费层（500K 请求/月）足够单人科研用量，零运维成本。
推荐：先用 LangChain SQLiteCache（3 分钟集成），需要时升级到 Upstash。


#### 科研适配

**domain_adaptability**: 强 — 语义缓存与领域无关

**incremental_update**: 支持 — 所有方案均自动写入新响应到缓存；Redis 支持 TTL 过期策略

**citation_traceability**: none — 缓存响应不追踪原始来源

**temporal_awareness**: static — 默认无时间感知；Redis/SQLite 支持 TTL 策略按时间过期缓存，实现有限时间管理

**provenance_tracking**: none — 无溯源功能

**memory_consolidation**: auto-dedup — 向量相似度检索隐式实现去重（相似查询复用缓存）；Redis LangCache 支持集中式缓存管理

#### 待核实字段

- Redis LangCache 2025年新版具体性能数据
- 各方案假阳性率的实际测量数据


### Upstash Semantic Cache

#### 基本信息

**name**: Upstash Semantic Cache

**category**: 缓存工程

**source**: https://upstash.com/blog/semantic-caching-for-speed-and-savings

**maturity**: production-ready

#### 核心机制

**architecture**: Upstash Semantic Cache 是基于 Upstash Vector 数据库的 Serverless 语义缓存方案。
核心组件：
(1) Upstash Vector Index——全托管向量数据库，内置 embedding 生成（无需外部 embedding API），使用 minProximity 参数（0.0-1.0）控制相似度阈值；

(2) SemanticCache 实例——管理缓存的 get/set 逻辑；

(3) 可选 TTL——控制缓存条目生命周期。
工作流程：输入查询→Upstash Vector 自动生成 embedding→向量检索（cosine 相似度）→相似度超过 minProximity 则返回缓存响应，否则调用 LLM 并写入缓存。
完全无服务器架构，按请求计费，免费层 500K 命令/月。
GitHub 开源库：upstash/semantic-cache，支持 JavaScript/TypeScript 和 Python。


**retrieval_trigger**: none — 纯语义缓存系统；命中判断基于向量相似度阈值（minProximity），不涉及主动知识库检索。

**verification_method**: none — 相似度阈值命中即返回，无事实验证机制。

**cache_tier_strategy**: single-tier — 单层语义缓存：embedding 相似度搜索 + minProximity 阈值判断，单一维度决策；无多级分层。

#### 技术特性

**knowledge_source_types**: 缓存 LLM API 响应（自然语言问答对）；适合任意文本类 LLM 交互的响应缓存

**retrieval_method**: 向量语义检索 — Upstash Vector 内置 embedding 生成 + cosine 相似度搜索，无需配置外部 embedding 模型

**hallucination_mitigation**: 间接效果 — 复用历史 LLM 响应减少同一问题的随机幻觉；主要价值是成本和延迟优化，非主动幻觉检测。

**offline_capability**: cloud-only — Serverless 架构，完全依赖 Upstash 云服务，无本地部署选项

**local_model_support**: 不支持（embedding 角度）— Embedding 由 Upstash 内部生成，无法替换为自定义本地模型；但缓存的 LLM 响应可来自任意模型（本地或云端）

**embedding_strategy**: standard — Upstash Vector 内置 embedding 生成，对用户透明（无需选择/配置 embedding 模型），简化了集成复杂度

#### 实用性评估

**setup_complexity**: low — 极简 API：new SemanticCache({ index, minProximity: 0.95 }) 即可使用；Upstash 免费注册，无需配置服务器；JS/Python SDK 开箱即用

**token_cost**: 降低 — 命中时完全跳过 LLM 调用，token 消耗为零；免费层 500K 请求/月对单人科研场景足够；付费层 $0.20/100K 命令（超出免费额度后）

**latency**: 毫秒级（命中）/ 正常 LLM 延迟（未命中）— Upstash 全球 CDN 分发，向量检索约 20-100ms（取决于地理位置）；命中时延迟远低于 LLM API 调用

**dqn10_fit**: 契合度较高，最低成本集成方案之一。
对 DQN10 的直接价值：
(1) 零运维成本（Serverless 全托管）；

(2) 免费层 500K/月足够单人科研日常用量；

(3) Python SDK 可直接在 MCP 工具链中使用，几行代码接入；

(4) 内置 embedding 无需配置外部 embedding API；

(5) 对高频 DQN 概念查询（公式/定义类）实现毫秒级响应。
主要限制：数据存在 Upstash 云端（科研数据主权）；
embedding 模型不透明（无法优化领域适配）；
无法本地离线运行。
推荐：作为 DQN10 LLM 调用的快速语义缓存层，优先于更复杂的本地方案。


#### 科研适配

**domain_adaptability**: 强 — 语义缓存与领域无关；内置 embedding 对专业术语（DQN/强化学习）的语义理解能力取决于 Upstash 底层 embedding 模型

**incremental_update**: 支持 — 缓存条目自动增量写入；支持 TTL 过期和手动删除控制缓存内容

**citation_traceability**: none — 不提供来源追踪

**temporal_awareness**: static — 无时间感知；TTL 参数可设置缓存过期时间，实现基本的时效性控制

**provenance_tracking**: none — 无溯源功能

**memory_consolidation**: auto-dedup — minProximity 相似度检索隐式去重（相似查询命中同一缓存条目）

#### 待核实字段

- Upstash内置embedding模型的具体名称和版本
- 在强化学习专业术语上的语义理解质量



---

## MCP生态

### ConPort (Context Portal)

#### 基本信息

**name**: ConPort (Context Portal)

**category**: MCP生态

**source**: https://github.com/GreatScottyMac/context-portal

**maturity**: early-stage

#### 核心机制

**architecture**: ConPort 是项目级知识图谱 MCP Server，以 Python/FastAPI 实现，通过 STDIO 模式集成到 IDE（Roo Code/CLine/Windsurf Cascade 等）。
存储层：每个工作区一个 SQLite 数据库（context_portal/context.db），用 Alembic 管理 schema 迁移。
功能层：暴露 40+ MCP Tools，涵盖决策日志（Decision Logging）、进度追踪（Progress Tracking）、系统模式文档（System Patterns）、自定义数据存储（词汇表/规格说明）。
检索层：FTS5 全文搜索 + 向量 embedding 语义搜索。
知识图谱层：捕获实体（决策/进度/架构）及其关系，构建项目专属知识图。


**retrieval_trigger**: always（IDE 集成后 Agent 按需调用工具检索）

**verification_method**: none

**cache_tier_strategy**: none

#### 技术特性

**knowledge_source_types**: 决策记录、进度状态、系统架构模式、自定义数据（词汇表/规格）、代码结构

**retrieval_method**: 混合（FTS5 全文检索 + 向量语义检索）

**hallucination_mitigation**: 通过持久化决策日志和架构记录，为 Agent 提供准确的项目上下文，减少因上下文遗忘导致的错误；无主动幻觉检测

**offline_capability**: full-local（SQLite 本地存储，无云依赖）

**local_model_support**: 支持（本地 LLM 可作为 MCP Host 使用 ConPort）

**embedding_strategy**: standard（向量检索使用标准 embedding）

#### 实用性评估

**setup_complexity**: low（推荐 uvx 运行：uvx --from context-portal-mcp conport-mcp --mode stdio；无需手动安装数据库）

**token_cost**: 不变或降低（结构化存储替代重读文件，减少无关上下文注入）

**latency**: ms 级（SQLite 本地查询 + STDIO 通信）

**dqn10_fit**: 高度对标，是现有 bigmemory/.pipeline/ 的最接近替代方案。
具体对比：ConPort 的 Decision Logging ↔ bigmemory 未关闭决策；
Progress Tracking ↔ 热区状态简报；
Custom Data ↔ .pipeline/terminology/；
Semantic Search ↔ ACE 语义检索。
优势：
(1) SQLite 可查询，优于 Markdown 平文件的 Grep；

(2) 40+ 工具开箱即用；

(3) FTS5+向量混合搜索优于纯 ACE；

(4) 与 Claude Code 集成简单。
局限：
(1) 无时序知识图谱，无事实有效期管理；

(2) 现有 bigmemory 数据迁移需人工整理；

(3) GitHub 760 stars，社区较小，维护风险；

(4) 无论文级别的学术引用追溯支持。


#### 科研适配

**domain_adaptability**: 强（项目无关的通用架构，可适配 DQN 实验记录）

**incremental_update**: 支持（SQLite 增量写入，支持 batch 操作）

**citation_traceability**: source-link（工具调用结果可携带来源标记，但无学术引用原生支持）

**temporal_awareness**: temporal-versioned（SQLite 记录含时间戳，支持按时间查询）

**provenance_tracking**: chunk-level（精确到具体决策/进度条目）

**memory_consolidation**: manual（需人工整理或 Agent 辅助归档，无自动去重）


### MCP 知识服务架构

#### 基本信息

**name**: MCP 知识服务架构

**category**: MCP生态

**source**: https://modelcontextprotocol.io/

**maturity**: production-ready

#### 核心机制

**architecture**: MCP 
(Model Context Protocol) 是 Anthropic 于 2024 年 11 月发布的开放协议，采用 Client-Server 架构：MCP Host（如 Claude Desktop、Claude Code）为宿主，每个 MCP Server 对应一个专属 MCP Client 保持连接。
数据层基于 JSON-RPC 2.0 实现，定义三种核心原语：Tools（可执行函数）、Resources（上下文数据源）、Prompts（交互模板）。
传输层支持两种模式：本地进程用 Stdio transport（标准输入输出，零网络开销），远程服务用 Streamable HTTP transport（支持 OAuth 认证）。
封装本地知识库为 MCP Server 的典型模式：将文档检索、向量搜索、图谱查询等功能封装为 Tools，将知识库 schema 和元数据暴露为 Resources，支持 tools/list 动态发现和 tools/call 调用。


**retrieval_trigger**: none

**verification_method**: none

**cache_tier_strategy**: none

#### 技术特性

**knowledge_source_types**: 文件系统、数据库、API、网页、代码仓库、知识图谱（由各 MCP Server 实现决定）

**retrieval_method**: 由各 MCP Server 自定义（向量语义/BM25/图谱遍历/混合均可）

**hallucination_mitigation**: MCP 协议本身不提供幻觉缓解机制；通过 Resources 原语将结构化事实数据注入 LLM 上下文，间接减少因知识缺失导致的幻觉。MCP Server 可自行集成验证逻辑。

**offline_capability**: full-local（Stdio transport 模式下完全本地运行，无需网络）

**local_model_support**: 支持。MCP 协议与底层 LLM 无关，本地模型（如 Llama、Qwen）可作为 MCP Host 使用

**embedding_strategy**: 由各 MCP Server 自定义，协议层无约束

#### 实用性评估

**setup_complexity**: medium（Python/TypeScript SDK 封装完善，单人实现一个基础 MCP Server 约需 1-2 天；与 Claude Code 集成配置约需 30 分钟）

**token_cost**: 增加（MCP Server 初始化时向 Agent 推送完整工具文档，包括名称、描述、JSON Schema，大量消耗 context window；多 Server 场景尤为明显）

**latency**: ms 级（Stdio transport 本地进程通信）

**dqn10_fit**: 高度契合。
DQN10 现有 bigmemory/.pipeline/ 已通过 ACE 
(augment-context-engine) 做语义检索，将其封装为 MCP Server 可统一接口、支持多 Agent 并行访问。
具体价值：
(1) 将热区/冷区/文献库分别暴露为不同 Resources，避免每次重读全部；

(2) 将 /archive 流程封装为 Tool，供 memory-worker 调用；

(3) 与 Claude Code 原生 MCP 工具链无缝集成。
集成 DQN10 的主要工作：实现 1 个 Python MCP Server 封装 bigmemory 检索接口，估计 2-3 天工作量。


#### 科研适配

**domain_adaptability**: 强。MCP 协议无领域约束，可适配任意研究领域（强化学习/DQN 实验数据、论文检索均可封装）

**incremental_update**: 支持。Resources 和 Tools 列表可动态变化，Server 通过 notifications/tools/list_changed 通知客户端更新

**citation_traceability**: 取决于 MCP Server 实现；协议层提供 Resources 原语可携带来源元数据

**temporal_awareness**: static（协议本身无时间感知，需 Server 实现携带时间戳）

**provenance_tracking**: source-link（Resource URI 可追溯到原始文档，具体粒度由 Server 实现决定）

**memory_consolidation**: manual（MCP 协议不涉及记忆整合，由上层应用处理）

#### 待核实字段

- benchmark_comparison


### Mem0

#### 基本信息

**name**: Mem0

**category**: MCP生态

**source**: https://arxiv.org/abs/2504.19413

**maturity**: production-ready

#### 核心机制

**architecture**: Mem0 是多层次 Agent 记忆层，动态提取、整合和检索对话中的关键信息，解决 LLM 固定上下文窗口限制。
基础版本：向量存储 + 自动记忆提取/合并/去重；
增强版本：引入图谱记忆表示（Graph Memory），捕获对话元素间的复杂关系结构。
系统核心机制：每次对话后自动从历史中提取关键事实，与已有记忆合并去重（LLM 辅助合并），再以结构化持久记忆形式存储，后续检索时只注入相关记忆片段而非完整历史，实现 token 消耗降低 90%。


**retrieval_trigger**: always（每次对话自动检索相关记忆注入上下文）

**verification_method**: none（无内置事实验证，依赖 LLM 自身判断）

**cache_tier_strategy**: none（不是缓存系统，是记忆层）

#### 技术特性

**knowledge_source_types**: 多轮对话历史、结构化用户偏好、任务状态

**retrieval_method**: 向量语义（基础版）+ 图谱遍历（增强版Graph Memory）

**hallucination_mitigation**: 通过结构化持久记忆代替完整历史传入，减少 LLM 处理超长上下文时的注意力分散；自动去重防止矛盾记忆并存；但无主动幻觉检测机制

**offline_capability**: hybrid（开源版可本地部署；Mem0 Platform 为 SaaS）

**local_model_support**: 支持（开源版本支持本地 LLM 做记忆提取和合并）

**embedding_strategy**: standard（向量存储使用标准 embedding；图谱版本额外用关系 embedding）

#### 实用性评估

**setup_complexity**: low（pip install mem0ai，开源版配置简单；SaaS 版 API key 即用）

**token_cost**: 降低 90%（原文：相比传入完整历史，节省超过 90% token 成本；p95 延迟降低 91%）

**latency**: ms 级（检索延迟；记忆提取和合并为后台异步处理）

**dqn10_fit**: 中等契合。
优势：
(1) token 消耗降低 90% 直接解决 memory-worker 每次重读全部热区的成本问题；

(2) 自动提取/合并/去重解决热区膨胀问题；

(3) 开源版本易于本地部署。
局限：
(1) 设计侧重对话记忆，对 DQN10 的实验数据、论文 PDF、代码变更等非对话知识的摄入支持有限；

(2) 现有 Markdown 平文件格式需要迁移；

(3) 图谱记忆版本的关系提取质量依赖底层 LLM；

(4) 无学术引用追溯能力。
最适合作为 memory-worker 的底层记忆引擎替换，不适合替换整个 .pipeline/ 知识库。


#### 科研适配

**domain_adaptability**: 中等（设计泛化，但强项是对话记忆；实验日志/论文等领域知识需定制摄入管道）

**incremental_update**: 支持（核心特性，每轮对话自动增量更新，去重合并）

**citation_traceability**: source-link（记忆节点可携带来源标记，但学术级别引用追溯非原生功能）

**temporal_awareness**: temporal-versioned（记忆节点带时间戳，支持时序检索）

**provenance_tracking**: chunk-level（记忆片段可追溯到来源对话轮次）

**memory_consolidation**: llm-merge（LLM 辅助自动合并冲突/重复记忆，核心差异化功能）


### Zep / Graphiti

#### 基本信息

**name**: Zep / Graphiti

**category**: MCP生态

**source**: https://arxiv.org/abs/2501.13956

**maturity**: production-ready

#### 核心机制

**architecture**: Zep 是一个 Agent 记忆层服务，核心引擎为 Graphiti——一个时序感知知识图谱引擎。
Graphiti 动态合成非结构化对话数据与结构化业务数据，同时维护历史关系。
每个事实节点携带有效期窗口（bi-temporal 设计：记录知识创建时间和知识在现实中的有效时间），支持知识的自动失效和更新。
系统提供 MCP Server 接口，AI Agent 可通过标准 MCP 协议访问记忆检索和存储功能。
知识以图谱形式组织，支持跨会话信息综合和长期上下文维护。


**retrieval_trigger**: always（Agent 每次需要记忆时主动检索）

**verification_method**: none（系统侧重存储和检索，不含内置验证机制）

**cache_tier_strategy**: none

#### 技术特性

**knowledge_source_types**: 对话历史、结构化业务数据、API 数据流

**retrieval_method**: 图谱遍历 + 向量语义（时序感知的混合检索）

**hallucination_mitigation**: 通过时序知识图谱维护事实的时间有效性，防止 Agent 使用过时信息；跨会话信息综合减少因上下文丢失导致的错误；但无主动事实核查机制

**offline_capability**: hybrid（Zep 提供 SaaS 版本；Graphiti 开源可本地部署）

**local_model_support**: 支持（Graphiti 开源，可配合本地 LLM 使用）

**embedding_strategy**: standard（知识图谱节点使用标准 embedding 做相似度检索）

#### 实用性评估

**setup_complexity**: medium（Graphiti 需要图数据库 Neo4j 或兼容存储；MCP Server 配置约需 1-2 天）

**token_cost**: 降低（时序图谱只检索相关子图，避免传入完整历史；响应延迟降低 90% 间接降低重试成本）

**latency**: 秒级（论文报告响应延迟降低 90%，绝对数值未公开）

**dqn10_fit**: 中等契合。
优势：时序知识图谱与 DQN10 冷区按天归档的模式互补，可将实验里程碑和决策记录为带时效性的图谱节点；
MCP Server 接口可直接集成。
局限：
(1) Zep SaaS 版依赖云服务；

(2) Graphiti 本地部署需 Neo4j，增加基础设施复杂度；

(3) 现有 bigmemory Markdown 数据需要迁移成本；

(4) 对单人科研场景的价值主要是防止使用过时配置/结论，需评估是否值得迁移成本。


#### 科研适配

**domain_adaptability**: 强，知识图谱结构无领域约束，可适配实验配置、论文结论、代码变更等任意类型知识

**incremental_update**: 支持（核心特性，新事实自动更新图谱节点，旧事实标记为历史）

**citation_traceability**: source-link（图谱节点携带来源元数据）

**temporal_awareness**: temporal-versioned（bi-temporal 设计，每条知识带创建时间和有效期窗口）

**provenance_tracking**: chunk-level（图谱节点对应知识片段，可追溯到源对话/文档）

**memory_consolidation**: graph-based（知识图谱自动合并冲突事实，标记失效节点）


### bigmemory/.pipeline/ 现有架构

#### 基本信息

**name**: bigmemory/.pipeline/ 现有架构

**category**: MCP生态

**source**: 本地分析

**maturity**: production-ready

#### 核心机制

**architecture**: DQN10 项目自研的三层记忆系统。
热区（bigmemory/hot/）：状态简报（≤1500字）+ 未关闭决策（≤1200字）+ 近期改动（≤1000字），为每次会话提供即时上下文；
冷区（bigmemory/cold/）：按天归档的改动/踩坑/调研/心路/里程碑/会话记录，长期知识沉淀；
知识库（.pipeline/）：包含 terminology/、literature/、survey/、experiments/、papers/ 子目录，存储研究领域结构化知识。
全部为 Markdown 平文件 + YAML 配置，无数据库依赖。
MCP 集成：通过 ACE 
(augment-context-engine) MCP Server 做语义搜索，Grep 工具做精确匹配。
记忆入口：session start 时 memory-worker（sonnet 模型）自动从 bigmemory 检索相关上下文。
记忆出口：用户调用 /archive 手动触发 5 Worker 并行落盘归档。


**retrieval_trigger**: always（每次会话开始时 memory-worker 自动检索）

**verification_method**: none

**cache_tier_strategy**: none（热区/冷区是按时间维度分层，非缓存命中分层）

#### 技术特性

**knowledge_source_types**: Markdown 平文件（实验日志/会话记录/踩坑/里程碑）、YAML 配置、论文 PDF（存于 1_survey/papers/）、代码注释

**retrieval_method**: 向量语义（ACE MCP Server）+ 精确匹配（Grep 工具）

**hallucination_mitigation**: 通过将历史决策、实验结果和踩坑记录注入 session context，减少 AI 对项目特有细节的幻觉；但无自动事实核查机制，依赖 Dr Sun 人工审核

**offline_capability**: full-local（全部本地 Markdown 文件，无云依赖）

**local_model_support**: 支持。memory-worker 使用 claude-sonnet 本地可用，ACE 语义搜索在本地运行

**embedding_strategy**: standard（ACE 使用标准 embedding，未做 chunk 级上下文描述增强）

#### 实用性评估

**setup_complexity**: low（已部署运行，无需额外安装）

**token_cost**: 增加（memory-worker 每次重读全部热区文件约 3700 字，约消耗 ~1500 token；无缓存机制）

**latency**: 秒级（memory-worker 检索约 5-15 秒，/archive 5 Worker 并行约 2-5 分钟）

**dqn10_fit**: 这就是 DQN10 的现有系统，是所有调研方案的对比基准。
当前主要不足：
(1) ACE 无缓存，每次会话重新检索全部文件；

(2) 热区无向量索引，Grep 精确匹配对语义相似内容覆盖不足；

(3) 文献库（.pipeline/literature/）无语义搜索，只能 Grep 关键词；

(4) memory-worker 每次重读全部热区，冷区大后检索成本线性增长。
改进方向：引入 MCP Server 封装检索接口、添加向量索引、实现增量归档。


#### 科研适配

**domain_adaptability**: 强，专为 DQN/强化学习研究定制，所有实验结果、超参数、踩坑均已结构化记录

**incremental_update**: 支持。冷区按天自动追加，热区由 /archive 增量刷新

**citation_traceability**: source-link（论文存于 1_survey/papers/<CitationKey>.pdf，文献记录含 BibTeX key）

**temporal_awareness**: temporal-versioned（冷区文件按日期命名，热区记录近期改动时间戳）

**provenance_tracking**: source-link（可追溯到原始 Markdown 文件，但无 chunk 级或 claim 级精确定位）

**memory_consolidation**: manual（/archive 由 Dr Sun 手动触发，LLM 辅助合并热区内容，但最终由人审核）


### txtai MCP Server

#### 基本信息

**name**: txtai MCP Server

**category**: MCP生态

**source**: https://github.com/neuml/txtai

**maturity**: production-ready

#### 核心机制

**architecture**: txtai 是全功能 AI 框架，核心为嵌入式数据库（embeddings database），融合稀疏向量索引 + 稠密向量索引 + 图网络 + 关系数据库于一体。
组件包括：向量搜索（语义/多模态）、文档 embedding（文本/PDF/音频/图像/视频）、LLM 管道（问答/摘要/标注/翻译）、Workflow（多模型管道）、Agent（组合 embeddings + 管道 + workflow）、API 层（REST Web API + MCP Server）。
MCP Server 特性：可将完整 txtai embeddings 数据库打包为可分享归档（.tar.gz），包含索引文件、文档存储、配置，实现知识库的跨机器迁移和分发。
支持多语言绑定（JavaScript/Java/Rust/Go）。


**retrieval_trigger**: always（MCP 工具调用触发检索）

**verification_method**: none（框架本身无内置验证，需外部集成）

**cache_tier_strategy**: none（不是缓存层，是知识存储和检索框架）

#### 技术特性

**knowledge_source_types**: 文本文件、PDF、音频、图像、视频、代码、数据库、API 数据流（多模态全覆盖）

**retrieval_method**: 混合（稀疏向量 + 稠密向量 + SQL 关系查询 + 图网络遍历）

**hallucination_mitigation**: 通过精确语义检索为 LLM 提供高质量上下文，减少知识缺失幻觉；支持知识图谱结构化存储增强事实一致性；但无主动幻觉检测机制

**offline_capability**: full-local（pip install txtai，纯本地运行，无云依赖；可用 micromodels 至大型 LLM）

**local_model_support**: 支持（从 micromodels 到大型 LLM 全覆盖，支持本地 GGUF/HuggingFace 模型）

**embedding_strategy**: hybrid-sparse-dense（稀疏 + 稠密混合向量索引，优于纯稠密方案）

#### 实用性评估

**setup_complexity**: low（pip install txtai；可选依赖按需安装；容器化部署可用）

**token_cost**: 不变（txtai 本身不消耗 LLM token；其 LLM 管道功能按需使用）

**latency**: ms 级（本地向量索引检索；复杂 LLM 管道为秒级）

**dqn10_fit**: 高契合。
最突出价值：可归档特性——将 bigmemory/.pipeline/ 全部内容打包为一个可分享的 txtai 归档，实现 Mac 和 Ubuntu GPU 服务器间的知识库同步（当前痛点）。
具体优势：
(1) MCP Server 接口直接集成到 Claude Code；

(2) 混合向量检索优于当前纯 ACE 方案；

(3) 多模态支持可检索论文图表/实验结果图；

(4) 全功能框架无需额外组件；

(5) 1872 commits，社区活跃。
局限：
(1) 无时序知识图谱（事实有效期管理）；

(2) 无自动记忆合并去重；

(3) 功能全面但配置复杂，调优需时间。


#### 科研适配

**domain_adaptability**: 强（多模态、多检索方式，可适配论文、代码、实验数据等所有 DQN10 知识类型）

**incremental_update**: 支持（embeddings 数据库支持增量索引更新）

**citation_traceability**: chunk-level（文档存储精确到 chunk，可追溯到原始文档片段）

**temporal_awareness**: static（无原生时序感知，需自定义元数据字段实现）

**provenance_tracking**: chunk-level（向量索引到文档片段级别精确溯源）

**memory_consolidation**: manual（无自动去重合并，需人工或脚本维护）

#### 待核实字段

- benchmark_comparison



---

## 验证核查

### AFEV

#### 基本信息

**name**: AFEV

**category**: 验证核查

**source**: https://arxiv.org/html/2506.07446v1

**maturity**: research

#### 核心机制

**architecture**: AFEV（Adaptive Fact-Evidence Verification）是迭代式原子事实验证框架，包含三个核心模块：
(1) 动态原子事实提取（Dynamic Atomic Fact Extraction）：迭代从复杂声明中提取原子事实，公式为 Ft=Extractor
(C, F_{1:t-1}, y_{1:t-1}, r_{1:t-1})，前一轮验证结果反馈指导下一轮提取，减少错误传播；

(2) 精细证据检索（Refined Evidence Retrieval）：先语义相似度检索 top-k' 候选，再用监督训练的重排器（InfoNCE loss，LLM 选正负样本）过滤噪声，同时用相似度评分动态采样事实专属示例；

(3) 自适应原子事实验证（Adaptive Atomic Fact Verification）：推理器生成事实性标签和可解释理由，理由反馈注入下一轮提取迭代。


**retrieval_trigger**: always（每条原子事实触发精细检索）

**verification_method**: claim-decomposition（迭代分解→证据重排→验证→反馈注入，比 SAFE 增加了迭代和重排步骤）

**cache_tier_strategy**: none

#### 技术特性

**knowledge_source_types**: 结构化知识库（LIAR-PLUS/HOVER/PolitiHop 等事实核查数据集作为证据源）

**retrieval_method**: 混合（语义相似度检索 + 监督重排器精细过滤）

**hallucination_mitigation**: 迭代反馈机制使每轮验证结果改善下一轮事实提取质量；可解释理由提供人工审核入口；重排器过滤噪声证据提高验证精度

**offline_capability**: hybrid（LLM 推理可本地，但证据库构建需要外部数据集）

**local_model_support**: 支持（LLM 推理组件可替换为本地模型）

**embedding_strategy**: standard（检索使用标准语义 embedding）

#### 实用性评估

**setup_complexity**: high（需要训练重排器、构建证据库、实现迭代管道；不是开箱即用工具）

**token_cost**: 增加（迭代分解 + 多次检索 + 重排：论文报告消耗时间 0.94h vs 消融版 0.71h，约增加 32%）

**latency**: 分钟级（迭代处理，完整验证需较长时间）

**dqn10_fit**: 低至中等。
AFEV 主要面向事实核查 benchmark 场景（政治声明、新闻核查），其证据库构建和重排器训练需要大量有标注数据，不适合直接用于 DQN10 项目知识管理。
价值点：迭代反馈机制（验证结果改善下一轮提取）是对 SAFE 的有价值改进，可借鉴其设计思路；
但工程实现成本高，不如 MiniCheck 直接可用。
最适合：若 DQN10 未来需要对 AI 生成论文内容做自动核查，可参考 AFEV 的迭代反馈设计，不必直接使用 AFEV 系统。


#### 科研适配

**domain_adaptability**: 中等（训练重排器需要领域标注数据，DQN 领域适配成本高）

**incremental_update**: 不涉及（验证工具，非知识库）

**citation_traceability**: claim-level（精确到每条原子事实及其验证理由）

**temporal_awareness**: static

**provenance_tracking**: claim-level（可解释理由精确到原子事实级别）

**memory_consolidation**: none


### MiniCheck

#### 基本信息

**name**: MiniCheck

**category**: 验证核查

**source**: https://arxiv.org/abs/2404.10774

**maturity**: production-ready

#### 核心机制

**architecture**: MiniCheck 是轻量级事实核查模型（最佳版本 MiniCheck-FT5，770M 参数，基于 Flan-T5）。
训练方法：使用 GPT-4 构建合成训练数据——通过结构化生成程序创建真实但具有挑战性的事实错误实例，涵盖 RAG 生成、摘要、文档对话等场景。
统一基准：构建 LLM-AggreFact 基准，整合来自事实核查和 LLM 生成溯源研究的多个数据集。
核查粒度：模型可检查声明中的每个事实，并识别跨句子信息综合中的错误。
发表于 EMNLP 2024。


**retrieval_trigger**: none（MiniCheck 是验证模型，非检索系统）

**verification_method**: claim-decomposition（检查声明中的每个事实，逐条核验）

**cache_tier_strategy**: none

#### 技术特性

**knowledge_source_types**: 文档文本（作为事实核查的参考来源）

**retrieval_method**: none（MiniCheck 是判别模型，输入为声明+参考文档，直接输出事实一致性评分）

**hallucination_mitigation**: 在知识写入前作为质量门控：给定声明和参考文档，MiniCheck 判断声明是否被文档支持，拦截不一致的事实写入知识库；770M 参数本地可运行，实现低成本高频率核查

**offline_capability**: full-local（770M 参数模型可本地部署，无 API 依赖）

**local_model_support**: 支持（MiniCheck-FT5 770M 参数，单 GPU 可运行）

**embedding_strategy**: none（判别模型，非向量检索系统）

#### 实用性评估

**setup_complexity**: low（HuggingFace 上公开发布，pip install 后下载模型即用）

**token_cost**: 不变（本地模型推理，不消耗 LLM API token）

**latency**: ms 级（770M 参数推理，GPU 上约 10-50ms/样本）

**dqn10_fit**: 高价值，适合用作知识写入前的质量门控。
具体场景：
(1) /archive 归档前对 memory-worker 提取的关键事实做自动核查，拦截幻觉信息写入 bigmemory；

(2) 论文摘要写入 .pipeline/literature/ 前验证与原文一致性；

(3) 实验结果记录前核查与代码输出的一致性。
核心优势：400x 成本优势意味着可以对每条归档事实做核查而不增加显著成本；
770M 参数 Mac M 系列芯片可运行。
局限：需要参考文档作为核查基准（无参考文档时无法核查）。


#### 科研适配

**domain_adaptability**: 强（模型训练覆盖多领域事实核查；对 DQN 实验结果记录的核查需要提供实验日志作为参考）

**incremental_update**: 不涉及（MiniCheck 是推理时工具，非知识库）

**citation_traceability**: claim-level（输出精确到哪条事实不被支持）

**temporal_awareness**: static（模型本身无时间感知）

**provenance_tracking**: claim-level（可精确指出哪条声明不被参考文档支持）

**memory_consolidation**: none（非知识管理系统）


### RAGLens / SAE-based

#### 基本信息

**name**: RAGLens / SAE-based

**category**: 验证核查

**source**: https://arxiv.org/abs/2512.08892

**maturity**: research

#### 核心机制

**architecture**: RAGLens 是轻量级 RAG 幻觉检测器，利用稀疏自编码器（Sparse Autoencoders, SAE）解缠 LLM 内部激活。
核心流程：
(1) 在 LLM 中间层提取内部激活（mid-layer activations）；

(2) 用预训练 SAE 将激活分解为稀疏特征表示；

(3) 使用基于信息的特征选择（Information-based Feature Selection）识别与 RAG 幻觉高度相关的特征；

(4) 用广义加法模型（GAM, Generalized Additive Model）将 SAE 特征映射到幻觉预测分数；

(5) 输出 token 级别的幻觉标注和可解释理由。
关键发现：中间层 SAE 特征对 RAG 幻觉检测信息量最大；
GAM 特别适合 SAE 特征到幻觉预测的映射。
无需大规模标注训练，无需调用外部 LLM judge。


**retrieval_trigger**: none（RAGLens 是后验检测工具，非检索系统）

**verification_method**: sae-based（稀疏自编码器解缠 LLM 内部激活，区别于所有外部验证方法）

**cache_tier_strategy**: none

#### 技术特性

**knowledge_source_types**: LLM 内部激活（不依赖外部知识源）

**retrieval_method**: none（基于模型内部状态，无检索）

**hallucination_mitigation**: 从 LLM 内部识别幻觉特征，提供 token 级别的可解释标注，使人工或自动审核可精确定位不可信输出；SAE 特征可用于后验缓解（post-hoc mitigation）

**offline_capability**: full-local（完全基于 LLM 内部激活，无外部 API 依赖）

**local_model_support**: 支持（在 Llama2-7B/13B、Llama3、Qwen 上验证；需要模型内部激活访问权限，适合开源本地模型）

**embedding_strategy**: none（不使用 embedding，基于内部激活分析）

#### 实用性评估

**setup_complexity**: high（需要访问 LLM 内部激活，仅适用于开源模型；需要预训练 SAE；GAM 训练需要少量标注样本）

**token_cost**: 不变（不消耗额外 LLM token；激活提取在推理时同步完成）

**latency**: ms 级（激活提取与推理同步，GAM 推理极快）

**dqn10_fit**: 低至中等。
核心限制：
(1) 需要开源模型（无法用于 Claude API，因为无法访问内部激活）；

(2) 需要预训练 SAE（当前仅有 Llama 等模型的公开 SAE）；

(3) 对本地运行的 Llama/Qwen 等模型有价值，但 DQN10 主要使用 Claude API。
价值场景：若 DQN10 引入本地开源 LLM 做辅助任务（如 memory-worker 用 Llama），可用 RAGLens 监控其输出质量。
可解释性优势：SAE 特征可视化帮助理解幻觉来源，有科研价值。


#### 科研适配

**domain_adaptability**: 强（模型内部激活方法无领域约束）

**incremental_update**: 不涉及

**citation_traceability**: claim-level（token 级别幻觉标注）

**temporal_awareness**: static

**provenance_tracking**: claim-level（可解释 SAE 特征提供 token 级别溯源）

**memory_consolidation**: none


### SAFE (Google DeepMind)

#### 基本信息

**name**: SAFE (Google DeepMind)

**category**: 验证核查

**source**: https://arxiv.org/abs/2403.18802

**maturity**: research

#### 核心机制

**architecture**: SAFE（Search-Augmented Factuality Evaluator）是 Google DeepMind 提出的长文本事实性评估框架。
工作流程：
(1) 将 LLM 长文本响应分解为独立的原子事实（Atomic Facts）；

(2) 对每条原子事实构建多步推理搜索查询；

(3) 使用 Google Search 检索支持/反驳证据；

(4) 基于检索证据判断每条事实是否被支持。
评估指标：扩展 F1 分数（平衡精确率和召回率），精确率 = 被支持事实比例，召回率 = 相对用户期望响应长度的事实覆盖率。
数据集：LongFact（数千问题，跨 38 个主题，GPT-4 生成）。


**retrieval_trigger**: always（每条原子事实触发搜索验证）

**verification_method**: claim-decomposition（长文本→原子事实→逐条搜索验证，两级分解）

**cache_tier_strategy**: none

#### 技术特性

**knowledge_source_types**: 网页搜索结果（Google Search）

**retrieval_method**: 向量语义 + 关键词（Google Search 内部实现）

**hallucination_mitigation**: 通过将长文本分解为原子事实逐条用外部搜索验证，精确识别不被支持的声明；与众包人工标注对比：SAFE 协议一致率 72%，在 100 个争议案例中胜出 76%，且成本降低 20x 以上

**offline_capability**: cloud-only（依赖 Google Search API，无法离线运行）

**local_model_support**: 部分支持（原子事实分解和推理可用本地 LLM，但搜索验证依赖 Google Search）

**embedding_strategy**: none（基于搜索的验证，不使用 embedding）

#### 实用性评估

**setup_complexity**: medium（需要 Google Search API 密钥；原子事实分解需要强 LLM；多步推理增加调用次数）

**token_cost**: 增加（每条原子事实触发多步 LLM 推理 + 搜索，长文本验证 token 消耗显著）

**latency**: 分钟级（每条原子事实多步搜索，长文本响应验证需数分钟）

**dqn10_fit**: 中等价值，主要限制是依赖外部搜索。
适用场景：
(1) 论文写作时验证技术声明是否有文献支撑；

(2) 归档前验证 AI 生成的实验结论摘要。
局限：
(1) Google Search 无法访问 DQN10 本地实验数据库；

(2) 延迟分钟级不适合高频归档流程；

(3) 成本虽比人工低 20x，但与 MiniCheck（本地运行，400x 更便宜）相比仍较高；

(4) 无法验证未公开的新实验结果。
对 DQN10 的最佳用途：论文写作阶段批量验证引用声明。


#### 科研适配

**domain_adaptability**: 强（评估框架领域无关；DQN 领域的技术声明可通过搜索 arXiv/文献验证）

**incremental_update**: 不涉及（评估工具，非知识库）

**citation_traceability**: claim-level（精确到每条原子事实的支持/反驳证据）

**temporal_awareness**: static（无时间感知，搜索结果可能引入时间偏差）

**provenance_tracking**: claim-level（每条原子事实对应具体搜索证据来源）

**memory_consolidation**: none（非知识管理系统）



---

## 架构范式

### A-RAG (Agentic RAG)

#### 基本信息

**name**: A-RAG (Agentic RAG)

**category**: 架构范式

**source**: https://arxiv.org/abs/2602.03442

**maturity**: research

#### 核心机制

**architecture**: A-RAG（Agentic RAG）框架将分层检索接口直接暴露给 LLM Agent，让模型主动参与检索决策，而非依赖固定算法或预定义工作流。
三种层次化检索工具：
(1) 关键词搜索（Keyword Search）：宽泛信息发现；

(2) 语义搜索（Semantic Search）：基于含义的精准检索；

(3) 块阅读（Chunk Read）：细粒度文档深度探索。
三原则设计：自主策略（Agent 自主决定何时检索、用哪种工具）+ 迭代执行（多轮检索逐步精化）+ 工具交替（不同粒度检索工具灵活切换）。
关键区别：传统 RAG 单轮固定检索→Agent 被动接收；
A-RAG 多轮自主检索→Agent 主动参与，实现随模型能力和测试时计算扩展的性能提升。


**retrieval_trigger**: rl-learned（Agent 自主决定检索策略，类似 RL 学习的决策过程）

**verification_method**: none（框架侧重检索策略，无内置验证）

**cache_tier_strategy**: none

#### 技术特性

**knowledge_source_types**: 文档知识库（支持向量语义和关键词检索的任意文档集）

**retrieval_method**: 混合（关键词搜索 + 语义搜索 + 块级读取，由 Agent 自主选择）

**hallucination_mitigation**: 多粒度迭代检索确保 Agent 获取充分证据后再生成，减少因证据不足导致的幻觉；Agent 可主动发起深度探索（Chunk Read）验证关键细节

**offline_capability**: hybrid（框架本身与云/本地无关；取决于底层 LLM 和检索库选择）

**local_model_support**: 支持（框架与模型无关，可配合本地 LLM）

**embedding_strategy**: standard（语义搜索组件使用标准 embedding）

#### 实用性评估

**setup_complexity**: medium（需要构建三种粒度的检索接口；与现有 RAG 基础设施集成相对简单）

**token_cost**: 不变或增加（迭代检索消耗更多 token，但检索到更相关内容减少生成时的冗余；论文报告使用相当或更少的检索 token）

**latency**: 秒级（多轮迭代检索；Agent 自主策略可能导致变长的检索序列）

**dqn10_fit**: 高契合，设计理念与 DQN10 需求高度匹配。
具体价值：
(1) 暴露分层检索接口给 Claude Agent（bigmemory 热区=关键词检索，.pipeline/=语义搜索，具体文件=块读取），复用现有三层架构语义；

(2) 迭代检索适合复杂问题（如「最近三周哪些实验配置被修改」需要多轮查询）；

(3) 随模型能力提升自动获益，无需修改框架。
实施路径：将现有 ACE 和 Grep 工具重新包装为三种层次化 MCP Tools，memory-worker 自动获得 A-RAG 能力，工程量最小。


#### 科研适配

**domain_adaptability**: 强（框架无领域约束，DQN 实验日志和论文知识库均可接入）

**incremental_update**: 支持（底层检索库增量更新，框架层无感知）

**citation_traceability**: chunk-level（Chunk Read 工具可追溯到文档片段级别）

**temporal_awareness**: static（框架本身无时序感知，需底层知识库支持）

**provenance_tracking**: chunk-level（精细粒度的 Chunk Read 工具支持精确溯源）

**memory_consolidation**: none（框架层不涉及记忆整合）

#### 待核实字段

- benchmark_comparison


### Anthropic Contextual Retrieval

#### 基本信息

**name**: Anthropic Contextual Retrieval

**category**: 架构范式

**source**: https://www.anthropic.com/news/contextual-retrieval

**maturity**: production-ready

#### 核心机制

**architecture**: Contextual Retrieval 在 embedding 前用 Claude（默认 Claude 3 Haiku）为每个文档 chunk 生成上下文描述（50-100 tokens），并将描述前置拼接到 chunk 内容后再建索引。
问题根源：传统 RAG 将文档切片后丢失了每个片段的文档级上下文（如「收入增长了 3%」不知道是哪家公司）。
解决方案：提示 Claude「为该 chunk 在文档中的位置生成简短上下文描述，用于改善搜索检索」，生成的上下文描述精确补充 chunk 缺失的文档级信息。
检索层：语义 embedding（Gemini/Voyage 效果最佳）+ BM25 词法匹配 + Rank Fusion 融合 + 可选 Reranker（进一步精化）。
成本优化：使用 Prompt Caching，为每个文档所有 chunk 生成上下文的一次性成本约为 $1.02/百万 token。


**retrieval_trigger**: always（标准检索触发，上下文描述在索引构建时预生成）

**verification_method**: none

**cache_tier_strategy**: none

#### 技术特性

**knowledge_source_types**: 文档知识库（PDF/文本/网页等，切片后处理）

**retrieval_method**: 混合（语义 embedding + BM25 词法 + Rank Fusion + 可选 Reranker）

**hallucination_mitigation**: 通过为每个 chunk 补充文档级上下文，减少检索到孤立片段（缺上下文）的概率，从而减少 LLM 因缺乏完整背景而产生的幻觉

**offline_capability**: hybrid（上下文生成需要 Claude API；但生成一次后索引可离线使用）

**local_model_support**: 部分（上下文描述生成依赖 Claude API；embedding 和检索可本地运行；可用本地 LLM 替代 Claude 做上下文生成，效果差异未官方测试）

**embedding_strategy**: contextual（核心特性：chunk 前添加上下文描述后再 embedding，显著区别于标准 embedding）

#### 实用性评估

**setup_complexity**: low（在现有 RAG 管道中插入上下文生成步骤；Claude API 调用，prompt caching 降低成本）

**token_cost**: 一次性增加（索引构建时约 $1.02/百万 token；检索阶段 token 消耗不变）

**latency**: 索引构建：分钟级（API 调用生成描述）；检索：ms 级（预构建索引查询）

**dqn10_fit**: 高契合，且实施成本最低。
核心价值：DQN10 的 .pipeline/literature/ 和 bigmemory 冷区存在大量孤立 chunk（如实验结果片段脱离了实验设计上下文），Contextual Retrieval 精确解决此问题。
具体应用：
(1) 为 .pipeline/literature/ 每篇论文的 chunk 生成「在论文 X 第 Y 节中，讨论了...」格式的上下文描述；

(2) 为 bigmemory 冷区每条归档记录生成「该记录来自 YYYY-MM-DD 的会话，涉及实验...」的描述；

(3) 与现有 ACE 语义搜索组合（ACE 可能已用类似方案），进一步提升检索质量。
检索失败率降低 35-67% 直接解决当前 ACE 检索质量不稳定的痛点。


#### 科研适配

**domain_adaptability**: 强（无领域约束；适配 DQN 领域只需调整上下文描述 prompt 模板）

**incremental_update**: 支持（新增 chunk 单独生成上下文描述后更新索引，成本可控）

**citation_traceability**: chunk-level（上下文描述包含文档位置信息，增强溯源能力）

**temporal_awareness**: static（无时序感知，需配合元数据字段）

**provenance_tracking**: chunk-level（上下文描述明确记录 chunk 在文档中的位置）

**memory_consolidation**: none（不涉及记忆整合）


### Domain-Grounded Tiered Retrieval

#### 基本信息

**name**: Domain-Grounded Tiered Retrieval

**category**: 架构范式

**source**: https://arxiv.org/abs/2603.17872

**maturity**: research

#### 核心机制

**architecture**: 基于 LangGraph 实现的四阶段自调节检索框架，每阶段均可早退（Early-Exit）优化计算效率：
(1) 内在验证（Intrinsic Verification）：LLM 自评是否已知答案，知则提前返回，未知则触发检索；

(2) 领域探测（Domain Detection/Adaptive Search Routing）：使用 Domain Detector 识别查询所属领域，路由到特定领域档案库（subject-specific archives）而非通用检索；

(3) 精细过滤（Refined Context Filtering, RCF）：消除无关或分散注意力的上下文信息，只保留核心证据；

(4) 外在再生成（Extrinsic Regeneration）：基于过滤后证据重新生成答案，并附加原子声明级别的事实验证。


**retrieval_trigger**: confidence-based（第一阶段内在验证：LLM 自评置信度，高置信直接返回，低置信触发后续阶段）

**verification_method**: claim-decomposition（第四阶段：原子声明级别的外在验证）

**cache_tier_strategy**: none（分层是检索流程分层，非缓存分层）

#### 技术特性

**knowledge_source_types**: 领域专属档案库（domain-specific archives）、通用知识库

**retrieval_method**: 混合（领域路由 + 语义检索 + 精细过滤）

**hallucination_mitigation**: 四阶段组合：早退避免不必要检索引入噪声→领域路由提高检索精准度→精细过滤消除干扰证据→外在再生成+验证确保输出一致性

**offline_capability**: hybrid（LangGraph 框架本地可运行；领域档案库可本地构建；LLM 部分依赖模型选择）

**local_model_support**: 支持（LangGraph 框架与模型无关，可配置本地 LLM）

**embedding_strategy**: standard（检索使用标准 embedding）

#### 实用性评估

**setup_complexity**: high（需要 LangGraph 编排、Domain Detector 训练/配置、领域档案库构建，整体工程量较大）

**token_cost**: 不变或降低（早退机制减少不必要的检索和生成；精细过滤减少上下文 token）

**latency**: 秒级（多阶段串行处理，早退优化最佳情况；完整四阶段约数秒）

**dqn10_fit**: 中等契合。
四阶段框架的设计理念（领域路由 + 分层检索 + 精细过滤）对 DQN10 知识系统升级有参考价值。
具体价值：
(1) 领域探测思路可用于区分「实验配置查询」vs「论文检索查询」vs「代码问题查询」，路由到不同知识库（.pipeline/experiments/ vs .pipeline/literature/）；

(2) 早退机制减少对 bigmemory 的无效检索。
局限：
(1) 2026 年论文，代码可获得性待确认；

(2) 工程实现成本高；

(3) Domain Detector 配置需要领域标注数据；

(4) 对单人科研场景可能过于复杂。


#### 科研适配

**domain_adaptability**: 强（框架领域无关；DQN 领域适配关键在 Domain Detector 和档案库构建）

**incremental_update**: 支持（领域档案库可增量更新）

**citation_traceability**: chunk-level（精细过滤阶段保留证据来源）

**temporal_awareness**: static（无时序感知机制）

**provenance_tracking**: chunk-level（第四阶段外在验证追踪到具体证据片段）

**memory_consolidation**: none

#### 待核实字段

- integration_effort


### Microsoft GraphRAG

#### 基本信息

**name**: Microsoft GraphRAG

**category**: 架构范式

**source**: https://github.com/microsoft/graphrag

**maturity**: production-ready

#### 核心机制

**architecture**: GraphRAG 是模块化图谱增强 RAG 系统，核心为从非结构化文本自动提取结构化知识图谱。
数据管道：
(1) 文本摄入→实体/关系提取（LLM 驱动）→知识图谱构建；

(2) 社区检测（层次聚类算法，如 Leiden 算法）识别图谱中的实体社区；

(3) 分层摘要生成（从叶节点到根节点逐层生成摘要）。
检索模式：Local Search（子图遍历，精确问题）和 Global Search（社区摘要层次遍历，宏观问题）。
溯源：知识图谱节点携带来源文档和 chunk 引用，支持完整溯源链。
技术栈：Python（88%），88 万行代码，32.1k GitHub stars，v3.0.8（2026年3月），支持 Azure OpenAI 和 OpenAI 模型。


**retrieval_trigger**: always（Local/Global Search 按需触发，由 Agent 选择）

**verification_method**: retrieval-based（知识图谱结构化存储提供间接事实锚定）

**cache_tier_strategy**: none

#### 技术特性

**knowledge_source_types**: 非结构化文本文档（PDF/Markdown/网页/代码注释均可）

**retrieval_method**: 图谱遍历（Local Search：子图查询；Global Search：社区摘要层次遍历）

**hallucination_mitigation**: 知识图谱结构化存储替代原始文本检索，实体关系明确减少歧义；分层摘要减少 LLM 需要推理的原始文本量；完整溯源链支持人工事后核查

**offline_capability**: hybrid（框架开源本地可运行；但当前主要文档和测试基于 Azure OpenAI/OpenAI API；本地 LLM 支持需要额外配置）

**local_model_support**: 部分支持（GitHub 有 Ollama/本地 LLM 集成 issue 和 PR，但非一级支持；实体提取需要强模型）

**embedding_strategy**: standard（实体和社区摘要使用标准 embedding 做向量检索辅助）

#### 实用性评估

**setup_complexity**: high（graphrag init → graphrag index 流程；提示调优（Prompt Tuning）强烈建议；索引构建对大型语料库需数小时；Azure OpenAI 部署或本地 LLM 配置均有学习曲线）

**token_cost**: 增加 3-5x（实体/关系提取、社区摘要生成消耗大量 LLM token；官方警告需仔细评估成本；小数据集先验估算）

**latency**: 索引构建：分钟至小时级；查询：秒级（Local Search 快于 Global Search）

**dqn10_fit**: 中等契合，成本是主要障碍。
优势：
(1) 从 DQN10 论文/实验日志提取知识图谱，自动识别算法关系（DQN→Double DQN→Dueling DQN 等演进关系）；

(2) 社区层次检测可聚类相关实验；

(3) 强溯源能力满足学术可信度要求；

(4) 32.1k stars，微软背书，维护有保障。
局限：
(1) 索引构建成本 3-5x 基线 RAG，对单人科研场景昂贵；

(2) 需要 Azure OpenAI 或 OpenAI API（本地 LLM 支持不稳定）；

(3) 实体提取质量对小语料库（百篇论文）是否足够有待验证；

(4) 复杂配置不适合快速迭代的研究工作流。
建议：在 DQN10 论文调研阶段（数百篇论文）考虑一次性构建，不用于日常 bigmemory 管理。


#### 科研适配

**domain_adaptability**: 强（支持任意非结构化文本；DQN 领域实体提取需要专门调优 Prompt）

**incremental_update**: 部分支持（v3.0 增加了增量索引能力，但完整重建仍是更稳定的方案）

**citation_traceability**: chunk-level（知识图谱节点携带来源文档和 chunk 引用，溯源能力是核心优势）

**temporal_awareness**: static（无时序有效期管理，图谱节点静态存储）

**provenance_tracking**: chunk-level（知识图谱每个节点/边精确追溯到源文档 chunk）

**memory_consolidation**: graph-based（知识图谱自动合并相关实体，社区检测聚类相关知识）


