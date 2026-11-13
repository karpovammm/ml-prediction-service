\set ON_ERROR_STOP on

INSERT INTO public.predictions (
    input_data,
    prediction,
    model_version
)
VALUES (
    '{"feature1": 1.2, "feature2": 3.4}',
    '{"class": "A", "probability": 0.92}',
    'v1.0'
);

SELECT *
FROM public.predictions
ORDER BY id;
