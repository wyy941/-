from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Mapping

import numpy as np
import pandas as pd

RISK_LEVELS = ("低风险", "中风险", "高风险")
DIMENSION_LABELS = {
    "behavior": "行为依赖",
    "cognition": "认知弱化",
    "ethics": "伦理与安全",
    "social": "社交与协作",
    "learning": "学习投入",
    "self_management": "自我调节",
    "custom": "自定义指标",
}
DIMENSION_ORDER = {
    "behavior": 1,
    "cognition": 2,
    "ethics": 3,
    "social": 4,
    "learning": 5,
    "self_management": 6,
    "custom": 9,
}

DEFAULT_INDICATORS = [
    {
        "code": "usage_frequency",
        "name": "使用频率",
        "weight": 0.06,
        "dimension": "behavior",
        "description": "AIGC 工具使用频率持续偏高，容易形成默认求助路径。",
        "score_standard": "0-34 分为低频辅助，35-69 分为阶段性依赖，70-100 分为高频惯性使用。",
        "suggestion": "为高频使用场景设置时间边界，优先保留阅读、推理和写作的独立完成环节。",
    },
    {
        "code": "scenario_pervasiveness",
        "name": "场景泛化程度",
        "weight": 0.06,
        "dimension": "behavior",
        "description": "AIGC 是否从单一辅助场景扩展到学习、生活、社交等多场景。",
        "score_standard": "0-34 分为单一场景使用，35-69 分为多场景渗透，70-100 分为跨学习生活全面泛化。",
        "suggestion": "限定 AIGC 的适用场景，把检索、校对与启发环节和核心产出环节区分开。",
    },
    {
        "code": "academic_substitution",
        "name": "学业替代程度",
        "weight": 0.06,
        "dimension": "behavior",
        "description": "学习任务、作业撰写、资料整理等环节被 AIGC 直接替代的程度。",
        "score_standard": "0-34 分为局部辅助，35-69 分为明显替代，70-100 分为核心学业任务高度外包。",
        "suggestion": "将 AIGC 定位为辅助工具，课程核心作业、论证结构和结论必须由本人完成。",
    },
    {
        "code": "independent_thinking_loss",
        "name": "独立思考弱化",
        "weight": 0.06,
        "dimension": "cognition",
        "description": "面对问题时是否在自主拆解和推理前就直接依赖 AIGC 给出答案。",
        "score_standard": "0-34 分为先独立思考再参考，35-69 分为思考与求助并行，70-100 分为优先向模型索取答案。",
        "suggestion": "先写出自己的问题框架、论点和推导过程，再使用 AIGC 做补充与校对。",
    },
    {
        "code": "result_verification_weakness",
        "name": "结果核验不足",
        "weight": 0.06,
        "dimension": "cognition",
        "description": "对 AIGC 输出缺乏事实查证、逻辑回溯与来源核验的程度。",
        "score_standard": "0-34 分为主动核验，35-69 分为关键节点核验不足，70-100 分为基本不做来源与事实复核。",
        "suggestion": "建立“生成-核验-修订”闭环，对关键信息至少进行一次独立交叉验证。",
    },
    {
        "code": "critical_judgement_weakness",
        "name": "批判判断弱化",
        "weight": 0.06,
        "dimension": "cognition",
        "description": "对模型结论、论证逻辑和价值立场缺乏质疑与反思的程度。",
        "score_standard": "0-34 分为能提出反例与限制，35-69 分为部分接受模型判断，70-100 分为高度依赖模型观点。",
        "suggestion": "对重要结论主动提出反例、限制条件与替代解释，训练反向审视能力。",
    },
    {
        "code": "academic_integrity_risk",
        "name": "学术诚信风险",
        "weight": 0.055,
        "dimension": "ethics",
        "description": "直接提交 AI 生成内容、引用不规范或弱化原创贡献说明的风险。",
        "score_standard": "0-34 分为规范标注，35-69 分为存在疏漏，70-100 分为原创与引用边界明显失守。",
        "suggestion": "明确标注 AI 辅助范围，补充原创部分说明，严格执行引用与查证规范。",
    },
    {
        "code": "privacy_security_risk",
        "name": "隐私与数据安全风险",
        "weight": 0.055,
        "dimension": "ethics",
        "description": "向 AIGC 工具输入个人隐私、课程资料或敏感信息的风险程度。",
        "score_standard": "0-34 分为严格脱敏，35-69 分为偶发敏感输入，70-100 分为边界模糊且频繁暴露数据。",
        "suggestion": "避免上传个人隐私、课程题库和敏感资料，对外部模型输入进行脱敏处理。",
    },
    {
        "code": "algorithm_bias_unawareness",
        "name": "算法偏差辨识不足",
        "weight": 0.055,
        "dimension": "ethics",
        "description": "对模型可能存在的偏差、幻觉和价值倾向缺少辨识与修正的程度。",
        "score_standard": "0-34 分为能识别偏差来源，35-69 分为偶尔忽视模型偏差，70-100 分为几乎不识别算法偏误。",
        "suggestion": "在使用模型输出前增加偏差检查步骤，关注立场倾向、样本偏差和事实幻觉。",
    },
    {
        "code": "social_collaboration_displacement",
        "name": "社交协作替代",
        "weight": 0.055,
        "dimension": "social",
        "description": "本应通过同伴协作、师生交流解决的问题，被 AIGC 替代的程度。",
        "score_standard": "0-34 分为保持真实协作，35-69 分为协作频率下降，70-100 分为明显以模型替代同伴沟通。",
        "suggestion": "在课程讨论、项目协作和答疑环节优先使用真实交流，保留人与人的反馈机制。",
    },
    {
        "code": "emotional_dependence",
        "name": "情绪依赖程度",
        "weight": 0.055,
        "dimension": "social",
        "description": "在焦虑、压力和情绪波动场景下对 AIGC 的情绪性依赖程度。",
        "score_standard": "0-34 分为偶发倾诉，35-69 分为情绪波动时依赖明显，70-100 分为将模型视为主要情绪出口。",
        "suggestion": "将 AIGC 从情绪支持退回工具位置，增加与教师、同学和家人的现实支持连接。",
    },
    {
        "code": "communication_avoidance",
        "name": "现实沟通回避",
        "weight": 0.055,
        "dimension": "social",
        "description": "遇到问题时优先与模型对话，而主动回避与同伴、教师面对面沟通的程度。",
        "score_standard": "0-34 分为沟通渠道均衡，35-69 分为现实沟通意愿下降，70-100 分为明显回避真实交流。",
        "suggestion": "把答疑、讨论和协商类问题优先放回真实沟通场景，提升面对面表达与反馈能力。",
    },
    {
        "code": "self_regulated_learning_weakness",
        "name": "自主学习调节不足",
        "weight": 0.055,
        "dimension": "learning",
        "description": "学习目标拆解、阶段推进和学习反思更多依赖模型安排的程度。",
        "score_standard": "0-34 分为能自主规划学习，35-69 分为部分依赖模型安排，70-100 分为学习节奏主要由模型驱动。",
        "suggestion": "先自行制定学习目标、周计划和复盘清单，再把 AIGC 作为补充建议工具。",
    },
    {
        "code": "knowledge_internalization_gap",
        "name": "知识内化不足",
        "weight": 0.055,
        "dimension": "learning",
        "description": "能够生成答案但难以真正理解、复述和迁移知识的程度。",
        "score_standard": "0-34 分为可独立复述迁移，35-69 分为理解停留在表层，70-100 分为产出与掌握明显脱节。",
        "suggestion": "增加无提示复述、错题回顾和迁移练习，检验是否真正掌握关键知识点。",
    },
    {
        "code": "task_planning_dependence",
        "name": "任务规划依赖",
        "weight": 0.055,
        "dimension": "learning",
        "description": "在选题、拆任务和安排执行路径时，对模型建议过度依赖的程度。",
        "score_standard": "0-34 分为能独立拆解任务，35-69 分为规划依赖逐步增加，70-100 分为任务路径高度依赖模型生成。",
        "suggestion": "将任务拆解、优先级判断和时间安排先由本人完成，再用模型做校验与优化。",
    },
    {
        "code": "time_management_disorder",
        "name": "时间管理失衡",
        "weight": 0.055,
        "dimension": "self_management",
        "description": "由于频繁切换模型交互、反复生成与修改，导致学习时间被打散和拖延的程度。",
        "score_standard": "0-34 分为时间安排稳定，35-69 分为存在拖延和碎片化，70-100 分为明显被工具牵引节奏。",
        "suggestion": "为模型使用设置固定时段和轮次限制，把阅读、思考、产出分成清晰阶段。",
    },
    {
        "code": "attention_dispersion_risk",
        "name": "注意力分散风险",
        "weight": 0.055,
        "dimension": "self_management",
        "description": "在频繁调用模型、切换提示词和比对答案过程中，持续专注能力被削弱的程度。",
        "score_standard": "0-34 分为专注稳定，35-69 分为专注时长下降，70-100 分为明显依赖频繁切换与即时反馈。",
        "suggestion": "采用番茄钟或单任务模式，减少无效提示词迭代与多窗口切换。",
    },
    {
        "code": "offline_problem_solving_avoidance",
        "name": "脱离技术解决问题回避",
        "weight": 0.055,
        "dimension": "self_management",
        "description": "在没有模型支持时，主动回避独立完成任务或解决问题的程度。",
        "score_standard": "0-34 分为可脱离工具独立完成，35-69 分为离线解决能力不稳定，70-100 分为明显回避无工具状态下的问题处理。",
        "suggestion": "定期安排无模型支持的练习任务，恢复离线思考、写作与问题求解能力。",
    },
]

DEFAULT_INDICATOR_MAP = {item["code"]: item for item in DEFAULT_INDICATORS}
FEATURE_COLUMNS = [item["code"] for item in DEFAULT_INDICATORS]
FEATURE_LABELS = {item["code"]: item["name"] for item in DEFAULT_INDICATORS}
FEATURE_DESCRIPTIONS = {item["code"]: item["description"] for item in DEFAULT_INDICATORS}
FEATURE_DIMENSIONS = {item["code"]: item["dimension"] for item in DEFAULT_INDICATORS}
INDICATOR_ORDER = {item["code"]: index for index, item in enumerate(DEFAULT_INDICATORS)}
BASE_INPUT_COLUMNS = [
    "usage_frequency",
    "academic_substitution",
    "independent_thinking_loss",
    "result_verification_weakness",
    "academic_integrity_risk",
    "emotional_dependence",
]
AHP_RANDOM_INDEX = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
    11: 1.51,
    12: 1.48,
    13: 1.56,
    14: 1.57,
    15: 1.59,
}


def clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 2)


def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").fillna(0.0)
    return pd.Series(np.zeros(len(df)), index=df.index, dtype=float)


def enrich_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if result.empty:
        for column in FEATURE_COLUMNS:
            if column not in result.columns:
                result[column] = pd.Series(dtype=float)
        return result

    for column in BASE_INPUT_COLUMNS:
        result[column] = _safe_series(result, column)

    usage_frequency = _safe_series(result, "usage_frequency")
    academic_substitution = _safe_series(result, "academic_substitution")
    independent_thinking_loss = _safe_series(result, "independent_thinking_loss")
    result_verification_weakness = _safe_series(result, "result_verification_weakness")
    academic_integrity_risk = _safe_series(result, "academic_integrity_risk")
    emotional_dependence = _safe_series(result, "emotional_dependence")

    scenario_pervasiveness = (
        0.45 * usage_frequency
        + 0.35 * academic_substitution
        + 0.20 * emotional_dependence
    )
    critical_judgement_weakness = (
        0.55 * result_verification_weakness
        + 0.30 * independent_thinking_loss
        + 0.15 * academic_integrity_risk
    )
    privacy_security_risk = (
        0.45 * academic_integrity_risk
        + 0.35 * usage_frequency
        + 0.20 * emotional_dependence
    )
    social_collaboration_displacement = (
        0.40 * academic_substitution
        + 0.35 * independent_thinking_loss
        + 0.25 * emotional_dependence
    )
    algorithm_bias_unawareness = (
        0.40 * result_verification_weakness
        + 0.35 * academic_integrity_risk
        + 0.25 * independent_thinking_loss
    )
    communication_avoidance = (
        0.45 * social_collaboration_displacement
        + 0.30 * emotional_dependence
        + 0.25 * usage_frequency
    )
    self_regulated_learning_weakness = (
        0.40 * academic_substitution
        + 0.35 * independent_thinking_loss
        + 0.25 * usage_frequency
    )
    knowledge_internalization_gap = (
        0.40 * academic_substitution
        + 0.35 * result_verification_weakness
        + 0.25 * independent_thinking_loss
    )
    task_planning_dependence = (
        0.40 * usage_frequency
        + 0.35 * academic_substitution
        + 0.25 * emotional_dependence
    )
    time_management_disorder = (
        0.40 * usage_frequency
        + 0.30 * scenario_pervasiveness
        + 0.30 * emotional_dependence
    )
    attention_dispersion_risk = (
        0.35 * usage_frequency
        + 0.35 * independent_thinking_loss
        + 0.30 * emotional_dependence
    )
    offline_problem_solving_avoidance = (
        0.40 * academic_substitution
        + 0.30 * emotional_dependence
        + 0.30 * result_verification_weakness
    )

    derived_columns = {
        "scenario_pervasiveness": scenario_pervasiveness,
        "critical_judgement_weakness": critical_judgement_weakness,
        "privacy_security_risk": privacy_security_risk,
        "algorithm_bias_unawareness": algorithm_bias_unawareness,
        "social_collaboration_displacement": social_collaboration_displacement,
        "communication_avoidance": communication_avoidance,
        "self_regulated_learning_weakness": self_regulated_learning_weakness,
        "knowledge_internalization_gap": knowledge_internalization_gap,
        "task_planning_dependence": task_planning_dependence,
        "time_management_disorder": time_management_disorder,
        "attention_dispersion_risk": attention_dispersion_risk,
        "offline_problem_solving_avoidance": offline_problem_solving_avoidance,
    }

    for column, default_values in derived_columns.items():
        existing = _safe_series(result, column)
        if column not in result.columns or existing.eq(0).all():
            result[column] = default_values
        else:
            result[column] = existing

    for column in FEATURE_COLUMNS:
        result[column] = _safe_series(result, column).clip(lower=0, upper=100)

    return result


def get_indicator_meta(code: str) -> dict:
    meta = DEFAULT_INDICATOR_MAP.get(code, {})
    dimension = meta.get("dimension", "custom")
    return {
        "dimension": dimension,
        "dimension_name": DIMENSION_LABELS.get(dimension, DIMENSION_LABELS["custom"]),
        "score_standard": meta.get("score_standard"),
        "suggestion": meta.get("suggestion"),
        **meta,
    }


def indicator_sort_key(item: Mapping) -> tuple[int, int, str]:
    code = item.get("code", "")
    dimension = item.get("dimension") or get_indicator_meta(code).get("dimension", "custom")
    return (
        DIMENSION_ORDER.get(dimension, 99),
        INDICATOR_ORDER.get(code, 10_000),
        code,
    )


def build_indicator_records(indicators: Iterable[Mapping] | None = None) -> List[dict]:
    source = indicators or DEFAULT_INDICATORS
    records = []
    for raw_item in source:
        item = dict(raw_item)
        meta = get_indicator_meta(item["code"])
        merged = {**meta, **item}
        dimension = merged.get("dimension", "custom")
        merged["dimension"] = dimension
        merged["dimension_name"] = DIMENSION_LABELS.get(dimension, DIMENSION_LABELS["custom"])
        merged["weight"] = float(merged.get("weight", 0) or 0)
        records.append(merged)

    records.sort(key=indicator_sort_key)
    return records


def normalize_weights(indicators: List[dict]) -> List[dict]:
    total = sum(float(item.get("weight", 0) or 0) for item in indicators) or 1
    normalized = []
    for item in indicators:
        normalized.append({**item, "weight": round(float(item.get("weight", 0) or 0) / total, 4)})
    return normalized


def _normalize_weight_map(weight_map: Mapping[str, float]) -> Dict[str, float]:
    total = sum(float(value) for value in weight_map.values()) or 1
    return {
        key: round(float(value) / total, 4)
        for key, value in weight_map.items()
    }


def _prepare_payload(payload: Mapping[str, float], indicator_records: List[dict]) -> Dict[str, float]:
    prepared = enrich_feature_frame(pd.DataFrame([dict(payload or {})]))
    row = prepared.iloc[0].to_dict()
    return {
        item["code"]: clamp_score(row.get(item["code"], 0))
        for item in indicator_records
    }


def _prepare_comparison_frame(
    comparison_df: pd.DataFrame | None,
    indicator_records: List[dict],
) -> pd.DataFrame:
    codes = [item["code"] for item in indicator_records]
    if comparison_df is None or comparison_df.empty:
        return pd.DataFrame(columns=codes)
    prepared = enrich_feature_frame(comparison_df)
    for code in codes:
        if code not in prepared.columns:
            prepared[code] = 0.0
    return prepared[codes].fillna(0).astype(float)


def compute_ahp_metrics(indicator_records: List[dict]) -> dict:
    codes = [item["code"] for item in indicator_records]
    if not codes:
        return {
            "weights": {},
            "lambda_max": 0.0,
            "consistency_index": 0.0,
            "consistency_ratio": 0.0,
        }

    priority = np.array(
        [float(item.get("weight", 0) or 0) for item in indicator_records],
        dtype=float,
    )
    priority = priority / (float(priority.sum()) or 1.0)

    denominator = np.where(priority == 0, 1e-8, priority)
    pairwise_matrix = priority[:, None] / denominator[None, :]
    eigenvalues, eigenvectors = np.linalg.eig(pairwise_matrix)
    principal_index = int(np.argmax(eigenvalues.real))
    lambda_max = float(eigenvalues[principal_index].real)

    eigen_priority = np.abs(eigenvectors[:, principal_index].real)
    eigen_priority = eigen_priority / (float(eigen_priority.sum()) or 1.0)

    n = len(codes)
    consistency_index = 0.0 if n <= 1 else (lambda_max - n) / max(n - 1, 1)
    random_index = AHP_RANDOM_INDEX.get(n, 1.59)
    consistency_ratio = 0.0 if random_index == 0 else consistency_index / random_index

    return {
        "weights": _normalize_weight_map(
            {
                code: float(value)
                for code, value in zip(codes, eigen_priority)
            }
        ),
        "lambda_max": round(lambda_max, 4),
        "consistency_index": max(0.0, round(float(consistency_index), 4)),
        "consistency_ratio": max(0.0, round(float(consistency_ratio), 4)),
    }


def compute_entropy_weights(
    comparison_df: pd.DataFrame | None,
    indicator_records: List[dict],
) -> Dict[str, float]:
    codes = [item["code"] for item in indicator_records]
    prepared = _prepare_comparison_frame(comparison_df, indicator_records)
    if prepared.empty or len(prepared.index) < 3:
        return _normalize_weight_map({code: 1 for code in codes})

    matrix = prepared.to_numpy(dtype=float)
    min_values = matrix.min(axis=0)
    max_values = matrix.max(axis=0)
    span = np.where((max_values - min_values) == 0, 1, max_values - min_values)
    normalized = (matrix - min_values) / span + 1e-6

    column_sums = normalized.sum(axis=0)
    probability = normalized / np.where(column_sums == 0, 1, column_sums)

    n = normalized.shape[0]
    entropy_constant = 1 / np.log(max(n, 2))
    entropy = -entropy_constant * np.sum(probability * np.log(probability), axis=0)
    divergence = 1 - entropy

    if float(divergence.sum()) <= 0:
        return _normalize_weight_map({code: 1 for code in codes})

    return _normalize_weight_map(
        {code: float(value) for code, value in zip(codes, divergence)}
    )


def compute_critic_weights(
    comparison_df: pd.DataFrame | None,
    indicator_records: List[dict],
) -> Dict[str, float]:
    codes = [item["code"] for item in indicator_records]
    prepared = _prepare_comparison_frame(comparison_df, indicator_records)
    if prepared.empty or len(prepared.index) < 3:
        return _normalize_weight_map({code: 1 for code in codes})

    matrix = prepared.to_numpy(dtype=float)
    min_values = matrix.min(axis=0)
    max_values = matrix.max(axis=0)
    span = np.where((max_values - min_values) == 0, 1, max_values - min_values)
    normalized = (matrix - min_values) / span

    std = normalized.std(axis=0)
    corr = np.corrcoef(normalized, rowvar=False)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
    conflict = np.sum(1 - corr, axis=0)
    information = std * conflict

    if float(information.sum()) <= 0:
        return _normalize_weight_map({code: 1 for code in codes})

    return _normalize_weight_map(
        {code: float(value) for code, value in zip(codes, information)}
    )


def blend_weights(
    expert_weights: Mapping[str, float],
    entropy_weights: Mapping[str, float],
    critic_weights: Mapping[str, float] | None = None,
    source_ratios: Mapping[str, float] | None = None,
) -> Dict[str, float]:
    critic_weights = critic_weights or {}
    source_ratios = source_ratios or {
        "expert": 0.5,
        "entropy": 0.25,
        "critic": 0.25,
    }
    hybrid = {}
    for code, value in expert_weights.items():
        hybrid[code] = (
            float(source_ratios.get("expert", 0)) * float(value)
            + float(source_ratios.get("entropy", 0)) * float(entropy_weights.get(code, value))
            + float(source_ratios.get("critic", 0)) * float(critic_weights.get(code, value))
        )
    return _normalize_weight_map(hybrid)


def fuzzify_score(score: float) -> str:
    if score < 40:
        return "低风险"
    if score < 70:
        return "中风险"
    return "高风险"


def indicator_membership(score: float) -> Dict[str, float]:
    score = clamp_score(score)
    if score <= 35:
        low = 1.0
        medium = 0.0
        high = 0.0
    elif score < 60:
        low = round((60 - score) / 25, 4)
        medium = round((score - 35) / 25, 4)
        high = 0.0
    elif score < 85:
        low = 0.0
        medium = round((85 - score) / 25, 4)
        high = round((score - 60) / 25, 4)
    else:
        low = 0.0
        medium = 0.0
        high = 1.0

    return {
        "低风险": round(low, 4),
        "中风险": round(medium, 4),
        "高风险": round(high, 4),
    }


def aggregate_fuzzy_membership(
    detail_map: Mapping[str, float],
    weight_map: Mapping[str, float],
) -> Dict[str, float]:
    memberships = {level: 0.0 for level in RISK_LEVELS}
    for code, score in detail_map.items():
        current = indicator_membership(score)
        for level in RISK_LEVELS:
            memberships[level] += float(weight_map.get(code, 0)) * current[level]

    return {
        level: round(value, 4)
        for level, value in memberships.items()
    }


def blend_memberships(*sources: tuple[Mapping[str, float], float]) -> Dict[str, float]:
    blended = {level: 0.0 for level in RISK_LEVELS}
    total_weight = 0.0

    for membership_map, source_weight in sources:
        numeric_weight = float(source_weight or 0)
        if numeric_weight <= 0:
            continue
        total_weight += numeric_weight
        for level in RISK_LEVELS:
            blended[level] += numeric_weight * float(membership_map.get(level, 0))

    if total_weight <= 0:
        return {level: 0.0 for level in RISK_LEVELS}

    normalized = {level: blended[level] / total_weight for level in RISK_LEVELS}
    probability_total = sum(normalized.values()) or 1.0
    return {
        level: round(value / probability_total, 4)
        for level, value in normalized.items()
    }


def summarize_dimensions(
    detail_map: Mapping[str, float],
    weight_map: Mapping[str, float],
    indicator_records: List[dict],
) -> List[dict]:
    grouped_scores: dict[str, list[dict]] = defaultdict(list)
    for item in indicator_records:
        code = item["code"]
        grouped_scores[item["dimension"]].append(
            {
                "code": code,
                "name": item["name"],
                "score": clamp_score(detail_map.get(code, 0)),
                "weight": round(float(weight_map.get(code, 0)), 4),
            }
        )

    result = []
    for dimension, rows in grouped_scores.items():
        denominator = sum(item["weight"] for item in rows) or 1
        weighted_score = sum(item["score"] * item["weight"] for item in rows) / denominator
        result.append(
            {
                "dimension": dimension,
                "dimension_name": DIMENSION_LABELS.get(dimension, DIMENSION_LABELS["custom"]),
                "average_score": round(sum(item["score"] for item in rows) / len(rows), 2),
                "weighted_score": round(weighted_score, 2),
                "risk_level": fuzzify_score(weighted_score),
                "items": rows,
            }
        )

    result.sort(key=lambda item: item["weighted_score"], reverse=True)
    return result


def summarize_top_risks(
    detail_map: Mapping[str, float],
    weight_map: Mapping[str, float],
    indicator_records: List[dict],
) -> List[dict]:
    rows = []
    meta_map = {item["code"]: item for item in indicator_records}
    for code, score in detail_map.items():
        meta = meta_map.get(code, {})
        weighted_contribution = float(weight_map.get(code, 0)) * float(score)
        rows.append(
            {
                "code": code,
                "name": meta.get("name", FEATURE_LABELS.get(code, code)),
                "dimension": meta.get("dimension", "custom"),
                "dimension_name": meta.get(
                    "dimension_name",
                    DIMENSION_LABELS.get("custom"),
                ),
                "score": clamp_score(score),
                "weight": round(float(weight_map.get(code, 0)), 4),
                "weighted_contribution": round(weighted_contribution, 2),
                "description": meta.get("description"),
                "suggestion": meta.get("suggestion"),
            }
        )

    rows.sort(key=lambda item: (item["weighted_contribution"], item["score"]), reverse=True)
    return rows


def generate_suggestions(
    detail_map: Mapping[str, float],
    risk_level: str,
    top_risks: List[dict],
    dimension_breakdown: List[dict],
) -> List[str]:
    suggestions = []
    seen = set()

    for item in top_risks:
        if item["score"] < 60:
            continue
        suggestion = item.get("suggestion")
        if suggestion and suggestion not in seen:
            suggestions.append(suggestion)
            seen.add(suggestion)
        if len(suggestions) >= 4:
            break

    if dimension_breakdown:
        dominant = dimension_breakdown[0]
        dimension_text = (
            f"当前风险主要集中在“{dominant['dimension_name']}”维度，"
            f"建议围绕该维度制定 2-4 周的连续干预计划。"
        )
        if dimension_text not in seen:
            suggestions.append(dimension_text)
            seen.add(dimension_text)

    fallback_map = {
        "低风险": "整体处于可控区间，建议保持自主学习、事实核验与规范引用的良好习惯。",
        "中风险": "建议建立每周复盘机制，重点压缩高替代型使用，恢复独立分析与协作讨论比例。",
        "高风险": "建议启动重点干预，联合教师指导、任务拆解和使用边界管理，持续跟踪风险变化。",
    }
    fallback = fallback_map[risk_level]
    if fallback not in seen:
        suggestions.append(fallback)

    return suggestions[:5]


def compute_topsis_score(
    detail_map: Mapping[str, float],
    weight_map: Mapping[str, float],
    indicator_records: List[dict],
    comparison_df: pd.DataFrame | None = None,
) -> float:
    codes = [item["code"] for item in indicator_records]
    if not codes:
        return 0.0

    current_vector = np.array([float(detail_map.get(code, 0)) for code in codes], dtype=float)
    prepared = _prepare_comparison_frame(comparison_df, indicator_records)
    matrix = (
        np.vstack([prepared.to_numpy(dtype=float), current_vector])
        if not prepared.empty
        else np.array([current_vector], dtype=float)
    )

    denominator = np.linalg.norm(matrix, axis=0)
    denominator = np.where(denominator == 0, 1, denominator)
    normalized = matrix / denominator

    weights = np.array([float(weight_map.get(code, 0)) for code in codes], dtype=float)
    weighted = normalized * weights
    positive_ideal = weighted.max(axis=0)
    negative_ideal = weighted.min(axis=0)
    current_weighted = weighted[-1]

    distance_positive = float(np.linalg.norm(current_weighted - positive_ideal))
    distance_negative = float(np.linalg.norm(current_weighted - negative_ideal))
    if distance_positive + distance_negative == 0:
        return round(float(np.dot(current_vector, weights)), 2)

    closeness = distance_negative / (distance_positive + distance_negative)
    return round(closeness * 100, 2)


def compute_grey_relation_score(
    detail_map: Mapping[str, float],
    weight_map: Mapping[str, float],
    indicator_records: List[dict],
    comparison_df: pd.DataFrame | None = None,
    resolution: float = 0.5,
) -> float:
    codes = [item["code"] for item in indicator_records]
    if not codes:
        return 0.0

    current_vector = np.array([float(detail_map.get(code, 0)) for code in codes], dtype=float)
    prepared = _prepare_comparison_frame(comparison_df, indicator_records)
    matrix = (
        np.vstack([prepared.to_numpy(dtype=float), current_vector])
        if not prepared.empty
        else np.array([current_vector], dtype=float)
    )

    reference = np.maximum(matrix.max(axis=0), 1.0)
    normalized_current = current_vector / reference
    normalized_reference = np.ones_like(normalized_current)
    delta = np.abs(normalized_reference - normalized_current)

    min_delta = float(delta.min()) if delta.size else 0.0
    max_delta = float(delta.max()) if delta.size else 0.0
    if max_delta == 0:
        return 100.0

    coefficients = (min_delta + resolution * max_delta) / (delta + resolution * max_delta)
    weights = np.array([float(weight_map.get(code, 0)) for code in codes], dtype=float)
    weighted_relation = float(np.sum(weights * coefficients))

    theoretical_min = resolution / (1 + resolution)
    normalized_relation = (weighted_relation - theoretical_min) / max(1 - theoretical_min, 1e-8)
    return clamp_score(normalized_relation * 100)


def evaluate_risk(
    payload: Mapping[str, float],
    indicators: Iterable[Mapping] | None = None,
    comparison_df: pd.DataFrame | None = None,
) -> dict:
    """
    高级评估引擎：
    1. AHP/专家权重
    2. 熵权法
    3. CRITIC 客观赋权
    4. TOPSIS 贴近度
    5. 灰色关联分析
    6. 模糊综合评价
    """
    indicator_records = normalize_weights(build_indicator_records(indicators))
    detail_map = _prepare_payload(payload, indicator_records)

    ahp_metrics = compute_ahp_metrics(indicator_records)
    expert_weights = ahp_metrics["weights"]
    entropy_weights = compute_entropy_weights(comparison_df, indicator_records)
    critic_weights = compute_critic_weights(comparison_df, indicator_records)
    source_ratios = {
        "expert": 0.5,
        "entropy": 0.25,
        "critic": 0.25,
    }
    hybrid_weights = blend_weights(
        expert_weights,
        entropy_weights,
        critic_weights,
        source_ratios=source_ratios,
    )

    weighted_score = round(
        sum(detail_map[code] * hybrid_weights.get(code, 0) for code in detail_map),
        2,
    )
    topsis_score = compute_topsis_score(
        detail_map,
        hybrid_weights,
        indicator_records,
        comparison_df=comparison_df,
    )
    grey_relation_score = compute_grey_relation_score(
        detail_map,
        hybrid_weights,
        indicator_records,
        comparison_df=comparison_df,
    )
    score_fusion = {
        "weighted_score": 0.45,
        "topsis_score": 0.35,
        "grey_relation_score": 0.20,
    }
    total_score = round(
        score_fusion["weighted_score"] * weighted_score
        + score_fusion["topsis_score"] * topsis_score
        + score_fusion["grey_relation_score"] * grey_relation_score,
        2,
    )

    indicator_memberships = aggregate_fuzzy_membership(detail_map, hybrid_weights)
    memberships = blend_memberships(
        (indicator_memberships, 0.45),
        (indicator_membership(weighted_score), 0.20),
        (indicator_membership(topsis_score), 0.20),
        (indicator_membership(grey_relation_score), 0.15),
    )
    risk_level = max(memberships, key=memberships.get)
    confidence = round(float(memberships[risk_level]), 4)

    dimension_breakdown = summarize_dimensions(detail_map, hybrid_weights, indicator_records)
    top_risks = summarize_top_risks(detail_map, hybrid_weights, indicator_records)
    suggestions = generate_suggestions(detail_map, risk_level, top_risks, dimension_breakdown)

    return {
        "total_score": total_score,
        "risk_level": risk_level,
        "confidence": confidence,
        "details": detail_map,
        "suggestions": suggestions,
        "memberships": memberships,
        "dimension_breakdown": dimension_breakdown,
        "top_risks": top_risks[:5],
        "model_details": {
            "weighted_score": weighted_score,
            "topsis_score": topsis_score,
            "grey_relation_score": grey_relation_score,
            "expert_weights": expert_weights,
            "ahp": ahp_metrics,
            "entropy_weights": entropy_weights,
            "critic_weights": critic_weights,
            "hybrid_weights": hybrid_weights,
            "indicator_fuzzy_memberships": indicator_memberships,
            "fuzzy_memberships": memberships,
            "confidence": confidence,
            "source_ratios": source_ratios,
            "score_fusion": score_fusion,
            "method": "AHP专家权重 + 熵权法 + CRITIC + TOPSIS + 灰色关联 + 模糊综合评价 + 相似群体修正",
        },
        "indicator_meta": indicator_records,
    }
