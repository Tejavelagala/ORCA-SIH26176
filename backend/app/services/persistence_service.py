import os
import json

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

try:
    from sqlalchemy import create_engine, text
except ImportError:
    create_engine = None
    text = None

_engine = None


def _get_engine():
    global _engine
    if _engine is None and DATABASE_URL and create_engine:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


def persist_query(result: dict) -> str:
    engine = _get_engine()
    if engine is None:
        return "disabled"

    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS orca_query_log (
                    id BIGSERIAL PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    location TEXT NOT NULL,
                    query TEXT NOT NULL,
                    language TEXT,
                    risk_status TEXT,
                    explanation_mode TEXT,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    risk_authority TEXT,
                    evidence_json JSONB,
                    geom geometry(Point, 4326)
                )
            """))
            coordinates = ((result.get("agents") or {}).get("geo") or {}).get("coordinates") or {}
            latitude = coordinates.get("latitude")
            longitude = coordinates.get("longitude")
            connection.execute(text("""
                INSERT INTO orca_query_log
                (created_at, location, query, language, risk_status, explanation_mode,
                 latitude, longitude, risk_authority, evidence_json, geom)
                VALUES (:created_at, :location, :query, :language, :risk_status,
                        :explanation_mode, :latitude, :longitude, :risk_authority,
                        CAST(:evidence_json AS JSONB),
                        CASE
                            WHEN :longitude IS NOT NULL AND :latitude IS NOT NULL
                            THEN ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
                            ELSE NULL
                        END)
            """), {
                "created_at": result.get("generated_at", ""),
                "location": result.get("location", ""),
                "query": result.get("query", ""),
                "language": result.get("language", ""),
                "risk_status": (result.get("risk") or {}).get("status"),
                "explanation_mode": result.get("explanation_mode"),
                "latitude": latitude,
                "longitude": longitude,
                "risk_authority": "deterministic_risk_engine",
                "evidence_json": json.dumps(result.get("evidence_summary", {})),
            })
        return "postgresql+postgis"
    except Exception:
        return "error"
