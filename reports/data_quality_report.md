# Data Quality Report

**Run timestamp:** 2026-09-18T13:31:57+00:00

## Crawl

- Configured destinations: Marrakech, Paris, Barcelona, Rome, Istanbul, Bangkok
- Pages requested: 6
- Pages successfully processed: 6
- Failed pages: 0

## Pipeline counts

- Raw records: 316
- Valid records: 316
- Invalid records: 0
- Duplicates detected: 1
- Duplicates removed: 1
- Final records: 315

## Records by destination

- Marrakech: 133
- Bangkok: 77
- Paris: 60
- Barcelona: 28
- Rome: 11
- Istanbul: 6

## Records by country

- Morocco: 133
- Thailand: 77
- France: 60
- Spain: 28
- Italy: 11
- Turkey: 6

## Records by category

- see: 146
- do: 64
- sleep: 52
- eat: 34
- drink: 11
- buy: 8

## Field completeness

- address: 201 present (63.81%), 114 missing
- phone: 192 present (60.95%), 123 missing
- email: 117 present (37.14%), 198 missing
- website: 209 present (66.35%), 106 missing
- opening_hours: 65 present (20.63%), 250 missing
- price: 74 present (23.49%), 241 missing
- coordinates: 244 present (77.46%), 71 missing

## Rejection reasons

- None

## Generated outputs

- csv: `data/processed/travel_listings.csv`
- jsonl: `data/processed/travel_listings.jsonl`
- sqlite: `data/processed/travel_listings.sqlite`
- sample_csv: `data/sample/travel_listings_sample.csv`
- sample_jsonl: `data/sample/travel_listings_sample.jsonl`
- quality_md: `reports/data_quality_report.md`
- quality_json: `reports/data_quality_report.json`
