from os import path, listdir
import pandas as pd

RAW_DIR = "data/raw/"


def list_raw_files() -> list:
	"""
	Lists the names of the csv files in the RAW_DIR sorted in descending order
	:return: list of csv filenames
	"""
	try:
		raw_path = RAW_DIR
		if not path.exists(raw_path):
			raw_path = path.join("..", raw_path)
		raw_files = listdir(raw_path)
	except FileNotFoundError:
		raise FileNotFoundError("data/raw/ does not exist")
	raw_files = [file for file in raw_files if file[-4:] == ".csv"]
	raw_files.sort(reverse=True)
	return raw_files


def raw_dataframe(filename: str) -> pd.DataFrame:
	"""
	Returns a pandas dataframe from the csv file in the RAW_DIR corresponding to the filename
	:param filename: name of the csv file
	:return: pandas dataframe
	"""
	if not ".csv" in filename:
		filename = f"{filename}.csv"
	if not RAW_DIR in filename:
		filename = path.join("data/raw", filename)
		if not path.exists(filename):
			filename = path.join("..", filename)
	if not path.exists(filename):
		raise FileNotFoundError(f"{filename} does not exist")
	df = pd.read_csv(filename, header=0, index_col=0)
	return df


def get_latest_raw_dataframe() -> pd.DataFrame:
	"""
	Returns a pandas dataframe from the latest csv file in the RAW_DIR
	:return: pandas dataframe
	"""
	raw_files = list_raw_files()
	raw_df = raw_dataframe(raw_files[0])
	return raw_df
