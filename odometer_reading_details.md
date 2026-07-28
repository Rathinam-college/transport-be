# Odometer Reading Details

This document explains the contents of the provided image (`reference-image\image.png`), which displays a detailed spreadsheet tracking the daily odometer readings for a fleet of college vehicles.

## General Overview
- **Title:** "College KM Details Oct'25"
- **Purpose:** The spreadsheet tracks the distance traveled by different vehicles on various routes over a series of dates. It records morning and afternoon odometer readings to calculate actual run kilometers, additional kilometers, and total kilometers.

## Data Columns

The leftmost section contains standard identifying information for each vehicle:
- **S.No:** Serial number (rows 1 to 8).
- **Vehicle No:** Registration numbers of the vehicles (e.g., `TN99 Q 3209`, `TN99 Q 4686`).
- **ROUTE:** The designated route or status for the vehicle (e.g., `UDAYAMPALAYAM`, `TIRUPUR`, `SPARE`, `THUDIYALUR`, `KANUVAI`).
- **Approved daily trip KM:** The standard expected distance for the route. This column is mostly highlighted in green, with one exception highlighted in orange (Row 6 - `THUDIYALUR`, 70 KM).
- **is_active:** Boolean flag indicating if the vehicle is in working condition and running. If false, it is under maintenance or inactive.
- **is_tracking:** Boolean flag indicating if the vehicle should be monitored with an odometer and available on odometer entry and reports.

## Date-Specific Tracking

Following the identifying columns, the spreadsheet is divided into sections by date (e.g., `01-05-2026`, `02-06-2026`, `03-06-2026`, `04-06-2026`). Under each date, there are five specific sub-columns:

1. **9.30am:** The morning (opening) odometer reading.
2. **3.30pm:** The afternoon (closing) odometer reading.
3. **Actual run Kms:** The difference between today's 9.30am reading and the previous working day's 3.30pm reading (distance covered overnight/early morning before the day shift).
4. **Additional Kms:** The difference between today's 3.30pm reading and today's 9.30am reading (distance covered during the day shift).
5. **Total kms:** The sum of `Actual run Kms` and `Additional Kms`.

## Color Coding
- The headers for dates `01-05-2026`, `02-06-2026`, and `04-06-2026` along with their sub-columns are highlighted with a bright yellow background.
- The header for `03-06-2026` has a light peach/pink background, with its sub-columns alternating between white and light blue backgrounds.
- The `Approved daily trip KM` column is highlighted in green for most rows, but orange for Row 6 (THUDIYALUR) and Row 8 (SPARE is green, but row 6 is orange).

## Sample Data Observations
- **Row 1 (`TN99 Q 3209`):** Travels the `UDAYAMPALAYAM` route. On `01-05-2026`, its 9:30am reading was `188969`. The previous reading was `188896`. Actual run kms = `188969 - 188896 = 73`. Its 3:30pm reading was `188969`, so Additional kms = `188969 - 188969 = 0`. Total = `73`.
- **Row 3 (`TN99 Q 4696`):** On `01-05-2026`, 9:30am reading `172413` minus previous reading `172295` gives `118` Actual run kms. 3:30pm reading `172416` minus 9:30am reading `172413` gives `3` Additional kms. Total = `118 + 3 = 121` kms.
- **Vehicles marked as `SPARE`** (Rows 5 and 8) still log kilometers, indicating they were utilized on those specific days. Row 5 logged `426` total kms on `01-05-2026`.
