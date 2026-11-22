import math
import os
import pickle
from contextlib import closing

import psycopg2

from flask import Flask, jsonify, request
from psycopg2.extras import Json


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

model_path = os.getenv("MODEL_PATH", "/model/model.pkl")

with open(model_path, "rb") as f:
    bundle = pickle.load(f)

model = bundle["model"]
VERSION = bundle["model_version"]
FEATURE_NAMES = bundle["feature_names"]


def get_db():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        sslmode=os.getenv("DB_SSLMODE", "require"),
        connect_timeout=5,
        application_name="ml-app-lab4",
    )


@app.get("/health")
def health():
    return jsonify(
        status="ok",
        model_version=VERSION,
    )


@app.post("/predict")
def predict():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="Expected a JSON object"), 400

    features = data.get("features")

    if not isinstance(features, list) or len(features) != 10:
        return jsonify(
            error="Expected a list of 10 numbers",
            feature_order=FEATURE_NAMES,
        ), 400

    for value in features:
        if type(value) not in (int, float):
            return jsonify(
                error="All features must be numbers"
            ), 400

        if not -1_000_000 <= value <= 1_000_000:
            return jsonify(error="Invalid feature value"), 400

    prediction = float(model.predict([features])[0])

    if not math.isfinite(prediction):
        return jsonify(error="Invalid model result"), 500

    result = {
        "prediction": round(prediction, 2),
        "model_version": VERSION,
    }

    try:
        with closing(get_db()) as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO public.predictions
                            (input_data, prediction, model_version)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            Json({"features": features}),
                            Json(result),
                            VERSION,
                        ),
                    )

    except psycopg2.Error:
        app.logger.exception("Database operation failed")
        return jsonify(error="Database unavailable"), 503

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
