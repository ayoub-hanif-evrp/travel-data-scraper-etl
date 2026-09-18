# Data Quality Report

**Run timestamp:** 2026-09-18T13:06:06+00:00

## Crawl

- Configured destinations: Marrakech, Fes, Essaouira, Chefchaouen, Rabat
- Pages requested: 5
- Pages successfully processed: 5
- Failed pages: 0

## Pipeline counts

- Raw records: 349
- Valid records: 349
- Invalid records: 0
- Duplicates detected: 1
- Duplicates removed: 1
- Final records: 348

## Records by destination

- Marrakech: 133
- Fes: 66
- Rabat: 57
- Chefchaouen: 48
- Essaouira: 44

## Records by category

- sleep: 126
- see: 72
- eat: 71
- do: 44
- drink: 27
- buy: 8

## Field completeness

- address: 206 present (59.2%), 142 missing
- phone: 157 present (45.11%), 191 missing
- email: 76 present (21.84%), 272 missing
- website: 151 present (43.39%), 197 missing
- opening_hours: 58 present (16.67%), 290 missing
- price: 159 present (45.69%), 189 missing
- coordinates: 256 present (73.56%), 92 missing

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
