from __future__ import annotations

from collections import defaultdict

SEVERITY_OPTIONS = [
    {"label": "无明显表现", "value": 0},
    {"label": "轻微", "value": 25},
    {"label": "较明显", "value": 50},
    {"label": "中度", "value": 75},
    {"label": "严重", "value": 100},
]

ANSWER_VALUES = {item["value"] for item in SEVERITY_OPTIONS}

QUESTION_BLUEPRINTS = [
    (
        "behavior",
        "行为依赖",
        [
            ("usage_frequency", "面对学习任务时，你会第一时间打开 AIGC 工具寻求帮助。"),
            ("usage_frequency", "即使问题并不复杂，你也倾向先让 AIGC 给出答案。"),
            ("usage_frequency", "一周内你使用 AIGC 辅助学习的频率较高。"),
            ("usage_frequency", "离开 AIGC 后，你会明显感觉学习效率下降。"),
            ("scenario_pervasiveness", "AIGC 的使用已经从课程作业延伸到生活安排、表达组织等多种场景。"),
            ("scenario_pervasiveness", "除了学习外，你也经常用 AIGC 处理日常事务。"),
            ("scenario_pervasiveness", "在大多数需要表达、整理或输出内容的场景中，你都会想到使用 AIGC。"),
            ("academic_substitution", "撰写作业主体内容时，你经常直接采用 AIGC 生成结果。"),
            ("academic_substitution", "整理文献、资料或提纲时，你主要依赖 AIGC 而不是自己筛选和组织。"),
            ("academic_substitution", "遇到课程任务时，你常把结构设计和主要内容交给 AIGC 完成。"),
        ],
    ),
    (
        "cognition",
        "认知弱化",
        [
            ("independent_thinking_loss", "看到题目时，你往往还没开始思考就先向 AIGC 提问。"),
            ("independent_thinking_loss", "面对开放性问题时，你更依赖 AIGC 帮你组织思路。"),
            ("independent_thinking_loss", "独立分析复杂问题时，你常因习惯求助模型而中断自己的推理过程。"),
            ("independent_thinking_loss", "没有 AIGC 支持时，你较难持续完成完整的思考链路。"),
            ("result_verification_weakness", "对 AIGC 给出的事实、数据和论据，你很少主动核查。"),
            ("result_verification_weakness", "引用 AIGC 内容时，你通常不会再追溯原始来源。"),
            ("result_verification_weakness", "使用 AIGC 后，你较少再自行验证答案的逻辑是否严密。"),
            ("critical_judgement_weakness", "面对 AIGC 的观点时，你很少主动提出反例或质疑。"),
            ("critical_judgement_weakness", "即使模型结论与你原本的判断不同，你也更愿意相信模型。"),
            ("critical_judgement_weakness", "在写作或讨论中，你较少反思模型答案是否存在局限。"),
        ],
    ),
    (
        "ethics",
        "伦理与安全",
        [
            ("academic_integrity_risk", "使用 AIGC 生成内容时，你不太关注是否需要说明 AI 辅助。"),
            ("academic_integrity_risk", "提交作业时，你会弱化 AIGC 的参与程度。"),
            ("academic_integrity_risk", "复制 AI 生成内容时，你较少补充原创说明或规范引用。"),
            ("privacy_security_risk", "向 AIGC 输入题目、作业或资料时，你不太考虑其中是否包含敏感信息。"),
            ("privacy_security_risk", "你会把包含个人信息或课程内部资料的内容输入 AIGC。"),
            ("privacy_security_risk", "使用外部 AIGC 服务时，你较少对输入内容做脱敏处理。"),
            ("algorithm_bias_unawareness", "面对 AIGC 输出内容时，你不太关注其中是否存在偏差或刻板印象。"),
            ("algorithm_bias_unawareness", "即使发现模型可能有幻觉，你通常也不会进一步核对。"),
            ("algorithm_bias_unawareness", "你对模型立场倾向和价值偏差的识别意识较弱。"),
            ("algorithm_bias_unawareness", "你默认认为主流 AIGC 的输出基本可靠，不需要额外警惕。"),
        ],
    ),
    (
        "social",
        "社交与协作",
        [
            ("social_collaboration_displacement", "遇到学习问题时，你更愿意先问 AIGC 而不是同学。"),
            ("social_collaboration_displacement", "本应与老师交流的问题，你也常直接交给 AIGC。"),
            ("social_collaboration_displacement", "团队协作任务中，你更依赖 AIGC 而不是成员讨论。"),
            ("emotional_dependence", "遇到情绪波动时，你会先向 AIGC 倾诉。"),
            ("emotional_dependence", "有压力时，你更依赖 AIGC 给出安慰、鼓励或建议。"),
            ("emotional_dependence", "AIGC 在一定程度上替代了你原本的现实支持渠道。"),
            ("communication_avoidance", "面对分歧或沟通难题时，你更倾向回到 AIGC，而不是当面交流。"),
            ("communication_avoidance", "需要表达观点时，你更愿意先让 AIGC 帮你组织话术。"),
            ("communication_avoidance", "因为习惯依赖 AIGC，你与同学、老师的主动沟通有所减少。"),
            ("communication_avoidance", "当需要沟通协调时，你会下意识回避现实交流，转向模型。"),
        ],
    ),
    (
        "learning",
        "学习投入",
        [
            ("self_regulated_learning_weakness", "制定学习计划时，你常先让 AIGC 安排步骤。"),
            ("self_regulated_learning_weakness", "学习任务拆解更多依赖 AIGC，而不是自己规划。"),
            ("self_regulated_learning_weakness", "复盘学习效果时，你较少自己总结，更多依赖 AIGC 分析。"),
            ("self_regulated_learning_weakness", "你的学习推进节奏容易被模型建议牵着走。"),
            ("knowledge_internalization_gap", "即使能够生成答案，你也不一定真正理解其中的知识点。"),
            ("knowledge_internalization_gap", "完成内容后，如果没有 AIGC 你较难复述关键知识。"),
            ("knowledge_internalization_gap", "同类问题稍有变化时，若没有 AIGC 你会难以迁移应用。"),
            ("task_planning_dependence", "选题或确定研究方向时，你很依赖 AIGC 给出思路。"),
            ("task_planning_dependence", "一旦 AIGC 不给方案，你会觉得任务难以下手。"),
            ("task_planning_dependence", "在安排执行优先级时，你更依赖 AIGC 做决定。"),
        ],
    ),
    (
        "self_management",
        "自我调节",
        [
            ("time_management_disorder", "使用 AIGC 时，你容易在不同提示词和回答之间反复切换。"),
            ("time_management_disorder", "AIGC 交互会打断你原本的学习专注节奏。"),
            ("time_management_disorder", "为了修改生成结果，你常花费超出预期的时间。"),
            ("attention_dispersion_risk", "使用 AIGC 后，你更容易出现拖延和临时赶工。"),
            ("attention_dispersion_risk", "学习过程中，你会频繁切换窗口或工具，导致注意力分散。"),
            ("attention_dispersion_risk", "使用 AIGC 后，持续专注完成单一任务变得更困难。"),
            ("offline_problem_solving_avoidance", "遇到问题时，如果不能使用 AIGC，你会更想回避任务。"),
            ("offline_problem_solving_avoidance", "没有 AIGC 支持时，你独立解决问题的意愿明显下降。"),
            ("offline_problem_solving_avoidance", "在无法联网或无法调用模型时，你的执行状态会受到明显影响。"),
            ("offline_problem_solving_avoidance", "你逐渐不愿意在完全不依赖技术的情况下完成学习任务。"),
        ],
    ),
]

STUDENT_QUESTIONNAIRE_QUESTIONS = []
question_index = 1
for dimension, dimension_name, items in QUESTION_BLUEPRINTS:
    for indicator_code, text in items:
        STUDENT_QUESTIONNAIRE_QUESTIONS.append(
            {
                "id": f"q{question_index:02d}",
                "dimension": dimension,
                "dimension_name": dimension_name,
                "indicator_code": indicator_code,
                "text": text,
                "order": question_index,
            }
        )
        question_index += 1

QUESTION_LOOKUP = {item["id"]: item for item in STUDENT_QUESTIONNAIRE_QUESTIONS}


def student_questionnaire_meta() -> dict:
    grouped = defaultdict(list)
    dimension_names = {}

    for item in STUDENT_QUESTIONNAIRE_QUESTIONS:
        grouped[item["dimension"]].append(
            {
                "id": item["id"],
                "text": item["text"],
                "order": item["order"],
            }
        )
        dimension_names[item["dimension"]] = item["dimension_name"]

    groups = []
    for dimension, items in grouped.items():
        groups.append(
            {
                "dimension": dimension,
                "dimension_name": dimension_names.get(dimension, "自定义维度"),
                "questions": items,
            }
        )

    groups.sort(key=lambda item: item["questions"][0]["order"])
    return {
        "question_count": len(STUDENT_QUESTIONNAIRE_QUESTIONS),
        "answer_options": SEVERITY_OPTIONS,
        "dimensions": groups,
    }


def questionnaire_answer_to_indicator_scores(answer_payload: dict) -> dict:
    indicator_scores = defaultdict(list)

    for question in STUDENT_QUESTIONNAIRE_QUESTIONS:
        score = float(answer_payload[question["id"]])
        indicator_scores[question["indicator_code"]].append(score)

    return {
        indicator_code: round(sum(scores) / max(len(scores), 1), 2)
        for indicator_code, scores in indicator_scores.items()
    }
