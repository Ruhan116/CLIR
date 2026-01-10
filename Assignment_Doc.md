\# CLIR Assignment Tasks Summary



\## Project Overview

Build a Cross-Lingual Information Retrieval (CLIR) Engine that retrieves, ranks, and evaluates multilingual documents (Bangla and English) using lexical and semantic techniques.



\*\*Group Size:\*\* 4 members  

\*\*Timeline:\*\* 3 weeks  

\*\*Total Marks:\*\* 100%



---



\## Core Tasks Breakdown



\### Module A: Dataset Construction \& Indexing (12 + 8 = 20 marks)



\#### Task A1: Dataset Collection

\- Crawl \*\*at least 2,500 documents per language\*\* (Bangla and English)

\- Use 5 Bangla news sites + 5 English news sites from provided lists

\- Alternative: Use Common Crawl/CC-MAIN extraction



\*\*Required Metadata per Document:\*\*

\- `title`

\- `body`

\- `url`

\- `date`

\- `language`

\- `tokens` (count)

\- `word\_embeddings` (optional but recommended)

\- `named\_entities` (optional)



\*\*Suggested Tools:\*\*

\- Crawling: Requests, BeautifulSoup, Selenium, Scrapy

\- Language Detection: langdetect, textblob, fasttext



\#### Task A2: Indexing

\- Build an \*\*inverted index\*\* with document metadata

\- Tools: Elasticsearch, Lucene, Whoosh, or custom Python implementation

\- Handle encoding issues and real-world data messiness



---



\### Module B: Query Processing \& Cross-Lingual Handling (15 marks)



Implement a query-processing pipeline with these steps:



1\. \*\*Language Detection\*\*: Identify if query is Bangla or English

2\. \*\*Normalization\*\*: Lowercase, remove whitespace, optional stopword removal

3\. \*\*Query Translation\*\* (Required): Translate query to target language for cross-lingual retrieval

4\. \*\*Query Expansion\*\* (Recommended): Add synonyms, morphological variants

5\. \*\*Named-Entity Mapping\*\* (Recommended): Map NEs across languages (e.g., "Bangladesh" ↔ "বাংলাদেশ")



---



\### Module C: Retrieval Models (18 marks)



Implement and compare multiple retrieval models:



\#### Model 1: Lexical Retrieval (Mandatory)

\- Implement BM25 or TF-IDF

\- Compare both on your dataset

\- Analyze failure cases



\#### Model 2: Fuzzy/Transliteration Matching

\- Use edit distance (Levenshtein), Jaccard similarity, or character n-grams

\- Handle transliteration matching (e.g., "Bangladesh" ↔ "বাংলাদেশ")

\- Tools: difflib, fuzzywuzzy, jellyfish



\#### Model 3: Semantic Matching (Mandatory)

\- Use multilingual embedding models:

&nbsp; - \*\*Recommended:\*\* LaBSE, XLM-R

&nbsp; - \*\*Alternatives:\*\* mBERT, mT5, multilingual SBERT

\- Measure similarity using cosine distance

\- Compare with lexical models



\#### Model 4: Hybrid Ranking (Optional)

\- Combine scores from multiple models

\- Example: `0.3 × BM25 + 0.5 × embedding + 0.2 × fuzzy`

\- Experiment with weighted fusion



---



\### Module D: Ranking, Scoring \& Evaluation (15 + 10 = 25 marks)



\#### Task D1: Ranking \& Scoring

\- Output sorted list of top-K documents per query

\- \*\*Matching Score (0-1 scale)\*\*: Confidence score for each result

\- \*\*Low-confidence warning\*\*: Display warning if top result score < 0.20

\- Report \*\*query execution time\*\* (total + breakdown)



\#### Task D2: Evaluation Metrics (Mandatory)

Evaluate using standard IR metrics with \*\*at least 15 labeled queries\*\*:



| Metric | Definition | Target |

|--------|------------|--------|

| Precision@10 | Relevant docs in top 10 / 10 | ≥ 0.6 |

| Recall@50 | Relevant retrieved / total relevant | ≥ 0.5 |

| nDCG@10 | Discounted cumulative gain | ≥ 0.5 |

| MRR | 1 / (rank of first relevant doc) | ≥ 0.4 |



\*\*Relevance Labeling:\*\*

\- Manually label 5-10 queries as relevant/not relevant

\- Store in CSV: `query, doc\_url, language, relevant (yes/no), annotator`



\*\*Comparison:\*\*

\- Compare results with Google, Bing, DuckDuckGo, or AI-powered search engines



\#### Task D3: Error Analysis (Detailed)

Analyze retrieval failures with specific examples for these categories:



1\. \*\*Translation Failures\*\*: Mistranslation leading to wrong results

2\. \*\*Named Entity Mismatch\*\*: NER failed to match entities across languages

3\. \*\*Semantic vs. Lexical Wins\*\*: When embeddings outperform BM25

4\. \*\*Cross-Script Ambiguity\*\*: Transliteration handling issues

5\. \*\*Code-Switching\*\*: Mixed Bangla-English queries



\*\*Format:\*\* At least one detailed case study per category (screenshot, query text, retrieved document, analysis)



---



\### Module E: Report, Literature Review \& Innovation (15 + 7 = 22 marks)



\#### Task E1: Literature Review (3-5 papers)

\- Identify 3-5 key CLIR/multilingual IR papers (excluding suggested ones)

\- Summarize each in 100-200 words

\- Include: authors, year, main technique, relevance to your system



\*\*Suggested Starting Papers:\*\*

\- "Cross-Lingual Information Retrieval" by Ballesteros \& Croft (ACL 2001)

\- "Massively Multilingual Sentence Embeddings" (2019)

\- "XLM-RobERTa" (ICLR 2020)



\#### Task E2: Methodology \& Tools Documentation

Document clearly:

\- Dataset construction process

\- Tools used

\- Indexing strategy and metadata

\- Query processing pipeline

\- Retrieval models (with code snippets/pseudocode)

\- Ranking and scoring approach



\#### Task E3: Results \& Analysis

\- \*\*Tables:\*\* Compare Precision@10, Recall@50, nDCG, MRR across models

\- \*\*Graphs:\*\* Bar charts/line plots showing performance, confusion matrices

\- \*\*Interpretation:\*\* Which model works best? Why? Trade-offs?



\#### Task E4: AI Usage Policy (Mandatory)

\*\*Strict Requirements:\*\*

\- \*\*Disclosure:\*\* Log ALL AI-generated content with exact prompts in appendix "AI Tool Usage Log"

\- \*\*Verification:\*\* Verify correctness before including

\- \*\*Correction:\*\* Document incorrect AI outputs (prompt, output, why wrong, correct version)

\- \*\*Code Understanding:\*\* All members must explain/modify AI-generated code



\*\*Example Log Entry:\*\*

```

Prompt: "Write Python code to compute nDCG@10"

Tool: ChatGPT (Nov 2024)

Output: \[code snippet]

Verification: Tested; correct for k=10

Included: Yes (Section 4.2)

```



\#### Task E5: Innovation Component (7 marks)

Propose one extension (even if not fully implemented):

\- Cross-lingual topic modeling

\- Query-time code-switching detection

\- Bias detection across political viewpoints

\- Graph-based concept linking

\- Domain adaptation

\- Temporal drift modeling



---



\## Deliverables



\### 1. Code Repository

\- Well-commented code for crawling, indexing, retrieval, evaluation

\- README.md with setup instructions

\- Labeled query set (CSV)



\### 2. Dataset

\- Processed documents (JSON/CSV) with metadata

\- If >100 MB, provide download link or recreation script



\### 3. Final Report (PDF)

\*\*Sections:\*\*

\- Motivation

\- Methodology

\- Results

\- Error Analysis

\- Literature Review

\- AI Usage Log

\- Innovation

\- References



\### 4. Evaluation Results (CSV/JSON)

\- Query-by-query results with matching scores

\- Summary table of model performance



---



\## Recommended News Sites



\### Bangla News Sites (5 required)

1\. Prothom Alo - prothomalo.com

2\. BD News 24 - bangla.bdnews24.com

3\. Kaler Kantho - kalerkantho.com

4\. Bangla Tribune - banglatribune.com

5\. Dhaka Post - dhakapost.com



\### English News Sites (5 required)

1\. The Daily Star - thedailystar.net

2\. New Age - newagebd.net

3\. The New Nation - dailynewnation.com

4\. Daily Sun - daily-sun.com

5\. Dhaka Tribune - dhakatribune.com



---



\## Timeline (3 Weeks)



| Week | Milestone | Targets |

|------|-----------|---------|

| Week 1 | Dataset crawling \& indexing | ≥2,500 docs per language; clean metadata |

| Week 1-2 | Models \& retrieval | BM25 + fuzzy + embeddings working; initial evaluation |

| Week 2-3 | Evaluation \& error analysis | 15-20 labeled queries; results tables/graphs |

| Week 3 | Report \& polish | Full report with all sections |



---



\## Key Success Criteria



\### Ideal Submission Includes:

\- ✅ Balanced multilingual dataset (2.5k+ docs per language)

\- ✅ Multiple retrieval models with fair comparison

\- ✅ Robust query processing with error handling

\- ✅ Matching scores with low-confidence warnings

\- ✅ Query execution time reporting

\- ✅ Strong evaluation with visualizations (20+ labeled queries recommended)

\- ✅ Detailed error analysis with case studies

\- ✅ Transparent AI usage documentation

\- ✅ Research-level innovation proposal



---



\## Important Notes



1\. \*\*Academic Integrity:\*\* All work must be original and attributed

2\. \*\*AI Transparency:\*\* Full disclosure required in appendix

3\. \*\*Group Accountability:\*\* All members must understand all code

4\. \*\*No Fabrication:\*\* Datasets, results, and citations must be genuine

5\. \*\*Crawling Ethics:\*\* Respect robots.txt, use reasonable request rates



---



\## Grading Distribution (100%)



\- Dataset Construction: 12%

\- Indexing \& Preprocessing: 8%

\- Query Processing \& CLIR: 15%

\- Retrieval Models: 18%

\- Ranking, Scoring \& Evaluation: 15%

\- Error Analysis: 10%

\- Report + Literature Review: 15%

\- Innovation Component: 7%

