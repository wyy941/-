from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from services.risk_engine import FEATURE_COLUMNS


def similarity_adjust_score(
    history_df: pd.DataFrame,
    target_vector: dict,
    base_score: float,
    top_k: int = 5,
) -> float:
    """
    用相似用户历史样本对单次评估结果进行轻量修正。
    修正规则：
    - 找到与当前用户最相似的 top_k 样本
    - 取其风险得分均值
    - 最终分数 = 0.8 * 原始分 + 0.2 * 相似用户均值
    """
    if history_df.empty or "adjusted_score" not in history_df.columns:
        return round(base_score, 2)

    usable = history_df.copy()
    missing_cols = [col for col in FEATURE_COLUMNS if col not in usable.columns]
    if missing_cols:
        for col in missing_cols:
            usable[col] = 0

    feature_matrix = usable[FEATURE_COLUMNS].fillna(0).astype(float).values
    target_array = np.array([[float(target_vector.get(col, 0)) for col in FEATURE_COLUMNS]])

    if len(feature_matrix) == 0:
        return round(base_score, 2)

    similarities = cosine_similarity(target_array, feature_matrix)[0]
    usable["similarity"] = similarities
    usable = usable.sort_values("similarity", ascending=False)
    usable = usable[usable["similarity"] > 0].head(top_k)

    if usable.empty:
        return round(base_score, 2)

    weights = usable["similarity"].clip(lower=0.01)
    peer_score = np.average(usable["adjusted_score"], weights=weights)
    confidence = min(len(usable) / max(top_k, 1), 1)
    peer_ratio = 0.12 + 0.13 * confidence
    adjusted = (1 - peer_ratio) * float(base_score) + peer_ratio * float(peer_score)
    return round(adjusted, 2)
