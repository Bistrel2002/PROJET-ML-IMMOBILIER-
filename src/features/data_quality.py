import pandas as pd

DATA_CONSTRAINTS = {
	"price": lambda price: price > 0,
	"surface": lambda surface: surface > 0,
	"price_m2": lambda price_m2: price_m2 < 50000,
	"city": lambda city: city is not None,
	"type": lambda type: type is not None,
}


def extract_m2(df: pd.DataFrame) -> pd.DataFrame:
	df = df.copy()
	area = df.title.str.extract(r"(?P<area>\d+)(\sm)(²|2)").area
	df["surface"] = pd.to_numeric(area)
	df["price_m2"] = df["price"] / df["surface"]
	return df


def validate_ban(df: pd.DataFrame) -> pd.DataFrame:
	return NotImplemented


def validate_constraints(df: pd.DataFrame) -> pd.DataFrame:
	df = df.copy()
	for column, condition in DATA_CONSTRAINTS.items():
		df = df[df[column].map(condition)]
	return df
