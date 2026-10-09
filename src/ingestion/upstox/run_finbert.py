
from pathlib import Path

import pandas as pd
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

MODEL_NAME = "ProsusAI/finbert"

INPUT_PATH = Path("data/raw/news/upstox_news.csv")
OUTPUT_PATH = Path("data/processed/news/finbert_sentiment.csv")


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"News dataset not found: {INPUT_PATH}"
        )

    news = pd.read_csv(INPUT_PATH)

    if news.empty:
        raise ValueError("The news dataset is empty.")

    news["headline"] = news["headline"].fillna("")
    news["summary"] = news["summary"].fillna("")

    # Combine headline and summary for richer context.
    news["text"] = (
        news["headline"].str.strip()
        + ". "
        + news["summary"].str.strip()
    ).str.strip()

    print("Loading FinBERT:", MODEL_NAME)
    print("Device: CPU")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME
    )
    model.eval()

    results = []

    # Small batches are appropriate for an 8 GB RAM laptop.
    batch_size = 2

    for start in range(0, len(news), batch_size):
        batch = news["text"].iloc[start:start + batch_size].tolist()

        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )

        with torch.inference_mode():
            outputs = model(**inputs)
            probabilities = torch.softmax(
                outputs.logits,
                dim=-1,
            )

        for text, scores in zip(batch, probabilities.tolist()):
            score_by_label = {
                model.config.id2label[i].lower(): float(score)
                for i, score in enumerate(scores)
            }

            results.append({
                "positive": score_by_label["positive"],
                "neutral": score_by_label["neutral"],
                "negative": score_by_label["negative"],
                "predicted_sentiment": max(
                    score_by_label,
                    key=score_by_label.get,
                ),
            })

        print(
            f"Processed {min(start + batch_size, len(news))}"
            f" / {len(news)} articles"
        )

    sentiment = pd.DataFrame(results)

    # Keep source data and predictions together for traceability.
    output = pd.concat(
        [
            news.drop(columns=["text"]),
            sentiment,
        ],
        axis=1,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(OUTPUT_PATH, index=False)

    print("\nFinBERT inference completed.")
    print("Articles scored:", len(output))
    print("\nSentiment predictions:")
    print(
        output[
            [
                "headline",
                "positive",
                "neutral",
                "negative",
                "predicted_sentiment",
            ]
        ].to_string(index=False)
    )
    print("\nSaved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
