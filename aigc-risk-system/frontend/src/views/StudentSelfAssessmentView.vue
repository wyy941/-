<template>
  <div class="page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Student Self Assessment</p>
        <h1>{{ PROJECT_NAME }}</h1>
        <p class="hero-text">
          学生自我评价采用 6 个维度、60 道题的问卷方式完成。你只需要根据每道题的实际情况，
          从“无明显表现”到“严重”之间选择对应程度，系统会自动按权值与评估模型计算最终总分。
        </p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" @click="router.push('/student-center')">返回学生首页</el-button>
      </div>
    </section>

    <el-row :gutter="18">
      <el-col :xs="24" :xl="16">
        <el-card class="panel" shadow="never">
          <template #header>
            <div class="panel-header">
              <div>
                <div class="panel-title">自我评价问卷</div>
                <p>请按真实情况完成全部题目。提交后系统只向学生端展示最终总分，不展示权重与模型细节。</p>
              </div>
              <el-tag type="primary">{{ questionCount }} 题</el-tag>
            </div>
          </template>

          <div class="progress-card">
            <div>
              <div class="progress-title">完成进度</div>
              <div class="progress-meta">已完成 {{ completedCount }} / {{ questionCount }} 题</div>
            </div>
            <div class="progress-value">{{ completionPercent }}%</div>
          </div>
          <el-progress :percentage="completionPercent" :stroke-width="10" />

          <section
            v-for="group in dimensions"
            :key="group.dimension"
            class="dimension-section"
          >
            <div class="dimension-head">
              <div>
                <h2>{{ group.dimension_name }}</h2>
                <p>共 {{ group.questions.length }} 道题，请按轻度到严重的实际程度完成选择。</p>
              </div>
              <el-tag effect="plain">{{ group.questions.length }} 题</el-tag>
            </div>

            <div class="question-list">
              <article
                v-for="question in group.questions"
                :key="question.id"
                class="question-card"
              >
                <div class="question-top">
                  <span class="question-no">Q{{ String(question.order).padStart(2, '0') }}</span>
                  <p>{{ question.text }}</p>
                </div>

                <el-radio-group
                  v-model="form.answers[question.id]"
                  class="option-group"
                >
                  <el-radio-button
                    v-for="option in answerOptions"
                    :key="option.value"
                    :label="option.value"
                  >
                    {{ option.label }}
                  </el-radio-button>
                </el-radio-group>
              </article>
            </div>
          </section>

          <div class="submit-bar">
            <div class="submit-copy">
              <strong>提交后自动写入系统</strong>
              <span>系统将把 60 道题的结果聚合为指标分值，并通过权值模型计算本次最终总分。</span>
            </div>
            <el-button
              type="primary"
              size="large"
              :loading="submitting"
              :disabled="!canSubmit || submitting"
              @click="submitAssessment"
            >
              提交自我评价
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="8">
        <el-card class="panel side-panel" shadow="never">
          <div class="panel-title">当前学生</div>
          <div class="profile-grid">
            <div class="profile-item">
              <span>用户名</span>
              <strong>{{ currentUser?.username || "--" }}</strong>
            </div>
            <div class="profile-item">
              <span>年级</span>
              <strong>{{ currentUser?.grade || "--" }}</strong>
            </div>
            <div class="profile-item">
              <span>专业</span>
              <strong>{{ currentUser?.major || "--" }}</strong>
            </div>
            <div class="profile-item">
              <span>班级</span>
              <strong>{{ currentUser?.class_name || "--" }}</strong>
            </div>
          </div>
        </el-card>

        <el-card class="panel side-panel" shadow="never">
          <div class="panel-title">本次结果</div>
          <el-empty
            v-if="!latestAssessment"
            description="完成全部 60 道题并提交后，这里会显示系统计算出的最终总分。"
          />
          <template v-else>
            <div class="score-card">
              <span>最终总分</span>
              <strong>{{ latestAssessment.final_score }}</strong>
            </div>
            <div class="side-metric">
              <span>累计评估次数</span>
              <strong>{{ overview.assessment_count || 0 }}</strong>
            </div>
            <div class="side-metric">
              <span>最近提交时间</span>
              <strong>{{ formatDateTime(latestAssessment.created_at) }}</strong>
            </div>
          </template>
        </el-card>

        <el-card class="panel side-panel" shadow="never">
          <div class="panel-title">总分趋势</div>
          <div ref="trendRef" class="chart"></div>
        </el-card>

        <el-card class="panel side-panel" shadow="never">
          <div class="panel-title">最近记录</div>
          <el-table :data="overview.recent_records || []" stripe max-height="320">
            <el-table-column prop="created_at" label="提交时间" min-width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="final_score" label="最终总分" width="110" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import {
  getStudentSelfAssessmentMetaApi,
  getStudentSelfAssessmentOverviewApi,
  submitStudentSelfAssessmentApi
} from "../api/modules";
import { PROJECT_NAME } from "../constants/branding";
import { getStoredUser } from "../utils/auth";

const router = useRouter();
const currentUser = ref(getStoredUser());
const dimensions = ref([]);
const answerOptions = ref([]);
const overview = ref({
  latest_assessment: null,
  assessment_count: 0,
  recent_records: [],
  trend: []
});
const trendRef = ref(null);
const submitting = ref(false);
const form = reactive({
  answers: {}
});

let trendChart;

const flatQuestions = computed(() =>
  dimensions.value.flatMap((group) => group.questions || [])
);
const questionCount = computed(() => flatQuestions.value.length);
const completedCount = computed(
  () =>
    flatQuestions.value.filter(
      (question) => form.answers[question.id] !== null && form.answers[question.id] !== undefined
    ).length
);
const completionPercent = computed(() =>
  questionCount.value ? Math.round((completedCount.value / questionCount.value) * 100) : 0
);
const canSubmit = computed(
  () => questionCount.value > 0 && completedCount.value === questionCount.value
);
const latestAssessment = computed(() => overview.value.latest_assessment || null);

const formatDateTime = (value) => {
  if (!value) {
    return "--";
  }
  return String(value).replace("T", " ").slice(0, 16);
};

const ensureAnswerDefaults = () => {
  for (const question of flatQuestions.value) {
    if (form.answers[question.id] === undefined) {
      form.answers[question.id] = null;
    }
  }
};

const renderTrend = async () => {
  await nextTick();
  if (!trendRef.value) {
    return;
  }

  trendChart = trendChart || echarts.init(trendRef.value);
  const trendRows = overview.value.trend || [];

  trendChart.setOption({
    grid: { left: 42, right: 16, top: 24, bottom: 36 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: trendRows.map((item) => item.date),
      axisLabel: { rotate: 16 }
    },
    yAxis: { type: "value", max: 100 },
    series: [
      {
        name: "最终总分",
        type: "line",
        smooth: true,
        data: trendRows.map((item) => item.final_score),
        lineStyle: { width: 3, color: "#2563eb" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(37, 99, 235, 0.22)" },
            { offset: 1, color: "rgba(37, 99, 235, 0.04)" }
          ])
        }
      }
    ]
  });
};

const loadMeta = async () => {
  try {
    const res = await getStudentSelfAssessmentMetaApi();
    dimensions.value = res.data?.dimensions || [];
    answerOptions.value = res.data?.answer_options || [];
    ensureAnswerDefaults();
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || "自我评价问卷加载失败");
  }
};

const loadOverview = async () => {
  try {
    const res = await getStudentSelfAssessmentOverviewApi();
    overview.value = res.data || overview.value;
    await renderTrend();
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || "自我评价结果加载失败");
  }
};

const submitAssessment = async () => {
  if (!canSubmit.value) {
    ElMessage.warning("请先完成全部 60 道题后再提交");
    return;
  }

  submitting.value = true;
  try {
    const payload = {};
    for (const question of flatQuestions.value) {
      payload[question.id] = form.answers[question.id];
    }

    const res = await submitStudentSelfAssessmentApi({ answers: payload });
    if (res.code === 201) {
      ElMessage.success("自我评价已提交，系统已完成本次总分计算");
      await loadOverview();
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      ElMessage.error(res.message || "自我评价提交失败");
    }
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || "自我评价提交失败");
  } finally {
    submitting.value = false;
  }
};

const handleResize = () => {
  trendChart?.resize();
};

watch(
  () => overview.value.trend,
  () => {
    renderTrend();
  },
  { deep: true }
);

onMounted(async () => {
  await loadMeta();
  await loadOverview();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  trendChart?.dispose();
});
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 24%),
    linear-gradient(180deg, #f7f9fc 0%, #eef3f8 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  padding: 30px 32px;
  border-radius: 30px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.12), transparent 32%),
    linear-gradient(135deg, #0f172a, #1f2e45 58%, #304861 100%);
  color: #fff;
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.14);
}

.hero-copy {
  max-width: 860px;
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.7);
}

.hero h1 {
  margin: 16px 0 0;
  font-size: 36px;
  line-height: 1.3;
}

.hero-text {
  margin-top: 16px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.84);
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.panel {
  margin-top: 18px;
  border: none;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14px 36px rgba(16, 37, 66, 0.08);
}

.panel :deep(.el-card__body) {
  padding: 22px;
}

.panel-header,
.dimension-head,
.submit-bar,
.progress-card {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.panel-title {
  font-size: 18px;
  font-weight: 700;
  color: #102542;
}

.panel-header p,
.dimension-head p {
  margin: 8px 0 0;
  color: #6b7b8e;
  line-height: 1.7;
}

.progress-card {
  padding: 16px 18px;
  margin-bottom: 12px;
  border-radius: 20px;
  background: linear-gradient(135deg, #f7fbff, #eef4ff);
}

.progress-title {
  font-size: 14px;
  color: #5f7287;
}

.progress-meta {
  margin-top: 8px;
  font-size: 20px;
  font-weight: 700;
  color: #102542;
}

.progress-value {
  font-size: 28px;
  font-weight: 700;
  color: #1d4ed8;
}

.dimension-section + .dimension-section {
  margin-top: 26px;
}

.dimension-head h2 {
  margin: 0;
  color: #102542;
  font-size: 22px;
}

.question-list {
  margin-top: 16px;
  display: grid;
  gap: 14px;
}

.question-card {
  padding: 18px;
  border-radius: 20px;
  background: linear-gradient(135deg, #fbfdff, #f3f7fc);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.question-top {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.question-no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  height: 30px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.12);
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.question-top p {
  margin: 0;
  line-height: 1.7;
  color: #102542;
}

.option-group {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
}

.option-group :deep(.el-radio-button__inner) {
  min-width: 92px;
}

.submit-bar {
  margin-top: 28px;
  padding: 18px 20px;
  border-radius: 22px;
  background: linear-gradient(135deg, #0f172a, #1f2e45);
  color: #fff;
}

.submit-copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.submit-copy strong {
  font-size: 18px;
}

.submit-copy span {
  color: rgba(255, 255, 255, 0.76);
  line-height: 1.7;
}

.side-panel {
  margin-top: 18px;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-item,
.side-metric {
  padding: 16px;
  border-radius: 18px;
  background: #f6f9fc;
}

.profile-item span,
.side-metric span,
.score-card span {
  display: block;
  color: #6e8094;
  font-size: 13px;
}

.profile-item strong,
.side-metric strong {
  display: block;
  margin-top: 8px;
  color: #102542;
  font-size: 18px;
}

.score-card {
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(135deg, #eff6ff, #f7fbff);
}

.score-card strong {
  display: block;
  margin-top: 10px;
  color: #102542;
  font-size: 40px;
  font-weight: 700;
}

.side-metric + .side-metric {
  margin-top: 12px;
}

.chart {
  height: 280px;
}

@media (max-width: 1200px) {
  .hero,
  .submit-bar {
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .page {
    padding: 16px;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }

  .question-top {
    flex-direction: column;
  }
}
</style>
