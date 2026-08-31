# Review-theme methodology

The Milestone 8 analyzer is a transparent rule-based baseline.

1. Normalize Unicode, lowercase text, remove non-semantic punctuation, and
   collapse whitespace.
2. Split contrastive clauses at words such as `but` and `although` and at
   commas or semicolons.
3. Match explicit vocabularies for 15 themes.
4. Count positive and negative terms within the same clause.
5. Attach sentiment and the clause as evidence to each matched theme.
6. Aggregate review predictions by theme and sentiment.
7. Only after extraction, compare predicted review/theme/sentiment tuples with
   the separately stored synthetic ground truth.

Current synthetic evaluation is precision 0.9655, recall 1.0000, and F1 0.9825.
These values measure performance on controlled template text only. Rules can
miss synonyms, sarcasm, negation, multilingual phrasing, implicit meaning, and
context across sentences. They can also over-trigger shared sentiment words.
The baseline is useful for comparison, not evidence of production accuracy.
