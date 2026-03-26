from os import path, listdir
from pathlib import Path
import pandas as pd

# Compute project root as two levels up from this file (src/features/ -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = str(PROJECT_ROOT / "data" / "raw")


def list_raw_files() -> list:
    """
    Lists the names of the csv files in the RAW_DIR sorted in descending order.
    :return: list of csv filenames
    """
    try:
        raw_files = listdir(RAW_DIR)
    except FileNotFoundError:
        raise FileNotFoundError(f"{RAW_DIR} does not exist")
    raw_files = [file for file in raw_files if file[-4:] == ".csv"]
    raw_files.sort(reverse=True)
    return raw_files


def raw_dataframe(filename: str) -> pd.DataFrame:
    """
    Returns a pandas dataframe from the csv file in the RAW_DIR corresponding to the filename.
    :param filename: name of the csv file
    :return: pandas dataframe
    """
    if ".csv" not in filename:
        filename = f"{filename}.csv"
    if RAW_DIR not in filename:
        filename = path.join(RAW_DIR, filename)
    if not path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist")
    df = pd.read_csv(filename, header=0, index_col=0)
    return df


def get_latest_raw_dataframe() -> pd.DataFrame:
    """
    Returns a pandas dataframe from the latest csv file in the RAW_DIR.
    :return: pandas dataframe
    """
    raw_files = list_raw_files()
    raw_df = raw_dataframe(raw_files[0])
    return raw_df


def load_raw(filename: str = None) -> pd.DataFrame:
    """
    Step 1 of the pipeline — loads the raw CSV as-is.
    Column renaming and cleaning are handled by the subsequent steps:
      data_quality.data_quality(df)  →  data_cleaner.clean_leboncoin_data(df)

    :param filename: optional CSV filename inside data/raw/; if None the
                     most recent file is used (alphabetically last)
    :return: unmodified raw DataFrame
    """
    if filename is not None:
        return raw_dataframe(filename)
    return get_latest_raw_dataframe()
