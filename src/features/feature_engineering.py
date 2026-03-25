import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import OneHotEncoder

FEATURES = [
	"type",
	"price",
	"price_m2",
	"surface",
	"city",
	"zipcode",
	"region",
	"author",
	"created_at",
]

TO_ENCODE = [
	"type",
]


def clustering(df: pd.DataFrame, on_cols: list = ["price", "surface"], n_clusters=4) -> pd.DataFrame:
	df = df.copy()
	X = df[on_cols]
	kmeans = KMeans(n_clusters=n_clusters)
	kmeans.fit(X)
	labels = kmeans.labels_
	df["cluster"] = labels
	return df


def feature_selection(df: pd.DataFrame) -> pd.DataFrame:
	df = df.copy()
	df = df[FEATURES]
	if df["zipcode"].dtype != "object":
		df["zipcode"] = df["zipcode"].astype("object")
	return df


def category_encoding(df: pd.DataFrame, categories: list = None) -> pd.DataFrame:
	if categories is None:
		categories = ["type"]
	df = df.copy()
	enc = OneHotEncoder(handle_unknown="ignore")
	encoded_features = enc.fit_transform(df[categories])
	return df


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
	df = feature_selection(df)
	df = clustering(df)
	# df = category_encoding(df)
	return df
