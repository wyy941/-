from __future__ import annotations

import json
import random
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from flask import current_app

from extensions import db
from models.assessment import AssessmentResult
from models.indicator import Indicator
from models.user import User
from models.workflow import InterventionRecord, StudentArchive, WarningTask
from services.cache_service import cache_delete_prefix
from services.data_preprocess import clean_dataframe
from services.risk_engine import (
    DEFAULT_INDICATORS,
    FEATURE_COLUMNS,
    FEATURE_LABELS,
    clamp_score,
    evaluate_risk,
    fuzzify_score,
    indicator_sort_key,
)
from services.workflow_service import bootstrap_workflow_demo_data

LEGACY_SAMPLE_USERNAME_PREFIX = "sample_student_"
DEFAULT_SAMPLE_SEED = 20260412
DEFAULT_SAMPLE_STUDENT_COUNT = 3000
SAMPLE_IMPORT_SIMILARITY_WINDOW = 1200
SQLITE_CHUNK_SIZE = 500

SAMPLE_USER_PROFILES = [
    {"grade": "2022", "major": "软件工程", "class_name": "2022级软件工程1班"},
    {"grade": "2023", "major": "数据科学与大数据技术", "class_name": "2023级数科1班"},
    {"grade": "2024", "major": "人工智能", "class_name": "2024级人工智能1班"},
    {"grade": "2025", "major": "计算机科学与技术", "class_name": "2025级计科1班"},
]

GRADE_OPTIONS = [
    ("2022", 0.20),
    ("2023", 0.26),
    ("2024", 0.29),
    ("2025", 0.25),
]

MAJOR_CATALOG = [
    {
        "major": "软件工程",
        "code": "01",
        "alias": "软工",
        "weight": 0.14,
        "ai_exposure": 0.82,
        "research_load": 0.58,
        "class_count": 3,
    },
    {
        "major": "计算机科学与技术",
        "code": "02",
        "alias": "计科",
        "weight": 0.13,
        "ai_exposure": 0.80,
        "research_load": 0.56,
        "class_count": 3,
    },
    {
        "major": "人工智能",
        "code": "03",
        "alias": "人工智能",
        "weight": 0.12,
        "ai_exposure": 0.88,
        "research_load": 0.61,
        "class_count": 2,
    },
    {
        "major": "数据科学与大数据技术",
        "code": "04",
        "alias": "数科",
        "weight": 0.10,
        "ai_exposure": 0.84,
        "research_load": 0.55,
        "class_count": 2,
    },
    {
        "major": "网络工程",
        "code": "05",
        "alias": "网工",
        "weight": 0.08,
        "ai_exposure": 0.72,
        "research_load": 0.51,
        "class_count": 2,
    },
    {
        "major": "数字媒体技术",
        "code": "06",
        "alias": "数媒",
        "weight": 0.08,
        "ai_exposure": 0.78,
        "research_load": 0.50,
        "class_count": 2,
    },
    {
        "major": "电气工程及其自动化",
        "code": "07",
        "alias": "电气",
        "weight": 0.08,
        "ai_exposure": 0.48,
        "research_load": 0.57,
        "class_count": 2,
    },
    {
        "major": "财务管理",
        "code": "08",
        "alias": "财管",
        "weight": 0.08,
        "ai_exposure": 0.52,
        "research_load": 0.46,
        "class_count": 2,
    },
    {
        "major": "汉语言文学",
        "code": "09",
        "alias": "汉文",
        "weight": 0.07,
        "ai_exposure": 0.40,
        "research_load": 0.45,
        "class_count": 2,
    },
    {
        "major": "心理学",
        "code": "10",
        "alias": "心理",
        "weight": 0.06,
        "ai_exposure": 0.45,
        "research_load": 0.42,
        "class_count": 2,
    },
    {
        "major": "市场营销",
        "code": "11",
        "alias": "营销",
        "weight": 0.06,
        "ai_exposure": 0.56,
        "research_load": 0.43,
        "class_count": 2,
    },
]

ARCHETYPE_CATALOG = [
    {
        "name": "谨慎低频型",
        "weight": 0.14,
        "digital": 0.22,
        "self_reg": 0.84,
        "verify": 0.82,
        "integrity": 0.84,
        "support": 0.73,
        "pressure": 0.38,
        "trend": -0.03,
        "risk_bias": 0.00,
    },
    {
        "name": "自主审慎型",
        "weight": 0.18,
        "digital": 0.34,
        "self_reg": 0.76,
        "verify": 0.75,
        "integrity": 0.78,
        "support": 0.70,
        "pressure": 0.46,
        "trend": -0.02,
        "risk_bias": 0.01,
    },
    {
        "name": "平衡辅助型",
        "weight": 0.24,
        "digital": 0.48,
        "self_reg": 0.66,
        "verify": 0.64,
        "integrity": 0.69,
        "support": 0.64,
        "pressure": 0.52,
        "trend": 0.00,
        "risk_bias": 0.02,
    },
    {
        "name": "效率驱动型",
        "weight": 0.18,
        "digital": 0.66,
        "self_reg": 0.56,
        "verify": 0.55,
        "integrity": 0.58,
        "support": 0.58,
        "pressure": 0.62,
        "trend": 0.02,
        "risk_bias": 0.05,
    },
    {
        "name": "高压替代型",
        "weight": 0.12,
        "digital": 0.74,
        "self_reg": 0.38,
        "verify": 0.40,
        "integrity": 0.38,
        "support": 0.48,
        "pressure": 0.81,
        "trend": 0.05,
        "risk_bias": 0.12,
    },
    {
        "name": "泛化依赖型",
        "weight": 0.08,
        "digital": 0.82,
        "self_reg": 0.35,
        "verify": 0.42,
        "integrity": 0.50,
        "support": 0.39,
        "pressure": 0.57,
        "trend": 0.03,
        "risk_bias": 0.10,
    },
    {
        "name": "情绪迁移型",
        "weight": 0.06,
        "digital": 0.60,
        "self_reg": 0.46,
        "verify": 0.57,
        "integrity": 0.62,
        "support": 0.28,
        "pressure": 0.68,
        "trend": 0.02,
        "risk_bias": 0.08,
    },
    {
        "name": "失衡高依赖型",
        "weight": 0.04,
        "digital": 0.88,
        "self_reg": 0.24,
        "verify": 0.28,
        "integrity": 0.24,
        "support": 0.32,
        "pressure": 0.86,
        "trend": 0.08,
        "risk_bias": 0.18,
    },
]

GRADE_PRESSURE_BIAS = {
    "2022": 0.08,
    "2023": 0.04,
    "2024": 0.01,
    "2025": -0.04,
}

GRADE_SELF_REG_BIAS = {
    "2022": 0.03,
    "2023": 0.02,
    "2024": 0.00,
    "2025": -0.05,
}

MONTH_PRESSURE = {
    1: 0.16,
    3: 0.08,
    4: 0.12,
    5: 0.16,
    6: 0.18,
    9: 0.05,
    10: 0.08,
    11: 0.12,
    12: 0.18,
}


def _resolve_sample_path(path: str | None = None) -> Path:
    sample_path = Path(path or current_app.config["SAMPLE_DATA_PATH"]).resolve()
    if not sample_path.exists():
        raise FileNotFoundError(f"示例数据文件不存在: {sample_path}")
    return sample_path


def _normalize_sample_metadata(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    text_columns = ["username", "role", "grade", "major", "class_name", "profile_tag"]
    for column in text_columns:
        if column in result.columns:
            result[column] = (
                result[column]
                .where(result[column].notna(), None)
                .apply(lambda value: None if value is None else str(value).strip())
            )

    if "assessment_date" in result.columns:
        result["assessment_date"] = (
            pd.to_datetime(result["assessment_date"], errors="coerce")
            .dt.strftime("%Y-%m-%d %H:%M:%S")
        )
        result["assessment_date"] = result["assessment_date"].where(
            result["assessment_date"].notna(),
            None,
        )

    return result


def _clip_unit(value: float) -> float:
    return max(0.05, min(0.95, float(value)))


def _safe_text(value) -> str | None:
    if value is None:
        return None
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _chunked_values(values: list, size: int = SQLITE_CHUNK_SIZE):
    for index in range(0, len(values), size):
        yield values[index:index + size]


def _weighted_choice(rng: random.Random, rows: list[dict], key: str = "weight") -> dict:
    return rng.choices(rows, weights=[float(item[key]) for item in rows], k=1)[0]


def _academic_anchor_dates(end_date: datetime) -> list[datetime]:
    current_year = end_date.year
    last_year = current_year - 1
    anchors = [
        datetime(last_year, 9, 18, 19, 30),
        datetime(last_year, 10, 16, 20, 15),
        datetime(last_year, 11, 12, 21, 0),
        datetime(last_year, 12, 23, 22, 10),
        datetime(current_year, 1, 11, 20, 30),
        datetime(current_year, 3, 14, 19, 50),
        datetime(current_year, 4, 8, 21, 5),
    ]
    return [item for item in anchors if item <= end_date]


def _assessment_dates(
    rng: random.Random,
    count: int,
    end_date: datetime,
) -> list[datetime]:
    anchors = _academic_anchor_dates(end_date)
    if not anchors:
        return [end_date - timedelta(days=7 * index) for index in range(count)][::-1]

    count = min(count, len(anchors))
    chosen_indexes = sorted(rng.sample(range(len(anchors)), count))
    dates = []
    for index in chosen_indexes:
        base = anchors[index]
        date = base + timedelta(
            days=rng.randint(-4, 4),
            hours=rng.randint(-2, 2),
            minutes=rng.randint(-25, 25),
        )
        if date > end_date:
            date = end_date - timedelta(hours=rng.randint(0, 8))
        dates.append(date)
    return sorted(dates)


def _pick_archetype(
    rng: random.Random,
    grade: str,
    major_meta: dict,
) -> dict:
    weights = {item["name"]: float(item["weight"]) for item in ARCHETYPE_CATALOG}

    if grade == "2022":
        weights["高压替代型"] += 0.05
        weights["效率驱动型"] += 0.03
        weights["失衡高依赖型"] += 0.02
    elif grade == "2025":
        weights["平衡辅助型"] += 0.04
        weights["泛化依赖型"] += 0.03

    if major_meta["ai_exposure"] >= 0.8:
        weights["效率驱动型"] += 0.04
        weights["泛化依赖型"] += 0.03
        weights["失衡高依赖型"] += 0.02
    elif major_meta["ai_exposure"] <= 0.48:
        weights["自主审慎型"] += 0.03
        weights["谨慎低频型"] += 0.02

    if major_meta["major"] in {"财务管理", "汉语言文学"}:
        weights["高压替代型"] += 0.02

    ordered = [{**item, "weight": weights[item["name"]]} for item in ARCHETYPE_CATALOG]
    return _weighted_choice(rng, ordered)


def _student_profile(
    rng: random.Random,
    grade: str,
    major_meta: dict,
    archetype: dict,
) -> dict:
    ai_exposure = major_meta["ai_exposure"]
    research_load = major_meta["research_load"]

    digital = _clip_unit(rng.gauss(archetype["digital"] + (ai_exposure - 0.5) * 0.18, 0.07))
    self_reg = _clip_unit(
        rng.gauss(archetype["self_reg"] + GRADE_SELF_REG_BIAS.get(grade, 0.0), 0.06)
    )
    verify = _clip_unit(rng.gauss(archetype["verify"] - (ai_exposure - 0.5) * 0.04, 0.06))
    integrity = _clip_unit(rng.gauss(archetype["integrity"], 0.06))
    support = _clip_unit(rng.gauss(archetype["support"], 0.07))
    pressure = _clip_unit(
        rng.gauss(
            archetype["pressure"] + GRADE_PRESSURE_BIAS.get(grade, 0.0) + (research_load - 0.5) * 0.10,
            0.06,
        )
    )

    return {
        "digital": digital,
        "self_reg": self_reg,
        "verify": verify,
        "integrity": integrity,
        "support": support,
        "pressure": pressure,
        "risk_bias": float(archetype.get("risk_bias", 0.0)),
    }


def _score_from_factors(
    rng: random.Random,
    factors: dict,
    major_meta: dict,
    month: int,
    progress: float,
    trend: float,
) -> dict:
    digital = _clip_unit(factors["digital"] + trend * progress + rng.gauss(0, 0.02))
    self_reg = _clip_unit(factors["self_reg"] - trend * 0.35 * progress + rng.gauss(0, 0.02))
    verify = _clip_unit(factors["verify"] - trend * 0.28 * progress + rng.gauss(0, 0.02))
    integrity = _clip_unit(factors["integrity"] - trend * 0.25 * progress + rng.gauss(0, 0.02))
    support = _clip_unit(factors["support"] - max(trend, 0) * 0.22 * progress + rng.gauss(0, 0.02))
    pressure = _clip_unit(
        factors["pressure"] + MONTH_PRESSURE.get(month, 0.07) + rng.gauss(0, 0.04)
    )
    risk_bias = float(factors.get("risk_bias", 0.0))
    ai_exposure = major_meta["ai_exposure"]
    research_load = major_meta["research_load"]
    noise = lambda spread=3.6: rng.gauss(0, spread)

    usage_frequency = clamp_score(
        10
        + 58 * digital
        + 8 * ai_exposure
        + 10 * pressure
        - 16 * self_reg
        + 12 * risk_bias
        + noise()
    )
    scenario_pervasiveness = clamp_score(
        8
        + 38 * digital
        + 18 * ai_exposure
        + 12 * pressure
        + 14 * (1 - self_reg)
        + 6 * (1 - support)
        + 18 * risk_bias
        + noise()
    )
    academic_substitution = clamp_score(
        6
        + 34 * digital
        + 24 * pressure
        + 12 * ai_exposure
        + 18 * (1 - self_reg)
        + 10 * research_load
        + 24 * risk_bias
        + noise()
    )
    independent_thinking_loss = clamp_score(
        8
        + 26 * digital
        + 18 * pressure
        + 18 * (1 - self_reg)
        + 14 * (1 - verify)
        + 20 * risk_bias
        + noise()
    )
    result_verification_weakness = clamp_score(
        6
        + 16 * digital
        + 16 * pressure
        + 24 * (1 - verify)
        + 6 * ai_exposure
        + 16 * risk_bias
        + noise()
    )
    critical_judgement_weakness = clamp_score(
        6
        + 14 * digital
        + 14 * pressure
        + 22 * (1 - verify)
        + 10 * (1 - self_reg)
        + 18 * risk_bias
        + noise()
    )
    academic_integrity_risk = clamp_score(
        4
        + 18 * digital
        + 20 * pressure
        + 24 * (1 - integrity)
        + 10 * research_load
        + 8 * (1 - self_reg)
        + 24 * risk_bias
        + noise()
    )
    privacy_security_risk = clamp_score(
        4
        + 18 * digital
        + 14 * (1 - integrity)
        + 10 * ai_exposure
        + 10 * (1 - self_reg)
        + 18 * risk_bias
        + noise()
    )
    social_collaboration_displacement = clamp_score(
        4
        + 14 * digital
        + 14 * pressure
        + 22 * (1 - support)
        + 8 * (1 - self_reg)
        + 18 * risk_bias
        + noise()
    )
    emotional_dependence = clamp_score(
        5
        + 14 * digital
        + 24 * pressure
        + 24 * (1 - support)
        + 8 * (1 - self_reg)
        + 20 * risk_bias
        + noise()
    )

    return {
        "usage_frequency": usage_frequency,
        "scenario_pervasiveness": scenario_pervasiveness,
        "academic_substitution": academic_substitution,
        "independent_thinking_loss": independent_thinking_loss,
        "result_verification_weakness": result_verification_weakness,
        "critical_judgement_weakness": critical_judgement_weakness,
        "academic_integrity_risk": academic_integrity_risk,
        "privacy_security_risk": privacy_security_risk,
        "social_collaboration_displacement": social_collaboration_displacement,
        "emotional_dependence": emotional_dependence,
    }


def build_realistic_sample_dataframe(
    student_count: int = DEFAULT_SAMPLE_STUDENT_COUNT,
    seed: int = DEFAULT_SAMPLE_SEED,
    end_date: datetime | None = None,
) -> pd.DataFrame:
    rng = random.Random(seed)
    current_end_date = end_date or datetime.now()
    grade_rows = [{"grade": grade, "weight": weight} for grade, weight in GRADE_OPTIONS]
    user_serials: dict[tuple[str, str], int] = {}
    rows = []

    for source_user_id in range(1001, 1001 + student_count):
        grade_meta = _weighted_choice(rng, grade_rows)
        grade = grade_meta["grade"]
        major_meta = _weighted_choice(rng, MAJOR_CATALOG)
        archetype = _pick_archetype(rng, grade, major_meta)
        factors = _student_profile(rng, grade, major_meta, archetype)

        serial_key = (grade, major_meta["code"])
        serial = user_serials.get(serial_key, 0) + 1
        user_serials[serial_key] = serial

        username = f"{grade}{major_meta['code']}{serial:04d}"
        class_section = 1 + ((serial - 1) % major_meta["class_count"])
        class_name = f"{grade}级{major_meta['alias']}{class_section}班"
        assessment_count = rng.choices([2, 3, 4, 5], weights=[0.15, 0.38, 0.33, 0.14], k=1)[0]
        assessment_dates = _assessment_dates(rng, assessment_count, current_end_date)

        for index, assessment_date in enumerate(assessment_dates):
            progress = index / max(len(assessment_dates) - 1, 1)
            payload = _score_from_factors(
                rng,
                factors,
                major_meta,
                assessment_date.month,
                progress,
                float(archetype["trend"]),
            )

            rows.append(
                {
                    "user_id": source_user_id,
                    "username": username,
                    "role": "student",
                    "grade": grade,
                    "major": major_meta["major"],
                    "class_name": class_name,
                    "profile_tag": archetype["name"],
                    "assessment_date": assessment_date.strftime("%Y-%m-%d %H:%M:%S"),
                    **payload,
                }
            )

    df = pd.DataFrame(rows)
    return df.sort_values(["user_id", "assessment_date"]).reset_index(drop=True)


def generate_realistic_sample_csv(
    path: str | None = None,
    student_count: int = DEFAULT_SAMPLE_STUDENT_COUNT,
    seed: int = DEFAULT_SAMPLE_SEED,
    overwrite: bool = True,
) -> dict:
    sample_path = Path(path or current_app.config["SAMPLE_DATA_PATH"]).resolve()
    sample_path.parent.mkdir(parents=True, exist_ok=True)

    if sample_path.exists() and not overwrite:
        df = pd.read_csv(sample_path)
    else:
        df = build_realistic_sample_dataframe(student_count=student_count, seed=seed)
        df.to_csv(sample_path, index=False, encoding="utf-8-sig")

    return {
        "path": str(sample_path),
        "total_rows": int(len(df)),
        "covered_users": int(df["user_id"].nunique()) if "user_id" in df.columns else 0,
        "majors": sorted(df["major"].dropna().unique().tolist()) if "major" in df.columns else [],
        "grades": sorted(df["grade"].dropna().unique().tolist()) if "grade" in df.columns else [],
    }


def load_sample_dataframe(path: str | None = None) -> tuple[pd.DataFrame, Path]:
    sample_path = _resolve_sample_path(path)
    df = pd.read_csv(sample_path)
    df = _normalize_sample_metadata(df)
    return clean_dataframe(df), sample_path


def preview_sample_data(limit: int = 10) -> dict:
    df, sample_path = load_sample_dataframe()
    safe_limit = max(1, min(limit, 50))

    indicator_average = {
        FEATURE_LABELS.get(column, column): round(float(df[column].mean()), 2)
        for column in FEATURE_COLUMNS
        if column in df.columns and not df.empty
    }

    grade_distribution = (
        df["grade"].value_counts().sort_index().to_dict() if "grade" in df.columns else {}
    )
    major_distribution = (
        df["major"].value_counts().head(8).to_dict() if "major" in df.columns else {}
    )

    return {
        "path": str(sample_path),
        "columns": list(df.columns),
        "total_rows": len(df),
        "rows": df.head(safe_limit).round(2).to_dict(orient="records"),
        "indicator_average": indicator_average,
        "grade_distribution": grade_distribution,
        "major_distribution": major_distribution,
    }


def _profile_for_source_user(source_user_id: int) -> dict:
    return SAMPLE_USER_PROFILES[(source_user_id - 1) % len(SAMPLE_USER_PROFILES)]


def _profile_from_row(row: dict, source_user_id: int) -> dict:
    fallback = _profile_for_source_user(source_user_id)
    grade = _safe_text(row.get("grade")) or fallback["grade"]
    major = _safe_text(row.get("major")) or fallback["major"]
    class_name = _safe_text(row.get("class_name")) or fallback["class_name"]
    username = _safe_text(row.get("username")) or f"{LEGACY_SAMPLE_USERNAME_PREFIX}{source_user_id}"
    role = _safe_text(row.get("role")) or "student"

    return {
        "username": username,
        "role": role,
        "grade": grade,
        "major": major,
        "class_name": class_name,
    }


def _prepare_sample_users(rows: list[dict]) -> tuple[dict[int, User], list[str]]:
    profiles_by_source_user_id = {}
    usernames = []

    for row in rows:
        source_user_id = int(row.get("user_id", 0) or 0)
        if source_user_id <= 0:
            continue
        profile = _profile_from_row(row, source_user_id)
        profiles_by_source_user_id[source_user_id] = profile
        usernames.append(profile["username"])

    existing_users = {}
    unique_usernames = sorted(set(usernames))
    if unique_usernames:
        for chunk in _chunked_values(unique_usernames):
            existing_rows = User.query.filter(User.username.in_(chunk)).all()
            existing_users.update({item.username: item for item in existing_rows})

    created_users = []
    user_map = {}

    for source_user_id, profile in profiles_by_source_user_id.items():
        user = existing_users.get(profile["username"])
        if user is None:
            user = User(
                username=profile["username"],
                role=profile["role"],
                grade=profile["grade"],
                major=profile["major"],
                class_name=profile["class_name"],
            )
            user.set_password("123456")
            db.session.add(user)
            existing_users[profile["username"]] = user
            created_users.append(user.username)
        else:
            for field in ("role", "grade", "major", "class_name"):
                value = profile[field]
                if value and getattr(user, field) != value:
                    setattr(user, field, value)

        user_map[source_user_id] = user

    db.session.flush()
    return user_map, created_users


def _get_or_create_sample_user(source_user_id: int, row: dict) -> tuple[User, bool]:
    profile = _profile_from_row(row, source_user_id)
    user = User.query.filter_by(username=profile["username"]).first()
    if user:
        updated = False
        for field in ("role", "grade", "major", "class_name"):
            value = profile[field]
            if value and getattr(user, field) != value:
                setattr(user, field, value)
                updated = True
        if updated:
            db.session.flush()
        return user, False

    user = User(
        username=profile["username"],
        role=profile["role"],
        grade=profile["grade"],
        major=profile["major"],
        class_name=profile["class_name"],
    )
    user.set_password("123456")
    db.session.add(user)
    db.session.flush()
    return user, True


def _current_indicator_dicts() -> list[dict]:
    indicators = Indicator.query.filter_by(enabled=True).all()
    return (
        sorted([item.to_dict() for item in indicators], key=indicator_sort_key)
        if indicators
        else DEFAULT_INDICATORS
    )


def _persisted_history_records() -> list[dict]:
    rows = []
    records = AssessmentResult.query.order_by(AssessmentResult.created_at.asc()).all()
    for item in records:
        raw_payload = json.loads(item.source_payload_json)
        rows.append(
            {
                **{key: raw_payload.get(key, 0) for key in FEATURE_COLUMNS},
                "adjusted_score": item.adjusted_score,
            }
        )
    return rows


def _existing_assessment_signatures(user_ids: list[int]) -> set[tuple[int, str]]:
    if not user_ids:
        return set()

    signatures = set()
    for chunk in _chunked_values(user_ids):
        rows = (
            AssessmentResult.query.with_entities(
                AssessmentResult.user_id,
                AssessmentResult.source_payload_json,
            )
            .filter(AssessmentResult.user_id.in_(chunk))
            .all()
        )
        signatures.update(
            {(int(user_id), source_payload_json) for user_id, source_payload_json in rows}
        )
    return signatures


def _feature_vector(payload: dict) -> np.ndarray:
    return np.array([float(payload.get(key, 0)) for key in FEATURE_COLUMNS], dtype=float)


def _history_similarity_adjust_score(
    history_vectors: deque[np.ndarray],
    history_scores: deque[float],
    target_vector: np.ndarray,
    base_score: float,
    top_k: int = 5,
) -> float:
    if not history_vectors or not history_scores:
        return round(float(base_score), 2)

    matrix = np.asarray(history_vectors, dtype=float)
    scores = np.asarray(history_scores, dtype=float)
    if matrix.size == 0 or scores.size == 0:
        return round(float(base_score), 2)

    target = np.asarray(target_vector, dtype=float)
    target_norm = np.linalg.norm(target)
    if target_norm <= 0:
        return round(float(base_score), 2)

    matrix_norm = np.linalg.norm(matrix, axis=1)
    denominator = matrix_norm * target_norm
    denominator = np.where(denominator == 0, 1e-8, denominator)
    similarities = (matrix @ target) / denominator

    positive_mask = similarities > 0
    if not np.any(positive_mask):
        return round(float(base_score), 2)

    filtered_similarities = similarities[positive_mask]
    filtered_scores = scores[positive_mask]
    top_indices = np.argsort(filtered_similarities)[-top_k:]
    top_similarities = filtered_similarities[top_indices]
    top_scores = filtered_scores[top_indices]

    weights = np.clip(top_similarities, 0.01, None)
    peer_score = np.average(top_scores, weights=weights)
    confidence = min(len(top_scores) / max(top_k, 1), 1)
    peer_ratio = 0.12 + 0.13 * confidence
    adjusted = (1 - peer_ratio) * float(base_score) + peer_ratio * float(peer_score)
    return round(adjusted, 2)


def _parse_created_at(row: dict) -> datetime | None:
    raw_value = row.get("assessment_date") or row.get("created_at")
    if raw_value is None or (isinstance(raw_value, float) and pd.isna(raw_value)):
        return None

    parsed = pd.to_datetime(raw_value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()


def _is_generated_demo_username(username: str | None) -> bool:
    if not username:
        return False
    if username.startswith(LEGACY_SAMPLE_USERNAME_PREFIX):
        return True
    return username.isdigit() and len(username) == 10 and username.startswith("20")


def reset_legacy_sample_data() -> dict:
    generated_users = [
        user
        for user in User.query.filter_by(role="student").all()
        if _is_generated_demo_username(user.username)
    ]
    if not generated_users:
        return {
            "removed_users": 0,
            "removed_assessments": 0,
            "removed_archives": 0,
            "removed_tasks": 0,
            "removed_interventions": 0,
        }

    legacy_user_ids = [user.id for user in generated_users]
    removed_assessments = 0
    removed_archives = 0
    removed_tasks = 0
    removed_interventions = 0
    removed_users = 0

    task_ids: list[int] = []
    for chunk in _chunked_values(legacy_user_ids):
        task_ids.extend(
            task_id
            for (task_id,) in db.session.query(WarningTask.id)
            .filter(WarningTask.user_id.in_(chunk))
            .all()
        )

    if task_ids:
        for chunk in _chunked_values(task_ids):
            removed_interventions += InterventionRecord.query.filter(
                InterventionRecord.task_id.in_(chunk)
            ).delete(synchronize_session=False)

    for chunk in _chunked_values(legacy_user_ids):
        removed_tasks += WarningTask.query.filter(
            WarningTask.user_id.in_(chunk)
        ).delete(synchronize_session=False)

    for chunk in _chunked_values(legacy_user_ids):
        removed_archives += StudentArchive.query.filter(
            StudentArchive.user_id.in_(chunk)
        ).delete(synchronize_session=False)

    for chunk in _chunked_values(legacy_user_ids):
        removed_assessments += AssessmentResult.query.filter(
            AssessmentResult.user_id.in_(chunk)
        ).delete(synchronize_session=False)

    for chunk in _chunked_values(legacy_user_ids):
        removed_users += User.query.filter(User.id.in_(chunk)).delete(synchronize_session=False)

    db.session.commit()

    return {
        "removed_users": int(removed_users),
        "removed_assessments": int(removed_assessments),
        "removed_archives": int(removed_archives),
        "removed_tasks": int(removed_tasks),
        "removed_interventions": int(removed_interventions),
    }


def import_sample_data(limit: int | None = None, path: str | None = None) -> dict:
    df, sample_path = load_sample_dataframe(path)
    if limit:
        df = df.head(limit)
    if "assessment_date" in df.columns:
        df = df.sort_values(["assessment_date", "user_id"], kind="stable")
    df = df.reset_index(drop=True)

    rows = df.to_dict(orient="records")

    indicator_dicts = _current_indicator_dicts()
    user_map, created_users = _prepare_sample_users(rows)
    existing_signatures = _existing_assessment_signatures(
        [user.id for user in user_map.values()]
    )
    imported_count = 0
    skipped_count = 0
    comparison_df = df[FEATURE_COLUMNS].copy() if not df.empty else pd.DataFrame(columns=FEATURE_COLUMNS)
    persisted_history = _persisted_history_records()

    if persisted_history:
        persisted_df = pd.DataFrame(persisted_history)
        comparison_df = pd.concat(
            [comparison_df, persisted_df[FEATURE_COLUMNS]],
            ignore_index=True,
        )

    history_seed = persisted_history[-SAMPLE_IMPORT_SIMILARITY_WINDOW:]
    history_vectors = deque(
        (_feature_vector(item) for item in history_seed),
        maxlen=SAMPLE_IMPORT_SIMILARITY_WINDOW,
    )
    history_scores = deque(
        (float(item["adjusted_score"]) for item in history_seed),
        maxlen=SAMPLE_IMPORT_SIMILARITY_WINDOW,
    )
    new_assessments = []

    for row in rows:
        source_user_id = int(row.get("user_id", 0) or 0)
        if source_user_id <= 0:
            skipped_count += 1
            continue

        user = user_map.get(source_user_id)
        if user is None:
            skipped_count += 1
            continue

        payload = {
            key: clamp_score(row.get(key, 0) or 0)
            for key in FEATURE_COLUMNS
        }
        source_payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)

        signature = (user.id, source_payload_json)
        if signature in existing_signatures:
            skipped_count += 1
            continue

        evaluation = evaluate_risk(payload, indicator_dicts, comparison_df=comparison_df)
        detail_vector = _feature_vector(evaluation["details"])
        adjusted_score = _history_similarity_adjust_score(
            history_vectors,
            history_scores,
            detail_vector,
            evaluation["total_score"],
        )
        final_level = fuzzify_score(adjusted_score)

        assessment_kwargs = {
            "user_id": user.id,
            "total_score": evaluation["total_score"],
            "adjusted_score": adjusted_score,
            "risk_level": final_level,
            "details_json": json.dumps(evaluation["details"], ensure_ascii=False),
            "suggestions_json": json.dumps(evaluation["suggestions"], ensure_ascii=False),
            "source_payload_json": source_payload_json,
        }
        created_at = _parse_created_at(row)
        if created_at is not None:
            assessment_kwargs["created_at"] = created_at

        new_assessments.append(AssessmentResult(**assessment_kwargs))

        existing_signatures.add(signature)
        history_vectors.append(detail_vector)
        history_scores.append(float(adjusted_score))
        imported_count += 1

    if new_assessments:
        db.session.add_all(new_assessments)
    db.session.commit()
    workflow_result = bootstrap_workflow_demo_data()
    cache_delete_prefix("dashboard:overview:")

    return {
        "path": str(sample_path),
        "total_rows": len(df),
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "created_user_count": len(created_users),
        "created_users": created_users[:20],
        "covered_users": len(df["user_id"].dropna().unique()) if "user_id" in df.columns else 0,
        "workflow": workflow_result,
    }
