import json
import pickle
from pathlib import Path

from sklearn.datasets import load_diabetes
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


OUT = Path(__file__).resolve().parent
VERSION = "diabetes-linear-v1"

# Загружаем исходные числовые признаки.
data = load_diabetes(scaled=False)

X = data.data
y = data.target

# Разделяем данные на обучение и тест.
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
)

# Масштабирование и линейная регрессия.
model = make_pipeline(
    StandardScaler(),
    LinearRegression(),
)

model.fit(X_train, y_train)

# Проверяем качество на тестовой выборке.
predictions = model.predict(X_test)

metrics = {
    "dataset": "Diabetes",
    "model_version": VERSION,
    "total_rows": len(X),
    "features": data.feature_names,
    "train_rows": len(X_train),
    "test_rows": len(X_test),
    "MAE": float(mean_absolute_error(y_test, predictions)),
    "R2": float(r2_score(y_test, predictions)),
}

# Сохраняем модель вместе с масштабированием.
bundle = {
    "model": model,
    "model_version": VERSION,
    "feature_names": data.feature_names,
}

with (OUT / "model.pkl").open("wb") as f:
    pickle.dump(bundle, f)

(OUT / "model.pkl").chmod(0o644)

# Сохраняем метрики.
(OUT / "metrics.json").write_text(
    json.dumps(metrics, indent=2),
    encoding="utf-8",
)

# Создаём два готовых запроса для API.
for number in range(2):
    request_data = {
        "features": X_test[number].tolist()
    }

    (OUT / f"request{number + 1}.json").write_text(
        json.dumps(request_data, indent=2),
        encoding="utf-8",
    )

print(json.dumps(metrics, indent=2))
print("Model saved to model/model.pkl")
print("Test requests saved to model/request1.json and request2.json")
