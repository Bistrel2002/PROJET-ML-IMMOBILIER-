import pandas as pd
from pickle import dump, load
from sklearn.cluster import KMeans
from sklearn.preprocessing import OneHotEncoder

KMEANS_FILE = "saved_models/kmeans.pickle"

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
	with open(KMEANS_FILE, "wb") as file:
		dump(kmeans, file, protocol=5)
	labels = kmeans.labels_
	df["cluster"] = labels
	return df


def predict_cluster(df: pd.DataFrame) -> pd.DataFrame:
	with open(KMEANS_FILE, "rb") as file:
		kmeans = load(file)
	df = df.copy()
	labels = kmeans.predict(df[kmeans.feature_names_in_])
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
