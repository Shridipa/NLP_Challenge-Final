import json
import sys
import re
from transformers import pipeline

print("Loading global sentiment analysis pipeline...")
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

print("Loading global distilled pipeline for urgency detection...")
zero_shot_pipeline = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")

def analyze_sentiment_and_urgency(query):
    """
    Determines sentiment (positive, neutral, negative) and urgency (true/false).
    """
    # 1. Sentiment Analysis
    sentiment_result = sentiment_pipeline(query)[0]
    label = sentiment_result['label'].lower()
    score = sentiment_result['score']
    
    if label == "positive" and score > 0.6:
        final_sentiment = "positive"
    elif label == "negative" and score > 0.6:
        final_sentiment = "negative"
    else:
        final_sentiment = "neutral"
        
    # 2. Urgency Detection
    # Use more distinct labels to prevent "serious" business queries from being flagged as urgent
    candidate_labels = ["urgent assistance required", "informational or general inquiry"]
    urgency_result = zero_shot_pipeline(query, candidate_labels)
    
    # Check if top label is urgent AND score is high
    is_urgent_ml = (
        urgency_result['labels'][0] == "urgent assistance required" 
        and urgency_result['scores'][0] > 0.85 # Increased threshold
    )
    
    # 3. Urgency Signal Detection (Heuristics)
    urgency_signals = []
    # Added parenthetical versions like (urgent) which are common in user tests
    keywords = [
        r"\basap\b", r"\burgent\b", r"\bcritical\b", r"\bimmediately\b", 
        r"\bfire\b", r"\bemergency\b", r"\bstuck\b", 
        r"\bblocking\b", r"\bdeadline\b",
        r"\(urgent\)", r"\(asap\)", r"\(critical\)" 
    ]
    
    for kw in keywords:
        if re.search(kw, query, re.IGNORECASE):
            # Clean up the signal name for reporting
            signal_name = re.sub(r'\\b|\(|\)', '', kw)
            urgency_signals.append(signal_name)
            
    final_urgent = is_urgent_ml or len(urgency_signals) > 0
    
    # SENTIMENT CORRECTION
    # If it's a financial/informational query, override 'negative' sentiment from SST-2
    # SST-2 is trained on movie reviews and often thinks "loss" or "risk" is negative sentiment,
    # but in business analysis, it's neutral/factual.
    if not final_urgent and (label == "negative" and score < 0.9):
         final_sentiment = "neutral"
    
    return {
        "sentiment": final_sentiment,
        "urgent": final_urgent,
        "signals": urgency_signals
    }

if __name__ == "__main__":
    test_query = sys.argv[1] if len(sys.argv) > 1 else "My laptop is broken and I have a meeting in 5 minutes! HELP!!!"
    try:
        results = analyze_sentiment_and_urgency(test_query)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error in analysis: {e}")
