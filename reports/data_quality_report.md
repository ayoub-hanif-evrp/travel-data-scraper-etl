# Data Quality Report

**Run timestamp:** 2026-09-18T15:38:44+00:00

## Crawl

- Configured destinations: Marrakech, Paris, Rome, Istanbul, Bangkok, Tokyo, New York City, Mexico City, Buenos Aires, Cape Town, Sydney
- Pages requested: 11
- Pages successfully processed: 11
- Failed pages: 0

## Pipeline counts

- Raw records: 636
- Valid records: 626
- Invalid records: 10
- Duplicates detected: 2
- Duplicates removed: 2
- Final records: 624

## Records by destination

- Cape Town: 184
- Marrakech: 132
- Mexico City: 86
- Bangkok: 77
- Paris: 60
- Sydney: 25
- Buenos Aires: 17
- New York City: 14
- Tokyo: 13
- Rome: 10
- Istanbul: 6

## Records by country

- South Africa: 184
- Morocco: 132
- Mexico: 86
- Thailand: 77
- France: 60
- Australia: 25
- Argentina: 17
- United States: 14
- Japan: 13
- Italy: 10
- Turkey: 6

## Records by category

- see: 221
- do: 180
- sleep: 95
- eat: 58
- buy: 50
- drink: 20

## Field completeness

- address: 386 present (61.86%), 238 missing
- phone: 364 present (58.33%), 260 missing
- email: 230 present (36.86%), 394 missing
- website: 388 present (62.18%), 236 missing
- opening_hours: 123 present (19.71%), 501 missing
- price: 151 present (24.2%), 473 missing
- coordinates: 409 present (65.54%), 215 missing

## Rejection reasons

- invalid_name: 10

## Generated outputs

- csv: `data/processed/travel_listings.csv`
- jsonl: `data/processed/travel_listings.jsonl`
- sqlite: `data/processed/travel_listings.sqlite`
- sample_csv: `data/sample/travel_listings_sample.csv`
- sample_jsonl: `data/sample/travel_listings_sample.jsonl`
- rejected: `data/processed/rejected_records.jsonl`
- quality_md: `reports/data_quality_report.md`
- quality_json: `reports/data_quality_report.json`
