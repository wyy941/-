from __future__ import annotations

from typing import Dict, Iterable, List, Mapping

from services.risk_engine import DEFAULT_INDICATORS, FEATURE_LABELS, get_indicator_meta


def _build_indicator_meta(indicator_meta: Mapping | Iterable | None) -> dict:
    meta_map = {item["code"]: item for item in DEFAULT_INDICATORS}

    if indicator_meta is None:
        return meta_map
    if isinstance(indicator_meta, Mapping):
        meta_map.update(indicator_meta)
        return meta_map

    for item in indicator_meta:
        meta_map[item["code"]] = item
    return meta_map


def _risk_flag(score: float) -> str:
    if score >= 75:
        return "重点关注"
    if score >= 55:
        return "持续观察"
    if score >= 35:
        return "总体可控"
    return "整体稳定"


def build_report(
    username: str,
    total_score: float,
    adjusted_score: float,
    risk_level: str,
    details: Dict,
    suggestions: List[str],
    indicator_meta: Mapping | Iterable | None = None,
    profile: Dict | None = None,
    source_payload: Dict | None = None,
    assessment_id: int | None = None,
    created_at: str | None = None,
    memberships: Dict | None = None,
    dimension_breakdown: List[dict] | None = None,
    top_risks: List[dict] | None = None,
    model_details: Dict | None = None,
) -> dict:
    """
    报告服务：输出结构化 JSON，便于前端展示、导出和论文答辩截图。
    """
    meta_map = _build_indicator_meta(indicator_meta)
    indicator_details = []

    for code, score in details.items():
        indicator = {**get_indicator_meta(code), **meta_map.get(code, {})}
        numeric_score = round(float(score), 2)
        indicator_details.append(
            {
                "code": code,
                "name": indicator.get("name", FEATURE_LABELS.get(code, code)),
                "weight": indicator.get("weight"),
                "dimension": indicator.get("dimension", "custom"),
                "dimension_name": indicator.get("dimension_name", "自定义指标"),
                "description": indicator.get("description"),
                "score_standard": indicator.get("score_standard"),
                "score": numeric_score,
                "flag": _risk_flag(numeric_score),
            }
        )

    indicator_details.sort(key=lambda item: item["score"], reverse=True)
    ranked_top_risks = top_risks or indicator_details[:3]
    if not ranked_top_risks:
        ranked_top_risks = indicator_details[:2]

    report_summary = {
        "total_score": total_score,
        "adjusted_score": adjusted_score,
        "risk_level": risk_level,
    }
    if memberships:
        report_summary["fuzzy_memberships"] = memberships
        report_summary["confidence"] = round(float(max(list(memberships.values()) or [0])), 4)

    dominant_dimension = dimension_breakdown[0] if dimension_breakdown else None
    conclusion = (
        f"{username} 的综合评估结果为 {risk_level}。"
        f"当前最需要关注的维度为“{dominant_dimension['dimension_name']}”。"
        if dominant_dimension
        else f"{username} 的综合评估结果为 {risk_level}。"
    )

    return {
        "title": "大学生AIGC技术依赖风险评估报告",
        "assessment_id": assessment_id,
        "generated_at": created_at,
        "username": username,
        "student_profile": profile or {},
        "summary": report_summary,
        "model_details": model_details or {},
        "dimension_breakdown": dimension_breakdown or [],
        "indicator_details": indicator_details,
        "top_risks": ranked_top_risks,
        "suggestions": suggestions,
        "source_payload": source_payload or {},
        "conclusion": conclusion,
    }
