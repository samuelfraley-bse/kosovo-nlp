import os
import re
import pandas as pd
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer

# 1. Define your data path
data_path = r'C:\Users\sffra\Downloads\BSE 2025-2026\kosovo_nlp\scraped'

# 2. Section Extraction Function
def extract_main_findings(text):
    # Regex to find the start of 1.2 and the start of Section 2
    # Accommodates slight variations in capitalization found in the reports
    start_pattern = r"1\.2\.?\s+(?:Main findings of the report|Summary of the report)"
    end_pattern = r"2\.\s+[Tt]he [Ff]undamentals of the [Aa]ccession [Pp]rocess"
    
    try:
        start_match = re.search(start_pattern, text)
        end_match = re.search(end_pattern, text)
        if start_match and end_match:
            return text[start_match.end():end_match.start()].strip()
    except Exception as e:
        return ""
    return ""

# 3. Custom Stopwords
# These are essential to filter out "noise" words that dominate EU reports
custom_stopwords = ['kosovo', 'eu', 'european', 'commission', 'report', 'year', 'progress', 
                   'level', 'continued', 'remained', 'further', 'overall', 'implementation']

# 4. Analysis Pipeline
def run_ngram_analysis(file_list):
    results = []
    
    for file_name in file_list:
        with open(os.path.join(data_path, file_name), 'r', encoding='utf-8') as f:
            raw_text = f.read()
            
        # Extract Section 1.2
        summary_text = extract_main_findings(raw_text)
        if not summary_text:
            continue
            
        # A. Raw Analysis (Unigrams & Bigrams)
        # B. Cleaned Analysis (Applying Stopwords)
        for stop_list in [None, custom_stopwords]:
            label = "Raw" if stop_list is None else "Cleaned"
            
            # Unigrams
            vec_uni = CountVectorizer(stop_words=stop_list, ngram_range=(1, 1)).fit([summary_text])
            bag_uni = vec_uni.transform([summary_text])
            sum_words = bag_uni.sum(axis=0)
            words_freq = [(word, sum_words[0, idx]) for word, idx in vec_uni.vocabulary_.items()]
            top_uni = sorted(words_freq, key=lambda x: x[1], reverse=True)[:5]
            
            # Bigrams
            vec_bi = CountVectorizer(stop_words=stop_list, ngram_range=(2, 2)).fit([summary_text])
            bag_bi = vec_bi.transform([summary_text])
            sum_bi = bag_bi.sum(axis=0)
            bi_freq = [(word, sum_bi[0, idx]) for word, idx in vec_bi.vocabulary_.items()]
            top_bi = sorted(bi_freq, key=lambda x: x[1], reverse=True)[:5]
            
            results.append({
                "Year": file_name.split('.')[0],
                "Type": label,
                "Top Unigrams": top_uni,
                "Top Bigrams": top_bi
            })
            
    return pd.DataFrame(results)

# Run the pipeline
# files = [f for f in os.listdir(data_path) if f.endswith('.txt')]
# df_results = run_ngram_analysis(files)
# print(df_results)