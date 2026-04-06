# SwarmSight AI - Findings

## From Businessplan Analysis
- SaaS platform, Zurich-based
- Multi-agent simulation via OASIS (camel-oasis)
- 100-500 LLM-powered personas per simulation
- 50-100 rounds of interaction
- Target: PR agencies, corporate comms in DACH
- Pricing: CHF 99-799/month
- Break-even: 38-63 customers at month 18-24
- Mid-market gap between Artificial Societies ($40/mo) and Enterprise ($100k+/yr)

## From Competitor Research
- Direct competitors with real simulation: Simile ($100k+), Aaru ($100k+), Socialtrait (unknown)
- Adjacent (survey-based): Artificial Societies ($40/mo), Expected Parrot, Evidenza, Lakmoos
- No DACH-specific competitor in simulation space
- Social listening tools (Brandwatch, Meltwater, Talkwalker) are complementary, not competing

## OASIS vs. Custom Engine (Recherche 2026-04-03)

### Was OASIS tatsächlich ist
- **SQLite-DB + async Message Router + LLM Function-Calling + optionale Embedding-RecSys**
- ~2'000-3'000 Zeilen Python, ~15 Dateien
- Kernloop: Feed refreshen → LLM fragen → Actions ausführen → wiederholen
- Designed für 1M Agents (overkill für unsere 100-500)
- Gebunden an CAMEL-AI Abstraktionen (Prompt-Kontrolle eingeschränkt)

### Custom Engine: Aufwand & Vorteile
- **Geschätzter Aufwand: 9-15 Tage** (1 erfahrener Entwickler)
- ~1'500 LOC vs. ~15'000 LOC OASIS
- Volle Kontrolle über Prompts, Output-Parsing, Analytics
- Direkter Zugriff auf beliebige LLM-Provider (kein CAMEL-Umweg)
- Einfacheres Debugging, keine Dependency-Risiken
- Perfekt dimensioniert für 100-500 Agents

### Quantitative Vorhersagen — Limitationen
- **"X% werden kaufen" ist NICHT zuverlässig möglich** mit LLM-Agenten
- "Validity Illusion": Output klingt realistisch weil Text fluent ist, aber Verhalten nicht kalibriert
- **Was funktioniert:** Direktionale Insights, Szenario-Vergleiche, Trend-Level-Prognosen
- **Richtige Positionierung:** "Strategie A erzeugt 3x mehr Engagement als B" statt "34.7% reagieren positiv"
- Multiple Runs (5-10) pro Szenario → Ranges statt Point-Estimates
- Passt zu PR-Agenturen: die wollen Strategien vergleichen, keine Aktuarientabellen

## LinkedIn B2B Simulation Opportunity (Recherche 2026-04-03)

### Market Size & LinkedIn Revenue
- **Social listening market:** $9.62B (2025) → $20.51B by 2031, CAGR 13.45%
- **LinkedIn ad revenue:** $8.2B (2025) → $9.7B (2026) → $11.3B (2027), +18% YoY
- LinkedIn exceeds Snapchat ($6B), Pinterest ($4.2B), Reddit ($2.2B)
- **LinkedIn commands 41% of total B2B ad budgets** (up 2% YoY)
- 56.4% of B2B marketers plan to increase LinkedIn budgets >10% in 2026
- LinkedIn Ads delivered 121% ROAS (vs Google 78%, Meta 29%)

### LinkedIn vs Twitter for Simulation
| Dimension | LinkedIn | Twitter/X |
|-----------|----------|-----------|
| Identity | Professional, real names, job titles | Often anonymous/pseudonymous |
| Algorithm | Favors long-form, expertise, dwell time, comment quality | Favors viral/short, retweets |
| Network | Connections (bilateral) | Followers (unilateral) |
| Content | Articles, newsletters, carousels, comments | Short posts, threads |
| Engagement | Substantive comments > reactions | Likes, retweets, quote tweets |
| Audience | Decision-makers, C-suite, B2B buyers | Mass public, journalists, consumers |
| Distribution | 3-stage: quality filter → early engagement → interest graph expansion | Algorithmic timeline + trending |
| Reach trend | Down ~50% in 2026 (precision engine shift) | Volatile, dependent on Musk-era changes |

**Key implication:** LinkedIn simulation requires modeling *professional personas* with job titles, company affiliations, industry expertise, and career motivations — fundamentally different from Twitter's anonymous crowd dynamics. This is harder but more valuable.

### What B2B Companies Spend on LinkedIn Marketing & Consulting
- **LinkedIn marketing agency retainers:** $750-$8,500/month
  - Cleverly: $397-$997/month (outreach + ghostwriting)
  - Sculpt: $3,000-$8,500/month (full service)
  - Addlium: $600-$2,000/month
- **Social media consulting fees:** $50-$200/hour, $2,000-$10,000/month retainers
- **LinkedIn ad costs:** CPC $2-$6, CPM $20-$55, cost per lead $150-$400
- **B2B message testing (Wynter):** $798-$5,000/month ($60k/year enterprise)

### Existing Tools & Competitors
1. **Social Simulator** (socialsimulator.com) — Crisis simulation since 2010
   - Simulates LinkedIn, X, TikTok, Facebook, YouTube, forums
   - Facilitator-operated, real-time script adaptation
   - Library of 1,000+ media brands
   - Custom enterprise pricing (likely $10k-$50k+ per exercise)
   - Manual/human-facilitated, NOT AI-agent driven

2. **Conducttr** (conducttr.com) — Crisis simulation platform
   - Tiered: Raven, Hawk, Osprey, Eagle licenses
   - 1-year minimum subscription, cloud or on-premise
   - Designed for crisis exercises, military/defense
   - NOT focused on marketing/comms pre-testing

3. **Wynter** (wynter.com) — B2B message testing
   - $798-$5,000/month, 8-50 tests/year
   - Uses real humans (70,000+ B2B professionals)
   - Tests website/ad/email copy, NOT social media dynamics
   - Results in 12-48 hours
   - Closest analog for "pre-testing messages" but NOT simulation

4. **No tool exists** that does AI-agent LinkedIn simulation for B2B comms pre-testing

### High-Value LinkedIn Simulation Scenarios (Ranked)

**Tier 1 — Highest Value (crisis/high-stakes, $10k-$50k per simulation):**
1. **CEO/Executive crisis communication** — Layoff announcements, M&A, scandals
   - Fortune 500 CEOs, decision-makers, stakeholders all on LinkedIn
   - Wrong messaging = stock price impact, talent flight, customer churn
   - Currently tested via $20k-$50k crisis simulation exercises (manual)
2. **Layoff announcement reactions** — Employer brand at stake
   - Glassdoor/LinkedIn ripple effect, viral employee posts
   - Companies spend $50k+ on crisis comms consulting for major layoffs
3. **M&A announcement reactions** — Stakeholder confidence
   - Multiple audiences: employees, customers, investors, partners
   - Critical 48-hour window for narrative control

**Tier 2 — High Value (strategic, $5k-$15k per simulation):**
4. **Employer branding campaigns** — Talent acquisition ROI
   - Companies spend $100k-$500k/year on employer branding
   - LinkedIn is #1 platform for employer branding
5. **B2B product launch announcements** — Market reception testing
   - Test messaging before committing to launch strategy
   - Appcues improved signup conversion 73% after message testing
6. **Thought leadership content strategy** — Executive positioning
   - Growing trend: 31.3% of LinkedIn spend now on brand/engagement (up from 17.5%)
   - CEO personal brand directly impacts company valuation

**Tier 3 — Solid Value (recurring, $2k-$5k per simulation):**
7. **ESG/sustainability communication** — Greenwashing risk detection
   - Test whether messaging reads as authentic vs performative
8. **Company culture/values communication** — Internal-external alignment
9. **Industry trend positioning** — Competitive narrative testing

### What Makes LinkedIn Simulation Valuable to Enterprise

**Unique value propositions vs. existing alternatives:**
1. **Pre-testing vs. post-mortem:** Current social listening is reactive ($9.6B market). Simulation is proactive — test BEFORE publishing
2. **Professional persona modeling:** LinkedIn personas have job titles, seniority, industry, company size — enables precise audience targeting in simulation
3. **Multi-stakeholder modeling:** A LinkedIn post reaches employees, customers, investors, competitors, journalists simultaneously — simulation can model each reaction separately
4. **Comment thread dynamics:** LinkedIn algorithm rewards comment quality. Simulation can predict whether a post sparks substantive discussion or controversy
5. **Network propagation:** LinkedIn's 3-stage distribution (quality → early engagement → interest graph) can be modeled to predict viral vs contained reach

**Pricing hypothesis for enterprise:**
- **Per-simulation pricing:** $2,000-$10,000 per simulation (comparable to Wynter test pricing + social listening retainers)
- **Monthly subscription:** $3,000-$15,000/month for recurring simulation access
- **Annual enterprise contract:** $50,000-$150,000/year (comparable to Simile/Aaru but positioned differently)
- **Key insight:** Current Swaarm pricing (CHF 99-799/month) may be too low for LinkedIn-focused B2B simulation. The market can bear 5-10x more if positioned as "pre-crisis testing" rather than "social media simulation"

### Business Opportunity Quantification
- **TAM:** Social listening market ($9.6B) + B2B LinkedIn ad spend (~$3.4B of $8.2B) + crisis comms consulting ($multi-B) = addressable adjacent markets worth $15B+
- **SAM (LinkedIn simulation niche):** If 1% of social listening spend shifts to simulation = $96M
- **Realistic beachhead:** 50-200 enterprise customers at $50k-$150k/year = $2.5M-$30M ARR
- **DACH beachhead:** 20-50 companies at CHF 50k-150k/year = CHF 1M-7.5M ARR
- **Key growth driver:** Budget shift from reactive (listening) to proactive (simulation) as AI makes it feasible

## Deep Research: Highest-Paying Use Cases (2026-04-03)

### MARKET LANDSCAPE & PRICING TIERS

**Enterprise Tier ($100k+/year):**
- Simile AI: $100M Series A (Feb 2026, Index Ventures). Customers: CVS, Telstra, Suntory. Use cases: earnings call rehearsal, litigation modeling, policy testing, product testing
- Aaru: $50M+ Series A (Dec 2025, Redpoint), $1B valuation. Enterprise-only, pricing not published
- Ditto: $50k-75k/year, unlimited studies. Self-serve with Figma/Canva integrations
- Evidenza: Full-service enterprise, 72h turnaround for polished reports

**Mid-Market ($500-5k/month):**
- Gap in market -- no strong player here
- Crisis simulation platforms (Conducttr, PREVENCY) charge per-exercise or annual subscription

**Self-Serve ($40-99/month):**
- Artificial Societies: $40/mo unlimited after free tier. 18M+ responses delivered to F100 via "Radiant" enterprise tier
- Socialtrait: SaaS platform, 70+ behavioral attributes per persona, 1,500+ AI agents per simulation

### TOP 5 HIGHEST-PAYING USE CASES (ranked by willingness-to-pay)

#### 1. CRISIS COMMUNICATION PRE-TESTING & SIMULATION
**Willingness-to-pay: $30k-80k per exercise / $150k-500k annual**
**Why it pays the most:**
- Average PR crisis costs companies 15% stock value loss over a year
- Severe crises: up to 30% market value loss within days (Deloitte 2023)
- VW emissions scandal: $33B in fines, 40% stock drop
- Chipotle E.coli: $8.3M direct losses, 40% stock drop
- Companies responding within hours: only 4% stock decline vs. 14% for weeks delay
- 72% of global enterprises had at least one reputational incident 2022-2024
- Crisis communication market: $6.2B in 2026, growing to $13.7B by 2035 (CAGR 9.12%)
- Current tabletop exercises cost $30k-50k each (40% of companies), 18% spend $50k-80k
- Reputation = 28% of S&P 500 market cap (~$12 trillion)
**Target:** Fortune 500 comms teams, top-tier PR agencies, pharma, financial services
**DACH:** PREVENCY (Vienna) serves this market. MSL Germany strong in crisis. Opportunity for AI-powered simulation at lower cost

#### 2. EARNINGS CALL / IPO / M&A ANNOUNCEMENT REHEARSAL
**Willingness-to-pay: $50k-200k per engagement / $200k-500k annual**
**Why it pays:**
- Simile's marquee use case -- CVS uses it for earnings call prep
- AI can simulate analyst Q&A, predict investor sentiment, reverse-engineer emotional response
- M&A: companies with good stakeholder comms are 30% more likely to meet financial objectives
- 40% of corporate earnings calls now use AI in preparation
- IPO roadshow prep: single engagement worth $100k+ to investment banks
**Target:** Public companies (CFO/IR teams), investment banks, M&A advisory firms
**DACH:** Swiss financial center (UBS, Swiss Re), German DAX companies

#### 3. PHARMA / REGULATED INDUSTRY COMMUNICATIONS
**Willingness-to-pay: $100k-300k annual**
**Why it pays:**
- Drug launches are $100M+ investments; messaging failure is catastrophic
- Regulatory announcement reactions need pre-testing (FDA, EMA decisions)
- Competitive simulation for biosimilar entry, MFN2 pricing, patent cliffs
- Stakeholder audiences hard to reach: KOLs, payers, regulators, patient advocates
- Artificial Societies built "Radiant" specifically for unreachable audiences
**Target:** Top 20 pharma, biotech, medical device, healthcare PR agencies
**DACH:** Basel pharma cluster (Roche, Novartis), German pharma (Bayer, Boehringer)

#### 4. B2B THOUGHT LEADERSHIP / EXECUTIVE POSITIONING (LinkedIn-focused)
**Willingness-to-pay: $2k-10k/month / $25k-120k annual**
**Why it pays:**
- 73% of B2B decision-makers trust thought leadership over product marketing (Edelman-LinkedIn 2025)
- 70% more likely to think positively of orgs with consistent high-quality thought leadership
- LinkedIn = single most effective B2B channel for 40% of B2B marketers
- Thought Leader Ads outperform corporate ads significantly
- CEO positioning is a $50k-200k/year agency engagement
**Target:** B2B SaaS, consulting firms, professional services, PE/VC portfolio companies
**DACH:** Strong B2B/Mittelstand economy, few tools for German-language simulation

#### 5. EMPLOYER BRANDING / RECRUITMENT CAMPAIGN SIMULATION
**Willingness-to-pay: $2k-8k/month / $25k-100k annual**
**Why it pays:**
- War for talent in DACH is acute (engineering, tech, healthcare)
- Employer branding campaigns on LinkedIn = major investment ($50k-500k/year)
- Testing before launch saves 25-60% on wasted ad spend
- Socialtrait case: 25% research cost reduction, 30% engagement increase, 83% faster
**Target:** HR departments of large employers, employer branding agencies
**DACH:** German Mittelstand struggling with employer branding, Swiss talent competition

### INDUSTRY VERTICALS BY SPENDING (ranked)

1. **Financial Services** -- Highest. Earnings calls, M&A, regulatory, IPO. $200k+/year
2. **Pharma / Healthcare** -- Drug launches, regulatory, KOL engagement, crisis. $100k-300k/year
3. **Technology / SaaS** -- Product launches, thought leadership, employer branding. $50k-150k/year
4. **FMCG / Consumer** -- Brand campaigns, product launches, pricing, crisis. $50k-100k/year
5. **Professional Services** -- Thought leadership, employer branding, M&A advisory. $25k-100k/year

### WHAT PR AGENCIES IN DACH WOULD PAY FOR

**Biggest pain points simulation solves:**
1. Pre-testing crisis messaging before real crisis hits (agencies charge clients $20k-50k for crisis prep)
2. Proving campaign strategy to clients before launch ("show don't tell")
3. Speed of insight delivery (focus groups 4-6 weeks vs simulation hours)
4. Access to hard-to-reach audiences (C-suite, policymakers, medical professionals)
5. Multilingual/multicultural testing (DACH = DE/FR/IT in Switzerland)

**Pricing sweet spot for DACH PR agencies:**
- Small agencies (5-20 people): CHF 99-299/month
- Mid-size agencies (20-100): CHF 499-999/month
- Large agencies (100+): CHF 2k-5k/month or per-project ($5k-15k per simulation)
- Enterprise direct: CHF 5k-20k/month

### COMPETITOR CASE STUDIES (what customers actually use it for)

**Simile AI:** CVS (inventory decisions, earnings call prep), Telstra (customer behavior), Suntory (brand strategy). Also: litigation modeling, policy testing

**Artificial Societies:** Fortune 100 (unnamed), 18M+ responses, $100M+ decisions influenced. Use: global expansion, product positioning, advertising, strategic comms. Radiant: policymaker + C-suite simulation

**Socialtrait:** Streaming platform (25% cost reduction, 30% engagement up, 83% faster). European tech conference (ad optimization). Use: creative testing (200 assets/min), focus groups, pricing, heatmaps, competitor analysis

### CRISIS COST vs. SIMULATION COST (Value Proposition)

| Crisis Impact | Cost | Simulation Cost | ROI Multiple |
|---|---|---|---|
| Minor brand incident | $100k-$1M | $5k-15k simulation | 7-67x |
| Moderate crisis (product recall) | $1M-$50M | $30k-80k crisis sim | 33-625x |
| Major crisis (VW-level) | $1B-$33B | $150k-500k annual | 6,600-66,000x |
| Stock price: hours vs weeks response | 4% vs 14% decline | Simulation enables faster response | N/A |
| Average enterprise incident | 15% stock value | $50k-200k annual | Potentially 1,000x+ |

### KEY STRATEGIC INSIGHT

The market is bifurcated: Enterprise ($100k+) vs Self-serve ($40/mo). The $500-5,000/month mid-market gap is where SwarmSight should play.

**Recommended positioning shift:** Instead of "social media simulation" (sounds like a toy), position as:
- "Strategic Communications Pre-Testing Platform" (for PR agencies)
- "Stakeholder Reaction Intelligence" (for corporate comms)
- "Crisis-Ready Communications" (for crisis use case)

This reframing alone could support 5-10x higher pricing than "social media simulation."

## LinkedIn Simulation: Technical Implementation Research (2026-04-03)

### 1. WHY NOBODY HAS BUILT AI-AGENT LINKEDIN SIMULATION YET

**It's NOT primarily a technical barrier -- it's a combination of legal, data access, and market timing:**

**API Restrictions:**
- LinkedIn's API is extremely locked down. You must be an official LinkedIn Partner to access most features
- API is designed for OAuth integrations where users consent to share their OWN data only
- You CANNOT look up other people's profiles, search for companies, or access the rich data via API
- Rate limits per endpoint, 429 errors on overuse
- Monthly API version releases with strict compliance requirements
- Data Storage Requirements enforced -- non-compliance = loss of access

**Legal Landscape (hiQ v. LinkedIn saga):**
- hiQ v. LinkedIn went through district court, Ninth Circuit, Supreme Court, and back -- ended in settlement
- hiQ paid damages and agreed to destroy ALL scraped data
- hiQ had used fake accounts and contractors to bypass login requirements -- found in breach of User Agreement
- 2024 Meta v. Bright Data ruling: scraping PUBLIC data (no login required) remains legal
- Key principle: scraping behind login walls or violating contractual ToS = legally risky
- Creating fake profiles to access data = definitively illegal

**Why this DOESN'T block us:**
- We DON'T need real LinkedIn data at all
- We're simulating a "LinkedIn-like professional network" with synthetic personas
- No scraping, no API abuse, no real profiles
- Our approach (LLM-generated personas from demographic data) sidesteps the entire legal/API problem

**Market timing reasons nobody built it yet:**
- LLM role-playing quality only became good enough in 2024-2025 (GPT-4o-mini level)
- S3 (Social-network Simulation System) paper was July 2023 -- still Twitter-focused
- GA-S3 extension for group dynamics only published 2025
- Stanford generative agents paper (April 2023) proved feasibility but focused on village simulation
- Professional persona simulation is harder than anonymous Twitter personas (more attributes to model)
- The enterprise buyers (PR agencies, corporate comms) are just now discovering AI simulation exists

### 2. CREATING REALISTIC LINKEDIN PERSONAS WITHOUT REAL DATA

**The answer is YES -- prompt engineering alone is sufficient. No fine-tuning needed.**

**Research evidence:**
- Tencent's Persona Hub: 1 billion diverse personas auto-curated from web data, acting as "distributed carriers of world knowledge"
- DeepPersona: generates personas with hundreds of structured attributes and ~1MB of narrative text per persona
- Stanford research: LLM agent interviews replicated real individuals' survey responses at 85% accuracy vs humans' own 2-week retest accuracy
- CoSER 70B matches/surpasses GPT-4o on role-playing benchmarks (75.8% InCharacter, 93.5% LifeC)
- GPT-4 demonstrated MBTI-differentiated planning behavior from persona prompts alone -- no fine-tuning

**Persona generation approach for LinkedIn simulation:**

```
Input: Demographic seed data
  - Job title, seniority level, industry, company size
  - Age range, gender, education level, location
  - Years of experience, career trajectory
  - Professional interests, content preferences

Output: Full LinkedIn persona
  - Professional background & expertise areas
  - Communication style (formal/casual, emoji use, post length preference)
  - Content engagement patterns (what they react to, comment on, share)
  - Network behavior (connection strategy, lurker vs active poster)
  - Professional motivations (career advancement, thought leadership, hiring, selling)
  - Reaction tendencies (which of the 6 reaction types they favor)
```

**Public data sources for demographic calibration:**

1. **Swiss BFS (Federal Statistical Office)**
   - PXWeb API for structured datasets (workforce, employment, education)
   - opendata.swiss portal with anonymized datasets
   - R package `BFS` for programmatic access
   - Covers: employment by sector, education levels, income brackets, company sizes

2. **Destatis (German Federal Statistical Office)**
   - Similar API access for German workforce demographics
   - Unternehmensregister (company register) for industry distribution

3. **LinkedIn's OWN published reports**
   - Workforce Report (quarterly, by country)
   - Economic Graph Research (publicly available)
   - Industry hiring trends, skill demand data
   - These are PUBLISHED for public use -- no scraping needed

4. **Eurostat / OECD**
   - Cross-country professional demographics
   - Education attainment, employment by sector

5. **Industry-specific sources**
   - Swiss Re sigma reports (insurance industry)
   - PwC/McKinsey workforce surveys
   - Glassdoor published salary/role data

**Key insight:** We don't need individual LinkedIn profiles. We need STATISTICAL DISTRIBUTIONS of professional demographics to generate realistic populations. BFS + LinkedIn Workforce Reports give us exactly this.

### 3. LINKEDIN ALGORITHM & CONTENT DYNAMICS (vs Twitter)

**LinkedIn's 360Brew Algorithm (2025-2026):**
- Replaced entire legacy ranking infrastructure with single LLM-powered system called "360Brew"
- Understands context, expertise, and relevance semantically (not just engagement metrics)
- Three ranking signals: Relevance, Expertise, Engagement
- Dwell time = strongest signal (how long someone pauses on content)

**Three-stage distribution model:**
1. **Quality filtering** -- AI checks for spam, engagement bait, policy violations
2. **Small-audience test** -- Show to 2-5% of your network
3. **Broader distribution** -- Based on early engagement, expand via interest graph

**Critical difference from Twitter:**
| Dimension | LinkedIn | Twitter/X |
|---|---|---|
| Virality design | Deliberately PREVENTS virality | Designed FOR virality |
| Content lifespan | 24-48 hour engagement window | 15-45 minute peak |
| Link penalty | External links = -60% reach | Less severe link penalty |
| Comment weight | Comments = 15x value of reactions | Retweets drive distribution |
| Format winners | Carousels (7%+ engagement), Polls (4.4%), Multi-image (6.6%) | Short text, threads |
| Downranked | Engagement bait, generic templates, automation, recycled content | Less aggressive filtering |
| Avg engagement | 5.20% (up 8% YoY in 2026) | ~1-3% typical |
| Recovery | Only 5% of posts that flop in first hour recover | Algorithmic second chances via Explore |

**Content format performance for simulation modeling:**
- Carousels/PDFs: 7.00% avg engagement, +14% YoY, 3.4x reach vs single image
- Multi-image: 6.60% engagement
- Polls: 4.40%, 1.64x reach multiplier
- Text-only: ~4%, viable if sharp/personal
- Video: growing but underperforms carousels on company pages
- Optimal carousel length: 7 slides (18% better than other lengths)
- Format rotation > single format (40%+ follower growth boost)

**Reaction types (6 total, "Curious" removed 2023):**
1. Like -- general approval, lowest effort
2. Celebrate -- milestones, achievements, promotions
3. Love -- heartwarming, emotional resonance
4. Insightful -- great point, new idea, helpful advice
5. Funny -- humor in professional context
6. Support -- solidarity with a cause

Algorithm treats all 6 reactions equally. Comments carry 15x more algorithmic weight than any reaction.

### 4. FINE-TUNING vs PROMPT ENGINEERING

**Verdict: Prompt engineering is sufficient. Fine-tuning is unnecessary and potentially counterproductive.**

**Evidence:**
- GPT-4o-mini can already role-play as specific professional personas convincingly
- Research shows persona prompting (demographic description at prompt head) effectively conditions LLM output
- Stanford showed 85% accuracy in replicating real individuals from interview transcripts alone
- CoSER achieves GPT-4o-level role-playing WITHOUT fine-tuning, just better prompting
- S3 system uses "prompt engineering and prompt tuning" to achieve human-like social network behavior

**Why NOT to fine-tune:**
- Fine-tuning on real LinkedIn posts would require scraping (legal risk)
- Fine-tuning locks you to one model (can't switch providers easily)
- Fine-tuning is expensive ($2k-$10k+ per model version)
- Prompt engineering gives you per-persona customization without model changes
- GPT-4o-mini at $0.15/1M input tokens makes prompt-heavy approaches economically viable

**Prompt engineering strategy for professional personas:**

```
System prompt structure:
1. IDENTITY: Job title, company type, industry, seniority, location
2. PERSONALITY: MBTI-like traits, communication style, risk tolerance
3. PROFESSIONAL CONTEXT: Current challenges, goals, industry trends
4. LINKEDIN BEHAVIOR: Posting frequency, content preferences, engagement style
5. REACTION RULES: What triggers each reaction type, comment threshold
6. CONSTRAINTS: Time budget, attention span, topic relevance filter
```

**What we CAN calibrate without real data:**
- Post length distributions (public research shows LinkedIn optimal = 1,300-2,000 characters)
- Posting frequency by seniority (C-suite: 1-2x/week, Manager: 2-3x/week, IC: sporadic)
- Engagement patterns by industry (tech = higher engagement, finance = more reserved)
- Content topic preferences by role (HR = employer branding, Sales = outreach, Eng = technical)

### 5. LINKEDIN SIMULATION ACTION SPACE

**Agent actions (expanded from Twitter's 6 to LinkedIn's richer interaction model):**

```python
class LinkedInAction(Enum):
    # Content creation
    CREATE_POST = "create_post"          # Text, image, poll, carousel
    CREATE_ARTICLE = "create_article"    # Long-form (1500+ words)
    CREATE_NEWSLETTER = "create_newsletter"  # Recurring publication

    # Engagement
    REACT = "react"                      # 6 types: like, celebrate, love, insightful, funny, support
    COMMENT = "comment"                  # Text comment (15x algorithmic weight vs reaction)
    REPLY_TO_COMMENT = "reply_comment"   # Thread depth
    SHARE = "share"                      # Repost with/without commentary

    # Network
    CONNECT = "connect"                  # Send connection request (with optional note)
    FOLLOW = "follow"                    # One-directional follow
    ENDORSE = "endorse"                  # Skill endorsement
    RECOMMEND = "recommend"              # Write recommendation

    # Passive
    VIEW = "view"                        # View post (dwell time signal)
    SCROLL_PAST = "scroll_past"          # Ignore (implicit negative signal)
    SAVE = "save"                        # Bookmark for later

    # Meta
    DO_NOTHING = "do_nothing"            # Skip turn (important: most users are lurkers)
```

**Feed algorithm simulation (simplified 360Brew model):**

```python
def calculate_feed_score(post, viewer):
    # Three-pillar scoring (mirrors LinkedIn's actual approach)
    relevance = compute_relevance(post.topic, viewer.interests, viewer.industry)
    expertise = compute_expertise(post.author.credentials, post.topic)
    engagement = compute_engagement(post.reactions, post.comments, post.dwell_times)

    # Connection strength modifier
    connection_strength = get_connection_strength(post.author, viewer)
    # 1.0 = direct connection, 0.5 = 2nd degree, 0.1 = followed creator

    # Content type modifier
    format_bonus = {
        "carousel": 1.4,    # Based on 7% engagement rate
        "multi_image": 1.3,  # 6.6%
        "poll": 1.1,         # 4.4%
        "text": 1.0,         # ~4% baseline
        "video": 1.05,       # Growing but variable
        "external_link": 0.4  # -60% reach penalty
    }

    # Dwell time signal
    dwell_score = min(post.avg_dwell_time / 30.0, 2.0)  # 30s = baseline

    # Comment quality bonus
    comment_quality = sum(c.depth * c.length_score for c in post.comments) / max(len(post.comments), 1)

    score = (relevance * 0.35 + expertise * 0.30 + engagement * 0.25 + dwell_score * 0.10)
    score *= connection_strength
    score *= format_bonus.get(post.format, 1.0)
    score *= (1 + comment_quality * 0.15)

    # Freshness decay (24-48h window)
    hours_old = (now() - post.created_at).hours
    freshness = max(0, 1 - (hours_old / 48))
    score *= (0.5 + 0.5 * freshness)

    return score

def simulate_distribution(post):
    """Three-stage LinkedIn distribution model"""
    # Stage 1: Quality filter
    if is_spam(post) or is_engagement_bait(post):
        return DistributionResult(reach=0, reason="filtered")

    # Stage 2: Small audience test (2-5% of network)
    test_audience = sample(post.author.connections, fraction=0.03)
    early_engagement = simulate_engagement(post, test_audience)

    # Stage 3: Broader distribution based on early signal
    if early_engagement.rate > VIRAL_THRESHOLD:
        # Expand to 2nd degree + interest graph
        expanded = get_interest_graph_audience(post, early_engagement)
        return simulate_engagement(post, expanded)
    elif early_engagement.rate > BASELINE_THRESHOLD:
        # Moderate expansion within network
        expanded = sample(post.author.connections, fraction=0.15)
        return simulate_engagement(post, expanded)
    else:
        # Post dies at stage 2 (95% of underperformers)
        return early_engagement
```

**Key modeling decisions:**
- Lurker ratio: ~90% of LinkedIn users never post, ~1% create content regularly
- Comment-to-reaction ratio: typically 1:10 to 1:20
- Connection acceptance rate: varies by seniority (C-suite: 20-30%, mid-level: 50-70%)
- Posting time sensitivity: business hours in viewer's timezone weighted
- Multi-stakeholder modeling: same post seen differently by employees vs investors vs journalists

### 6. LEGAL: SIMULATING A "LINKEDIN-LIKE" PLATFORM

**Trademark analysis:**

**What we CAN do (nominative/descriptive fair use):**
- Describe our product as "simulating professional network dynamics similar to LinkedIn"
- Use LinkedIn's name in marketing to explain what we simulate (nominative fair use)
- Create a simulation environment that looks/functions differently but models similar dynamics
- Call it a "professional network simulation" without using LinkedIn branding

**What we should NOT do:**
- Use LinkedIn's logo, "in" mark, or trade dress
- Call our simulated platform "LinkedIn" in the simulation UI
- Create a visual clone that could be confused with LinkedIn
- Claim LinkedIn endorsement or partnership

**Safe naming approaches for the simulated platform:**
- "ProNet" / "BizConnect" / "CareerHub" (generic professional network)
- Or simply call it "the professional network" in simulation context
- The simulation report can reference "LinkedIn-like dynamics" in the methodology section

**Nominative fair use three-part test (established law):**
1. The product is not readily identifiable without using the mark -- we can say "LinkedIn-style" in marketing
2. Only so much of the mark as reasonably necessary -- use name, not logo
3. No suggestion of sponsorship/endorsement -- clear disclaimer

**Strongest legal position:**
- We simulate a GENERIC professional network informed by publicly available research about LinkedIn's algorithm
- We use PUBLIC workforce statistics (BFS, Destatis, LinkedIn's own published reports) for demographics
- We NEVER scrape, access, or store any LinkedIn user data
- Our simulation engine is original software, not a LinkedIn clone

### 7. EXISTING ACADEMIC/RESEARCH SYSTEMS TO LEARN FROM

**S3 (Social-network Simulation System) -- Fudan University, 2023:**
- LLM-powered agents simulating social network behavior
- Prompt engineering + prompt tuning approach
- Demonstrated emergent phenomena: information propagation, attitude shifts, emotional contagion
- Limitation: focused on Twitter-like dynamics, not professional networks

**GA-S3 (Group Agents extension) -- 2025:**
- Added group-level dynamics and societal heterogeneity
- Dynamic modeling of evolving social structures
- Automated agent generation from environmental perception
- More scalable than original S3

**Stanford Generative Agents (Park et al., 2023):**
- 25 agents in a simulated town ("Smallville")
- Memory, reflection, and planning architecture
- Proved LLMs can maintain consistent persona behavior over extended interactions
- Architecture: observation -> reflection -> planning -> action loop

**Social media conversation simulation (EPJ Data Science, 2025):**
- Macro structure via Agent-Based Modeling (ABM)
- Defines who interacts with whom, interaction type, and stance
- Separates structural dynamics from content generation

**What we should borrow:**
- From S3: prompt engineering approach for persona conditioning
- From Stanford: memory/reflection architecture for multi-round consistency
- From GA-S3: group dynamics modeling for department/industry clusters
- From conversation simulation: separate structural model from content generation

### 8. PRACTICAL FEASIBILITY ASSESSMENT

**What we need to build (custom engine, NOT OASIS):**

| Component | Effort | Complexity |
|---|---|---|
| Persona generator (demographic -> full profile) | 2-3 days | Medium |
| LinkedIn action space (15 actions vs Twitter's 6) | 2-3 days | Medium |
| Feed algorithm simulation (3-stage model) | 3-4 days | High |
| Content generation (posts, comments, articles) | 2-3 days | Medium |
| Network graph (connections, follows, 2nd degree) | 1-2 days | Low |
| Engagement simulation (reactions, dwell time) | 2-3 days | Medium |
| Multi-round orchestration | 1-2 days | Low (already solved in MVP) |
| Report generation (LinkedIn-specific metrics) | 2-3 days | Medium |
| **Total** | **15-23 days** | -- |

**Cost estimate per simulation (GPT-4o-mini):**
- 200 agents x 50 rounds = 10,000 LLM calls
- LinkedIn requires richer prompts (~800 tokens input vs ~400 for Twitter)
- Estimated: ~$3-5 per simulation (vs $1.95 for Twitter)
- Still well within viable unit economics even at CHF 99/month

**What we DON'T need:**
- Real LinkedIn data (synthetic personas from demographics)
- Fine-tuned models (prompt engineering sufficient)
- LinkedIn API access (we simulate, not integrate)
- Perfect algorithm replication (directional accuracy is enough)
- Training data from LinkedIn posts (public research about content patterns suffices)

**Biggest technical risks:**
1. Persona consistency over 50+ rounds (mitigation: memory/reflection from Stanford approach)
2. Realistic comment thread dynamics (mitigation: structured conversation modeling)
3. Professional tone calibration across industries (mitigation: industry-specific prompt templates)
4. Computational cost scaling (mitigation: GPT-4o-mini is cheap, async processing)

## From Working Notes
- OASIS integration: `camel-oasis==0.2.5` + `camel-ai==0.2.78`
- Twitter Actions: CREATE_POST, LIKE_POST, REPOST, FOLLOW, DO_NOTHING, QUOTE_POST
- Cost per simulation: ~$1.95 (GPT-4o-mini, 200 agents x 50 rounds)
- MiroFish pipeline: 5 stages (Ontology, Graph, Profiles, Simulation, Report)
- Previous stack was Vue 3 + Vite + Python backend

---

## SOCIALTRAIT DEEP RESEARCH (2026-04-03)

### Company Overview

- **Full Name**: Socialtrait Inc
- **Founded**: ~2022 (Berkeley SkyDeck 2022 cohort, named one of 20 most innovative startups)
- **HQ**: San Francisco Bay Area
- **Co-founders**: Vivek Kumar (CEO, 15+ years business strategy/AI), Suraj Narayanan Sasikumar, Gopakumar Balakrishnan
- **Positioning**: "The World's First Behavioral Simulation Engine Powered by Synthetic Audiences"
- **Target Market**: Marketing teams from midsized to enterprise; Fortune 500 clients across CPG, FMCG, retail, and media
- **Patent**: US12412128B1 -- "Methods for generating synthetic data using computer-simulated personas and machine learning-based persona selection"
- **Product**: "Cliques" SaaS platform at cliques.socialtrait.com
- **Pricing**: Credit-based self-serve SaaS (exact prices not public)

### Technical Architecture (from Patent US12412128B1)

**System Design:**
API-based application on distributed cloud infrastructure with two main subsystems:
1. **Virtual Persona Community Generation Subsystem** -- creates/manages synthetic personas
2. **Automated Discourse Subsystem** -- manages interactions between users and virtual agents

**Persona Generation:**
- Iterative batch generation: system generates batches of n personas, automatically adjusts subsequent iterations to match target demographic/psychographic distributions
- Each persona stored as a **"persona artifact"** -- data structure containing persona variables, vector embeddings, and characteristics
- Attributes include: demographics, psychographic traits (Big Five aligned), behavioral tendencies, communication patterns, knowledge domains, AI-generated visual representations

**Simulation Flow:**
1. Input Processing: user queries via API endpoints
2. Embedding Generation: GPU-accelerated model converts discourse to vectors
3. Candidate Identification: k-NN filtering retrieves relevant personas from vector database
4. Activation Scoring: "discourse activation values" indicating persona interest levels
5. Response Generation: selected personas generate via transformer-based LLMs
6. History Management: discourse history subsystem records all exchanges

**Willingness Scoring (key innovation):**
- Persona Willingness Score: intrinsic engagement tendency (0-1 scale)
- Conversation Willingness Score: context-dependent participation likelihood
- Unified Willingness Score: `s_unified = s_persona_willingness * e^(-lambda * (s_conversation_willingness - s_persona_willingness))`
- This determines WHICH agents speak in a given round -- not all agents respond equally

**ML Methods:**
- Supervised: logistic regression, neural networks, random forests, decision trees
- Unsupervised: k-means clustering, Apriori algorithms
- Reinforcement: Q-learning and temporal difference learning for persona behavior optimization
- Transformer models fine-tuned to persona attributes
- KV caching for common persona-query responses (cost optimization)
- SGLang framework for batch processing (upgraded from vLLM)
- ANN indexing for efficient persona retrieval

### The "70+ Behavioral/Psychographic Attributes"

Marketing materials cite both "70+" and "50+" attributes (likely grew over time or varies by product). Based on patent + marketing, attributes include:

- **Demographic**: Age, gender, income, occupation, education, location, household
- **Psychographic (Big Five)**: Openness, conscientiousness, extraversion, agreeableness, neuroticism
- **Behavioral**: Price sensitivity, brand loyalty, sustainability prefs, lifestyle fit, media consumption, tech adoption, purchase frequency, channel preferences
- **Communication**: Style, verbosity, formality, emoji usage, response length
- **Decision-Making**: Risk tolerance, info-seeking behavior, social proof sensitivity, impulse vs deliberation
- **Values**: Health consciousness, environmental awareness, status orientation, value-for-money

All encoded as vector embeddings for similarity matching in persona selection.

### Multi-Round Simulation: YES, Confirmed

This IS genuine multi-round simulation, not single-pass:
- **Agent World Protocol**: persistent identity across rounds -- personas remember prior interactions, maintain consistent beliefs
- **Discourse history subsystem**: records all exchanges, feeds back into subsequent interactions
- **Context-aware truncation**: when history exceeds token limits (confirms long multi-turn conversations)
- **Social Media Multiverse**: explicitly models narrative evolution "over time"
- Emergent phenomena reproduced: influence concentration, information jumping between communities

### Product Suite ("Cliques" Platform)

| Product | Description |
|---------|-------------|
| Custom Target Audience Builder | Psychographic persona construction |
| Automated Focus Group Intelligence | AI-led chat discussions generating infographic reports |
| Creative Shortlisting Engine | Ranks up to 200 visual assets against engagement criteria |
| Visual Attention Heatmaps | ML on millions of eye-tracking data; gaze sequence + attention hotspots by segment |
| High-Scale Survey Simulator | Quantitative + qualitative at scale |
| Social Media Multiverse | Content engagement, opinion evolution, viral spread simulation |

**Heatmap Output Metrics:**
- Attention Distribution: proportion of attention per section
- Gaze Sequence: predicted scan order
- Segment-Specific Data: by age, psychographics, region

### Crisis Simulation

Listed as key use case ("PR crisis simulation"). Claims "95%+ accuracy on crisis benchmarks." Uses Social Media Multiverse to:
- Model how negative narratives spread through populations
- Simulate counter-messaging strategies
- Test crisis comms across segments before deployment
- Show how influence concentrates during crisis events
- NOT a dedicated crisis product -- application of general simulation engine

### Accuracy Claims

| Claim | Context |
|-------|---------|
| 86% validated accuracy | Across industries and geographies (general claim) |
| 95%+ accuracy | Specifically on brand crisis benchmarks |
| 50% improvement | Creative performance using platform recommendations |
| 80% cost reduction | vs traditional research methods |

**Validation:** "Representativeness framework" comparing outputs to actual market outcomes. Validated across FMCG, retail, consumer electronics. Two years enterprise deployment with Fortune 100 companies. **BUT: specific methodology for 86% figure is NOT publicly documented.**

### Case Studies

| Client/Type | Result |
|-------------|--------|
| Insurance company | 50% engagement boost + 80% cost reduction |
| Streaming platform | 40% more engagement |
| ICICI PruLife | 50% higher engagement from AI-recommended captions vs agency suggestions |

### Known Limitations (Industry-Wide for Synthetic Audiences)

- Synthetic personas tend to be MORE POSITIVE than real humans (sycophancy bias)
- Responses converge toward safe, generic territory when under-constrained
- Cannot capture present-moment experiences or very recent cultural shifts
- Underlying models skew toward younger, educated, liberal demographics (training data bias)
- Cannot fully replicate complex emotions, cultural nuance, or spontaneous behavior
- "Garbage in, garbage out" applies to underlying data quality

### What We Should Learn From Socialtrait

**Architecture Ideas to Adopt:**
1. **Willingness Scoring**: Their unified score determines which agents speak per round -- avoids unrealistic "everyone responds" behavior. Critical for our engine.
2. **Agent World Protocol (Persistent Memory)**: Personas maintaining beliefs/memory across rounds. Essential for multi-round realism.
3. **k-NN Persona Selection**: Vector embeddings to select relevant personas per topic instead of activating all. Efficient and realistic.
4. **Iterative Distribution Matching**: Generating persona batches to match target demographics. Smart for representative panels.
5. **KV Caching**: Caching common persona-query patterns to reduce redundant LLM calls. Important for cost control.

**Product Features Worth Adopting:**
1. Visual Attention Heatmaps (highly tangible output)
2. Creative Asset Ranking (up to 200 images simultaneously)
3. Social Network Spread Modeling (emergent network effects)
4. Crisis Simulation Mode (specific workflows)
5. Credit-based self-serve SaaS model

**Positioning Lessons:**
- Lead with "simulation" not "research" -- predictive infrastructure, not research tool
- Emphasize "what customers will do" not "what they said"
- The 86% accuracy claim is central to credibility (even if methodology unclear)
- Speed (hours not weeks) marketed as aggressively as accuracy

### What We Should Do DIFFERENTLY or BETTER

**Their Weaknesses We Can Exploit:**

1. **Black-Box Accuracy**: 86% figure lacks published methodology. We differentiate with TRANSPARENT validation -- publish methodology, show confidence intervals, let users compare predictions to outcomes.

2. **Marketing-Only Focus**: Socialtrait is 100% marketing/advertising. We expand to policy simulation, organizational behavior, crisis comms (LinkedIn/professional context), social science -- markets they ignore.

3. **No Open Architecture**: Patented closed system. We offer extensible agent architecture -- researchers customize behaviors, plug in models, modify parameters.

4. **Limited Social Dynamics**: Social Media Multiverse models information diffusion. We model DEEPER dynamics: coalition formation, norm emergence, opinion polarization, trust network evolution.

5. **Sycophancy Problem**: Industry-wide positive bias. We build adversarial persona design and devil's advocate agents into every simulation.

6. **No Explainability**: Users can't see WHY a persona responded a certain way. We offer explainable simulation -- reasoning chains, attribute-driven responses, confidence levels.

7. **Training Data Bias**: Models reflect internet-era biases. We invest in diverse ground-truth calibration from underrepresented populations.

8. **Single-Platform Lock-in**: Credit-based SaaS, no external API. We offer API-first architecture for integration into existing workflows.

**Technical Improvements Over Their Approach:**
1. Real social graph modeling with network topology (degree distributions, clustering, weak ties)
2. Temporal dynamics with decay, reinforcement, and forgetting (not just persistent memory)
3. Multi-model agent architecture (sophisticated models for opinion leaders, faster for crowd)
4. Systematic calibration framework comparing outputs to real-world outcomes
5. Adversarial testing with contrarian agents and black swan scenarios

### Competitive Position Summary

| Dimension | Socialtrait | Our Opportunity |
|-----------|-------------|-----------------|
| Maturity | 2+ years, US patent, Fortune 500 | Learn from their playbook, move fast |
| Tech | Patented persona gen + willingness scoring + vector retrieval | Build on open research for deeper social dynamics |
| Accuracy | 86% claimed (methodology unclear) | Transparent, published validation |
| Use Cases | Marketing/advertising only | Policy, social science, crisis, organizational |
| Output | Heatmaps, ranked lists, infographics, dashboards | Add network viz, opinion timelines, explainable reasoning |
| Pricing | Credit-based self-serve SaaS | API-first + self-serve hybrid |
| Scale | Claims 1M+ agents, 200K+ parameters | Match with cloud-native architecture |
| Differentiator | First mover, patent, enterprise trust | Deeper simulation, transparency, broader applications |
| Geography | US-focused, global enterprise | DACH-first, German-language capability |
| Platform | General social media / consumer | Professional network / LinkedIn focus |

### Key Sources
- Socialtrait website: https://www.socialtrait.com/
- Patent US12412128B1 (Google Patents)
- PR Newswire: Social Media Multiverse launch (Apr 2026)
- Benzinga: Predictive Audience Simulation Platform (Apr 2026)
- AI Journal: SaaS platform launch (Oct 2025)
- Socialtrait blog: AI trends, heatmaps methodology

## Willingness Scoring / Agent Activation Research (2026-04-05)

### 1. Socialtrait's Approach (US Patent 12412128B1)

**Unified Willingness Score Formula:**
```
s_unified = s_persona_willingness * e^(-lambda * (s_conversation_willingness - s_persona_willingness))
```

**Components:**
- `s_persona_willingness` (0-1): Intrinsic engagement tendency. Represents the degree of willingness of the virtual persona to participate in any conversation at any point in time, regardless of conversation details. Derived from personality traits like introversion/extraversion and openness.
- `s_conversation_willingness` (0-1): Context-dependent participation likelihood. Represents how the current conversation influences the willingness of the candidate agent to respond. Adjusts dynamically using reinforcement learning models.
- `lambda`: Exponential smoothing parameter modulating the influence of conversational context on the persona's base willingness.
- `e`: Euler's number (mathematical constant ~2.718)

**How lambda works:**
- When `s_conversation > s_persona`: the exponential term `e^(-lambda * positive_value)` < 1, so `s_unified < s_persona`. The conversation context dampens inherent willingness (e.g., boring conversation for an otherwise chatty person).
- When `s_conversation < s_persona`: the exponential term `e^(-lambda * negative_value)` > 1, so `s_unified > s_persona`. The conversation context amplifies willingness beyond base level (e.g., controversial topic activating a normally quiet person).
- When `s_conversation == s_persona`: `s_unified = s_persona` (no contextual adjustment).
- Higher lambda = stronger contextual influence; lower lambda = persona dominates.

**Selection mechanism:**
- Agents with unified scores exceeding a predefined threshold qualify as "willing candidate agents"
- System selects top m responders (m randomly sampled from a distribution, typically mean=3)
- Uses structured generation with normalized log probabilities to rank candidates by confidence

**Takeaway for Swaarm:** This is an elegant, computationally cheap formula. The exponential coupling between persona and context is smart -- it preserves persona dominance while allowing contextual modulation. We should adopt a similar two-factor approach.

---

### 2. Real-World Social Media Activity Distributions

**The 90-9-1 Rule (Participation Inequality):**
- 90% lurkers (consume content only)
- 9% contributors (occasionally engage: like, comment, share)
- 1% creators (produce most original content)
- Source: Nielsen Norman Group, validated across many platforms
- Modern data suggests it may be closer to 70-20-10 on some platforms (up to 23% creating content)
- In health communities: Superusers generate 59-75% of posts, Contributors 24-37%, Lurkers 1-8%

**Twitter/X Posting Frequency:**
- Median user: ~2.16 tweets per week (2024 data, down from 5.04 in 2021)
- 10% of users generate 92% of all tweets (extreme power law)
- Most highly active users: ~157 tweets/month (~5.2/day)
- Average user posts approximately once per month
- Distribution follows a power law with lognormal cutoff
- Inter-tweet intervals: power law with exponential cutoff
- Retweet frequency: power law with exponent 0.6-0.7

**LinkedIn Posting Frequency:**
- Recommended sweet spot: 2-5 posts per week
- Average brand: 5-7 image posts + 2-4 video posts per month
- Most professionals: significantly less than daily
- Moving from 1 to 2-5 posts/week yields ~1,182 more impressions per post
- Much lower volume than Twitter overall

**Implications for simulation at 50k agents:**
- Per round (simulating ~1 hour of real time):
  - ~500 agents (1%) should be "creators" who might post
  - Of those, maybe 10-20% actually post in a given hour = 50-100 posts per round
  - ~4,500 agents (9%) are "contributors" who might react (like/comment/share)
  - Of those, maybe 5-15% engage per round = 225-675 reactions
  - ~45,000 agents (90%) are lurkers who read but don't act
- Total active agents per round: ~300-800 (0.6-1.6% of population)

---

### 3. Factors Determining Agent Activation

**A. Personality (Big Five Model):**
- Extraversion: strongest predictor of posting frequency. High-E agents post more, comment more, share more.
- Openness: correlated with more diverse content engagement and information sharing.
- Neuroticism: positively associated with social media use but more passive/reactive (emotional posting).
- Agreeableness: negative relationship with information sharing (less likely to post controversial takes).
- Conscientiousness: negative relationship with frequency (more deliberate, less impulsive posting).
- Research confirms introverts cluster in "very rarely post" and "rarely post" categories.

**B. Topic Relevance:**
- Match between post content and agent's interests/expertise.
- Domain experts are more likely to engage on their topic.
- Irrelevant content = low activation, even for extroverts.

**C. Network Effects (Social Influence):**
- Did someone the agent follows post? (Direct feed exposure)
- Granovetter's Threshold Model: each agent has a threshold = proportion of network neighbors who must act before they will act.
- Cascade dynamics: early adopters activate, which pushes borderline agents over their threshold.
- Network position matters: high-centrality agents see more content, get activated more.

**D. Emotional Engagement (Controversy/Virality):**
- Controversial or emotionally charged content increases activation probability.
- Negative sentiment drives more engagement than positive (outrage effect).
- Moral-emotional language in content amplifies sharing by 20% per moral-emotional word (Brady et al., 2017).

**E. Fatigue/Cooldown:**
- Agents should not post every round -- implement exponential decay cooldown.
- Recent activity should reduce activation probability.
- Model as: `fatigue_factor = e^(-decay_rate * rounds_since_last_action)`
- Prevents unrealistic hyper-active agents.

**F. Time-of-Day Patterns:**
- Activity peaks: morning (7-9am), lunch (12-1pm), evening (7-9pm).
- Night hours (11pm-6am) should have near-zero activation.
- Weekend vs. weekday patterns differ by platform.

---

### 4. Academic Approaches to Agent Activation

**4.1 Activation Regimes (Alizadeh & Cioffi-Revilla, JASSS 2015)**

Four asynchronous updating schemes compared:

1. **Uniform Activation:** All agents activated exactly once per turn in random order (sampling without replacement). Most common baseline.
2. **Random Activation:** Agents selected with replacement for n/2 pairs per turn. Some agents may activate multiple times, others zero.
3. **Poisson-1 (Extreme-Biased):** Agents with extreme opinions activate more frequently. lambda_i proportional to |opinion|. Counterintuitive result: produces FEWER extremists.
4. **Poisson-2 (Moderate-Biased):** Moderate agents activate more frequently. Produces MORE extremists (counterintuitive).

Key finding: activation regime significantly affects outcomes (p < 0.05 across all measures). The choice of who speaks when is NOT just an implementation detail -- it fundamentally shapes simulation outcomes.

**Takeaway:** State-driven activation (where agent properties influence activation frequency) is more realistic than random/uniform. Our willingness score is essentially a state-driven Poisson activation regime.

**4.2 Bounded Confidence Models (Hegselmann-Krause)**

- Agents only interact with others whose opinions are within a "confidence bound" epsilon.
- Leads naturally to: consensus (large epsilon), polarization (medium epsilon), or fragmentation (small epsilon).
- Each agent updates opinion to mean of all neighbors within confidence bound.
- Critical for preventing "everyone agrees" -- agents with very different views simply don't influence each other.

**4.3 Granovetter's Threshold Model:**

- Binary choice: participate or not.
- Each agent has a threshold (proportion of others who must act first).
- Threshold drawn from a distribution (often normal or uniform).
- Cascade dynamics: low-threshold agents go first, pushing others past their thresholds.
- Application: viral content spreading, protest dynamics, adoption cascades.
- Key insight: small perturbations in threshold distribution can lead to dramatically different collective outcomes.

**4.4 Mesa ABM Schedulers (Python framework):**

- `RandomActivation`: Each agent activated once per step, random order.
- `SimultaneousActivation`: All agents compute next state, then all update simultaneously.
- `StagedActivation`: Agents execute multiple stages per step (e.g., observe, decide, act).
- Mesa 3 simplified to: `model.agents.shuffle_do("step")` for random, `model.agents.do("step")` for sequential.

**Recommendation for Swaarm:** Use a hybrid approach:
- Probabilistic activation (not uniform/random) based on willingness scores
- Staged execution within a round: (1) compute willingness, (2) select active agents, (3) generate actions, (4) propagate effects

---

### 5. Preventing the "Everyone Agrees" Problem

**5.1 The Core Problem with LLM Agents:**
- LLMs trained with RLHF develop sycophantic tendencies -- they prefer agreeable responses.
- In multi-agent debate: disagreement rate decreases as debate progresses, correlated with performance degradation.
- LLMs produce "average persona" behavior -- lower variance than real humans.
- Tendency to overrepresent perspectives of wealthy, young, politically liberal individuals.
- Wu et al.: LLM agents display lower variance and reduced behavioral diversity vs. humans.

**5.2 Mitigation Strategies:**

**A. Strong Persona Anchoring:**
- Define explicit opinion values (not just personality traits) per agent.
- Include "stubbornness" parameter: probability of ignoring social influence.
- Some agents should be "zealots" who never change opinion (5-10% of population).

**B. Bounded Confidence Mechanism:**
- Agents only process/respond to content within their "confidence bound."
- Very different opinions are ignored or trigger counter-reactions.
- Implement negative influence: exposure to very different views can push agents AWAY (backfire effect).

**C. Prompt Engineering for Diversity:**
- Avoid generic prompts. Use highly specific persona descriptions.
- Include explicit opinion anchors: "You believe X strongly and are skeptical of Y."
- Add contrarian instructions for some agents: "You tend to disagree with popular opinions."
- Use temperature variation: higher temperature for creative/controversial agents.

**D. Structural Diversity:**
- Initialize opinion distribution from real survey data (not random).
- Use echo chamber topology: agents primarily connected to like-minded others.
- Limit cross-group exposure to prevent unrealistic convergence.

**E. Smaller/Different Models:**
- Mix model providers to get different "personality" baselines.
- Smaller models may actually be better for behavioral diversity.
- Use function calling / structured output to constrain response format.

**F. Mechanical Safeguards:**
- Track opinion drift per agent. If opinion changes more than X% from initial, apply resistance.
- "Opinion inertia" parameter: weighted average of current opinion and initial opinion.
- Formula: `new_opinion = alpha * social_influence + (1 - alpha) * initial_opinion` where alpha is small (0.1-0.3).

**5.3 From the Literature:**
- SocioVerse approach: initialize agents from millions of real-world user profiles.
- Role-specific memory structures storing relevant knowledge.
- Focus validation on collective patterns (distribution shapes) rather than individual trajectories.
- Hybrid approach: combine LLM reasoning with classical rule-based opinion dynamics.

---

### 6. Performance at 50k Agents

**6.1 Vectorized Activation Scoring with NumPy:**

The activation computation is embarrassingly parallel -- all agents can be scored simultaneously:

```python
import numpy as np

# Agent properties as arrays (50k x N_features)
persona_willingness = np.array([...])      # shape: (50000,)
conversation_willingness = np.array([...]) # shape: (50000,)
lambda_param = np.array([...])             # shape: (50000,) or scalar
cooldown_factor = np.array([...])          # shape: (50000,)

# Vectorized unified score computation -- all 50k agents at once
unified_scores = persona_willingness * np.exp(
    -lambda_param * (conversation_willingness - persona_willingness)
) * cooldown_factor

# Select active agents via threshold or top-k
threshold = 0.6
active_mask = unified_scores > threshold
# OR probabilistic: each agent's score = probability of activation
random_draws = np.random.random(50000)
active_mask = random_draws < unified_scores

active_agent_ids = np.where(active_mask)[0]
```

**Performance estimates:**
- NumPy vectorized computation for 50k floats: < 1ms
- Even with 10 features per agent: < 5ms
- The bottleneck is NOT activation scoring -- it's the LLM calls for active agents
- If ~300-800 agents are active per round, that's 300-800 LLM calls (or batched)

**6.2 Optimization Strategy:**
- Store all agent state in NumPy arrays (not Python objects).
- Compute activation scores vectorized.
- Only instantiate full agent context for active agents (the 1-2%).
- Use batch LLM calls for active agents.
- Social graph operations (networkx) may be the real bottleneck at 50k nodes -- consider sparse adjacency matrices.

**6.3 Expected Active Agents Per Round:**

For realistic simulation matching real-world distributions:
- Creators (1%): 500 agents with high base willingness
- Contributors (9%): 4,500 agents with medium base willingness
- Lurkers (90%): 45,000 agents with very low base willingness

Per round (simulating ~1 hour):
- Active creators: 50-100 (10-20% of creator pool)
- Active contributors: 100-300 (2-7% of contributor pool)
- Active lurkers: 5-20 (0.01-0.04% of lurker pool)
- **Total active per round: ~155-420 agents**
- This means ~0.3-0.8% of agents are active per round

With LLM calls only for the active agents, this is manageable: 155-420 LLM calls per round.
At ~$0.001 per call (GPT-4o-mini), that's $0.15-0.42 per round, $7.50-$21.00 for a 50-round simulation.

---

### 7. Recommended Willingness Score Architecture for Swaarm

**Composite Score Formula:**
```
activation_probability = sigmoid(
    w1 * personality_score        # Big Five derived (stable)
    + w2 * topic_relevance        # Content-persona match (per-post)
    + w3 * network_exposure       # Feed/graph based (per-round)
    + w4 * emotional_engagement   # Controversy/sentiment (per-post)
    + w5 * fatigue_modifier       # Cooldown decay (per-round)
    + w6 * time_of_day_factor     # Temporal pattern (per-round)
    + bias                        # Class bias (creator/contributor/lurker)
)
```

Where `sigmoid` maps to (0, 1) probability, and bias encodes the 90-9-1 class.

**Alternative (Socialtrait-inspired):**
```
base_score = persona_willingness * exp(-lambda * (context_score - persona_willingness))
activation_prob = base_score * cooldown_factor * time_factor
active = random() < activation_prob
```

**Implementation approach:**
1. All agent features stored as NumPy arrays.
2. Per-round: vectorized score computation (< 5ms for 50k agents).
3. Probabilistic selection via random draw against scores.
4. Only active agents (0.3-0.8%) get LLM calls.
5. Bounded confidence filter: active agents only engage with content within their opinion range.
6. Opinion inertia to prevent convergence: `new_opinion = 0.2 * influence + 0.8 * initial`.

### Key Sources
- Alizadeh & Cioffi-Revilla (2015): "Activation Regimes in Opinion Dynamics" https://www.jasss.org/18/3/8.html
- Hegselmann & Krause (2002): "Opinion Dynamics and Bounded Confidence" https://www.jasss.org/5/3/2.html
- Granovetter (1978): "Threshold Models of Collective Behavior" https://sociology.stanford.edu/publications/threshold-models-collective-behavior
- Socialtrait Patent US12412128B1: https://patents.google.com/patent/US12412128B1
- Springer (2025): "Selective agreement, not sycophancy" https://link.springer.com/article/10.1140/epjds/s13688-025-00579-1
- JASSS submission (2025): "Integrating LLM in Agent-Based Social Simulation" https://arxiv.org/html/2507.19364v1
- Nielsen Norman Group: "Participation Inequality" https://www.nngroup.com/articles/participation-inequality/
- Pew Research (2025): "Americans Social Media Use" https://www.pewresearch.org/internet/2025/11/20/americans-social-media-use-2025/
- David Sayce: "How Many Posts on X" https://www.dsayce.com/digital-marketing/tweets-day/
- LDG: "Faster ABMs in Python" https://lrdegeest.github.io/blog/faster-abms-python

---

## Agent Memory, Prompting & Architecture Research (2026-04-05)

### 1. Agent Memory Systems

**Stanford Generative Agents Architecture (Park et al., 2023)**

The gold-standard architecture has three components: Memory Stream, Reflection, and Planning.

**Memory Stream Storage:**
Each memory object stores:
- Natural language description of the event
- Creation timestamp
- Most recent access timestamp
- Importance score (1-10, rated by LLM at creation time)

**Retrieval Function (three-factor scoring):**
```
score = alpha_recency * recency + alpha_importance * importance + alpha_relevance * relevance
```
- **Recency**: Exponential decay with factor 0.995 per game-hour since last access
- **Importance**: LLM-rated 1-10 scale (1 = brushing teeth, 10 = breakup/college acceptance)
- **Relevance**: Cosine similarity between memory embedding and query embedding
- All alpha weights = 1.0, scores normalized to [0,1] via min-max scaling
- Top-ranked memories fitting the context window are included in prompts

**Reflection Mechanism:**
- Trigger: When cumulative importance score of recent events exceeds threshold (150 in original implementation)
- Occurs ~2-3 times per simulated day
- Process: (1) Feed 100 most recent memories to LLM, ask for 3 salient high-level questions, (2) use questions as retrieval queries, (3) extract insights with evidence citations
- Reflections form hierarchical trees (observations -> reflections -> meta-reflections)

**Planning:**
- Daily plan: 5-8 broad chunks generated from agent summary + previous day
- Recursive decomposition: hour chunks -> 5-15 minute actions
- At each timestep: evaluate observations, decide to continue plan or react

**Practical Recommendation for Swaarm (token-constrained, ~500 tokens/agent):**

The full Stanford architecture is too expensive for 100-500 agents. Simplified approach:

```python
# Simplified memory for Swaarm agents
class AgentMemory(BaseModel):
    """Lightweight memory optimized for social media simulation."""
    # Static persona (in system prompt, cached)
    persona_summary: str          # ~100 tokens

    # Rolling summary (compressed periodically)
    experience_summary: str       # ~80 tokens, updated every 5 rounds

    # Recent observations (sliding window)
    recent_memories: list[str]    # Last 3-5 events, ~100 tokens

    # Strong opinions formed (importance >= 7)
    strong_opinions: list[str]    # Max 3-5 items, ~50 tokens

    # Current plan/intention
    current_plan: str             # ~20 tokens
```

**Token Budget Allocation (~500 tokens input):**
- System prompt (persona): ~150 tokens (STATIC, cacheable)
- Memory context: ~100 tokens (experience summary + strong opinions)
- Feed content: ~200 tokens (3-5 posts the agent "sees")
- Action instructions: ~50 tokens (what actions are available)

**Memory Strategy: Hybrid approach**
- Sliding window for last 3-5 observations (cheap, always recent)
- Importance-based retention: keep high-importance memories permanently
- Summary-based compression: every N rounds, compress recent history into a paragraph
- Skip embeddings initially (expensive); use importance score + recency only

### 2. Prompt Engineering for Consistent Personas

**Key Research Finding:** Increasing persona detail yields power-law improvement in alignment with human trait distributions, with diminishing returns as detail increases.

**System Prompt Structure for Agent Personas:**

```python
AGENT_SYSTEM_PROMPT = """Du bist {name}, {age} Jahre alt, {occupation} aus {location}.

## Persoenlichkeit
- Grundhaltung: {disposition} (z.B. skeptisch, begeisterungsfaehig, pragmatisch)
- Kommunikationsstil: {style} (z.B. emotional, sachlich, provokativ, humorvoll)
- Politische Tendenz: {political_leaning}
- Medienkonsum: {media_habits}
- Expertise: {expertise_areas}

## Meinungen
{strong_opinions_list}

## Posting-Verhalten
- Typische Postlaenge: {typical_length} (kurz/mittel/lang)
- Nutzt Emojis: {uses_emojis} (ja/nein/manchmal)
- Reagiert auf: {triggers} (z.B. Ungerechtigkeit, Innovationen, Kontroversen)
- Ignoriert: {ignores} (z.B. Werbung, irrelevante Themen)

## Wichtig
- Bleib IMMER in der Rolle von {name}
- Antworte NUR auf Deutsch
- Deine Antworten spiegeln deine Persoenlichkeit und Meinungen wider
"""
```

**Trait Descriptions vs. Few-Shot Examples:**
- Trait descriptions are more token-efficient and work well for GPT-4o-mini
- Few-shot examples improve consistency for specific behaviors (e.g., posting style) but cost more tokens
- Best approach: Use trait descriptions in system prompt + 1-2 very short few-shot examples in the first user message for critical behaviors
- Personas are fragile for extreme styles (very sarcastic, very formal); anchor with explicit constraints

**Anchoring Techniques for Consistency:**
1. Include explicit constraints ("Du sagst NIEMALS..." / "Du verwendest IMMER...")
2. Define what the persona does NOT do
3. Place persona at the start of system prompt (benefits from caching)
4. Use structured sections (Markdown headers) for clarity
5. Restate key personality trait in the action prompt as a reminder

### 3. Structured Output for Agent Actions

**Recommendation: Use Function Calling with strict: true**

This is the most reliable approach for action selection. Structured Outputs guarantees schema adherence when strict mode is enabled.

```python
from pydantic import BaseModel
from enum import Enum
from typing import Optional

class ActionType(str, Enum):
    POST = "post"
    REPLY = "reply"
    LIKE = "like"
    SHARE = "share"
    SKIP = "skip"

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class AgentAction(BaseModel):
    """Schema for agent action output via Structured Outputs."""
    reasoning: str          # Brief internal reasoning (useful for analysis)
    action: ActionType
    target_post_id: Optional[str] = None  # Which post to react to
    content: Optional[str] = None         # Text for post/reply
    sentiment: Sentiment
    emotional_intensity: int  # 1-5 scale

# Function definition for OpenAI API
AGENT_ACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "take_action",
        "description": "Choose and execute a social media action",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Brief reasoning for this action (1-2 sentences)"
                },
                "action": {
                    "type": "string",
                    "enum": ["post", "reply", "like", "share", "skip"]
                },
                "target_post_id": {
                    "type": ["string", "null"],
                    "description": "ID of post to react to, null for new posts or skip"
                },
                "content": {
                    "type": ["string", "null"],
                    "description": "Text content for post or reply, null for like/share/skip"
                },
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral", "mixed"]
                },
                "emotional_intensity": {
                    "type": "integer",
                    "description": "1=calm, 5=very emotional"
                }
            },
            "required": ["reasoning", "action", "target_post_id",
                         "content", "sentiment", "emotional_intensity"],
            "additionalProperties": False
        }
    }
}
```

**Key Implementation Notes:**
- strict: true guarantees valid JSON matching the schema (no validation/retry needed)
- All fields must be required when using strict mode; use nullable types for optional fields
- Pydantic integration: use `client.chat.completions.parse(response_format=AgentAction)` for direct deserialization
- Handle refusals programmatically (check response.refusal field)
- GPT-4o-mini supports structured outputs natively
- Keep tool count low (6-15 per platform, well within 128 tool limit)

**Error Handling Strategy:**
```python
async def get_agent_action(response) -> AgentAction:
    if response.choices[0].message.refusal:
        # Model refused (safety filter) -> default to skip
        return AgentAction(
            reasoning="Refused by model",
            action=ActionType.SKIP,
            target_post_id=None,
            content=None,
            sentiment=Sentiment.NEUTRAL,
            emotional_intensity=1
        )
    # With strict mode, parsing is guaranteed to succeed
    return AgentAction.model_validate_json(
        response.choices[0].message.tool_calls[0].function.arguments
    )
```

### 4. Feed Representation in Prompts

**Key Finding:** JSON is token-inefficient (40-70% overhead). Use compact text formats.

**Recommended Feed Format (compact, ~40 tokens per post):**

```
## Dein Feed

[P1] @MaxMueller (Journalist, 12.4K Follower) - vor 2h
"Die neue Klimastrategie der Firma X ist reine Greenwashing-PR"
+47 c23 s12

[P2] @SarahTech (Ingenieurin, 890 Follower) - vor 1h
"Interessanter Ansatz, aber die Zahlen stimmen nicht. Thread:"
+12 c5 s3
Antwort auf [P1]

[P3] ORIGINAL-POST (Firma X, 50K Follower) - vor 3h
"Wir verpflichten uns zu 100% erneuerbarer Energie bis 2030"
+234 c89 s45
```

**Format Design Principles:**
- Use short IDs [P1], [P2] for reference in actions
- Include social proof signals (followers, engagement) compactly
- Show relationship (reply chains) explicitly
- Timestamps as relative ("vor 2h") not absolute
- Skip unnecessary metadata (profile pictures, verified badges)
- 3-5 posts per round is optimal (balances context vs. cost)

**How Many Posts Per Round:**
- 3-5 posts is the sweet spot for 500-token budget
- Show the original stimulus post + 2-4 most relevant reactions
- Prioritize: (1) posts from the agent's social connections, (2) high-engagement posts, (3) recent posts
- Rotate which posts different agents see (simulates algorithmic feeds)

**Alternative: Ultra-Compact Format (~25 tokens per post):**
```
P1|@Max|Journalist|12K|2h|"Greenwashing-PR"|+47/c23/s12
P2|@Sarah|Ingenieurin|890|1h|"Zahlen stimmen nicht"|+12/c5/s3|re:P1
```
This saves ~40% tokens but may reduce LLM comprehension. Test both.

### 5. Preventing Mode Collapse

**The Problem:** Post-RLHF models exhibit mode collapse (favoring narrow, typical responses). In multi-agent simulation, this causes all agents to sound similar despite different personas.

**Strategy 1: Temperature Differentiation (Simple)**
```python
# Per-agent temperature based on personality
def get_agent_temperature(persona: AgentPersona) -> float:
    base = 0.7  # Default
    if persona.disposition == "provocative":
        return min(base + 0.3, 1.2)  # More varied
    if persona.disposition == "analytical":
        return max(base - 0.2, 0.4)  # More consistent
    return base

# WARNING: High temperature (>1.0) causes reasoning drift
# in multi-step agent loops. Use cautiously.
```

**Strategy 2: Verbalized Sampling (Research-Backed)**

Verbalized Sampling (VS) prompts the model to generate multiple responses with probability estimates, then samples from that distribution. Achieves 1.6-2.1x diversity improvement over direct prompting without quality loss.

```python
# Instead of: "How would you react to this post?"
# Use: "Generate 3 possible reactions with probabilities:"

VS_PROMPT_SUFFIX = """
Generiere 3 moegliche Reaktionen auf diesen Post.
Fuer jede Reaktion, gib eine Wahrscheinlichkeit an (summiert zu 1.0):

Reaktion 1 (p=?): ...
Reaktion 2 (p=?): ...
Reaktion 3 (p=?): ...
"""
# Then sample from the distribution programmatically
```

Note: VS costs ~3x more tokens per decision but is orthogonal to temperature. Consider using it selectively (e.g., only for "opinion leader" agents or for the initial seeding round).

**Strategy 3: Structural Diversity Mechanisms**
- Assign explicit contrarian roles: "Du bist IMMER skeptisch gegenueber Unternehmensmeldungen"
- Vary information access: different agents see different subsets of posts
- Include opinion anchors in persona: "Du findest Greenwashing inakzeptabel" vs. "Du unterstuetzt Klimainitiativen der Wirtschaft"
- Use different system prompt styles per agent cluster (formal vs. casual)
- Add randomized context: "Heute hattest du einen schlechten Tag" / "Du hast gerade gute Nachrichten bekommen"

**Strategy 4: Population-Level Calibration**
- Pre-define opinion distribution for the population (e.g., 30% supportive, 40% neutral, 30% critical)
- Assign stances explicitly in persona, not left to LLM inference
- Monitor and adjust: if output distribution drifts, adjust persona prompts
- Use willingness scoring to filter which agents even engage (not everyone reacts)

### 6. Token Optimization & Prompt Caching

**OpenAI Prompt Caching (Automatic since Oct 2024):**
- Minimum prefix: 1,024 tokens
- Cache increments: 128 tokens
- Duration: 5-10 minutes standard, up to 24 hours with extended retention
- Cost savings: 50% on GPT-4o-mini cached tokens, 75% on GPT-4.1
- Latency reduction: up to 80% for cached prefixes

**Prompt Structure for Maximum Cache Hits:**

```
[STATIC PREFIX - cacheable]                    ~1,100+ tokens
  System prompt with persona definition         ~150 tokens
  Platform rules and constraints                ~100 tokens
  Action schema / tool definitions              ~400 tokens
  General instructions                          ~200 tokens
  Padding/examples to reach 1,024 minimum       ~150 tokens

[DYNAMIC SUFFIX - not cached]                  ~400 tokens
  Current memory context                        ~100 tokens
  Feed content for this round                   ~200 tokens
  Round number and time context                 ~20 tokens
  Action prompt                                 ~80 tokens
```

**Critical Implementation Tips:**
1. Pad static prefix to exceed 1,024 tokens (include few-shot examples or detailed platform rules)
2. Keep tool definitions stable (schema changes invalidate cache)
3. Use `prompt_cache_key` parameter to improve routing (60% -> 87% hit rate in documented case)
4. Batch similar agents together (same persona type = same prefix = better caching)
5. Group agents by persona archetype so system prompts overlap more
6. Use Responses API instead of Chat Completions (40-80% better cache utilization)

**Cacheable vs. Dynamic Breakdown:**

| Component | Static? | Cacheable? | Tokens |
|-----------|---------|------------|--------|
| Persona definition | Yes | Yes | ~150 |
| Platform rules | Yes | Yes | ~100 |
| Tool schema | Yes | Yes | ~400 |
| Instructions | Yes | Yes | ~200 |
| Memory summary | Semi (updates every 5 rounds) | Partial | ~100 |
| Feed content | No (changes every round) | No | ~200 |
| Round context | No | No | ~20 |

**Cost Estimation (500 agents, 50 rounds, GPT-4o-mini):**
- Per call: ~1,500 input tokens + ~100 output tokens
- Total calls: 500 * 50 = 25,000
- Without caching: 25,000 * 1,500 = 37.5M input tokens
- With caching (~70% hit rate on ~1,100 token prefix):
  - Cached: 25,000 * 1,100 * 0.7 = 19.25M tokens at 50% discount
  - Uncached: 25,000 * 1,100 * 0.3 + 25,000 * 400 = 18.25M tokens full price
  - Savings: ~30-35% on input tokens
- GPT-4o-mini pricing: $0.15/1M input, $0.075/1M cached input
- Estimated cost per simulation: ~$4-6 (down from ~$5.60 without caching)

**Further Optimization: Agent Archetype Batching**

Instead of 500 unique personas, define 20-30 archetype templates. Agents within the same archetype share the same system prompt prefix, dramatically improving cache hit rates:

```python
ARCHETYPES = {
    "skeptischer_journalist": {
        "system_prompt": "...",  # Shared across all agents of this type
        "variable_fields": ["name", "age", "specific_opinions"]
    },
    "technik_enthusiast": { ... },
    "besorgter_buerger": { ... },
    # ... 20-30 archetypes
}
# Variable fields injected AFTER the cached prefix
```

### Key Sources
- Stanford Generative Agents: https://dl.acm.org/doi/10.1145/3586183.3606763
- Verbalized Sampling: https://arxiv.org/html/2510.01171v1
- OpenAI Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- OpenAI Prompt Caching 201: https://developers.openai.com/cookbook/examples/prompt_caching_201
- GPT-4.1 Prompting Guide: https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide
- OpenAI Persona Prompting: https://developers.openai.com/cookbook/examples/gpt-5/prompt_personalities
- LLM Persona Simulation: https://www.emergentmind.com/topics/llm-based-persona-simulation
- Multi-Agent Prompt Engineering: https://www.emergentmind.com/topics/multi-agent-prompt-engineering
- Temperature and Agent Failure: https://machinelearningmastery.com/why-agents-fail-the-role-of-seed-values-and-temperature-in-agentic-loops/

---

## Open-Source Social Simulation Landscape (Recherche 2026-04-05)

### 1. MiroFish (github.com/666ghj/MiroFish)

**Overview:** Open-source "swarm intelligence prediction engine" that went viral in March 2026 (49k+ GitHub stars). Built by a Chinese undergraduate, funded by Shanda Group. AGPL-3.0 licensed. Uses OASIS under the hood. Very close to what Swaarm is building.

**Tech Stack:** Python 3.11-3.12 backend, Vue.js frontend, OASIS simulation engine, Zep Cloud for agent memory, GraphRAG for knowledge extraction, uv package manager.

**5-Stage Pipeline:**
1. **Graph Construction** -- GraphRAG parses seed document (press release, news article), extracts entities and relationships, builds a knowledge graph. This is the key differentiator vs. raw OASIS.
2. **Environment & Agent Setup** -- Personas auto-generated from knowledge graph. Each agent gets: unique personality, stance on topic, long-term memory (Zep Cloud), behavioral logic. Agent beliefs initialized from graph relations, relationships from graph edges. High-centrality nodes become opinion leaders.
3. **Dual-Platform Simulation** -- Runs OASIS on two platforms simultaneously (Twitter-like + Reddit-like). OASIS handles the 23 social actions. Simulation runs as subprocess via `simulation_runner.py`.
4. **Report Generation** -- ReportAgent (ReACT agent with tool-calling) analyzes simulation results. Has full toolset access to post-simulation environment. Produces structured prediction report.
5. **Deep Interaction** -- Users can chat with any agent post-simulation to understand reasoning, or inject new variables for scenario testing.

**Backend Architecture (13 services):**
- `graph_builder.py` -- Ontology-to-graph pipeline
- `ontology_generator.py` -- Creates ontology definitions from seed material
- `oasis_profile_generator.py` -- Generates OASIS-compatible agent profiles
- `simulation_config_generator.py` -- Creates simulation configurations
- `simulation_runner.py` -- Runs OASIS as subprocess
- `simulation_manager.py` -- Orchestrates simulation lifecycle
- `simulation_ipc.py` -- Inter-process communication with OASIS
- `report_agent.py` -- ReACT agent for report generation
- `text_processor.py` -- Text processing utilities
- `zep_entity_reader.py` -- Reads entities from Zep
- `zep_graph_memory_updater.py` -- Updates graph memory
- `zep_tools.py` -- Zep utility functions
- `config.py` -- Configuration

**Key Architectural Decisions:**
- OASIS runs as a **subprocess**, not in-process. Communication via IPC (`simulation_ipc.py`). This keeps the simulation engine isolated.
- **Zep Cloud** for long-term agent memory -- agents remember across interactions. This is expensive at scale but powerful.
- **GraphRAG** as the knowledge foundation means agents are grounded in the actual content, not just random personas.
- Provider-agnostic LLM layer (OpenAI SDK format, works with Qwen, OpenAI, etc.)
- Docker Compose for deployment (ports 3000 frontend, 5001 backend)
- Memory grows rapidly: 16GB RAM needed for >40 rounds. MAX_CONCURRENT_AGENTS=10 for throttling.

**Limitations (relevant for Swaarm):**
- Agents show heightened susceptibility to herd behavior vs. real humans
- Outputs are "plausible scenarios, not probability estimates"
- Heavy memory footprint at scale
- Zep Cloud dependency (single point of failure, cost)

### 2. MiroFish-Offline (github.com/nikmcfly/MiroFish-Offline)

English-language fork replacing cloud dependencies with local services:
- **Neo4j** replaces Zep Cloud for graph memory
- **Ollama** replaces cloud LLMs
- **nomic-embed-text** for local embeddings
- Introduces `GraphStorage` **abstract interface** -- swap Neo4j for any graph DB by implementing one class. Good pattern.
- Hybrid search: 70% vector similarity + 30% BM25 keyword matching
- Dependency injection via Flask's `app.extensions` dict (no global singletons)
- Requires 32GB RAM recommended for larger models

### 3. OASIS (github.com/camel-ai/oasis) -- The Simulation Engine

**Architecture (4 core modules):**
1. **Environment Server** -- Centralized platform simulation. SQLite3 database with tables for users, posts, comments, likes, dislikes, follows, traces. Action-dispatch pattern via `getattr(self, action.value, None)`.
2. **Recommendation System** -- Two algorithms: interest-based (TwHIN-BERT embeddings) and hot-score-based (Reddit's disclosed ranking formula: `h = log10(max(|u-d|,1)) + sign(u-d)*(t-t0)/45000`).
3. **Time Engine** -- Agents activated probabilistically using 24-dimensional hourly activity vector. 3-minute time steps. Linear time-mapping for simulation acceleration.
4. **Agent Module** -- LLM-powered with memory module + action module.

**Agent Design:**
- `SocialAgent` extends `ChatAgent` from CAMEL-AI framework
- Key methods: `perform_action_by_llm()` (autonomous), `perform_action_by_hci()` (manual), `perform_action_by_data()` (scripted)
- Decision loop: Environment observation -> text prompt -> LLM reasoning (Chain-of-Thought) -> tool/function selection -> execution
- 23 actions exposed as `FunctionTool` objects via OpenAI function-calling
- Memory: inherits CAMEL memory system, stores conversation history in OpenAI message format

**Platform Abstraction:**
- Single `Platform` class handles all social media operations
- Async message-driven with channel-based communication
- Methods for content (create_post, repost, quote_post), engagement (like, dislike, comment), network (follow, unfollow, mute), discovery (search, trend), moderation (report), groups (create_group, join_group)
- Standardized response contracts: all methods return success/failure dicts with relevant IDs
- Pluggable recommendation system (Reddit, Twitter, TWHIN, Random)

**Scalability:**
- Up to 1M agents (18 hours per time step with 27 A100 GPUs at that scale)
- Distributed architecture: agents, environment server, inference as independent modules
- vLLM for efficient inference at scale
- ~48,500 new posts per step at 1M agent scale

**User Generation Algorithm:**
- Combines real user data with relationship networks
- Core users connect to ordinary users via interest-based sampling
- 0.2 probability of following core users
- Maintains scale-free network properties

**Code Pattern (basic simulation):**
```python
env = oasis.make(
    agent_graph=agent_graph,
    platform=oasis.DefaultPlatformType.REDDIT,
    database_path="./data/simulation.db"
)
await env.reset()
# Manual actions
await env.step({agent: ManualAction(action_type=..., content=...)})
# LLM-driven actions
await env.step({agent: LLMAction() for agent in agents})
await env.close()
```

### 4. mastodon-sim (github.com/social-sandbox/mastodon-sim)

**Unique approach:** Runs simulations on an actual Mastodon server instance, not a simulated platform.

**Architecture:**
- Built on Google DeepMind's **Concordia** framework
- Fully YAML-configurable (no code changes needed for new simulations)
- 4 YAML files: `soc_sys.yaml` (shared knowledge), `agents.yaml` (personas), `probes.yaml` (surveys), `sim.yaml` (runtime params)
- Hydra configuration management
- Supports base agents and custom agents (voter.py, candidate.py, malicious.py)
- Dual output: `events.json` (agent actions) + `prompts_and_responses.jsonl` (LLM traces)
- **Probe system** as first-class feature: deploy longitudinal surveys on agent population during simulation
- Exogenous "gamemaster" agents for injecting controlled events
- NeurIPS 2024 Workshop paper

**Key Insight for Swaarm:** The YAML-configurable approach and probe system are interesting patterns. Being able to define entire simulations declaratively could be valuable for our SaaS customers who want to tweak parameters without technical knowledge.

### 5. AgentSociety (github.com/tsinghua-fib-lab/AgentSociety)

**Architecture (6 layers):**
1. Model Layer -- Agent config and task management
2. Agent Layer -- Multi-head workflows with memory, reasoning, routing, action blocks
3. Message Layer -- P2P, peer-to-group, group chat
4. Environment Layer -- Sensing, interaction, message processing
5. LLM Layer -- Provider-agnostic (OpenAI, Qwen, Deepseek)
6. Tool Layer -- String processing, JSON parsing, storage

**Key Pattern:** "Mind-Behavior Coupling" -- LLM reasoning integrated with behavioral theories like Maslow's Hierarchy of Needs. Agents don't just respond to prompts; they have explicit needs and motivations modeled as psychological frameworks.

**Relevant for Swaarm:** The concept of grounding agent behavior in behavioral science theories (not just LLM personality prompts) could produce more realistic simulation outcomes.

### 6. Other Notable Projects

- **AgentVerse** (github.com/OpenBMB/AgentVerse) -- ICLR 2024, general multi-agent deployment framework
- **GenSim** (NAACL 2025 demo) -- General social simulation platform
- **SoMe Benchmark** (arxiv 2512.14720) -- Realistic benchmark for LLM social media agents

---

## Architectural Lessons for Swaarm

### What MiroFish Does Well (and We Should Learn From)

1. **GraphRAG as Foundation:** Extracting entities/relationships from the seed document before generating personas means agents are grounded in the actual communication content. Our current approach should incorporate this.

2. **5-Stage Pipeline is Clean:** Graph construction -> Environment setup -> Simulation -> Report -> Deep interaction. We should adopt a similar staged approach.

3. **ReportAgent as ReACT Agent:** Using a tool-calling agent (not a simple summarizer) for report generation means the report can dynamically query the simulation data. Much more powerful.

4. **Subprocess Isolation for OASIS:** Running the simulation engine as a subprocess keeps it isolated from the API server. Good for stability and resource management.

5. **Provider-Agnostic from Day 1:** Their LLM layer uses OpenAI SDK format but works with any compatible provider.

### Where We Can Differentiate

1. **DACH Focus:** German-language UI, European data handling, GDPR compliance -- none of the open-source projects address this.

2. **SaaS-First Architecture:** MiroFish is a self-hosted tool. We're building a multi-tenant SaaS with Stripe billing, Supabase auth, proper user management.

3. **Communication-Specific Optimization:** MiroFish is general-purpose ("predict anything"). We can optimize specifically for corporate communications: press releases, crisis comms, product launches, public statements.

4. **Better Report Quality:** The ReportAgent pattern is good, but we can build communication-specific analytical frameworks (sentiment trajectory, key opinion leader identification, crisis escalation prediction, message resonance scoring).

5. **Custom Simulation Engine vs. OASIS Dependency:** Building our own engine (as currently planned) gives us full control over the simulation loop, action system, and platform abstraction without OASIS's overhead and complexity.

### Specific Technical Patterns to Adopt

1. **Action-as-FunctionTool Pattern (from OASIS):** Expose platform actions as function tools via OpenAI function-calling. Clean, extensible, well-understood by LLMs.

2. **Standardized Response Contracts (from OASIS Platform):** All action methods return `{success: bool, id: str, ...}` dicts. Consistent interface regardless of action type.

3. **Probabilistic Activation (from OASIS Time Engine):** Don't activate all agents every round. Use a 24-dim hourly activity vector to probabilistically activate agents, mimicking real usage patterns.

4. **Hybrid Search for Memory (from MiroFish-Offline):** 70% vector similarity + 30% BM25 for knowledge retrieval. Better than pure vector search.

5. **GraphStorage Abstract Interface (from MiroFish-Offline):** Swap graph backends by implementing one class. Good pattern for our storage layer.

6. **YAML-Configurable Simulations (from mastodon-sim):** Allow customers to configure simulation parameters declaratively.

7. **Probe/Survey System (from mastodon-sim):** Deploy longitudinal surveys on agent population during simulation. Useful for tracking opinion shifts over time.

8. **Mind-Behavior Coupling (from AgentSociety):** Ground agent behavior in behavioral science, not just personality prompts. More realistic outcomes.

### Error Handling & Retry Best Practices (from Research)

- **Exponential backoff with full jitter** for LLM API retries: `wait = random(0, min(cap, base * 2^attempt))`. Prevents thundering herd.
- **Classify errors:** Client errors (4xx) should not be retried. Server errors (5xx) and rate limits should be retried.
- **Circuit breaker pattern:** After N consecutive failures, stop retrying and fail fast for a cooldown period.
- **Fallback models:** If primary LLM fails, fall back to a cheaper/different model.
- **Checkpoint simulation state:** Save state between rounds so simulation can resume after failure.

### Key Sources
- MiroFish Main Repo: https://github.com/666ghj/MiroFish
- MiroFish Offline Fork: https://github.com/nikmcfly/MiroFish-Offline
- OASIS: https://github.com/camel-ai/oasis
- OASIS Paper: https://arxiv.org/abs/2411.11581
- OASIS Docs: https://docs.oasis.camel-ai.org/
- mastodon-sim: https://github.com/social-sandbox/mastodon-sim
- AgentSociety: https://github.com/tsinghua-fib-lab/AgentSociety
- AgentVerse: https://github.com/OpenBMB/AgentVerse
- MiroFish Guide: https://openclawapi.org/en/blog/2026-03-17-mirofish-guide
- MiroFish DEV Article: https://dev.to/arshtechpro/mirofish-the-open-source-ai-engine-that-builds-digital-worlds-to-predict-the-future-ki8

## Simulation Quality Assurance & Validation Research (2026-04-05)

### 1. How Competitors Claim Accuracy

**Socialtrait (86% accuracy claim):**
- Users report simulations match real-world results 86% of the time
- Claims 95% accuracy on brand crisis benchmarks specifically
- Methodology: "Representativeness framework" comparing simulation outputs against actual market outcomes
- Each AI persona defined across 50+ demographic, psychographic, and behavioral variables
- Uses proprietary persona algorithms, LLMs, and reinforcement learning
- Self-reported metrics, no independent audit published
- Source: https://finance.yahoo.com/news/socialtrait-launches-first-ai-powered-123900791.html

**Artificial Societies (95% accuracy claim):**
- Claims 95% distribution accuracy against "human self-replication"
- 90% persona internal coherence
- Each society: 300-5,000 interconnected AI personas from public social media profiles
- Critical limitation: self-reported, not independently audited
- Overrepresents digitally active populations, underrepresents offline demographics
- Source: https://www.ycombinator.com/companies/artificial-societies

**Stanford/Google DeepMind reference benchmark:**
- Generative agents replicated real participants' responses 85% as accurately as individuals replicated their own answers two weeks later on the General Social Survey
- Social behavior mimicked with 98% correlation
- This is the most rigorous independent validation available
- Source: https://news.stanford.edu/stories/2025/07/ai-social-science-research-simulated-human-subjects

**Industry-wide synthetic audience benchmarks:**
- 85-92% parity score depending on audience type (Synthetic Users)
- 80-90% correlation to actual engagement metrics across leading platforms
- Source: https://research.aimultiple.com/audience-simulation/

**Key takeaway for Swaarm:** Competitors' accuracy claims are marketing numbers. The real bar is the Stanford benchmark (85% self-replication accuracy). We should aim for transparent, reproducible validation rather than inflated claims.

### 2. Validation Methodology Framework

Based on the comprehensive review "Validation is the central challenge for generative social simulation" (PMC, 2025):

**Three critical validation challenges for LLM-based ABMs:**
1. **Black-box opacity** - impossible to determine why a specific input yields a specific output
2. **Stochastic behavior and bias** - different outputs for identical inputs; social stereotypes instead of accurate representations
3. **Hallucination and out-of-distribution** - factually incorrect outputs, especially for unprecedented scenarios

**Five validation approaches currently used (from review of 35 studies):**

| Approach | Usage | Description |
|----------|-------|-------------|
| Human/expert judgment | 22/35 studies | Subjective but most common |
| Comparison against known social patterns | ~50% | Do outputs follow power laws, etc.? |
| Empirical human data comparison | ~50% | Compare to real social media data |
| Comparison with prior models | Rare | Benchmark against existing simulations |
| Internal consistency checks | Rare | Does the model contradict itself? |

**Critical gap identified:** Most studies validate surface-level outputs (linguistic style) rather than underlying mechanisms.

**Recommended "Operational Validity" standard (three requirements):**
1. **Purpose alignment** - validation targets must match what the model actually addresses
2. **External grounding** - evidence from human data or pre-registered benchmarks
3. **Robustness** - results across multiple runs with sensitivity analyses

Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC12627210/

### 3. Concrete Quality Metrics to Implement

#### A. Opinion Diversity (Shannon Entropy)

```python
import math
from collections import Counter

def shannon_entropy(sentiments: list[str]) -> float:
    """Measure opinion diversity. Higher = more diverse.

    For 5 sentiment categories (very_negative, negative, neutral, positive, very_positive):
    - Maximum entropy: log2(5) = 2.32 (uniform distribution)
    - Minimum entropy: 0 (all same sentiment)
    - Healthy simulation: > 1.5 (diverse but not uniform)
    """
    counts = Counter(sentiments)
    total = len(sentiments)
    entropy = -sum(
        (count/total) * math.log2(count/total)
        for count in counts.values()
        if count > 0
    )
    return entropy

def normalized_entropy(sentiments: list[str]) -> float:
    """Entropy normalized to [0, 1]. Target: 0.5-0.8."""
    n_categories = len(set(sentiments))
    if n_categories <= 1:
        return 0.0
    max_entropy = math.log2(n_categories)
    return shannon_entropy(sentiments) / max_entropy
```

**Thresholds:**
- < 0.3 normalized: CRITICAL - mode collapse, all agents agree
- 0.3-0.5: WARNING - low diversity, might be acceptable for consensus topics
- 0.5-0.8: HEALTHY - realistic opinion spread
- > 0.9: WARNING - suspiciously uniform distribution (real opinions cluster)

#### B. Engagement Distribution (Power Law Fit)

Real social media engagement follows power law distributions. A few posts get most engagement, most posts get little.

```python
import numpy as np
from scipy import stats

def power_law_fit(engagement_counts: list[int]) -> dict:
    """Test if engagement follows power law distribution.

    Returns fit quality metrics.
    Real social media: alpha typically 1.5-2.5
    """
    data = np.array([x for x in engagement_counts if x > 0])
    if len(data) < 10:
        return {"valid": False, "reason": "insufficient data"}

    # Fit power law using MLE
    log_data = np.log(data)
    alpha = 1 + len(data) / np.sum(log_data - np.log(min(data)))

    # Gini coefficient as simpler proxy
    sorted_data = np.sort(data)
    n = len(sorted_data)
    gini = (2 * np.sum((np.arange(1, n+1) * sorted_data)) / (n * np.sum(sorted_data))) - (n + 1) / n

    return {
        "alpha": alpha,
        "gini": gini,  # Real social media: 0.6-0.8
        "valid": True
    }
```

**Thresholds:**
- Gini < 0.3: WARNING - engagement too uniform (unrealistic)
- Gini 0.5-0.8: HEALTHY - realistic engagement inequality
- Gini > 0.9: WARNING - one post dominates everything (possible but check)

**Reference:** Real social media follows power law across all 8 major platforms studied (Twitter, YouTube, Instagram, TikTok, etc.) with alpha typically 1.5-2.5
Source: https://ideas.repec.org/p/wai/econwp/22-07.html

#### C. Content Repetition / Lexical Diversity

```python
from collections import Counter

def content_repetition_score(posts: list[str]) -> dict:
    """Measure how repetitive content is across agents.

    Uses multiple metrics:
    - Unique n-gram ratio
    - Pairwise cosine similarity (needs embeddings)
    - Type-token ratio
    """
    # Simple: unique trigram ratio
    all_trigrams = []
    for post in posts:
        words = post.lower().split()
        trigrams = [tuple(words[i:i+3]) for i in range(len(words)-2)]
        all_trigrams.extend(trigrams)

    if not all_trigrams:
        return {"unique_ratio": 0, "repetitive": True}

    unique_ratio = len(set(all_trigrams)) / len(all_trigrams)

    return {
        "unique_trigram_ratio": unique_ratio,
        # < 0.3: CRITICAL repetition
        # 0.3-0.6: some repetition (check)
        # > 0.6: healthy diversity
        "repetitive": unique_ratio < 0.3
    }

def pairwise_semantic_similarity(posts: list[str], embeddings) -> float:
    """Mean pairwise cosine similarity of post embeddings.

    Healthy range: 0.2-0.5 (topically related but not identical)
    > 0.7: agents are saying the same thing
    < 0.1: agents are talking about unrelated topics
    """
    # Use embedding model (e.g., text-embedding-3-small)
    # Compute mean pairwise cosine similarity
    pass
```

#### D. Persona Consistency (Drift Detection)

Based on research from "Measuring and Controlling Persona Drift in Language Model Dialogs":

**Key findings from the research:**
- LLM agents progressively abandon their assigned personas over multi-turn conversations
- Agents begin ADOPTING the user's/other agents' personas during longer exchanges
- Larger models experience GREATER identity drift (counterintuitive)
- Performance degrades sharply between conversation turns

**Three metrics for persona consistency:**
1. **Prompt-to-line consistency** - does each post align with the original persona definition?
2. **Line-to-line consistency** - does the agent contradict itself within a simulation?
3. **Q&A consistency** - does the agent maintain stable beliefs when probed?

Source: https://arxiv.org/html/2402.10962v1

```python
def persona_consistency_score(
    persona_definition: str,
    agent_posts: list[str],
    llm_judge
) -> dict:
    """Use an LLM judge to evaluate persona consistency.

    For each post, ask: "Does this post align with the following persona?"
    Track drift over rounds.
    """
    scores = []
    for i, post in enumerate(agent_posts):
        score = llm_judge.evaluate(
            prompt=f"""Rate 0-1 how well this post aligns with the persona.

Persona: {persona_definition}
Post: {post}
Round: {i+1}

Score (0=completely off-persona, 1=perfectly in-character):""",
        )
        scores.append(score)

    return {
        "mean_consistency": sum(scores) / len(scores),
        "drift_slope": _calculate_drift(scores),  # Negative = drifting away
        "min_consistency": min(scores),
        "rounds_below_threshold": sum(1 for s in scores if s < 0.5),
    }
```

**Thresholds:**
- Mean < 0.5: CRITICAL - persona not maintained
- Mean 0.5-0.7: WARNING - noticeable drift
- Mean > 0.7: HEALTHY
- Drift slope < -0.02 per round: WARNING - progressive degradation

#### E. Network Clustering Coefficient

```python
import networkx as nx

def network_realism_metrics(G: nx.Graph) -> dict:
    """Evaluate if the interaction network looks realistic.

    Real social networks have:
    - Clustering coefficient: 0.1-0.5 (communities exist)
    - Average path length: 3-6 (small world property)
    - Degree distribution: power law
    """
    return {
        "clustering_coefficient": nx.average_clustering(G),
        # Real social networks: 0.1-0.5
        # < 0.05: too random
        # > 0.7: too clustered

        "avg_path_length": nx.average_shortest_path_length(G)
            if nx.is_connected(G) else None,
        # Real networks: 3-6

        "density": nx.density(G),
        # Real social networks: 0.001-0.1
        # > 0.3: unrealistically dense

        "degree_assortativity": nx.degree_assortativity_coefficient(G),
        # Real social networks: slightly negative to slightly positive
    }
```

#### F. Narrative Emergence Detection

```python
def narrative_emergence_score(
    posts_by_round: list[list[str]],
    embedding_model
) -> dict:
    """Detect if organic narratives/themes develop over time.

    Healthy simulations develop new themes beyond the initial stimulus.
    Measure: topic diversity increases in middle rounds, then may converge.
    """
    round_topics = []
    for round_posts in posts_by_round:
        # Cluster posts by topic using embeddings
        embeddings = embedding_model.embed(round_posts)
        # Use simple k-means or DBSCAN
        n_topics = _count_clusters(embeddings)
        round_topics.append(n_topics)

    return {
        "initial_topics": round_topics[0] if round_topics else 0,
        "peak_topics": max(round_topics) if round_topics else 0,
        "topic_growth": (max(round_topics) - round_topics[0])
            if round_topics else 0,
        "narrative_emerged": max(round_topics) > round_topics[0] + 1
        # Healthy: topics grow from stimulus, then may converge
        # Unhealthy: topic count stays flat (no organic discussion)
    }
```

### 4. Known Failure Modes and Mitigations

#### Mode Collapse (ALL agents sound the same)
- **Cause:** RLHF training causes models to favor narrow, typical responses (typicality bias, alpha=0.57 measured)
- **Detection:** Shannon entropy < 0.3, pairwise similarity > 0.7, unique trigram ratio < 0.3
- **Mitigation:** Verbalized sampling (1.6-2.1x diversity gain), temperature differentiation, explicit opinion anchors in personas
- Source: https://arxiv.org/html/2510.01171v1

#### Sycophancy (agents agree too much)
- **Cause:** LLMs trained to be helpful, leading to excessive validation
- **Quantified:** LLMs offer emotional validation 76% vs 22% for humans; accept user's framing 90% vs 60% for humans; false negative rate on moral judgments: 44%
- **Detection:** Agreement rate across agents, sentiment skew toward positive
- **Mitigation:** Explicit contrarian personas, "challenge the majority view" instructions, social sycophancy-aware prompting
- Source: https://arxiv.org/html/2505.13995v1 (ELEPHANT framework)

#### Persona Drift (agents lose their personality)
- **Cause:** Inherent to multi-turn LLM conversations; larger models drift MORE
- **Detection:** Persona consistency score declining over rounds, drift slope metric
- **Mitigation:** Re-inject persona definition every N rounds, shorter simulation windows, memory summaries that reinforce persona
- Source: https://arxiv.org/html/2402.10962v1

#### Unrealistic Engagement Patterns
- **Cause:** LLM agents tend to all engage at similar rates (uniform distribution)
- **Detection:** Gini coefficient < 0.3, no power law in engagement
- **Mitigation:** Willingness scoring (already planned), activity budgets per agent, explicit lurker personas

#### Hallucination / Factual Errors
- **Cause:** LLMs generate plausible-sounding but incorrect statements
- **Detection:** Fact-checking against stimulus content, contradiction detection
- **Mitigation:** Ground agent knowledge explicitly, limit agent "knowledge" to what they could plausibly know

#### Echo Chamber Formation (too fast)
- **Cause:** Agents reinforcing each other without external information injection
- **Detection:** Decreasing opinion entropy over rounds, network homophily increasing
- **Mitigation:** Introduce "news events" or external information at intervals, diverse feed algorithms

### 5. A/B and Retrospective Validation Strategy

#### Retrospective Validation (Most Feasible for MVP)

**Approach:** Simulate past public events and compare to actual social media reactions.

**Steps:**
1. Select 10-20 well-documented PR events/crises with known outcomes
2. Input only the original stimulus (press release, statement, etc.)
3. Run simulation with a representative population
4. Compare simulation outputs to actual social media data

**Comparison metrics:**
- Sentiment distribution correlation (Pearson r)
- Top-N theme overlap (Jaccard similarity)
- Engagement distribution shape (KL divergence)
- Timeline of reaction phases (awareness -> discussion -> opinion formation)
- Presence of key counter-narratives that actually emerged

**Validation dataset candidates:**
- Major corporate crises (data breaches, product recalls)
- Controversial advertising campaigns
- CEO statements during social movements
- Sustainability pledges / greenwashing accusations
- Product launches with mixed reception

**Important:** Don't cherry-pick validations. Pre-register the events and metrics before running simulations.

Source: https://www.jasss.org/27/1/11.html

#### Prospective Validation (Phase 2)

**Approach:** Run simulation BEFORE a real event, then compare to actual outcomes.

**Steps:**
1. Partner with PR agencies doing real campaigns
2. Run simulation on draft communications before publication
3. After publication, compare simulation predictions vs actual reaction
4. Track prediction accuracy over time

**This is the gold standard** but requires customer partnership and patience.

#### Calibration Dataset Strategy

Build a "Golden Dataset" incrementally:
1. **Scraped historical data:** Public reactions to 50+ corporate communications (Twitter/X, LinkedIn)
2. **Annotated ground truth:** Sentiment labels, theme tags, engagement metrics
3. **Simulation outputs:** Store every simulation result with parameters
4. **Continuous calibration:** Re-run against golden dataset after each engine change

### 6. Production Quality Assurance System

#### Per-Simulation Quality Score

Every simulation should produce an automated quality report:

```python
from pydantic import BaseModel

class SimulationQualityReport(BaseModel):
    """Automated quality assessment for each simulation run."""

    # Overall
    overall_score: float  # 0-1 weighted average
    passed: bool  # meets minimum thresholds
    warnings: list[str]

    # Individual metrics
    opinion_diversity: float  # normalized Shannon entropy
    engagement_realism: float  # power law fit score
    content_uniqueness: float  # 1 - repetition score
    persona_consistency: float  # mean across agents
    network_realism: float  # clustering coefficient score
    narrative_emergence: bool  # did new themes develop?

    # Red flags
    mode_collapse_detected: bool
    sycophancy_detected: bool
    persona_drift_detected: bool

    # Detailed breakdowns
    sentiment_distribution: dict[str, float]
    engagement_gini: float
    top_themes: list[str]
    agent_consistency_scores: dict[str, float]


class QualityThresholds(BaseModel):
    """Minimum thresholds for a valid simulation."""

    min_opinion_diversity: float = 0.4  # normalized entropy
    min_content_uniqueness: float = 0.3  # unique trigram ratio
    min_persona_consistency: float = 0.6  # mean score
    max_pairwise_similarity: float = 0.7  # semantic similarity
    min_engagement_gini: float = 0.3  # engagement inequality
    max_engagement_gini: float = 0.95
    min_active_agents_pct: float = 0.15  # at least 15% of agents should post
    max_active_agents_pct: float = 0.85  # not everyone should post
```

#### Quality Gate System

```
Simulation Complete
        |
        v
[Run Quality Metrics]
        |
        v
  Score >= 0.6? ----No----> [Flag as LOW QUALITY]
        |                        |
       Yes                       v
        |              [Auto-retry with different seed?]
        v                        |
  Any CRITICAL? ----Yes--> [Flag + notify team]
        |
       No
        |
        v
  [Deliver results to user with quality badge]

Quality Badges:
- GREEN (>0.8): High confidence results
- YELLOW (0.6-0.8): Acceptable, some caveats noted
- RED (<0.6): Low confidence, interpret with caution
```

#### Monitoring Dashboard Metrics (Aggregate)

Track across all simulations over time:
- **Mean quality score** per day/week
- **Failure rate** (simulations below threshold)
- **Common failure modes** (which metric fails most?)
- **Quality by topic** (some topics harder to simulate?)
- **Quality by population size** (100 vs 500 agents)
- **Drift detection** (is quality degrading over time due to model changes?)

#### Automated Alerts

```python
ALERT_CONDITIONS = {
    "mode_collapse_spike": "More than 20% of simulations in last 24h show mode collapse",
    "persona_drift_increase": "Mean persona consistency dropped >10% from last week",
    "quality_degradation": "Rolling 7-day mean quality score dropped below 0.7",
    "model_change_impact": "Quality metrics shifted >15% after LLM provider/model update",
}
```

### 7. Realism Indicators: What Makes Simulations Look Real vs Fake

**Indicators of realistic simulated discussions:**
- Post length follows log-normal distribution (most short, some long)
- Not everyone responds (lurker majority: 90-9-1 rule)
- Some agents change their mind; some never do
- Counter-arguments emerge organically
- Emotional tone varies (not uniformly rational or uniformly emotional)
- Some posts are tangential or off-topic
- Engagement inequality (few viral, many ignored)
- Reply chains of varying depth (not all single-level)
- Temporal patterns (early reactions differ from later ones)

**Indicators of fake/unrealistic simulation:**
- All posts are similar length
- Every agent participates equally
- Universal agreement or disagreement
- Overly polished language (no typos, no informal speech)
- No tangential or off-topic contributions
- Flat engagement distribution
- No narrative development over time
- All replies are direct (no nested discussions)
- Sycophantic tone / excessive politeness

**LLM-generated text detection research shows:**
- Humans perform poorly at identifying LLM-generated social media posts
- Key tell: LLM text lacks diversity in sentence structure and vocabulary range
- Synthetic posts collectively lack topic connectivity and realistic interaction patterns even when individual posts appear realistic
- Source: https://arxiv.org/html/2409.06653v1

### 8. Recommended Implementation Priority

**Phase 1 (MVP - implement now):**
1. Shannon entropy of sentiment distribution (cheap, fast, catches mode collapse)
2. Content repetition score (unique trigram ratio - no external dependencies)
3. Engagement Gini coefficient (simple, validates power law)
4. Per-simulation quality report (Pydantic model, store in DB)
5. Quality badge on results (GREEN/YELLOW/RED)

**Phase 2 (Post-launch, with data):**
6. Persona consistency scoring via LLM judge (expensive but critical)
7. Retrospective validation against 10 historical events
8. Network clustering metrics
9. Pairwise semantic similarity (needs embedding model)
10. Narrative emergence detection

**Phase 3 (Growth, with customer data):**
11. Prospective validation with customer partnerships
12. Golden dataset calibration pipeline
13. Automated quality monitoring dashboard
14. A/B testing framework (different engine parameters)
15. Quality-based auto-retry system

### Key Sources
- Validation challenges review: https://pmc.ncbi.nlm.nih.gov/articles/PMC12627210/
- ELEPHANT sycophancy framework: https://arxiv.org/html/2505.13995v1
- Persona drift measurement: https://arxiv.org/html/2402.10962v1
- Verbalized sampling for diversity: https://arxiv.org/html/2510.01171v1
- Power law in social media: https://ideas.repec.org/p/wai/econwp/22-07.html
- ABM validation methods overview: https://www.jasss.org/27/1/11.html
- LLM text detection survey: https://direct.mit.edu/coli/article/51/1/275/127462/
- Human perception of LLM text: https://arxiv.org/html/2409.06653v1
- Socialtrait: https://www.socialtrait.com/
- Artificial Societies: https://societies.io/
- Stanford generative agents validation: https://news.stanford.edu/stories/2025/07/ai-social-science-research-simulated-human-subjects
- Audience simulation accuracy: https://research.aimultiple.com/audience-simulation/
- Anthropic agent evals: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Shannon entropy for diversity: https://onlinelibrary.wiley.com/doi/10.1155/2017/8715605

## Social Network Graph Generation Research (2026-04-05)

### 1. Real Social Network Properties

#### Degree Distribution (Power Law)
- Social networks follow power-law degree distributions: P(k) ~ k^(-gamma)
- Typical gamma for social networks: **2.0 to 3.0**
- Twitter follower distribution: gamma ~ **2.1 to 2.2** (empirically measured across multiple studies)
- LinkedIn: less extreme power-law, gamma ~ **2.5 to 3.0** (more uniform due to reciprocal connections)
- Median Twitter followers: ~1 (extreme skew; most users have very few followers)
- Key insight: roughly two-thirds of large-scale empirical networks exhibit power-law tail behavior

#### Clustering Coefficient
- Twitter: **0.14 to 0.75** depending on community subset (overall ~0.30)
  - ~10^5 times higher than equivalent random networks
- LinkedIn: higher clustering within professional/industry clusters (~0.3-0.5)
- Real social networks: typically **0.1 to 0.5**, much higher than random graphs
- Clustering coefficient decreases as node degree increases (also follows power law)

#### Average Path Length
- Twitter: ~**4.1 to 7.3** (varies by study and subgraph)
- Flickr: ~5.67
- General social networks: **4 to 7** ("six degrees of separation")
- Small-world property: avg path length scales as O(log N)

#### Community Structure
- Real networks have strong modular/community structure
- Community sizes also follow power law distribution
- For N=10,000 nodes: typically 10-50 meaningful communities
- For N=50,000 nodes: typically 50-200 communities
- Community size exponent (tau2): typically 1.0 to 2.0

### 2. Graph Generation Algorithms Comparison

#### Barabasi-Albert (Preferential Attachment)
- Produces: power-law degree distribution
- Missing: no community structure, low clustering coefficient
- NetworkX: `nx.barabasi_albert_graph(n, m)`
- Fast generation, simple parameters
- Good for: quick prototype, influencer hub structure
- Bad for: realistic community structure

#### Watts-Strogatz (Small World)
- Produces: high clustering, short path lengths
- Missing: no power-law degree distribution, no community structure
- NetworkX: `nx.watts_strogatz_graph(n, k, p)`
- Good for: modeling clustering and small-world properties
- Bad for: realistic degree distribution

#### Stochastic Block Model (SBM)
- Produces: explicit community structure with tunable inter/intra-community edge probabilities
- Missing: no power-law degree distribution (uniform within blocks)
- NetworkX: `nx.stochastic_block_model(sizes, probs)`
- Good for: testing community-dependent behavior
- Bad for: realistic degree heterogeneity

#### LFR Benchmark (RECOMMENDED for Swaarm)
- Produces: power-law degree distribution AND community structure simultaneously
- Parameters: tau1 (degree exponent), tau2 (community size exponent), mu (mixing parameter)
- NetworkX: `nx.generators.community.LFR_benchmark_graph(n, tau1, tau2, mu, ...)`
- Each node gets a 'community' attribute automatically
- Best match for realistic social network simulation
- Limitation: undirected only in networkx; parameter tuning can be finicky

### 3. Recommended Approach for Swaarm

#### Primary: LFR Benchmark Graph

```python
import networkx as nx
from networkx.generators.community import LFR_benchmark_graph

def generate_social_graph(
    n: int,
    platform: str = "public",  # "public" (Twitter-like) or "professional" (LinkedIn-like)
    seed: int | None = None,
) -> nx.Graph:
    """Generate a realistic social network graph with community structure."""

    if platform == "public":
        # Twitter-like: steeper power law, more hubs, lower mixing
        tau1 = 2.1    # degree distribution exponent (Twitter empirical)
        tau2 = 1.5    # community size distribution exponent
        mu = 0.15     # 15% inter-community edges (tight communities)
        avg_degree = 8
        min_community = max(20, n // 100)
        max_community = max(200, n // 10)
    else:
        # LinkedIn-like: gentler power law, more clustering, higher mixing
        tau1 = 2.7    # less extreme degree distribution
        tau2 = 1.8    # more uniform community sizes
        mu = 0.25     # 25% inter-community edges (more cross-industry)
        avg_degree = 12
        min_community = max(30, n // 80)
        max_community = max(300, n // 8)

    G = LFR_benchmark_graph(
        n=n,
        tau1=tau1,
        tau2=tau2,
        mu=mu,
        average_degree=avg_degree,
        min_community=min_community,
        max_community=max_community,
        seed=seed,
    )

    return G
```

#### Post-Processing: Add Influencer Hubs and Bridge Nodes

```python
def add_influencer_hubs(G: nx.Graph, n_influencers: int = 5, extra_edges: int = 50) -> None:
    """Boost top-degree nodes to create realistic influencer hubs that bridge communities."""
    communities = {frozenset(G.nodes[v]["community"]) for v in G}
    community_list = list(communities)

    # Find top-degree nodes (natural hubs from preferential attachment)
    top_nodes = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)[:n_influencers]

    for hub in top_nodes:
        # Connect hub to random nodes in OTHER communities
        hub_community = G.nodes[hub]["community"]
        other_communities = [c for c in community_list if c != hub_community]

        for _ in range(extra_edges):
            target_community = random.choice(other_communities)
            target_node = random.choice(list(target_community))
            if not G.has_edge(hub, target_node):
                G.add_edge(hub, target_node)


def add_weak_ties(G: nx.Graph, fraction: float = 0.02) -> None:
    """Add Granovetter-style weak ties (bridges) between communities."""
    communities = {frozenset(G.nodes[v]["community"]) for v in G}
    community_list = list(communities)
    n_bridges = int(G.number_of_edges() * fraction)

    for _ in range(n_bridges):
        c1, c2 = random.sample(community_list, 2)
        n1 = random.choice(list(c1))
        n2 = random.choice(list(c2))
        if not G.has_edge(n1, n2):
            G.add_edge(n1, n2)
```

#### For Directed Graphs (Twitter-like follow relationships)

```python
def to_directed_social_graph(G: nx.Graph) -> nx.DiGraph:
    """Convert undirected LFR graph to directed (follow) graph.

    Strategy: each undirected edge becomes one or two directed edges.
    Higher-degree nodes are more likely to be followed (not following back).
    """
    DG = nx.DiGraph()
    DG.add_nodes_from(G.nodes(data=True))

    max_degree = max(dict(G.degree()).values())

    for u, v in G.edges():
        deg_u = G.degree(u)
        deg_v = G.degree(v)

        # Higher degree node is less likely to follow back
        # P(u follows v) proportional to v's degree
        p_u_follows_v = deg_v / max_degree
        p_v_follows_u = deg_u / max_degree

        if random.random() < p_u_follows_v:
            DG.add_edge(u, v)  # u follows v
        if random.random() < p_v_follows_u:
            DG.add_edge(v, u)  # v follows u

        # Ensure at least one direction exists
        if not DG.has_edge(u, v) and not DG.has_edge(v, u):
            if deg_v > deg_u:
                DG.add_edge(u, v)
            else:
                DG.add_edge(v, u)

    return DG
```

### 4. Platform Parameterization Differences

| Property | Public Network (Twitter-like) | Professional Network (LinkedIn-like) |
|---|---|---|
| Edge type | Directed (follow) | Undirected (connection) |
| Power-law exponent (tau1) | 2.1 | 2.7 |
| Average degree | 5-10 | 10-20 |
| Clustering coefficient | 0.15-0.30 | 0.30-0.50 |
| Mixing parameter (mu) | 0.10-0.20 | 0.20-0.35 |
| Community basis | Interest/topic | Industry/company |
| Influencer hubs | Extreme (10k+ followers) | Moderate (500-2000 connections) |
| Reciprocity | Low (~20%) | High (~90%) |

### 5. Scaling and Performance

#### NetworkX (pure Python)
- 1,000 nodes: <1 second (LFR generation)
- 10,000 nodes: ~5-30 seconds (LFR, depends on parameters)
- 50,000 nodes: ~2-15 minutes (LFR, can be slow/fail with tight parameters)
- Memory: ~50-200 MB for 50K node graph with attributes
- NetworkX stores graphs as dicts-of-dicts, high memory overhead per edge

#### igraph (C-based, Python wrapper)
- 10-100x faster than networkx for graph algorithms (PageRank, shortest path, etc.)
- Does NOT have a built-in LFR generator (would need external C LFR binary)
- Better for: running analysis after generation
- Memory: significantly more compact than networkx

#### Recommended Strategy for Swaarm
1. Use **networkx LFR_benchmark_graph** for generation (convenience, built-in community labels)
2. For N <= 10,000: networkx is fine for everything (generation + simulation queries)
3. For N > 10,000: generate with networkx, optionally convert to igraph for neighbor lookups during simulation
4. Pre-generate and cache graphs: generate once, pickle/serialize, reuse across simulation ticks
5. Consider **igraph** if neighbor-query performance becomes bottleneck during simulation loop

```python
# Conversion between networkx and igraph
import igraph as ig

def nx_to_igraph(G: nx.Graph) -> ig.Graph:
    """Convert networkx graph to igraph for faster algorithms."""
    mapping = {node: idx for idx, node in enumerate(G.nodes())}
    edges = [(mapping[u], mapping[v]) for u, v in G.edges()]

    ig_graph = ig.Graph(n=G.number_of_nodes(), edges=edges, directed=G.is_directed())

    # Transfer node attributes
    for attr in list(G.nodes[list(G.nodes())[0]].keys()):
        ig_graph.vs[attr] = [G.nodes[n].get(attr) for n in G.nodes()]

    return ig_graph, mapping
```

### 6. Validation Checklist

After generating a graph, verify these properties match empirical targets:

```python
def validate_graph(G: nx.Graph, platform: str = "public") -> dict:
    """Validate that generated graph has realistic social network properties."""
    n = G.number_of_nodes()
    m = G.number_of_edges()
    degrees = [d for _, d in G.degree()]

    stats = {
        "nodes": n,
        "edges": m,
        "avg_degree": sum(degrees) / n,
        "max_degree": max(degrees),
        "density": nx.density(G),
        "n_communities": len({frozenset(G.nodes[v]["community"]) for v in G}),
    }

    # Clustering (sample for large graphs)
    if n <= 10000:
        stats["avg_clustering"] = nx.average_clustering(G)
    else:
        sample = random.sample(list(G.nodes()), 1000)
        stats["avg_clustering"] = nx.average_clustering(G, nodes=sample)

    # Connected components
    if not G.is_directed():
        stats["n_components"] = nx.number_connected_components(G)
        largest_cc = max(nx.connected_components(G), key=len)
        stats["largest_component_fraction"] = len(largest_cc) / n

    return stats
```

### 7. Key References
- Scale-free networks: https://en.wikipedia.org/wiki/Scale-free_network
- LFR benchmark: https://networkx.org/documentation/stable/reference/generated/networkx.generators.community.LFR_benchmark_graph.html
- Twitter power-law exponents: https://www.johndcook.com/blog/2022/08/09/twitter-follower-distribution/
- Twitter small-world: https://arxiv.org/pdf/1508.03594
- SBM in networkx: https://networkx.org/documentation/stable/reference/generated/networkx.generators.community.stochastic_block_model.html
- Graph library benchmarks: https://www.timlrx.com/blog/benchmark-of-popular-graph-network-packages-v2/
- Power-law origins in social networks: https://www.nature.com/articles/srep01783
- Twitter degree distribution study: https://www.ece.ucdavis.edu/~chuah/rubinet/people/chuah/classes/eec273/eec273-s14/refs/%5BKL+10%5Dwww-twitter.pdf
