# SKU sales forecast

Predicts daily sales volume (qty) for each SKU, **14 days ahead**, and explains every forecast to the sales team with **SHAP**.

The company forecasts demand from staff experience. That leads to stockouts of best-sellers, overstock of slow movers, and purchase plans that are hard to justify. This project replaces that with a model, a hold-out test against simple rules of thumb, and a report the sales team can read.

| Input | | Output | | |
|---|---|---|---|---|
| **Date** | **SKU** | **Date** | **SKU** | **qty** |
| 2022-01-04 | FJDJ6B | 2022-01-04 | FJDJ6B | 2,489 |

---

## Results

Tested on the **last 8 weeks** of data (9 Nov 2021 to 2 Jan 2022, the holiday peak), which the model never saw during training. Every forecast is made 14 days ahead.

| Method | WMAPE | MAE | RMSE | R² | Bias |
|---|---|---|---|---|---|
| **Model (Random Forest)** | **53.5%** | **79** | **343** | **0.631** | −17.5% |
- The model beats both rules of thumb on every error metric. On two earlier 8-week validation windows (checked during development) it also won: 50.7% vs 53.3% WMAPE, and 48.0% vs 51.4%.
- **A-class SKUs** (80 SKUs, 75% of units) have a WMAPE of 46.7%, vs 50.3% for the 4-week average. These SKUs matter most for stockouts.
- **Weak spot:** in the holiday peak the model under-forecasts total volume by 17.5%. It only sees the surge once it appears in sales from 2+ weeks earlier, and with one year of data it has never seen a previous peak. Plan Nov–Dec purchases with a seasonal uplift or extra safety stock until a second year of data exists.

### What the metrics mean

| Metric | Meaning |
|---|---|
| **WMAPE** | Total absolute error ÷ total units sold. The main business metric. Unlike MAPE, it is not blown up by SKU-days that sell 0–1 units. |
| **MAE** | Average miss per SKU-day, in units. |
| **RMSE** | Like MAE, but squares errors first, so big misses count more. RMSE far above MAE means a few large misses (spikes, best-sellers) dominate. |
| **R²** | Share of day-to-day variation explained. 1 = perfect, 0 = no better than always predicting the average. |

---

## Data findings (read before modelling this dataset)

`data/sales.csv`: 48,363 rows, 676 SKUs, 6 sales channels (AWH, ADS, FBA, FBM, ADI, LAL), from 1 Jan 2021 to 2 Jan 2022.

1. **`MOQ order` leaks the target.** For every SKU it equals exactly 1×, 2× or 3× that SKU's total qty across the whole file, so it is computed from future sales. A model that uses it looks far better than it really is. **Not used.**
2. **One record every 2 days.** There are 184 dates, always exactly 2 days apart, so a "day" here is a sales day on a 2-day cadence. It is worth asking the company whether each record covers 1 or 2 days.
3. **Incomplete days.** 7 Jan, 28 Oct, 19 Dec and 21 Dec 2021 have fewer than half the usual records (21 Dec has a single record vs about 270 normally). These are treated as missing, not as zero demand.
4. **No record = 0 sold.** Missing SKU-days are filled with 0, which is 55% of SKU-days. Without stock data, "no demand" can't be told apart from "out of stock".
5. **Returns.** 3 rows have negative qty. Each SKU-day is clipped at 0.
6. **Calendar-like features removed.** SKU age and store-wide totals were tried. 244 of 676 SKUs first appear on the file's first day, so these features mostly encode the calendar date. The trees can't extrapolate that past the training period, and it pushed the test forecast about 16% too high.

---

## How it works

1. **Aggregate:** sum qty and revenue across channels into one row per SKU per day.
2. **Grid:** every SKU × every date from its first sale onwards, plus 14 future days to forecast.
3. **Features:** each one uses only sales **at least 14 days older** than the forecast day. That is what makes a 14-day-ahead forecast honest, and `forecast.py` asserts it on every run (`check_no_leakage`).

   | Feature | Meaning |
   |---|---|
   | Avg sales, prior 2 / 4 / 8 wks | Recent sales level |
   | Sales 2 / 4 wks before | Same weekday, 14 and 28 days earlier |
   | Sales swings, prior 4 wks | Volatility (std) |
   | Days with a sale, 8 wks | How intermittent the SKU is |
   | Days since last sale | Detects dormant SKUs |
   | Avg price, prior 8 wks | Revenue ÷ qty, captures discounts |
   | Day of week, day of month | Weekly and payday patterns |

4. **Model:** scikit-learn `HistGradientBoostingRegressor` with a **Poisson loss**, which suits non-negative counts with many zeros. One global model covers all SKUs.
5. **Evaluate:** train on data before the last 8 weeks, score on the last 8 weeks, and compare with the two rules of thumb.
6. **Forecast:** retrain on all data and forecast the next 14 days, written to `outputs/forecast.csv`.
7. **Explain:** SHAP `TreeExplainer` (exact). Because of the Poisson loss, the model predicts in log space, so each factor **multiplies** the forecast (for example ×1.4). The report converts those multipliers into units: the gap between a typical SKU-day and the forecast is split in proportion to each factor's SHAP value, so the bars add up exactly to the forecast.

### Using SHAP with the sales team

The report has two views:

- **What drives the forecast:** a beeswarm of every factor across the test window. Recent sales level and days since the last sale dominate.
- **Explain one forecast:** pick a SKU and a day to see a waterfall in units plus a plain-language sentence. For example: *"The model starts from a typical SKU-day of 15 units. The biggest push up is 'Avg sales, prior 8 wks' (2,864 units/day), +1,131 units."*

---

It takes about 20 seconds. It prints the metrics table and writes:

| File | What |
|---|---|
| `outputs/forecast.csv` | Next 14 days for every SKU: `Date, SKU, qty` |
| `outputs/test_predictions.csv` | Test window: actual, model forecast, both baselines |
| `index.html` | The report. Open it locally, or push and GitHub Pages serves it |

To update the live report, run the script, then commit and push `index.html`.

## Project structure

```


## Limitations and next steps

- **One year of history.** Seasonality (the Nov–Dec peak) can't be learned yet. A second year, or a holiday/promo calendar, would help most.
- **No stock data.** Zero sales may be stockouts. Inventory levels would let the model learn true demand.
- **Fixed hyperparameters.** Tuning on rolling time splits could add a few points of accuracy.
- **Shorter horizons.** A 7-day model would be more accurate where lead times allow it.
