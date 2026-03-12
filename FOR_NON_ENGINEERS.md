# What This Portfolio Does — In Plain Language
## Mario Casanova | Data Science & Analytics

> **Who this document is for:** Anyone who wants to understand what this portfolio does without needing to know Python, statistics, or software engineering. Including me on a bad Monday morning.

---

## What Is This Portfolio About?

This portfolio applies data science and statistical analysis to **enterprise technical support operations** — specifically for companies that run cloud infrastructure (servers, storage, and the software that keeps everything working inside large data centers).

Think of it as the analytical brain behind a large-scale support operation. The team this work targets watches over thousands of servers for thousands of customers worldwide.

**The problem they face:** They get hundreds of support tickets every day. Each ticket is a customer saying "something is wrong." They need to:
1. Know which ones are most urgent
2. Predict how many will come tomorrow so they can staff properly
3. Catch hardware problems *before* the customer even notices them
4. Know which tickets are about to become a big problem before it's too late

**What this portfolio does:** Demonstrates, in working code, four different ways to solve those four problems — using only statistics and Python, without needing a team of data engineers to set up a data warehouse first.

---

## The Hospital Analogy

The easiest way to understand this portfolio is to imagine a support operation as a **hospital emergency room**.

```
Support Concept              →    Hospital Equivalent
─────────────────────────────────────────────────
Support ticket               →    Patient arriving at ER
Priority (P1/P2/P3/P4)      →    Triage level (critical / urgent / semi-urgent / routine)
TTR (Time to Resolution)     →    How long until the patient is treated and discharged
SLA breach                   →    Patient waited longer than the hospital's promised wait time
NPS score                    →    Patient satisfaction survey after discharge
Escalation                   →    Patient deteriorated and needed ICU — preventable with earlier intervention
Support engineer             →    Doctor on duty
Region                       →    Hospital branch (LATAM, APAC, EMEA...)
Infrastructure telemetry     →    The hospital's vital signs monitors on each patient
Platform version             →    The medical equipment model being used (older = harder to repair)
Platform migration           →    A mass transfer of patients from another hospital
```

With that in mind, here's what each piece of the portfolio does:

---

## Layer 1: "How Is the ER Doing Right Now?" (Descriptive)

**File:** `cloud_infrastructure_support/notebooks/01_descriptive_health_monitor.ipynb`

**The question it answers:** *What is actually happening in our support operations?*

**In hospital terms:** Imagine a big screen on the wall of the hospital administration office showing: "Right now, 23% of critical patients are waiting longer than promised. The Brazil branch is performing worse than the Germany branch on urgent cases. Patient satisfaction dropped 0.3 points this month compared to last month."

**What the notebook actually produces:**

- **TTR P50 / P90 chart:** A bar chart showing two things per priority level: how long the *typical* ticket takes (P50 = median), and how long the *worst 10%* of tickets take (P90). The red dashed lines show the SLA promise. If the orange bars cross the red lines, there's a problem.

- **SLA Compliance Heatmap:** A colored grid (green = good, red = bad) showing, for each combination of region and priority tier, what percentage of tickets were resolved on time. Dark red square at "LATAM × P1"? That's where to send more engineers.

- **Backlog Aging chart:** A stacked bar chart showing how old the open tickets are. A big "dark red" section means many old, stale tickets that might be about to breach SLA.

- **NPS Trend with confidence bands:** A line showing customer satisfaction over time, with a shaded band representing the uncertainty around that average. When the band is narrow, we're confident in the number. When the band is wide, we need more survey responses.

- **Executive Summary box:** At the very end, a formatted text box summarizing the 5 most important numbers. Built for a VP who has 30 seconds.

**Why this matters:** Most support orgs do this in Excel and static dashboards. This notebook shows it can be automated, updated daily, and extended without touching the original code.

---

## Layer 2: "Why Is That Alarm Going Off?" (Diagnostic)

**File:** `cloud_infrastructure_support/notebooks/02_diagnostic_anomaly_detection.ipynb`

**The question it answers:** *Why are ticket spikes happening — and can we see them coming?*

**In hospital terms:** Every patient in the ICU is connected to monitors. A monitor beeping does not always mean a crisis — it could be the patient moving. But if the heart rate monitor shows a pattern of gradual irregularity over several hours *before* the patient crashes, a good nurse catches it early. This notebook teaches the computer to be that good nurse.

**The specific signal we watch:** `avg_io_latency_usecs` — how long (in microseconds) it takes for a server's storage to respond. Normal: 200–800 microseconds. Problem: anything above 3,000 microseconds. It's like checking whether the hospital's blood test machines are responding in under a minute or starting to lag.

**What the notebook actually produces:**

- **Fleet overview charts:** Three time series (IO latency, CPU usage, disk throughput) over 3 years for all monitored servers. You see the weekly rhythm: servers work harder on weekdays.

- **Decomposition chart:** The computer takes the IO latency signal and mathematically separates it into:
  - **Trend:** Is overall latency going up or down over months?
  - **Weekly pattern:** The predictable Monday–Friday higher load
  - **Residual:** Everything that's left after removing trend and weekly pattern — this is where anomalies hide

- **Anomaly detection chart:** The residual signal plotted with a gray band (the "normal range"). Red dots mark days where the signal jumped outside that band. Those are the days when a pre-emptive customer call could have prevented a P1 ticket.

- **Cross-correlation chart:** A bar chart answering: "If we see an anomaly in latency today, how many days before the customer opens a ticket?" The bar that's tallest tells you your warning window.

**Why this matters:** The difference between *reactive* support (customer calls, problem gets fixed) and *proactive* support (you call the customer before they notice). Proactive support is significantly better for NPS.

---

## Layer 3: "How Many Patients Will Show Up Next Month?" (Predictive)

**File:** `cloud_infrastructure_support/notebooks/03_predictive_ticket_forecasting.ipynb`

**The question it answers:** *How many support tickets should we expect in the next 18 months — and how many engineers do we need to hire?*

**In hospital terms:** A hospital administrator needs to plan staffing months in advance. If a big sporting event is coming to the city, the ER will be busier. If a flu epidemic is starting, they need more doctors. This notebook is a mathematical way to predict future ticket volume based on past patterns — so staffing decisions can be made before the crisis arrives, not during it.

**The model used:** SARIMA — a name that means "Seasonal AutoRegressive Integrated Moving Average." It sounds terrifying. What it actually does: it looks at the history of ticket counts week by week, finds the repeating patterns, finds the trend direction, and projects them forward. Like a very sophisticated version of "this time of year, we always get more tickets."

**What the notebook actually produces:**

- **Stationarity test:** Before forecasting, the notebook checks if the data has a stable pattern. If the number of tickets is constantly growing with no stable baseline, a simple trend projection would be useless. The test (ADF test) tells us whether we need to "flatten" the data first.

- **ACF / PACF plots:** Four technical charts that help configure the forecasting model correctly. They show how much "memory" the data has — does this week's ticket count depend on last week's? Two weeks ago? A month ago?

- **Model quality validation (Ljung-Box test):** After fitting the model, the notebook checks if there's any pattern left that the model didn't capture. If yes, improve the model. If no, the model is ready.

- **18-month forecast chart:** The headline result. A line showing predicted ticket volume per week for the next 18 months, with a shaded band representing uncertainty (wider band = less certain further out).

- **Staffing recommendation box:** "Based on the forecast, you need 12 engineers today and will need 17 at peak. Hire 5 additional over the next 18 months. Prioritize LATAM and APAC-INDIA."

**Why this matters:** Hiring an engineer takes 3–6 months (job posting, interviews, onboarding). If you wait until the ticket volume spikes to start hiring, you're already 6 months behind. This model gives the lead time needed to hire proactively.

---

## Layer 4: "Which Patient Is About to Deteriorate?" (Prescriptive)

**File:** `cloud_infrastructure_support/notebooks/04_prescriptive_escalation_risk.ipynb`

**The question it answers:** *Which open tickets right now have the highest risk of becoming an escalation that damages our relationship with the customer?*

**In hospital terms:** A triage nurse in a busy ER cannot personally watch every patient. But they can scan the waiting room and think: "That gentleman in the corner has been waiting 4 hours, he came in with chest pain, he's a 70-year-old with known heart disease — I need to check on him now before he codes." This notebook automates that decision for support tickets.

**What the notebook actually produces:**

- **Class imbalance chart:** Shows that only ~6% of tickets escalate. This is important because a dumb model that says "no ticket ever escalates" would be 94% accurate but completely useless.

- **ROC curve:** A graph showing how good each model is at distinguishing "will escalate" from "won't escalate". A model that's no better than guessing is a diagonal line; a perfect model is a right angle. Our Random Forest is much closer to the right angle.

- **Precision-Recall tradeoff chart:** Answers the question: "If I flag 100 tickets as high-risk, how many of those will actually escalate?" (Precision) AND "Out of all tickets that *did* escalate, what fraction did we catch?" (Recall).

- **Optimal threshold chart:** Because we care more about not missing a real escalation than about avoiding false alarms, we adjust the model's sensitivity. This chart shows the sweet spot.

- **Feature importance chart:** What does the model actually look at to decide if a ticket is risky? The longer the bar, the more the model relies on that feature. Typically: SLA breach, customer tier, and how long the ticket has been open matter most.

- **Real-time scorecard table:** The final output: a ranked table of the 10 highest-risk open tickets right now, with the probability score and a red/yellow/green label. This is what a resolution manager would see in their CRM dashboard.

**Why this matters:** One escalated P1 ticket from a Fortune 500 customer can cost millions in contract renewals. If a manager can review 5 high-risk tickets every morning and make a proactive call on the highest-risk ones, they can prevent 2–3 escalations per week. At enterprise contract values, that's significant.

---

---

## "Can This Model Beat the Stock Market?" (Quantitative Finance)

**Directory:** `quantitative_finance/`

**The question it answers:** *Can we apply institutional-grade financial engineering to model market microstructure, price exotic derivatives, and build portfolios that don't blow up?*

**In everyday terms:** Imagine three different problems a Wall Street quant desk faces every day:

1. **The Order Book (Notebook 01):** Every stock exchange has a "line" of buyers and sellers waiting to trade at different prices. This notebook rebuilds that line from raw transaction data — like reconstructing a movie from individual frames. It shows: what was the price gap between buyers and sellers at any given moment? That gap (the "spread") is the cost of trading.

2. **Exotic Options (Notebook 02):** A regular stock option says "you can buy Stock X at $100 in 3 months." An *Asian* option says "you can buy at the *average* price over the next 3 months." Averaging makes it harder to price — there's no simple formula. This notebook runs 50,000 simulated market scenarios (Monte Carlo simulation) using a model where volatility itself is random (the Heston model). Think of it as rolling 50,000 dice simultaneously and averaging the results.

3. **Portfolio Construction (Notebook 03):** The classic problem: "I have 20 stocks — how much of my money goes into each one?" The traditional method (Markowitz, 1952) requires solving a math problem that becomes unstable when stocks are correlated. This notebook uses a newer technique (Hierarchical Risk Parity) that groups similar stocks together like a family tree, then allocates money based on how risky each group is — without the instability.

**Why this matters:** These are not theoretical exercises. LOB reconstruction is what every trading platform does. Monte Carlo pricing is how banks value derivatives worth billions. HRP is used by quantitative hedge funds managing real capital.

---

## "What Happens When Governments Print Too Much Money?" (Macroeconomics)

**Directory:** `macroeconomic_capture/`

**The question it answers:** *How does government spending affect private investment, and why do some insolvent companies refuse to die?*

**In everyday terms:**

1. **Fiscal Crowding-Out (Notebook 01):** When a government runs a deficit, it borrows money by issuing bonds. More bonds on the market → interest rates go up → it becomes more expensive for companies to borrow → companies invest less. This notebook measures that chain reaction mathematically. It's like watching a bathtub: the government is pouring water in (deficit spending) while private investment is draining out through the same pipe.

2. **Zombie Corporations (Notebook 02):** Some companies earn less money than they owe in interest payments — they literally cannot pay their debts from their revenue. Normally, these companies would go bankrupt (what economists call "creative destruction" — making room for new, healthier companies). But government subsidies keep them alive. This notebook uses a clustering algorithm to find these "zombies" in the data — companies that cluster in the "high debt, low revenue, high subsidies" corner of the financial landscape.

**Why this matters:** Understanding crowding-out is essential for fiscal policy analysis. Zombie identification has real policy implications — Japan's "Lost Decade" was partly attributed to zombie firms propped up by government support.

---

## "What Shape Is a Protein?" (Structural Biology)

**Directories:** `proteins_alphafold_distances/` and `proteins_ramachandran_plot/`

**The question it answers:** *Can we turn the 3D structure of a protein — thousands of atoms in space — into a flat picture that reveals its secrets?*

**In everyday terms:** A protein is a chain of amino acids that folds into a 3D shape, like a very long necklace crumpled into a ball. The shape determines the function: a misfolded protein can cause disease (Alzheimer's, Parkinson's). These two notebooks analyze that 3D shape:

1. **Distance Map (Notebook 01):** Imagine numbering every bead on the necklace, then measuring the straight-line distance between every pair. You get a grid where colors show "close" (warm) or "far" (cool). Bands of warm color off the main diagonal reveal that bead #5 and bead #150 are actually touching — they're far apart on the chain but close in 3D space. These contacts are what hold the shape together.

2. **Ramachandran Plot (Notebook 02):** At each bead, the chain can twist in two directions (called φ and ψ angles). Not all angle combinations are physically possible — some would cause atoms to collide. This notebook calculates those angles from scratch using vector math (cross products, just like in high school physics) and plots them. The resulting scatter plot shows clusters: one cluster is "alpha helix" (like a spiral staircase), another is "beta sheet" (like a pleated fan). Empty zones are "forbidden" — the protein physically cannot twist that way.

**Why this matters:** Drug design, disease research, and biotech all depend on understanding protein structure. AlphaFold (Google DeepMind) predicts these structures — these notebooks demonstrate the ability to work with and analyze that output.

---

## "Can Hegel and Kojève Be Programmed?" (Continental Philosophy)

**Directory:** `continental_philosophy/`

**The question it answers:** *Can abstract philosophical ideas — dialectics, the struggle for recognition, the "end of history" — be translated into mathematical models that actually produce meaningful results?*

**In everyday terms:**

1. **Knowledge Graph (Notebook 01):** The philosopher Hegel described how human understanding evolves: "Being" leads to "Nothing," which leads to "Becoming," and so on — each concept containing and transcending the previous one (a process he called *Aufhebung*). This notebook turns that philosophical progression into a network diagram (like a social network, but for ideas instead of people). The computer then calculates which concepts are the most "influential" — which ones are pointed to by the most other important concepts. The result confirms Hegel's intuition: "Becoming" and "Self-knowledge" emerge as the most central nodes.

2. **Game Theory (Notebook 02):** The philosopher Alexandre Kojève described history as a series of encounters where individuals either "risk their life for recognition" (advance) or "submit out of fear of death" (yield). This creates a master/slave dynamic. Over time, through a process of reconciliation (*Aufhebung*), this inequality resolves into universal equality. This notebook simulates 1,000 agents making these choices randomly over many rounds. The remarkable result: the system reliably evolves from chaos → inequality → equality, empirically demonstrating Kojève's "End of History" thesis.

**Why this matters:** This demonstrates the ability to take concepts from a completely non-technical domain (19th-century German philosophy) and formalize them into working computational models. The same skill — translating domain knowledge into data structures and algorithms — is exactly what data scientists do in every industry.

---

## "How Do Particles Bounce and Tunnel?" (Computational Physics)

**Directory:** `computational_physics/`

**The question it answers:** *Can we simulate fundamental physics — a particle bouncing off a nucleus, or a quantum particle tunneling through a wall — from nothing but Newton's and Schrödinger's equations?*

**In everyday terms:**

1. **Rutherford Scattering (Notebook 01):** In 1911, Ernest Rutherford shot tiny particles at a gold foil and found that some bounced straight back — proving the atom has a dense nucleus. This notebook recreates that experiment computationally: 5,000 particles are "fired" at a positively charged nucleus. Each particle feels an electric repulsive force (stronger when closer) and curves away. The angle it deflects by depends on how close it passed. The resulting histogram of deflection angles matches Rutherford's famous formula — confirming the simulation is physically correct. The key innovation: using a "symplectic" integrator (Velocity-Verlet) that preserves the total energy exactly, unlike simpler methods that would cause the energy to slowly "leak."

2. **Quantum Tunneling (Notebook 02):** In quantum mechanics, a particle can pass through a barrier that it classically shouldn't be able to cross — like a ball rolling through a hill instead of over it. This notebook solves the Schrödinger equation using a method (Crank-Nicolson) that is unconditionally stable and conserves probability exactly. The result: a wave packet approaches a barrier, and a fraction of it appears on the other side. The transmission percentage depends exponentially on the barrier height and width — exactly as quantum theory predicts.

**Why this matters:** These are not toy problems — they demonstrate proficiency with numerical methods (PDE solvers, symplectic integrators, sparse linear algebra) that are directly applicable to engineering simulation, financial modeling, and computational science.

---

## "How Do You Keep Subscribers From Leaving?" (Subscription Economics)

**Directory:** `subscription_economics/`

**The question it answers:** *For a company that sells hardware with a subscription service, how do you measure customer value, predict who will cancel, and test whether a product change actually works?*

**In everyday terms:** Imagine a company that sells security cameras and charges $8/month for cloud video storage. Three questions:

1. **How Much Is a Customer Worth? (Notebook 01):** Not all customers are equal. A customer who bought a camera and never subscribed to cloud storage is worth $0 in recurring revenue. A customer who subscribes for 3 years at $8/month is worth $288. This notebook calculates the "Lifetime Value" (LTV) of each customer segment: how much revenue will this customer generate over their entire relationship with us? It also tracks the "attach rate" — what percentage of hardware buyers convert to subscribers? If cameras have a 55% attach rate and doorbells only 35%, marketing should focus on cameras.

2. **Who Is About to Cancel? (Notebook 02):** If a subscriber used the app 25 out of 31 days last month (81% stickiness), they're probably happy. If they used it 5 out of 31 days (16%), they're probably about to cancel. This notebook builds a model that draws a curve: at what stickiness level does churn probability cross 50%? The answer (about 30%) becomes the trigger for an automated "we miss you!" reactivation email.

3. **Did the New Onboarding Flow Work? (Notebook 03):** The product team redesigned the setup experience for new camera buyers. Did more people subscribe to cloud storage after the redesign? This notebook runs a proper A/B test: half of new users got the old flow (Control), half got the new flow (Variant). A statistical test (z-test for proportions) determines whether the difference in conversion rates is real or just random noise. If the p-value is below 0.05, the improvement is statistically significant and the new flow should be shipped to everyone.

**Why this matters:** LTV, churn prediction, and A/B testing are the three pillars of product analytics at any SaaS or subscription company. Every product manager, growth team, and data analyst uses these exact techniques daily.

---

## The Foundation: Where Mario Learned This

**File:** `real_estate/house_sales_king_county.ipynb`

This is a project from IBM's Data Analysis course — predicting house prices in King County, Washington using real estate data. Think of it as learning to drive in a parking lot before getting on the highway.

The techniques practiced here (regression, feature selection, model validation) are exactly the same ones used in the infrastructure support case study, just applied to a simpler, public dataset.

---

## The Data We Used — And Why We Created It Ourselves

You might ask: *"Where did the support data come from?"*

The answer demonstrates one of the core skills: **data sovereignty**. Instead of waiting for access to production data, we built a synthetic data generator (`cloud_infrastructure_support/src/data_generator.py`) that creates realistic-looking data with the same statistical properties that real support data would have.

The generator creates:
- **100,000 support tickets** spread over 3 years, with realistic patterns: more P3 tickets than P1, migration tickets taking longer to resolve, Strategic customers having higher escalation rates when SLAs breach
- **54,750 telemetry readings** from 50 server clusters: normal daily IO latency patterns, weekly seasonality (servers work harder on weekdays), and 5% of days with injected anomaly spikes
- **24 migration waves** representing batches of customers moving between hypervisor platforms, with realistic timelines and cluster counts

**Why this is a big deal:** Many analysts would say "I can't build this portfolio without real data." Data sovereignty means designing the scenario yourself. It proves that you can work autonomously, contribute immediately on day 1, and understand the domain well enough to simulate it.

---

## The Extra Piece: API Integration

**File:** `cloud_infrastructure_support/notebooks/05_api_integration.ipynb`

This notebook shows how all of the above would work with *real* data from a live infrastructure management platform. It demonstrates connecting to a REST API (v4) that allows authorized users to pull live server metrics — the same IO latency data that Layer 2 analyzes from synthetic data.

In plain English: this notebook is a demonstration that I can go from "portfolio project" to "production-ready tool" the moment I get API credentials. It shows I've already read the documentation and understand how to query the data correctly without creating unnecessary load on the system.

---

## The Bottom Line

If you've read this far without getting lost, here's the one-sentence version of each piece:

| Piece | One sentence |
|---|---|
| **Cloud Infra — Layer 1** | A dashboard that tells you, at a glance, whether the support operation is healthy |
| **Cloud Infra — Layer 2** | A system that detects server problems in the telemetry data before customers open tickets |
| **Cloud Infra — Layer 3** | A forecast that tells you how many support tickets to expect and how many engineers to hire |
| **Cloud Infra — Layer 4** | A risk score for every open ticket, highlighting which ones will damage the customer relationship if ignored |
| **Quantitative Finance** | Institutional-grade financial engineering: order book reconstruction, exotic option pricing, and stable portfolio construction |
| **Macroeconomic Capture** | Mathematical proof of how government deficits crowd out private investment, and how subsidies keep zombie firms alive |
| **Proteins & Biology** | Turns 3D atomic coordinates into flat visualizations that reveal protein structure and function |
| **Continental Philosophy** | Demonstrates that even 19th-century German philosophy can be formalized into working computational models |
| **Computational Physics** | Simulates fundamental physics (particle scattering, quantum tunneling) from first principles using numerical methods |
| **Subscription Economics** | The three pillars of product analytics: customer lifetime value, churn prediction, and A/B testing |
| **Real Estate** | Evidence that the statistical methods used here were learned rigorously through structured coursework |
| **Data Generators** | Proof of the ability to build analytical systems without waiting for someone else to provide the data |
| **API Integration** | Proof that this can transition from a portfolio project to a production tool without rewriting everything |

---

*Mario Casanova | Data Science & Analytics Portfolio*
*For deep technical details: see `TECHNICAL_GUIDE.md`*
