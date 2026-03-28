import pandas as pd
import re
import os

# 1. Define your Research Dictionaries
REFORM_WORDS = ['progress', 'implemented', 'improved', 'adopted', 'alignment', 
                'positive', 'strengthened', 'established', 'functional', 'advanced']

CRITICISM_WORDS = ['concern', 'weak', 'lack', 'limited', 'backsliding', 
                   'insufficient', 'delay', 'outstanding', 'pressure', 'interference']

def preprocess_text(text):
    """Standard NLP preprocessing as per your methodology."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text) # Remove punctuation
    return text

def get_word_counts(text, dictionary):
    """Counts occurrences of dictionary words in text."""
    words = text.split()
    return sum(1 for word in words if word in dictionary), len(words)

# 2. Load the Master Corpus
df = pd.read_csv('corpus_processed/enlargement_corpus.csv')

# 3. Apply Scoring at Sentence Level
df['clean_text'] = df['text'].apply(preprocess_text)

results = []
for index, row in df.iterrows():
    ref_count, total_words = get_word_counts(row['clean_text'], REFORM_WORDS)
    crit_count, _ = get_word_counts(row['clean_text'], CRITICISM_WORDS)
    
    results.append({
        'reform_count': ref_count,
        'crit_count': crit_count,
        'word_count': total_words
    })

df_scores = pd.concat([df, pd.DataFrame(results)], axis=1)

# 4. Aggregate to Country-Year Level (Your Research Unit)
# This fulfills your 'Data' requirement for country-year level observations
final_analysis = df_scores.groupby(['country', 'year']).agg({
    'reform_count': 'sum',
    'crit_count': 'sum',
    'word_count': 'sum'
}).reset_index()

# 5. Compute Final Research Metrics
final_analysis['ReformScore'] = final_analysis['reform_count'] / final_analysis['word_count']
final_analysis['CriticismScore'] = final_analysis['crit_count'] / final_analysis['word_count']
final_analysis['NetScore'] = final_analysis['ReformScore'] - final_analysis['CriticismScore']

# Export for Visualization
final_analysis.to_csv('country_year_analysis.csv', index=False)
print("Analysis Complete. Country-Year scores generated.")