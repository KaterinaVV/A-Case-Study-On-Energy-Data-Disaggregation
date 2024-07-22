# NILMTK

Install instructions in :
https://github.com/nilmtk/nilmtk/blob/master/docs/manual/user_guide/install_user.md

## NILMTK data format transfer 
Before the disaggregation, the format transfer has to be done in advance,
from .csv file to .h5 file with metadata feeding.

### Raw data
The raw data is **"oth-regensburg-1.csv"** from **oth-regensburg-1** folder. As data 
contains 7 Wohnungen, so divided into 7 folders with second level labeled as 
the month by **"data_all_buildings.ipynb"**. See the outcome folder **"Wohnung"**, the 
file structure is inspired by the data converter for Smart data in NILMTK webpage:
https://github.com/nilmtk/nilmtk/tree/master/nilmtk/dataset_converters/smart

### Raw data transformation to NILMTK-DF .h5 file
The python file for transformation implementation is in **"generate_smartme.py"**.
The function in **"generate_smartme.py"** is called in file **"convert_smartme.ipynb"**, 
and output **"SmartMe.h5"**, which is our target file for disaggregation.

## NILMTK data disaggregation
**"SmartMe.h5"** is then parsed in **"hart_algo.ipynb"**. Some descriptions and the diaggregation for building1 (Wohnung1) are all included in this .ipynb file.
