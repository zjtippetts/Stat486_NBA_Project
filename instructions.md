# Final Project Instructions

**Course:** STAT 486  
**Term:** Winter/Spring 2026  

All deadlines are strict unless prior arrangements are made.


## Requirements

Your final project should demonstrate the full machine learning workflow in a reproducible format: problem definition, data acquisition/cleaning, exploratory analysis, supervised modeling, additional ML analysis, and communication of results.

### What this project is

- A reproducible, end-to-end ML workflow
- An opportunity to demonstrate technical depth and thoughtful evaluation
- A communication exercise (clear writing, structured results, responsible AI use)

### What this project is not

- A Kaggle-style leaderboard competition
- A collection of loosely related notebooks
- A "run once on my laptop" analysis without reproducibility
- A multi-model hyperparameter dump without interpretation

The central deliverable is a **GitHub repository** that allows others to reproduce your main results.

### Team policy

- Teams of 1-3 students are allowed.
- Teams are expected to divide work clearly and contribute throughout the timeline.

### Expected scope

This is a 4-5 week project. A well-scoped project typically:

- Uses (at least) one primary dataset
- Implements 2-3 supervised models
- Includes one additional ML method
- Focuses on interpretation, not model count

Depth is valued more than breadth.

Datasets requiring large-scale GPU training, distributed systems, or multi-hour training runs are discouraged unless pre-approved.

## Main Deliverable: Reproducible GitHub Repository

Your repository is the primary graded artifact. It should be organized, documented, and your results should be reproducible from the code. The repository should include all project code used for results, data (if small, otherwise links and retrieval instructions), slides for the final presentation, and a demo file.

### Repository organization policy

You may organize files flexibly, but organization must be logical, consistent, and documented in your `README.md`. Some guidelines are given below.

Use clear names and consistent layout so that another student can quickly find your data access instructions, reproducibility scripts, and demo artifact.

### Required repository contents

1. `README.md`
   The README is the first thing somebody sees when accessing your repository. It should serve as a roadmap for your project and should include at least the following:
   - Project question/hypotheses and motivation
   - Steps to reproduce your results
   - Figures/tables/main results
   - Data sources with citation and license/usage notes
2. `data/`
   - Include data files if reasonably small
   - If data is large, include a file with download links and retrieval instructions in the `data` directory.
3. Reproducibility scripts/code (for example, in a `src` directory)
   - Script(s) or modules that run your workflow (data prep/modeling/evaluation)
4. Demo
   - At least one demonstration format: Jupyter notebook (`.ipynb`) **or** Streamlit app (`.py`)
5. Environment/reproducibility files
   - `requirements.txt` minimum (or equivalent environment file)
6. Communication files (e.g., `progress` directory)
   - Progress check files (Markdown files)
   - Presentation slides (PowerPoint, Keynote, Beamer, or link to Google Slides)
   - Other applicable documentation files

### Reproducibility standard

At minimum, the repository must satisfy all of the following:

- A user can install dependencies from your instructions.
- A user can run scripts/notebooks in your stated order.
- File paths are relative (no machine-specific absolute paths).
- Final notebook runs top-to-bottom without manual intervention.
- Randomness is controlled and documented (seed or equivalent).

If full reproduction requires external data access, your `README.md` must include exact retrieval steps.

#### Reproducibility self-test

Before submitting, verify all of the following:

- Clone your repo into a new folder.
- Create a new environment.
- Install dependencies.
- Follow your `README.md` instructions exactly.
- Regenerate at least one main result (figure, table, or metric).

If a grader cannot reproduce at least one main result within about 10 minutes by following your README, reproducibility requirements are not met.

### Demo format

- **Required:** one clean, runnable demo in either format:
  - Jupyter notebook (`.ipynb`), or
  - Streamlit app (`.py`)
- If Streamlit is used, publish the app and include the link in your `README.md` file.
- You may submit both formats, but only one is required.

A demo notebook/app should:

- Run top-to-bottom without errors
- Focus on main results
- Avoid exploratory dead code
- Be cleanly organized and readable

## Progress Deliverables

All due times are **Saturday, 11:59 PM**, unless noted.

### Deliverable 0 (5%): Group selection

**Due:** Saturday, March 14

Submission:

- Canvas:
  - Team member names
  - One-sentence project area (for example: NFL draft data, music, video games, dance, medical data, or government surveys)
  - GitHub repository link (an empty scaffold is acceptable)
- GitHub:
  - Repository scaffold created and accessible to instructor

Minimum evidence checklist:

- [ ] Group members listed in Canvas submission
- [ ] Project area listed in Canvas submission
- [ ] Repository link submitted
- [ ] Repository is public or shared with instructor access

### Deliverable 1 (15%): Proposal checkpoint

**Due:** Saturday, March 21

Create `progress/01_proposal.md` (1-2 pages) addressing the following:

Individually or with your group, use generative AI (for example, ChatGPT or Copilot) to generate project ideas based on your general project area.

You may use your own prompts or one of the following recommendations:

- I am working on a senior-level machine learning project that must involve both supervised learning (e.g., regression, classification) and one other ML technique, such as clustering, anomaly detection, recommender systems, or reinforcement learning. Can you suggest project ideas across different domains (like healthcare, finance, sports analytics, and social media) that allow me to apply both types of techniques using real-world datasets?
- I am interested in [domain, e.g., healthcare, finance, sports, social media]. I need a project idea that combines both supervised learning (classification or regression) and another ML approach, such as clustering, anomaly detection, or recommender systems. Can you suggest feasible project ideas with publicly available datasets?
- I want to compare the effectiveness of supervised learning models and unsupervised (or other) ML techniques on the same dataset. Can you suggest project ideas where both approaches could provide unique insights?

Interacting with AI effectively:

- Be specific but open-minded: Provide details about your interests and constraints while staying open to new ideas.
- Iterate and refine: Follow up with AI by asking questions such as:
  - Can you suggest a variation of this project that is more practical for a semester?
  - How could I make this project more unique?
- Use AI as a collaborator: AI can generate ideas, but you should integrate your own expertise and creativity. Reflect on:
  - What excites me about this idea?
  - Do I have the technical background to implement this, or do I need to simplify?

Include in your proposal file:

- 2-3 candidate project ideas generated with AI
- A short note (4-6 sentences) describing how AI influenced your idea selection
- A brief excerpt of one AI exchange that helped refine your project direction

Your proposal should also address:

- Final research question
- Candidate target variable for supervised analysis
- Dataset choice and backup dataset
- Feasibility (time, compute, scope)
- Ethical/legal considerations
- Planned additional ML methods

By this date, repository should also include:

- Initial project scaffold with clearly named locations for code and progress checks
- Initial `README.md` and `data`

Submission:

- Canvas:
  - Repo link
  - Short note: "Deliverable 1 complete"
- GitHub:
  - `progress/01_proposal.md`
  - Initial `README.md`
  - Initial data access file (for example: `data/README.md`)

Minimum evidence checklist:

- [ ] `progress/01_proposal.md` exists
- [ ] 2-3 AI-generated ideas included
- [ ] AI reflection and excerpt included
- [ ] Final question and target variable included
- [ ] Dataset choice and backup dataset included

### Deliverable 2 (10%): Data and EDA checkpoint

**Due:** Saturday, March 28

Create `progress/02_eda.md` (approximately 250-500 words, plus figures/tables) using the format below.

#### 1) Research Question and Dataset Overview

Include all of the following:

- State your main research question.
- Provide a brief summary of your dataset: where it came from and what it represents.
- Cite your data source with proper credit/reference.
- Briefly explain how you determined the dataset is legally and ethically appropriate (for example: license, terms of use, and PII considerations). If no ethical concerns exist, explicitly state that.

#### 2) Data Description and Variables

Include all of the following:

- Provide a clear description of key variables used in your analysis.
- Identify your target variable(s): what you are predicting or analyzing.
- Document preprocessing steps completed so far (for example: missing-value handling, duplicates removed, renamed columns, filtering). If no preprocessing was needed, state why.

#### 3) Summary Statistics

Provide summary statistics for the most relevant variables.

For numeric variables, report:

- Sample size
- Mean and standard deviation, or five-number summary

For categorical variables, report:

- Sample size and category counts (frequency distribution)

Also include:

- Correlation matrix, if applicable (optional if not useful for your data)
- Brief notes on interesting relationships between numeric variables
- A short interpretation (2-3 sentences) highlighting key insights, patterns, or outliers

#### 4) Visual Exploration

Include at least 2 insightful visualizations that begin addressing your research question.

Visualizations should move you closer to answering your research question. Avoid generic plots unless they reveal something meaningful.

Examples:

- Weak: a standalone histogram with no interpretation
- Strong: target distribution compared across meaningful groups, with interpretation tied to your question

For each visualization, include a brief explanation:

- What does it show?
- Why is it relevant to your research question?

#### 5) Challenges and Reflection

Address at least one of the following questions:

- What challenges did you face in finding the right dataset?
- What concerns/challenges are you currently facing in the project?

#### Deliverable summary

Your `progress/02_eda.md` report must contain:

- Dataset overview
- Data description and preprocessing
- Summary statistics and correlation matrix (if applicable)
- Visualizations and interpretations
- Reflection

Submission:

- Canvas:
  - Repo link
  - Short note: "Deliverable 2 complete"
- GitHub:
  - `progress/02_eda.md`
  - EDA notebook/script used to generate statistics, and figures/tables

Minimum evidence checklist:

- [ ] `progress/02_eda.md` exists
- [ ] Data source/legality information included
- [ ] Summary statistics included
- [ ] At least 2 visualizations included with short explanations
- [ ] At least one EDA notebook/script in repo

Report writing tips (applies to Deliverables 2-4):

- Start with a clear purpose: each section should support your research question.
- Use clean, readable visuals with titles, axis labels, and short captions.
- Be concise but complete: focus on insights, not step-by-step narration.
- Show thought, not just output. Explain what results mean for your data and question.
- Do not include screenshots of code or terminal output.
- Do not over-explain basic steps such as `.fit()`/`.predict()` steps.
- Do not paste long hyperparameter grids or pages of raw model output.
- Do not write a travel log of every attempt; summarize what mattered.

### Deliverable 3 (25%): Supervised modeling checkpoint

**Due:** Saturday, April 4

#### Objective

Perform a supervised learning analysis of your data by implementing multiple models, optimizing performance, and using explainable AI techniques to interpret results.

#### Requirements

- Implement at least two meaningfully different supervised learning models using Scikit-Learn or other appropriate libraries (for example: linear regression, regularized regression, k-NN, decision trees, random forests, SVM, feed-forward neural networks, CNNs).
- Optimize model performance through feature selection, hyperparameter tuning, and cross-validation.
- Use explainable AI methods (for example: SHAP, permutation importance, feature importance from tree-based models) to analyze model decisions.
- Evaluate models using appropriate performance metrics (for example: accuracy, precision-recall, RMSE, AUC, R2).


Create `progress/03_supervised.md` (approximately 250-500 words, plus one table or figure) as a short methods-and-results report with the following sections.

#### 1) Problem Context and Research Question

- Provide 1-2 sentences summarizing your project goal.
- Do not repeat full EDA details.

#### 2) Supervised Models Implemented

Create a table or concise summary listing:

- Model type
- Key hyperparameters explored
- Validation setup used (for example: train/validation split or cross-validation)
- Performance metrics used and final values

#### 3) Model Comparison and Selection

Discuss insights from model results:

- What patterns or trends emerged across models?
- Which model performed best and why?
- What challenges did you face (for example: overfitting, hyperparameter tuning)?

#### 4) Explainability and Interpretability

- Present one explainability output and interpret what it suggests about model behavior.

#### 5) Final Takeaways

- Summarize key insights gained from supervised learning.
- Explain how this analysis answers your research question.

Submission:

- Canvas:
  - Repo link
  - Short note: "Deliverable 3 complete"
- GitHub:
  - `progress/03_supervised.md`
  - Supervised modeling code and interpretability artifact

Minimum evidence checklist:

- [ ] `progress/03_supervised.md` exists
- [ ] At least two supervised models compared
- [ ] Model table with metrics and hyperparameters included
- [ ] Interpretability method/output included
- [ ] Train/validation strategy documented

Minimum modeling detail:

- Clear train/validation strategy
- At least one baseline and one stronger model
- Baseline should be simple and interpretable (for example: decision tree, linear regression, logistic regression)
- Metric choice justified for problem type

#### Common pitfall: data leakage

- Do not preprocess using the full dataset before splitting.
- Use pipelines when appropriate.
- Ensure scaling, encoding, and feature selection occur inside cross-validation.
- Tune hyperparameters on training/validation folds only; do not tune on the test set.

### Deliverable 4 (25%): Final repository and additional ML method

**Due:** Saturday, April 11

#### Requirements


Create `progress/04_unsupervised.md` (150-300 words) with:

- Additional method used (clustering, anomaly detection, dimensionality reduction, etc.)
- New insight gained beyond supervised analysis
- Final conclusion (2-4 sentences)

#### Options for Additional ML Methods

- Clustering: perform cluster analysis (for example: k-Means, DBSCAN, hierarchical clustering) and interpret data patterns.
- Anomaly detection: identify unusual patterns using methods such as Isolation Forest, Local Outlier Factor, or One-Class SVM.
- Recommender systems: build a simple collaborative filtering or content-based recommendation model.
- Reinforcement learning: implement a basic RL model (optional; intended for advanced students).
- Dimensionality reduction: apply PCA, t-SNE, or another method for visualization or as model input features.
- Other method: alternative methods are allowed with prior approval and a short justification of appropriateness.

Submission:

- Canvas:
  - Repo link
  - Short note: "Deliverable 4 complete"
- GitHub:
  - `progress/04_unsupervised.md`
  - Final reproducibility updates and presentation slides

Minimum evidence checklist:

- [ ] `progress/04_unsupervised.md` exists
- [ ] At least one approved additional ML method implemented
- [ ] Final `README.md` includes exact run order
- [ ] Demo artifact included (`.ipynb` or Streamlit app)
- [ ] Slides included

Additional method detail should include:

- Why method fits the data and question
- Key parameter choices
- At least one supporting visualization/output
- Connection back to supervised results

### Deliverable 5 (20%): In-class presentation

**Dates:** Thursday, April 9 and Tuesday, April 14

Present your final analysis. Minor polishing before the April 11 repository deadline is acceptable.

Presentation requirements:

- Target length: 8-12 minutes per group
- All group members must participate
- Must cover question, data, methods, results, and conclusion
- Must use evidence created in your repository (figures, notebook outputs, metrics)
- You may choose to use your demo as a part of your presentation
- Final time windows may be adjusted slightly based on the number of groups.

Submission:

- Canvas:
  - Final repo link
  - Slides file/link (if not already in repo)
- GitHub:
  - Final slides
  - Final demo artifact and code

Minimum evidence checklist:

- [ ] All members present
- [ ] Presentation within assigned time window
- [ ] Slides submitted
- [ ] Presentation uses project evidence from repo

Presentation tips:

- Introduce your question clearly and assume ML background, not domain background.
- Tell a story: what you tried to find out, what you discovered, and what you would try next.
- Use slides to show, not tell; prioritize visuals over dense text.
- Keep slides uncluttered; avoid too much text or too many plots on one slide.
- Do not read slide text directly.
- Do not use code screenshots.

Suggested structure:

1. Problem and motivation
2. Data and EDA highlights
3. Supervised model comparison
4. Additional method findings
5. Limitations and next steps


---
# General Guidelines 

## Deliverable Percentage Summary

| Deliverable | Weight |
| --- | --- |
| Deliverable 0: Group selection | 5% |
| Deliverable 1: Proposal checkpoint | 15% |
| Deliverable 2: Data and EDA checkpoint | 10% |
| Deliverable 3: Supervised modeling checkpoint | 25% |
| Deliverable 4: Final repository and additional ML method | 25% |
| Deliverable 5: In-class presentation | 20% |
| **Total** | **100%** |

## Grading Emphasis

Projects are evaluated primarily on reproducibility, technical quality, and presentation.

Evaluation priorities:

- Reproducibility and organization of the repository
- Technical quality of methods and evaluation
- Quality of interpretation and communication


Important interpretation guidance:

- Model performance is not the only factor and is not automatically the main factor.
- A model with weaker metrics can still earn a strong evaluation if your analysis yields meaningful insight.
- Poor performance can be informative (for example: weak signal, noisy features, or data limitations).
- Exceptional performance should trigger skepticism; check for leakage and invalid evaluation design.
- Strong projects show critical thinking: are results surprising, useful, and non-trivial?

## Academic Integrity and AI Use

Use of AI tools (Copilot, ChatGPT, etc.) is allowed for brainstorming, coding support, and editing.

You may use AI to:

- Generate ideas
- Help debug code
- Suggest modeling strategies

You may not:

- Submit AI output without understanding it
- Include code you cannot explain
- Fabricate data sources or citations

You remain responsible for:

- Verifying code correctness
- Understanding and explaining your workflow
- Proper citation of datasets and external content

Do not submit copied or unattributed work.

## Common Failure Modes

Common reasons projects lose points:

- Broken file paths or non-relative paths
- Missing environment/dependency file
- No train/test (or validation) separation
- Hyperparameter tuning performed on test data
- No interpretation of model outputs
- Dataset too large for available compute, leading to incomplete analysis
- Repository cluttered with unused files and unclear run order

## Submission Logistics

- Submit each milestone on Canvas with the GitHub link.
- Be sure to push all changes for each milestone before submitting on Canvas.
- If using a private repository, provide instructor/TA access before each deadline.

## Timeline Summary

- Tuesday, March 10: Project launch
- Saturday, March 14: Group selection
- Saturday, March 21: Proposal checkpoint
- Saturday, March 28: Data + EDA checkpoint
- Saturday, April 4: Supervised modeling checkpoint
- Thursday, April 9: Presentations (round 1)
- Saturday, April 11: Final repo submission + additional method checkpoint + slides
- Tuesday, April 14: Presentations (round 2, last class day)

## Quick Checklist

- [ ] Group selected by March 14
- [ ] Repository scaffold created (flexible structure)
- [ ] Proposal checkpoint submitted by March 21
- [ ] Data + EDA checkpoint submitted by March 28
- [ ] Supervised checkpoint submitted by April 4
- [ ] Final repository freeze submitted by April 11
- [ ] Demo included (`.ipynb` or Streamlit app)
- [ ] Presentation delivered on April 9 or April 14
