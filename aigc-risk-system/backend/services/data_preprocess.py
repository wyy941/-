from __future__ import annotations

import pandas as pd
import numpy as np

from services.risk_engine import BASE_INPUT_COLUMNS, FEATURE_COLUMNS, enrich_feature_frame

NUMERIC_FIELDS = sorted(set(BASE_INPUT_COLUMNS + FEATURE_COLUMNS))


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    数据清洗流程：
    1. 去重
    2. 数值字段缺失值用中位数填充
    3. 异常值用 IQR 规则裁剪
    """
    result = df.copy()
    result = result.drop_duplicates()

    for column in NUMERIC_FIELDS:
        if column not in result.columns:
            result[column] = 0

        result[column] = pd.to_numeric(result[column], errors="coerce")
        median_value = result[column].median()
        if np.isnan(median_value):
            median_value = 0
        result[column] = result[column].fillna(median_value)

        q1 = result[column].quantile(0.25)
        q3 = result[column].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        result[column] = result[column].clip(lower=lower, upper=upper)

    return enrich_feature_frame(result)
