from Import.CSV_Import_Pipeline import import_csv

import_csv(
    filepath  = "AAPL_2023.csv",
    symbol    = "AAPL",
    name      = "Apple Inc.",
    asset_type= "stock"
)