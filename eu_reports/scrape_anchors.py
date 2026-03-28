import fitz  # PyMuPDF
import os
import re
import pandas as pd

# Define the thematic "Anchors" for the two different eras
ANCHORS = {
    "fundamentals": [r"2\.1\.?\s*Functioning", r"2\.2\.?\s*Rule of law", r"Cluster 1", r"Chapter 23", r"Chapter 24"],
    "economy": [r"3\.?\s*Economic Development", r"2\.3\.?\s*Economic Development"],
    "internal_market": [r"Cluster 2", r"Chapter 1\s", r"Chapter 3\s"] 
}

def fix_encoding(text):
    """Fix common UTF-8 to Windows-1252 encoding artifacts (Mojibake)."""
    replacements = {
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "â€“": "-",
        "\xad": ""  # Soft hyphens
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    # Remove excessive whitespace and newlines often found in PDF extractions
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def classify_sentence(text):
    """Categorize sentences based on EU assessment 'code words'."""
    text_lower = text.lower()
    
    # Action/Status: Indicators of current preparation or implemented progress
    action_indicators = [
        'remains limited', 'has been established', 'is in place', 
        'has adopted', 'no progress', 'some progress', 'well advanced',
        'moderately prepared', 'early stage', 'is operational'
    ]
    
    # Intention/Requirement: Indicators of future needs or recommended policy
    intention_indicators = [
        'should ensure', 'is encouraged to', 'needs to', 'should be',
        'is invited to', 'must prioritize', 'plans to', 'aims at'
    ]
    
    if any(word in text_lower for word in action_indicators):
        return 'Action_Status'
    elif any(word in text_lower for word in intention_indicators):
        return 'Intention_Requirement'
    return 'Description'

def segment_by_sentences(text, year, country):
    """Break text into sentences and attach metadata with a fix for look-behind errors."""
    
    # 1. Clean the text first
    text = fix_encoding(text)
    
    # 2. Use a simpler split that doesn't trigger the fixed-width error
    # This looks for a period followed by a space and an uppercase letter
    raw_sentences = re.split(r'\.\s+(?=[A-Z])', text)
    
    corpus_entries = []
    current_topic = "General"
    
    # Common abbreviations that might cause false splits
    abbreviations = ['no', 'viz', 'i.e', 'e.g', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'art', 'vol']

    processed_sentences = []
    temp_sent = ""

    for s in raw_sentences:
        s = s.strip()
        if not s: continue
        
        # If the previous "sentence" ended in a common abbreviation, re-attach this one
        if temp_sent and any(temp_sent.lower().endswith(f" {abbr}") or temp_sent.lower() == abbr for abbr in abbreviations):
            temp_sent += ". " + s
        else:
            if temp_sent:
                processed_sentences.append(temp_sent)
            temp_sent = s
    
    if temp_sent:
        processed_sentences.append(temp_sent)

    # 3. Process the re-glued sentences
    for sent in processed_sentences:
        if len(sent) < 25: continue 
        
        # Identify thematic section
        for topic, patterns in ANCHORS.items():
            if any(re.search(p, sent, re.IGNORECASE) for p in patterns):
                current_topic = topic
        
        corpus_entries.append({
            "year": year,
            "country": country,
            "topic": current_topic,
            "label": classify_sentence(sent),
            "text": sent + "." # Add the period back
        })
        
    return corpus_entries
    """Break text into sentences and attach metadata."""
    # Split on sentence enders, ensuring we don't split on abbreviations like 'No.' or 'viz.'
    sentences = re.split(r'(?<!\b(?:No|viz|i\.e|e\.g|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\.(?=\s|[A-Z])', text)
    corpus_entries = []
    
    current_topic = "General"
    
    for sent in sentences:
        sent = fix_encoding(sent)
        if len(sent) < 25: continue # Skip fragments and short headers
        
        # Identify if we've moved into a new thematic section
        for topic, patterns in ANCHORS.items():
            if any(re.search(p, sent, re.IGNORECASE) for p in patterns):
                current_topic = topic
        
        corpus_entries.append({
            "year": year,
            "country": country,
            "topic": current_topic,
            "label": classify_sentence(sent),
            "text": sent
        })
    return corpus_entries

# --- Main Execution ---
output_dir = "corpus_processed"
os.makedirs(output_dir, exist_ok=True)
pdf_files = [f for f in os.listdir('.') if f.endswith(('.pdf', '.PDF'))]

final_corpus = []

for filename in pdf_files:
    clean_name = filename.lower().replace(".pdf", "")
    parts = re.split(r"[-_]", clean_name)
    year = next((p for p in parts if re.fullmatch(r"\d{4}", p)), "Unknown")
    country = parts[0]

    print(f"🚀 Processing: {country} {year}")

    try:
        doc = fitz.open(filename)
        full_text = ""
        for i in range(doc.page_count):
            # Extracting page text and cleaning markers
            page_text = doc.load_page(i).get_text("text")
            full_text += page_text + " "
        
        sentences = segment_by_sentences(full_text, year, country)
        final_corpus.extend(sentences)
        doc.close()
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")

# Create DataFrame
df = pd.DataFrame(final_corpus)

# Filtering Noise: Remove Table of Contents dots and PDF artifacts
df = df[~df['text'].str.contains(r'\.\.\.\.\.', regex=True)]
df = df[~df['text'].str.contains('Table of Contents', case=False)]

# Final cleanup of numbers at start of sentences
df['text'] = df['text'].str.replace(r'^\d+\.?\s*', '', regex=True)

df.to_csv(os.path.join(output_dir, "enlargement_corpus.csv"), index=False)
print(f"\n✨ Done! Created corpus with {len(df)} tagged sentences in '{output_dir}/enlargement_corpus.csv'")