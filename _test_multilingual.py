from transformers import pipeline

MODEL = "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual"
print("Loading multilingual model...")
p = pipeline("sentiment-analysis", model=MODEL, tokenizer=MODEL, top_k=1, truncation=True, max_length=512)
print("Model loaded!\n")

tests = [
    ("Que video incrivel, amei demais!", "PT-positive"),
    ("Esse video e horrivel, odiei", "PT-negative"),
    ("normal, nada demais", "PT-neutral"),
    ("I love this video!", "EN-positive"),
    ("This is terrible", "EN-negative"),
]

for text, expected in tests:
    result = p(text)
    label = result[0][0]["label"] if isinstance(result[0], list) else result[0]["label"]
    score = result[0][0]["score"] if isinstance(result[0], list) else result[0]["score"]
    print(f"  {expected:15s} | {label:10s} {score:.3f} | \"{text}\"")

print("\nDone!")
