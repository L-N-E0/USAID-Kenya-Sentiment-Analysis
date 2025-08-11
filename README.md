# USAID Online Discourse Analysis

##  Project Overview

This project analyzes online discussions related to **USAID in Kenya** after the funding cuts, using data collected from **Reddit** and **News API** sources.  
The goal was to identify **key topics, trends, and sentiment patterns** in public discourse and provide insights to inform policy, outreach, and communication strategies.

The analysis was conducted as part of a collaborative group project.  
While the dataset selection was decided collectively, **data collection, merging, cleaning, analysis, and visualization** were done individually.  
This ensured methodological diversity while working with a shared dataset.

---

##  Steps Followed

1. **Data Collection** – Gathered USAID-related content from multiple online sources.  
2. **Data Cleaning & Preprocessing** – Removed noise, normalized formats, and prepared text for analysis.  
3. **Exploratory Data Analysis (EDA)** – Analyzed distributions, trends, and word frequencies.  
4. **Sentiment Analysis** – Measured polarity trends over time.  
5. **Topic Modeling** – Extracted and interpreted key themes.  
6. **Visualization & Communication** – Presented findings through clear, accessible visuals.

---

##  Data Sources

- **Reddit API** – Discussion threads and comments.  
- **News API** – Articles and headlines referencing USAID.  

---

##  Tools & Technologies

- **Python** – Core programming language for analysis.  
- **Pandas / NumPy** – Data manipulation and numerical computation.  
- **NLTK / spaCy** – Natural Language Processing (tokenization, lemmatization, stopword removal).  
- **VADER** – Lexicon-based sentiment analysis.  
- **LDA / BERTopic** – Topic modeling to uncover latent themes.  
- **Scikit-learn** – Machine learning workflows.  
- **Matplotlib / Seaborn / Plotly** – Visualization tools.  
- **Tableau / Power BI** – Interactive dashboards.  
- **Jupyter Notebook** – Experimentation, prototyping, and documentation.

---

##  Findings & Insights

- **Dominant Themes** – Conversations focused on humanitarian aid, development policy, and political implications.  
- **Sentiment Patterns** – Highly polarized discourse, with majority of views being strongly positive or negative.  

---

##  Opportunities for Improvement

- **Data Quality** – Some topics from modeling were off-topic, indicating the need for better source filtering.  
- **API Limitations** – API restrictions may have missed certain narratives.  
- **Granular Sentiment** – More fine-grained sentiment models could capture nuanced emotions.

---
##  Acknowledgements
Group Members – For collaborative dataset selection and discussions.
API Providers – Reddit API, News API.
Libraries & Tools – Open-source Python ecosystem contributors.

##  Installation & Requirements

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd <repository-folder>
pip install -r requirements.txt
```
## How to Run

```bash

jupyter notebook notebooks/'****'.ipynb
```
Run all cells in sequence to reproduce the results.
For custom data, replace API keys and adjust data collection parameters in the script