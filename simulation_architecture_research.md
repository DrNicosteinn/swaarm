# Multi-Agent Social Simulation Architecture Research

## 1. OASIS Architecture (camel-ai) -- Deep Dive

**Source:** [OASIS Paper](https://arxiv.org/abs/2411.11581) | [GitHub](https://github.com/camel-ai/oasis)

### Core Architecture

OASIS consists of four independent modules communicating through async channels:

1. **Environment Server** -- SQLite database storing users, posts, interactions, social graph, recommendations, and action traces
2. **Agent Module** -- LLM-powered agents extending CAMEL-AI's ChatAgent
3. **Recommendation System** -- Pluggable algorithms (Random, Twitter-style, TwHIN-BERT, Reddit hot-score)
4. **Time Engine** -- Discrete time steps (1 step = 3 minutes simulated time)

### The Round Loop

```
Per time step:
  1. Environment Server sends user info + posts to RecSys
  2. RecSys filters/ranks content using platform-specific algorithms
  3. Time Engine probabilistically activates eligible agents
     - Each agent has a 24-dimensional hourly activity probability vector
     - NOT all agents are active each tick -- stochastic activation
  4. Activated agents receive recommended posts + context
  5. Agent Module generates chain-of-thought reasoning -> selects action(s)
  6. Actions modify environment state (DB updates)
  7. Cycle repeats
```

### Agent-Platform Channel

The Platform class runs an async event loop:

```python
async def running(self):
    while True:
        message_id, data = await self.channel.receive_from()
        agent_id, message, action = data
        action = ActionType(action)
        action_function = getattr(self, action.value, None)
        # ... execute action ...
        await self.channel.send_to((message_id, agent_id, result))
```

Key design: Agents and Platform are fully decoupled via a Channel abstraction. Agents send `(agent_id, message, action_type)` tuples. Platform dispatches via reflection (`getattr`). Results flow back through the same channel.

### Agent Decision Pipeline

The `SocialAgent` class:
1. Receives environment state via `env.to_text_prompt()` (converts DB state to natural language)
2. Constructs a user message requesting social media actions
3. Calls `await self.astep(user_msg)` for LLM inference
4. Extracts tool calls from `response.info['tool_calls']`
5. Executes actions via `SocialAction` wrapper -> Channel -> Platform

Three selection modes: LLM-based (autonomous), HCI-based (human-in-the-loop), Data-driven (external system)

### Scaling to 1M Agents

- GPU resource manager balances agent requests across available GPUs
- vLLM for optimized inference batching
- 1M agents, 10 time steps = 27 A100 GPUs, 18 hours per time step
- Generates ~48.5K new posts + 97.1K comments per step

### 21 Supported Action Types

create_post, like, unlike, dislike, undo_dislike, comment, repost, share, follow, unfollow, mute, unmute, block, unblock, search, trend, view_profile, update_profile, create_group, join_group, send_group_message

---

## 2. Stanford Generative Agents (Park et al. 2023)

**Source:** [Paper](https://arxiv.org/abs/2304.03442) | [ACM](https://dl.acm.org/doi/10.1145/3586183.3606763)

### Three-Pillar Architecture

#### A. Memory Stream

A time-ordered database of all agent experiences stored as natural language observations. Each memory entry contains:
- Natural language description
- Creation timestamp
- Last access timestamp
- Importance score (integer, assigned by LLM)
- Embedding vector (for relevance computation)

#### B. Retrieval Function

Memories are retrieved using a weighted combination of three scores:

```
retrieval_score = alpha * recency + beta * importance + gamma * relevance
```

Where (with equal weighting, alpha = beta = gamma):
- **Recency:** Exponential decay function, decay factor = 0.995 per hour
  - Formula: recency = 0.995^(hours_since_last_access)
- **Importance:** LLM-assigned integer (1-10 scale)
  - Prompt: "On the scale of 1 to 10, where 1 is purely mundane and 10 is extremely poignant, rate the likely poignancy of the following memory"
  - Example: "brushing teeth" = 1, "breaking up" = 8
- **Relevance:** Cosine similarity between memory embedding and current query embedding

All three scores are min-max normalized before combination.

#### C. Reflection System

Triggered when the cumulative importance scores of recent (unreflected) memories exceed a threshold (~150). Agents reflect approximately 2-3 times per simulated day.

Reflection generation process:
1. Retrieve top-100 recent memories
2. Ask LLM: "Given only the information above, what are 3 most salient high-level questions we can answer about the subjects?"
3. For each question, retrieve relevant memories
4. Generate insight statement with citations to source memories
5. Store reflection as a new memory entry (with its own importance score)

Reflections can reference other reflections -- creating a hierarchy of abstraction.

#### D. Planning System

Top-down recursive decomposition:
1. **Day plan:** 5-8 broad agenda items (based on agent summary + yesterday's activities)
2. **Hour blocks:** Each agenda item decomposed into hour-long chunks
3. **Fine-grained:** Each hour block into 5-15 minute activities

Plans are stored and can be revised when:
- An unexpected observation occurs
- The agent decides the new observation warrants a reaction
- The agent enters dialogue with another agent

#### E. Per-Step Decision Loop

```
Each game step (roughly 1 minute simulated):
  1. Agent perceives nearby objects/agents in environment
  2. Observations stored in memory stream with importance scores
  3. Retrieved memories inform: should I continue my plan or react?
  4. If continue: execute next planned action
  5. If react: generate new plan from this moment, execute first action
  6. If another agent nearby: decide whether to initiate dialogue
  7. If in dialogue: generate utterance using memories + relationship context
```

---

## 3. S3 Social Network Simulation

**Source:** [Paper](https://arxiv.org/abs/2307.14984)

### Agent Decision Pipeline (Markov Process)

Each agent's per-tick decision follows a pipeline:

```
Input: user demographics + current state + received posts + memory pool
  |
  v
Step 1: EMOTION UPDATE (Markov chain)
  - Three levels: calm -> moderate -> intense
  - LLM evaluates emotional triggers given demographics, current state, message content
  - Decay coefficient controls temporal fade
  |
  v
Step 2: ATTITUDE UPDATE (Markov chain)
  - Binary spectrum: negative <-> positive
  - LLM predicts shift based on user profile + message influence
  |
  v
Step 3: INTERACTION DECISION
  - Given demographics + specific post content
  - LLM decides: repost / create new content / remain inactive
  - 66.2-69.5% accuracy vs. real behavior
  |
  v
Step 4: CONTENT GENERATION (if active)
  - LLM generates text matching user expression patterns
  - Prompted with user profile + current emotional/attitudinal state
  - 0.723-0.741 cosine similarity to real posts
```

### Memory Pool (Weighted)

Each agent maintains a weighted message history using three influence factors:
1. **Temporal:** Exponential decay -- recent posts score higher
2. **Relevance:** Cosine similarity between user attributes and content
3. **Authenticity:** Source-based scoring:
   - Mutual followers > unidirectional followers > platform recommendations

### Initialization

- Network from real social media data (keyword extraction -> user identification -> directed edges)
- Missing demographics inferred via LLM:
  - Gender: P-Tuning v2, 71% accuracy
  - Age: MAE 7.53 years
  - Occupation: 10 categories, zero-shot LLM inference

### Key Insight: Prompt Engineering + Prompt Tuning

S3 uses BOTH:
- **Prompt engineering** for behavior simulation (emotion, attitude, interaction decisions)
- **Prompt tuning / P-Tuning v2** for demographic inference (fine-tuned on labeled data)

---

## 4. Persona Hub (Tencent)

**Source:** [Paper](https://arxiv.org/abs/2406.20094) | [GitHub](https://github.com/tencent-ailab/persona-hub)

### Architecture for Generating 1 Billion Diverse Personas

#### Text-to-Persona Pipeline

1. Take web text from RedPajama v2 dataset
2. Prompt LLM: "Who would [read/write/like/dislike] this text?"
3. LLM infers fine-grained persona descriptions
4. Granularity is controllable:
   - Coarse: "a computer scientist"
   - Fine: "a machine learning researcher focused on neural network architectures and attention mechanisms"

#### Persona-to-Persona Expansion

Based on six-degrees-of-separation theory:
1. Take initial persona from Text-to-Persona
2. Ask LLM: "Who is in close relationship with this persona?"
3. Example: "a nurse at a children's hospital" -> "a child", "a parent", "a pediatrician"
4. Repeat for 6 iterations per initial persona
5. This captures underrepresented demographics with low web visibility

#### Deduplication (Multi-Stage)

1. MinHash-based surface deduplication (n-gram features, 1-gram, signature size 128, 0.9 threshold)
2. Embedding-based semantic deduplication (text-embedding-3-small, cosine similarity, 0.9 threshold)
3. Heuristic quality filtering
4. Result: 1,015,863,523 unique personas

#### Applicability to Swaarm

This approach can be adapted for generating diverse agent personas for simulations:
- Use company context / industry / audience data as "seed text"
- Generate personas via Text-to-Persona
- Expand social networks via Persona-to-Persona
- Deduplicate to ensure genuine diversity

---

## 5. Best Practices for LLM-Agent Simulation

### Keeping Agent Behavior Consistent

1. **Persona in system prompt:** Define demographics, personality traits, beliefs, communication style
2. **Temperature control:**
   - Use T=1.0 during persona generation (maximize diversity)
   - Use T=0.3 during behavior inference (maximize consistency)
3. **Prompt completion technique:** Pre-fill the start of the desired output to steer format and tone
4. **Memory context:** Include recent actions in each prompt so agents maintain narrative coherence
5. **Self-consistency sampling:** Sample multiple outputs, pick the most common reasoning path

### Preventing Mode Collapse (All Agents Responding Similarly)

1. **Diverse persona descriptions:** Use detailed, specific persona text (not just "a 35-year-old man")
2. **Demographic-specific language patterns:** Include preferred vocabulary, sentence complexity, emotional expression style in system prompt
3. **Heterogeneous activity patterns:** Different agents have different activation probabilities per time of day
4. **Emergent individuality:** Research shows that even without predefined characteristics, personalities can diverge through agent interactions (similar to MBTI distribution)
5. **Varied temperature per agent type:** More opinionated personas -> slightly higher temperature
6. **Structural diversity in prompts:** Give different agents different prompt structures or emphasis areas

### Structured Output vs. Free-Form

**Recommendation: Use structured output (function calling / JSON mode) for actions.**

| Approach | Pros | Cons |
|----------|------|------|
| **Function calling** | Reliable parsing, schema validation, type safety, integrates with platform action system | Token overhead for function definitions, constrains creative expression |
| **JSON mode** | Flexible schema, lighter than function calling, good for multi-field responses | No built-in validation, model can hallucinate keys |
| **Free-form text** | Natural expression, good for content generation (posts, comments) | Hard to parse reliably, ambiguous actions |
| **Constrained decoding** | Guaranteed valid output, zero parsing failures | Requires self-hosted models (vLLM/TGI), not available via API |

**Best hybrid approach for Swaarm:**
- Function calling for action selection (like, comment, repost, scroll, ignore)
- Free-form text for content generation (the actual post/comment text)
- JSON mode for structured reasoning (emotion state, engagement probability)

---

## 6. Performance Optimization

### Prompt Caching Strategy

**Critical for cost reduction (up to 90% savings on input tokens).**

Structure prompts with static content first, dynamic content last:

```
[CACHED PREFIX -- identical across all calls for same agent type]
  System prompt: You are a social media user...
  Platform rules and available actions
  Agent persona description (static per agent)
  Tool/function definitions

[DYNAMIC SUFFIX -- changes each tick]
  Current feed content (recommended posts)
  Recent agent actions (memory window)
  Current emotional/attitudinal state
  Specific instruction for this tick
```

**Key rules:**
- The exact token sequence must match from the start of the prompt
- A single different token invalidates cache from that point onward
- DO NOT put timestamps at the start of system prompts
- Group agents by persona type to maximize cache hits across agents
- Anthropic Claude: cache reads cost 0.1x base price (90% discount)
- OpenAI: automatic prefix caching for prompts > 1024 tokens

### Token Optimization

1. **Compress persona descriptions:** Use structured key-value pairs instead of prose
   ```
   name: Maria | age: 42 | role: marketing_manager | political: center-left
   traits: analytical, cautious, data-driven | tone: professional, measured
   ```
   vs. a 200-word narrative (saves ~150 tokens per agent per call)

2. **Sliding window memory:** Only include last N actions/observations (not full history)

3. **Summarize feed content:** Don't pass full post text -- summarize to key signals:
   ```
   Post #1: [political, controversial, 847 likes, from influencer]
   Post #2: [product review, neutral, 12 likes, from connection]
   ```

4. **Tiered prompt complexity:** Simple agents (lurkers) get shorter prompts than active agents

### Batching Strategies

**Can you batch multiple agents into one LLM call?**

This is tempting but problematic:

- **Single-agent-per-call is recommended** for quality and cache optimization
- Batching multiple agents in one prompt causes:
  - Cross-contamination of personas
  - Reduced output quality
  - Cache invalidation (each batch has different agent combinations)
  - Harder error recovery (one failure affects whole batch)

**Better batching approaches:**
- **Async concurrent calls:** Fire off many independent agent calls simultaneously
- **API-level batching:** Use OpenAI Batch API (50% discount, 24h turnaround) for non-real-time simulation
- **vLLM continuous batching:** If self-hosting, vLLM automatically batches at the inference level (1,500 tokens/sec vs 200 for sequential)
- **Prefix caching + concurrent calls = best combination:** Same prefix cached, different dynamic suffixes, all fired concurrently

### Architecture Pattern: Agent Tiers

For cost optimization, not all agents need full LLM reasoning:

```
Tier 1: FULL LLM AGENTS (10-15% of population)
  - Key opinion leaders, influencers, active commenters
  - Full chain-of-thought reasoning each tick
  - Complete memory and reflection system

Tier 2: LIGHTWEIGHT LLM AGENTS (30-40%)
  - Occasional posters, moderate engagement
  - Simpler prompts, fewer retrieved memories
  - Activated less frequently

Tier 3: RULE-BASED AGENTS (50-60%)
  - Lurkers, passive consumers
  - Probabilistic engagement (like with P=0.05, comment with P=0.01)
  - No LLM calls -- pure statistical behavior
  - Provide realistic engagement numbers without cost
```

OASIS reports: 1M agents, 27 A100s, 18 hours per time step. This is impractical for a SaaS product. The tiered approach can reduce LLM calls by 80-90% while maintaining realistic emergent behavior.

---

## Summary: Architectural Recommendations for Swaarm

### Core Loop Design (inspired by OASIS + S3)

```
1. Initialize: Generate diverse personas (Persona Hub approach)
2. Build social graph (networkx, interest-based connections)
3. Per time step:
   a. Inject content (the corporate message being tested)
   b. Recommendation system selects what each agent sees
   c. Probabilistically activate agents (time-of-day patterns)
   d. For each active agent (async, concurrent):
      i.   Retrieve relevant memories
      ii.  Build prompt: persona + state + feed + actions
      iii. LLM call -> structured action selection
      iv.  If posting/commenting: second LLM call -> content generation
      v.   Update agent state (emotion, attitude)
      vi.  Store action in memory + environment DB
   e. Update recommendation tables
   f. Advance time step
4. After N steps: Generate analysis report
```

### Memory System (inspired by Stanford Generative Agents)

Simplified for social media simulation:
- **No spatial observation** (agents don't move in physical space)
- **Feed-based observation** (agents see posts in their feed)
- **Importance scoring** still valuable (distinguish viral content from noise)
- **Reflection** simplified to periodic attitude/opinion synthesis
- **No complex planning** needed (social media actions are reactive, not planned)

### Key Technical Decisions

1. **SQLite per simulation** (already in CLAUDE.md) -- matches OASIS approach
2. **Async channel between agents and platform** -- use asyncio queues
3. **Function calling for actions** -- reliable, parseable, matches OASIS ActionType enum
4. **Tiered agent complexity** -- essential for SaaS cost viability
5. **Prompt caching** -- structure prompts with static prefix for 90% input cost reduction
6. **Provider-agnostic LLM layer** (already in CLAUDE.md) -- enables switching for cost/quality
