# Applied Generative AI and Agentic AI Systems Knowledge Assessment

**Assessed individual:** John Barksdale  
**Professional context:** Software Verification Engineer and AI Champion  
**Assessment focus:** Applied Generative AI and Agentic AI Systems, including LLMs, prompt engineering, AI agents, memory and context management, retrieval, evaluation, observability, security, and workflow automation  
**Assessment date:** September 2026

---

## Executive Summary

This assessment indicates that John is a **strong agentic workflow engineer and competent Applied AI practitioner who is approaching the advanced-practitioner level**. His strongest capabilities are workflow design, software-engineering integration, deterministic automation, human-in-the-loop controls, auditability, and multi-agent architecture. His largest gaps are retrieval-augmented generation (RAG), formal AI evaluation science, model and tool-routing decision frameworks, AI-specific observability, and AI-native production failure analysis.

The original score was **19.5 out of 30**. That score should not be interpreted as evenly distributed capability. Several answers demonstrated advanced or near-expert systems-engineering instincts, while a few AI-specific areas remain underdeveloped.

### Overall grade

- **Score:** 19.5/30, or 65%
- **Level:** Competent practitioner approaching advanced practitioner
- **Best current description:** Applied AI and Agentic Systems Practitioner
- **Strongest specialization:** Agentic workflow engineering and AI-assisted software-engineering automation
- **Primary path toward AI Systems Architect:** Retrieval, hybrid local/cloud LLM architecture, AI evaluation, and observability

### Scoring scale

- **0:** Does not yet understand the area
- **1:** Has basic conceptual familiarity
- **2:** Can explain and apply the concept
- **3:** Can design a solution and defend its tradeoffs

---

# Detailed Assessment

## Question 1: Context Window vs. Memory

### Question

A coworker says:

> “Our model has a 200K-token context window, so we do not need memory.”

How would you respond? Discuss context versus memory, short-term versus long-term memory, retrieval, cost, and why larger context windows do not eliminate memory architectures.

### John's answer

Context windows and memory systems serve different functions. John compared a context window to RAM and a memory system to persistent storage. The context window is the model's working set for the current task, while memory preserves useful information across sessions, such as project history and prior decisions. Retrieval tools can select relevant stored information as needed so the system does not have to load everything into the active context window.

### Grade

**3/3**

### Assessment

This answer correctly distinguished active context from persistent memory and recognized the importance of selective retrieval. The RAM analogy is useful, although “persistent storage” is more technically precise than ROM because practical memory systems are writable and continually updated.

### Takeaways

- Strong conceptual distinction between context and persistent memory
- Understands retrieval as a way to manage limited working context
- Understands cross-session continuity
- Future growth area: token economics, context degradation, memory write policies, consolidation, conflict resolution, and retrieval quality

---

## Question 2: RAG Failure Analysis

### Question

An agent uses RAG and keeps producing incorrect answers even though it retrieves documents from the correct SharePoint site. Describe a systematic debugging approach covering retrieval quality, chunking, embeddings, reranking, prompt design, grounding verification, and evaluation metrics.

### John's answer

John identified RAG as a current knowledge gap and stated that he does not actively design or use RAG systems. His repeatable processes currently rely more heavily on skills with distinctive names and descriptions so the correct skill is selected when needed.

### Grade

**0.5/3**

### Assessment

The answer was candid and correctly recognized that skill discovery is a form of retrieval and routing, but it did not address the RAG pipeline itself. This is the clearest technical gap in the assessment.

### Takeaways

Knowledge to develop:

- Embeddings and semantic similarity
- Keyword, vector, and hybrid retrieval
- Chunk size, overlap, boundaries, and metadata
- Query rewriting and decomposition
- Candidate recall and top-k selection
- Cross-encoder or LLM-based reranking
- Context assembly and citation grounding
- Retrieval evaluation separately from answer-generation evaluation
- Precision, recall, mean reciprocal rank, normalized discounted cumulative gain, groundedness, faithfulness, and answer relevance

---

## Question 3: Tool-Use Architecture

### Question

An agent has access to Azure DevOps, Git, Jira, Outlook, and SharePoint. How should it decide when to answer directly, search, call a tool, or ask a follow-up question?

### John's answer

John proposed domain-based routing:

- Answer directly for general knowledge
- Use Git and Azure DevOps or Jira for code-related work
- Use Jira or Azure DevOps for tasks
- Use SharePoint for documents
- Use Outlook for conversations or email notifications

### Grade

**1.5/3**

### Assessment

The answer demonstrates practical source awareness but is primarily a source-to-topic lookup table. A production agent also needs a policy governing freshness, authority, ambiguity, side effects, permissions, confidence, cost, and escalation.

### Takeaways

A stronger decision framework should ask:

1. Can the request be answered reliably from current context?
2. Is current, user-specific, or enterprise information required?
3. Which source is authoritative for the requested fact or action?
4. Is retrieval sufficient, or is a state-changing tool call required?
5. Are identity, permissions, and approval requirements satisfied?
6. Is ambiguity material enough to require clarification?
7. What confidence threshold requires escalation to a human?
8. What evidence and audit trail must be retained?

---

## Question 4: Multi-Agent Systems

### Question

A team proposes replacing one AI agent with ten specialized agents. What benefits and risks would you raise, including coordination overhead, latency, error propagation, cost, evaluation complexity, and human oversight?

### John's answer

John noted that multi-agent systems require greater oversight and intentional orchestration. He identified the need for a routing or orchestration agent, explicit system flow, output evaluation for each worker, and human checkpoints. He also identified agent loops as a token-cost risk and explained that an early uncaught error can cascade through downstream stages. He suggested packaging repeated deterministic work into skills or scripts.

### Grade

**2.5/3**

### Assessment

This was one of the strongest answers. It demonstrated practical understanding of cascading failures, coordination, evaluation, and the value of making repeatable operations deterministic.

### Takeaways

- Strong grasp of orchestration and error propagation
- Strong instinct to separate reasoning from deterministic execution
- Understands human approval and evaluation needs
- Future growth area: when a single agent with tools is preferable, shared-state design, idempotency, concurrency, termination conditions, compensation logic, and end-to-end versus per-agent evaluation

---

## Question 5: Limits of Prompt Engineering

### Question

Explain what prompt engineering solves, what it cannot solve, when architecture changes are needed, and when fine-tuning might be justified.

### John's answer

John described prompt engineering as foundational but insufficient by itself. Good prompts help identify the correct context, purpose, and output, but they do not create persistent memory, external-system integration, auditable repeatable processes, or multi-agent orchestration. System behavior also depends heavily on available tools, skills, scripts, and MCP integrations.

### Grade

**3/3**

### Assessment

This answer demonstrated mature understanding. John does not treat prompting as a substitute for architecture and correctly identifies tools, memory, workflows, and deterministic components as separate system concerns.

### Takeaways

- Strong prompt-engineering maturity
- Correctly treats prompting as one layer of a larger system
- Future refinement: explicitly distinguish prompt problems from data, retrieval, capability, policy, model, and evaluation problems
- Learn practical decision criteria for prompting versus RAG versus tools versus fine-tuning

---

## Question 6: Agent Reliability

### Question

A backlog-generation agent reads requirements, creates features and user stories, and opens Azure DevOps work items. Management asks how the organization knows it is reliable. Design an evaluation strategy covering offline evaluation, human review, metrics, regression testing, failure modes, and monitoring.

### John's answer

John applied standard software-engineering discipline: happy-path and edge-case evaluation suites, human-review gates, operational metrics, regression automation, model-change testing, and ongoing human spot checks.

### Grade

**2/3**

### Assessment

The engineering foundation is strong, but the answer did not define AI-specific metrics, datasets, rubrics, baseline comparisons, statistical treatment, or trace-level diagnosis.

### Takeaways

Add the following:

- Golden datasets and representative scenario suites
- Requirement-to-feature and feature-to-story traceability
- Completeness, correctness, duplication, ambiguity, and testability rubrics
- Pairwise comparison against a baseline
- Human agreement and adjudication procedures
- Confidence intervals and repeated-run variance
- Safety and permission tests for work-item creation
- Production drift, failure taxonomy, cost, latency, and approval-rejection rates
- Separate evaluation of retrieval, reasoning, output quality, and tool execution

---

## Question 7: Guardrails and Safety

### Question

An enterprise agent can access source code, customer data, and internal documents. What guardrails are needed for prompt injection, data exfiltration, tool permissions, identity, auditability, and human approvals?

### John's answer

John emphasized deterministic skills backed by scripts, test environments without sensitive data, CI/CD controls, source control, pull-request review, restricted tool permissions, protected MCP endpoints, auditable Markdown and scripts, detailed logs, continuous improvement, and narrowly scoped application credentials rather than personal credentials.

### Grade

**2/3**

### Assessment

The answer showed strong DevSecOps instincts, particularly around least privilege, test environments, source control, and auditability. It did not directly cover all AI-specific threats, especially prompt injection, untrusted retrieved content, data-flow controls, output filtering, and secret handling.

### Takeaways

Add explicit controls for:

- Treating retrieved content and tool output as untrusted data
- Separating instructions from retrieved content
- Prompt-injection detection and resistant tool policies
- Data-loss-prevention and egress restrictions
- Tenant and user authorization checks at execution time
- Secret vaulting, rotation, expiration monitoring, and revocation
- Tool allowlists, parameter validation, and transaction limits
- Approval gates based on action risk
- Immutable audit logs and correlation IDs
- Red-team scenarios for exfiltration and privilege escalation

---

## Question 8: Agentic Workflow Design

### Question

For the workflow Requirements Document → Feature → User Stories → Test Cases → Pull Request Review, choose one large agent, sequential workflow, event-driven workflow, or multi-agent architecture, and defend the choice.

### John's answer

John chose a multi-agent architecture. He proposed a requirements agent for decomposition into features, stories, and test cases; a separate pull-request review agent with different instructions and preferably a different model from the coding agent; plus coding and testing agents. He noted that separation improves specialization, change isolation, logging, metrics, and per-function evaluation.

### Grade

**2.5/3**

### Assessment

The answer was architecturally strong and aligned with John's practical experience. The main opportunity is to distinguish logical roles from separately deployed agents. Some roles may be implemented as deterministic workflow stages, skills, or tools rather than autonomous agents.

### Takeaways

- Strong decomposition and separation-of-concerns thinking
- Good awareness of model diversity and independent review
- Future growth area: use the least autonomous component that can reliably perform each stage
- Add explicit state contracts, acceptance criteria, retry behavior, idempotency, failure recovery, and stop conditions

---

## Question 9: LLM Evaluation

### Question

A team claims that one LLM is better than another. How would you verify the claim using benchmarks, real-world tasks, cost, latency, reliability, and statistical significance?

### John's answer

John proposed reusable tests that can be run across models, covering documentation, coding, complex tasks, single-agent workflows, and multi-agent workflows. He would use a grading rubric and produce a comparative report. He acknowledged that he does not yet maintain a personal evaluation suite and currently relies partly on industry experts.

### Grade

**1.5/3**

### Assessment

The answer has the correct overall structure but needs greater rigor. “Better” must be defined relative to a specific task distribution and constraints. Model evaluation also needs repeated trials, blinded grading where possible, cost and latency normalization, baseline comparisons, and uncertainty estimates.

### Takeaways

Learn to design:

- Task-specific benchmark suites
- Representative and adversarial datasets
- Deterministic and rubric-based graders
- Pairwise and blind comparisons
- LLM-as-judge with human calibration
- Pass-at-k and repeated-run reliability measures
- Confidence intervals and significance testing
- Quality-cost-latency tradeoff analysis
- Model-routing policies based on task class
- Regression gates for model or prompt changes

---

## Question 10: Production Failure Analysis

### Question

For a system containing an LLM, vector database, long-term memory, tool calling, planner, multi-agent execution, and human approvals, identify the three most likely production failures. For each, explain cause, detection, and mitigation.

### John's answer

John identified:

1. Humans fail to review approvals, leaving work gated.
2. Tool credentials expire or are revoked and the failure is detected too slowly.
3. The multi-agent workflow deviates from the orchestrated path and becomes lost.

### Grade

**1/3**

### Assessment

All three are legitimate operational failures, particularly approval bottlenecks and credential lifecycle problems. However, the answer missed several AI-native silent-failure modes that can produce plausible but incorrect results.

### Takeaways

Important additional failure modes include:

- Incorrect retrieval contaminates downstream reasoning
- A plausible but incorrect plan propagates through the workflow
- The system optimizes a proxy metric rather than the business objective
- Long-term memory stores incorrect, stale, or conflicting information
- Prompt injection manipulates tool use
- Tool output is misinterpreted despite successful execution
- Model or data drift degrades performance gradually
- Per-agent components pass while the end-to-end workflow fails

For every failure mode, define:

- Trigger or root cause
- Observable signals
- Detection latency
- Containment boundary
- Recovery or compensation action
- Regression test
- Owner and escalation route

---

# Scorecard

| Question | Area | Score |
|---:|---|---:|
| 1 | Context and memory | 3.0/3 |
| 2 | RAG | 0.5/3 |
| 3 | Tool-use decision architecture | 1.5/3 |
| 4 | Multi-agent systems | 2.5/3 |
| 5 | Prompt-engineering limits | 3.0/3 |
| 6 | Reliability and evaluation | 2.0/3 |
| 7 | Guardrails and safety | 2.0/3 |
| 8 | Workflow architecture | 2.5/3 |
| 9 | LLM evaluation | 1.5/3 |
| 10 | Production failure analysis | 1.0/3 |
|  | **Total** | **19.5/30** |

---

# Primary Strengths

## 1. Agentic workflow engineering

John naturally decomposes complex work into stages, assigns clear responsibilities, and considers routing, review, and failure propagation.

## 2. Software-engineering integration

He consistently connects AI systems to testing, source control, pull requests, CI/CD, scripts, permissions, and repeatable automation.

## 3. Deterministic execution where possible

John's instinct is to use AI for judgment and flexible reasoning while moving repeated operations into testable skills or scripts. This is a strong enterprise architecture principle.

## 4. Human oversight and auditability

He recognizes that autonomous systems require checkpoints, logs, scoped authority, and reviewable artifacts.

## 5. Mature view of prompt engineering

He understands that better prompts cannot compensate for missing retrieval, memory, tools, security controls, or workflow architecture.

---

# Principal Gaps

## 1. Retrieval systems

The largest gap is understanding and debugging the complete RAG pipeline rather than retrieval only as skill or tool selection.

## 2. AI evaluation science

John already has the verification mindset, but needs AI-specific metrics, experimental design, judge calibration, repeated-run analysis, and quality-cost-latency comparisons.

## 3. AI-specific failure analysis

Operational failures are recognized well. Additional depth is needed in silent semantic failures such as bad retrieval, incorrect planning, metric gaming, stale memory, and plausible but ungrounded output.

## 4. Formal tool and model routing

Current routing is primarily based on which system owns a kind of information. A stronger architecture considers authority, freshness, confidence, permissions, cost, latency, side effects, and escalation.

## 5. Observability

Logging is already valued, but agent traces, spans, prompt and tool lineage, token analytics, cost attribution, and semantic failure telemetry need further study.

---

# Highest-Value Learning Priorities

The ordering below is tailored to John's current strengths, gaps, professional responsibilities, interest in local models, and goal of moving toward AI systems architecture.

## 1. Retrieval-Augmented Generation and Retrieval Architecture

**Why it ranks first:** It is the largest identified gap and is foundational to enterprise assistants, grounded agents, document intelligence, memory retrieval, and local knowledge systems.

### Core topics

- Embeddings and embedding-model selection
- Vector similarity and indexing concepts
- Vector databases
- Keyword, semantic, and hybrid search
- Chunking by tokens, structure, meaning, and document type
- Metadata extraction and filtering
- Query rewriting, expansion, and decomposition
- Candidate generation and top-k tuning
- Reranking
- Context construction and citation grounding
- Retrieval evaluation versus answer evaluation
- Graph RAG and agentic retrieval after fundamentals

### Suggested practical outcome

Build a small RAG system over a bounded set of technical documents, create a labeled query set, measure retrieval before and after reranking, and evaluate whether quality gains justify latency and complexity.

---

## 2. Hybrid Local and Cloud LLM Architectures

**Why it ranks second:** It aligns strongly with John's Python, Docker, privacy, automation, and agent interests. It also connects directly to RAG, model routing, cost control, resilience, and secure enterprise architecture.

### Core topics

- Local inference using tools such as Ollama, LM Studio, vLLM, and Open WebUI
- Model formats and serving interfaces
- Quantization and quality-performance tradeoffs
- CPU, GPU, RAM, and VRAM constraints
- Throughput, tokens per second, time to first token, and concurrency
- Context-window behavior and memory pressure
- Local embedding and reranking models
- Privacy-aware and cost-aware model routing
- Cloud fallback and graceful degradation
- Structured-output and function-calling compatibility
- Model capability profiling by task
- Local RAG
- Offline and disconnected workflows
- Security boundaries between local and cloud execution

### Suggested practical outcome

Create a router that sends low-risk classification, extraction, or summarization tasks to a local model and sends high-complexity reasoning to a cloud model. Evaluate quality, latency, cost, and privacy tradeoffs using the same test set.

---

## 3. AI Evaluation and Quality Engineering

**Why it ranks third:** This is the learning area most likely to become John's differentiating specialty because it builds directly on his verification experience.

### Core topics

- Golden datasets and scenario selection
- Groundedness, faithfulness, relevance, and completeness
- Retrieval precision and recall
- Pairwise comparisons and win rates
- LLM-as-judge design and calibration
- Human annotation and inter-rater agreement
- Repeated-run variance and statistical confidence
- Regression testing for prompts, models, tools, and retrieval changes
- Safety, security, and policy evaluations
- End-to-end versus component-level evaluation
- Quality-cost-latency optimization
- Benchmark leakage and overfitting
- Online monitoring and feedback loops

### Suggested practical outcome

Build a reusable Python evaluation harness that can compare local and cloud LLMs, prompt versions, and RAG configurations against a version-controlled scenario set and rubric.

---

## 4. Agent Observability and Production Operations

**Why it ranks fourth:** John already values logging and auditability. Formal observability would turn those instincts into a production diagnostic capability.

### Core topics

- Traces and spans
- Agent, model, retrieval, and tool-call lineage
- Correlation and run identifiers
- Token usage and context composition
- Latency breakdown by component
- Cost attribution
- Retry, timeout, and fallback telemetry
- Semantic error taxonomies
- Approval wait time and human-intervention metrics
- Prompt and model version tracking
- Privacy-safe telemetry and redaction
- Drift and degradation detection

### Suggested practical outcome

Instrument an agent workflow so a failed run can be reconstructed from request through retrieval, planning, model calls, tool execution, approval, and final output.

---

## 5. Tool Orchestration and Workflow-Control Patterns

**Why it ranks fifth:** John is already strong conceptually. The value is in formalizing and expanding his design vocabulary and control strategies.

### Core topics

- ReAct and tool-use loops
- Planner-executor patterns
- Router-worker and orchestrator-worker patterns
- State machines and durable workflows
- Sequential, parallel, and event-driven execution
- Idempotency and compensation
- Retry and termination policies
- Structured state and handoff contracts
- Human-in-the-loop and human-on-the-loop controls
- MCP architecture and trust boundaries
- Dynamic versus deterministic planning
- Single-agent versus multi-agent selection

### Suggested practical outcome

Implement the same bounded workflow in a deterministic pipeline and an agentic planner-executor design, then compare reliability, maintainability, latency, and cost.

---

## 6. Advanced Memory Systems

**Why it ranks sixth:** John already understands the context-memory distinction. Advanced memory becomes most valuable after retrieval fundamentals are stronger.

### Core topics

- Working, semantic, episodic, procedural, and reflective memory
- Memory write policies
- Consolidation and summarization
- Retrieval and ranking
- Time decay and freshness
- Contradiction and conflict resolution
- User correction and deletion
- Provenance and confidence
- Graph-based memory
- Privacy, retention, and access control
- Preventing memory poisoning and self-reinforcing profiles

### Suggested practical outcome

Build a memory layer that stores decisions with provenance, distinguishes user statements from agent inferences, supports correction, and retrieves only relevant, authorized memories.

---

## 7. Targeted LLM Foundations and Model Engineering

**Why it ranks seventh:** John should understand LLM behavior deeply enough to make architecture and evaluation decisions, but low-level model research is not currently the highest-return path.

### Core topics

- Tokenization
- Transformer and attention concepts at an architectural level
- Training, instruction tuning, preference optimization, and inference
- Temperature, sampling, and determinism
- Context limits and context degradation
- Hallucination and calibration limits
- Structured outputs and tool calling
- Small language models versus frontier models
- Open-weight versus hosted proprietary models
- Quantization and distillation
- Fine-tuning, adapters, and when they are justified
- Model serving, batching, caching, and concurrency
- Licensing and data-governance considerations

### Depth recommendation

Target **architect-level decision competence**, not foundation-model research depth. John should be able to explain how model properties affect system design, choose an appropriate model class, evaluate alternatives, and recognize when prompting, RAG, tools, or fine-tuning is the appropriate intervention.

---

# Lower-Priority Topics for Now

These topics are useful but should generally follow the higher-value priorities unless a specific project creates an immediate need:

- Training foundation models from scratch
- Advanced transformer mathematics
- Large-scale distributed training
- Novel model architecture research
- Deep fine-tuning specialization before mastering retrieval and evaluation
- Chasing every new model release without a stable benchmark
- Graph RAG before mastering basic and hybrid retrieval
- Elaborate multi-agent architectures where a deterministic workflow is sufficient

---

# Recommended Professional Positioning

A truthful current description is:

> **Applied Generative AI and Agentic AI Systems, including LLMs, prompt engineering, AI agents, memory and context management, and workflow automation.**

A more precise LinkedIn-oriented version is:

> **Software Verification Engineer | AI Champion | Applied AI and Agentic Systems Practitioner specializing in AI-assisted software engineering, prompt engineering, agentic workflows, memory-aware systems, and workflow automation**

As retrieval, hybrid local/cloud LLMs, evaluation, and observability mature, an appropriate future positioning would be:

> **Applied AI Engineer specializing in Agentic Systems, AI Quality Engineering, and Hybrid Local/Cloud LLM Architectures**

---

# Final Takeaways

1. The claimed specialization in Applied Generative AI and Agentic AI Systems is truthful.
2. John's strongest differentiator is not low-level LLM research. It is applying AI to real engineering workflows with verification, automation, governance, and human oversight.
3. RAG is the clearest immediate knowledge gap.
4. Hybrid local/cloud LLM architecture is a high-value specialization that aligns with John's technical experience and privacy concerns.
5. AI evaluation could become John's strongest long-term differentiator because it combines his verification background with a major weakness across the AI industry.
6. Observability and AI-native failure analysis are necessary to move from successful prototypes to production-grade systems.
7. Prompt engineering is already a strength and should no longer be the primary learning investment.
8. Advanced memory should follow retrieval fundamentals because memory systems depend on good storage, selection, ranking, provenance, and update policies.
9. The learning goal should be architect-level judgment: knowing what architecture to choose, how it fails, how to test it, and how to operate it.
10. Progress should be demonstrated through applied projects, teach-back, failure analysis, and repeatable evaluation rather than course completion alone.

---

# Internal Context Used to Validate the Assessment

The assessment is primarily based on John's quiz answers and the follow-up discussion. It is also consistent with existing workplace materials showing prior focus on:

- AI Champion training involving prompt frameworks, context, verification patterns, agentic coding, and workflow automation
- Agent and skill standards, portable workflows, MCP governance, and CI-based drift prevention
- Team AI adoption, autonomy, validation, and governance
- Agentic workflow patterns, CI/CD integration, and human-in-the-loop controls

These materials reinforce that workflow automation, validation, and agentic engineering are established areas of practice, while the learning priorities above represent the highest-value next steps.
