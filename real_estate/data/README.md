# Data

## Files

### `kc_house_data_synthetic.csv`
Synthetic dataset of 500 residential property sales modeled after the King County, Washington housing dataset. Features realistic distributions: right-skewed prices, predominance of 3-4 bedroom homes, coordinates bounded to King County, and intentionally injected NaN values in bedrooms (~2.5%) and bathrooms (~2%) for data wrangling exercises.

| Column | Type | Description |
|--------|------|-------------|
| Unnamed: 0 | int | Sequential index (legacy from original CSV format) |
| id | int | Unique cadastral-style property ID |
| date | str | Sale date in YYYYMMDDTHHMMSS format (May 2014 - May 2015) |
| price | float | Sale price in USD (75,000 - 5,000,000) |
| bedrooms | float | Number of bedrooms (1-6, with ~2.5% NaN) |
| bathrooms | float | Number of bathrooms (0.5-5.0 in 0.25 increments, with ~2% NaN) |
| sqft_living | int | Interior living area in square feet |
| sqft_lot | int | Lot size in square feet |
| floors | float | Number of floors (1.0, 1.5, 2.0, 2.5, 3.0) |
| waterfront | int | Waterfront property flag (0 or 1, ~1% waterfront) |
| view | int | View quality rating (0-4, majority 0) |
| condition | int | Property condition rating (1-5, centered at 3) |
| grade | int | Building grade (construction quality index) |
| sqft_above | int | Above-ground living area in square feet |
| sqft_basement | int | Basement area in square feet |
| yr_built | int | Year the house was built |
| yr_renovated | int | Year of last renovation (0 if never renovated) |
| zipcode | int | 5-digit ZIP code within King County |
| lat | float | Latitude coordinate |
| long | float | Longitude coordinate |
| sqft_living15 | int | Average interior living area of the 15 nearest neighbors |
| sqft_lot15 | int | Average lot size of the 15 nearest neighbors |

## Regeneration

To regenerate the data file, run from the project root:

```bash
python src/data_generator.py
```

The file is generated deterministically with `np.random.seed(42)`.
