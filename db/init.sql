\set ON_ERROR_STOP on

-- Создать роль, только если её ещё нет.
SELECT 'CREATE ROLE ml_app LOGIN'
WHERE NOT EXISTS (
    SELECT 1 FROM pg_roles WHERE rolname = 'ml_app'
)
\gexec

-- У приложения нет административных привилегий.
ALTER ROLE ml_app
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION
    NOBYPASSRLS
    NOINHERIT;

-- Создать базу, только если её ещё нет.
SELECT 'CREATE DATABASE ml_predictions OWNER postgres'
WHERE NOT EXISTS (
    SELECT 1 FROM pg_database WHERE datname = 'ml_predictions'
)
\gexec

-- Приложение не должно владеть базой.
ALTER DATABASE ml_predictions OWNER TO postgres;

REVOKE ALL PRIVILEGES ON DATABASE ml_predictions FROM PUBLIC;
REVOKE ALL PRIVILEGES ON DATABASE ml_predictions FROM ml_app;
GRANT CONNECT ON DATABASE ml_predictions TO ml_app;

\connect ml_predictions

ALTER SCHEMA public OWNER TO postgres;

REVOKE ALL PRIVILEGES ON SCHEMA public FROM PUBLIC;
REVOKE ALL PRIVILEGES ON SCHEMA public FROM ml_app;
GRANT USAGE ON SCHEMA public TO ml_app;

CREATE TABLE IF NOT EXISTS public.predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    input_data JSONB NOT NULL,
    prediction JSONB NOT NULL,
    model_version VARCHAR(50) NOT NULL
);

ALTER TABLE public.predictions OWNER TO postgres;

REVOKE ALL PRIVILEGES ON TABLE public.predictions FROM PUBLIC;
REVOKE ALL PRIVILEGES ON TABLE public.predictions FROM ml_app;
GRANT SELECT, INSERT ON TABLE public.predictions TO ml_app;

REVOKE ALL PRIVILEGES
    ON SEQUENCE public.predictions_id_seq FROM PUBLIC;

REVOKE ALL PRIVILEGES
    ON SEQUENCE public.predictions_id_seq FROM ml_app;

GRANT USAGE, SELECT
    ON SEQUENCE public.predictions_id_seq TO ml_app;

-- Пароль задаётся отдельно интерактивной командой:
-- \password ml_app
-- Настоящий пароль в этот файл не записывать.
