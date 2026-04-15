<template>
  <div class="page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Assessment Report</p>
        <h1>评估报告中心</h1>
        <p class="hero-text">
          支持按学生和评估记录查看完整报告，展示风险等级、模型结果、趋势和重点风险因子。
        </p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" :disabled="!selectedAssessmentId" @click="exportReport">
          导出 JSON
        </el-button>
      </div>
    </section>

    <el-card class="panel selector-card" shadow="never">
      <el-row :gutter="12">
        <el-col :xs="24" :md="10">
          <div class="selector-label">选择学生</div>
          <el-select
            v-model="selectedUserId"
            class="full-width"
            filterable
            placeholder="请选择学生"
          >
            <el-option
              v-for="item in users"
              :key="item.id"
              :label="`${item.username} / ${item.major || '未设置专业'} / ${item.class_name || '未设置班级'}`"
              :value="item.id"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :md="14">
          <div class="selector-label">选择评估记录</div>
          <el-select
            v-model="selectedAssessmentId"
            class="full-width"
            placeholder="请选择评估记录"
          >
            <el-option
              v-for="item in histories"
              :key="item.id"
              :label="`${item.created_at} / ${item.risk_level} / ${item.adjusted_score}`"
              :value="item.id"
            />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <template v-if="report">
      <section class="stats-grid">
        <el-card
          v-for="item in summaryCards"
          :key="item.label"
          class="panel stat-card"
          shadow="never"
        >
          <div class="stat-label">{{ item.label }}</div>
          <div class="stat-value">{{ item.value }}</div>
          <div class="stat-note">{{ item.note }}</div>
        </el-card>
      </section>

      <el-row :gutter="16">
        <el-col :xs="24" :xl="10">
          <el-card class="panel" shadow="never">
            <div class="card-title">学生画像</div>
            <div class="profile-grid">
              <div class="profile-item">
                <span>用户名</span>
                <strong>{{ report.username }}</strong>
              </div>
              <div class="profile-item">
                <span>角色</span>
                <strong>{{ report.student_profile.role || "--" }}</strong>
              </div>
              <div class="profile-item">
                <span>年级</span>
                <strong>{{ report.student_profile.grade || "--" }}</strong>
              </div>
              <div class="profile-item">
                <span>专业</span>
                <strong>{{ report.student_profile.major || "--" }}</strong>
              </div>
              <div class="profile-item">
                <span>班级</span>
                <strong>{{ report.student_profile.class_name || "--" }}</strong>
              </div>
              <div class="profile-item">
                <span>生成时间</span>
                <strong>{{ report.generated_at || "--" }}</strong>
              </div>
            </div>

            <el-alert
              class="conclusion"
              :title="report.conclusion"
              :type="tagType"
              :closable="false"
            />
          </el-card>
        </el-col>

        <el-col :xs="24" :xl="14">
          <el-card class="panel" shadow="never">
            <div class="card-title">模型结果概览</div>
            <div class="model-grid">
              <div class="model-item">
                <strong>风险等级</strong>
                <p>{{ report.summary.risk_level }}</p>
              </div>
              <div class="model-item">
                <strong>风险置信度</strong>
                <p>{{ formatConfidence(report.summary.confidence) }}</p>
              </div>
              <div class="model-item">
                <strong>评估方法</strong>
                <p>{{ report.model_details.method || "综合评价模型" }}</p>
              </div>
              <div class="model-item">
                <strong>主要风险维度</strong>
                <p>{{ topDimensionLabel }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :xs="24" :xl="10">
          <el-card class="panel chart-card" shadow="never">
            <div class="card-title">风险隶属度</div>
            <div ref="membershipRef" class="chart"></div>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="14">
          <el-card class="panel chart-card" shadow="never">
            <div class="card-title">个人趋势</div>
            <div ref="trendRef" class="chart"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :xs="24" :xl="10">
          <el-card class="panel chart-card" shadow="never">
            <div class="card-title">维度雷达图</div>
            <div ref="dimensionRadarRef" class="chart"></div>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="14">
          <el-card class="panel chart-card" shadow="never">
            <div class="card-title">个人与群体对比</div>
            <div ref="comparisonRef" class="chart"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :xs="24" :xl="10">
          <el-card class="panel chart-card" shadow="never">
            <div class="card-title">重点风险因子</div>
            <div ref="topRiskRef" class="chart"></div>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="14">
          <el-card class="panel" shadow="never">
            <div class="card-title">干预建议</div>
            <div class="suggestion-list">
              <div
                v-for="(item, index) in report.suggestions || []"
                :key="index"
                class="suggestion-item"
              >
                {{ item }}
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :xs="24" :xl="12">
          <el-card class="panel" shadow="never">
            <div class="card-title">维度分解</div>
            <el-table :data="report.dimension_breakdown || []" stripe>
              <el-table-column prop="dimension_name" label="维度" min-width="140" />
              <el-table-column prop="average_score" label="平均分" width="90" />
              <el-table-column prop="weighted_score" label="加权分" width="90" />
              <el-table-column prop="risk_level" label="等级" width="90" />
            </el-table>
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="12">
          <el-card class="panel" shadow="never">
            <div class="card-title">历史记录</div>
            <el-table :data="histories" stripe>
              <el-table-column prop="created_at" label="评估时间" min-width="150" />
              <el-table-column prop="risk_level" label="等级" width="90" />
              <el-table-column prop="adjusted_score" label="修正分" width="90" />
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="panel" shadow="never">
        <div class="card-title">指标明细</div>
        <el-table :data="report.indicator_details || []" stripe>
          <el-table-column prop="name" label="指标" min-width="130" />
          <el-table-column prop="dimension_name" label="维度" width="110" />
          <el-table-column prop="score" label="得分" width="90" />
          <el-table-column prop="weight" label="权重" width="90" />
          <el-table-column prop="flag" label="标记" width="100" />
          <el-table-column prop="description" label="说明" min-width="220" />
        </el-table>
      </el-card>
    </template>

    <el-empty
      v-else
      description="当前没有可展示的评估报告，请先选择学生或评估记录。"
    />
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRoute } from "vue-router";
import {
  exportAssessmentReportApi,
  getAssessmentReportApi,
  getHistoryApi,
  getOverviewApi,
  getTrendApi,
  getUsersApi
} from "../api/modules";

const route = useRoute();

const users = ref([]);
const histories = ref([]);
const userTrend = ref([]);
const benchmarkOverview = ref({
  dimension_average: {}
});
const selectedUserId = ref(null);
const selectedAssessmentId = ref(null);
const report = ref(null);

const membershipRef = ref(null);
const trendRef = ref(null);
const dimensionRadarRef = ref(null);
const comparisonRef = ref(null);
const topRiskRef = ref(null);
const charts = {};

const tagType = computed(() => {
  const score = Number(report.value?.summary?.adjusted_score || 0);
  if (score >= 75) {
    return "error";
  }
  if (score >= 55) {
    return "warning";
  }
  return "success";
});

const topDimensionLabel = computed(
  () => report.value?.dimension_breakdown?.[0]?.dimension_name || "--"
);

const summaryCards = computed(() => {
  const summary = report.value?.summary || {};
  return [
    {
      label: "原始分",
      value: summary.total_score ?? "--",
      note: "依据原始指标输入直接计算得到的基础得分。"
    },
    {
      label: "修正分",
      value: summary.adjusted_score ?? "--",
      note: "综合模型修正后的最终风险分数。"
    },
    {
      label: "风险等级",
      value: summary.risk_level ?? "--",
      note: "系统当前用于展示和预警的风险等级。"
    },
    {
      label: "风险置信度",
      value: formatConfidence(summary.confidence),
      note: "模糊综合评价与群体修正后的结果可信度。"
    }
  ];
});

const comparisonRows = computed(() => {
  const groupAverage = benchmarkOverview.value.dimension_average || {};
  return (report.value?.dimension_breakdown || []).map((item) => ({
    dimension_name: item.dimension_name,
    current: Number(item.average_score || 0),
    cohort: Number(groupAverage[item.dimension_name] || 0)
  }));
});

const formatConfidence = (value) => {
  const numeric = Number(value || 0);
  if (!numeric) {
    return "--";
  }
  return `${(numeric * 100).toFixed(1)}%`;
};

const initChart = (key, el) => {
  if (!el) {
    return null;
  }
  if (!charts[key]) {
    charts[key] = echarts.init(el);
  }
  return charts[key];
};

const renderCharts = async () => {
  if (!report.value) {
    return;
  }

  await nextTick();

  const memberships = report.value.summary?.fuzzy_memberships || {};
  const dimensionBreakdown = report.value.dimension_breakdown || [];
  const topRisks = report.value.top_risks || [];

  initChart("membership", membershipRef.value)?.setOption({
    grid: { left: 46, right: 16, top: 24, bottom: 30 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: Object.keys(memberships)
    },
    yAxis: {
      type: "value",
      max: 1
    },
    series: [
      {
        type: "bar",
        barWidth: 34,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#1d4ed8" },
            { offset: 1, color: "#60a5fa" }
          ]),
          borderRadius: [10, 10, 0, 0]
        },
        data: Object.values(memberships)
      }
    ]
  });

  initChart("trend", trendRef.value)?.setOption({
    grid: { left: 48, right: 20, top: 24, bottom: 44 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: userTrend.value.map((item) => item.date),
      axisLabel: { rotate: 24 }
    },
    yAxis: {
      type: "value",
      max: 100
    },
    series: [
      {
        name: "修正分",
        type: "line",
        smooth: true,
        symbolSize: 8,
        lineStyle: { width: 3, color: "#d97706" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(245, 158, 11, 0.35)" },
            { offset: 1, color: "rgba(245, 158, 11, 0.04)" }
          ])
        },
        data: userTrend.value.map((item) => item.adjusted_score)
      }
    ]
  });

  initChart("dimensionRadar", dimensionRadarRef.value)?.setOption({
    color: ["#0f766e"],
    tooltip: { trigger: "item" },
    radar: {
      radius: "62%",
      indicator: dimensionBreakdown.map((item) => ({
        name: item.dimension_name,
        max: 100
      })),
      splitArea: {
        areaStyle: {
          color: ["rgba(255,255,255,0.75)", "rgba(239,248,248,0.95)"]
        }
      }
    },
    series: [
      {
        type: "radar",
        areaStyle: { color: "rgba(15, 118, 110, 0.18)" },
        lineStyle: { width: 2.5 },
        data: [
          {
            value: dimensionBreakdown.map((item) => item.average_score)
          }
        ]
      }
    ]
  });

  initChart("comparison", comparisonRef.value)?.setOption({
    color: ["#f59e0b", "#94a3b8"],
    grid: { left: 54, right: 20, top: 24, bottom: 36 },
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    xAxis: {
      type: "category",
      data: comparisonRows.value.map((item) => item.dimension_name)
    },
    yAxis: {
      type: "value",
      max: 100
    },
    series: [
      {
        name: "个人",
        type: "bar",
        barWidth: 18,
        data: comparisonRows.value.map((item) => item.current)
      },
      {
        name: "群体均值",
        type: "bar",
        barWidth: 18,
        data: comparisonRows.value.map((item) => item.cohort)
      }
    ]
  });

  initChart("topRisk", topRiskRef.value)?.setOption({
    grid: { left: 110, right: 20, top: 24, bottom: 30 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "value",
      max: 100
    },
    yAxis: {
      type: "category",
      data: [...topRisks].reverse().map((item) => item.name)
    },
    series: [
      {
        type: "bar",
        barWidth: 18,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: "#ef4444" },
            { offset: 1, color: "#f59e0b" }
          ]),
          borderRadius: [0, 10, 10, 0]
        },
        data: [...topRisks].reverse().map((item) => item.score)
      }
    ]
  });
};

const loadUsers = async () => {
  try {
    const res = await getUsersApi({ role: "student" });
    users.value = res.data || [];
    const queryUserId = Number(route.query.userId || 0);
    selectedUserId.value =
      users.value.find((item) => item.id === queryUserId)?.id || users.value[0]?.id || null;
  } catch (error) {
    ElMessage.error("学生列表加载失败");
  }
};

const loadHistories = async () => {
  if (!selectedUserId.value) {
    histories.value = [];
    selectedAssessmentId.value = null;
    report.value = null;
    return;
  }

  try {
    const res = await getHistoryApi(selectedUserId.value);
    histories.value = res.data || [];
    const queryAssessmentId = Number(route.query.assessmentId || 0);
    selectedAssessmentId.value =
      histories.value.find((item) => item.id === queryAssessmentId)?.id ||
      histories.value[histories.value.length - 1]?.id ||
      null;
  } catch (error) {
    histories.value = [];
    selectedAssessmentId.value = null;
    report.value = null;
    ElMessage.error("评估历史加载失败");
  }
};

const loadTrend = async () => {
  if (!selectedUserId.value) {
    userTrend.value = [];
    return;
  }

  try {
    const res = await getTrendApi(selectedUserId.value);
    userTrend.value = res.data || [];
    await renderCharts();
  } catch (error) {
    userTrend.value = [];
  }
};

const loadBenchmark = async () => {
  try {
    const res = await getOverviewApi();
    benchmarkOverview.value = res.data || benchmarkOverview.value;
    await renderCharts();
  } catch (error) {
    benchmarkOverview.value = { dimension_average: {} };
  }
};

const loadReport = async () => {
  if (!selectedAssessmentId.value) {
    report.value = null;
    return;
  }

  try {
    const res = await getAssessmentReportApi(selectedAssessmentId.value);
    report.value = res.data || null;
    await renderCharts();
  } catch (error) {
    report.value = null;
    ElMessage.error("报告加载失败");
  }
};

const exportReport = async () => {
  if (!selectedAssessmentId.value) {
    return;
  }

  try {
    const response = await exportAssessmentReportApi(selectedAssessmentId.value);
    const blob = new Blob([response.data], { type: "application/json;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `aigc-risk-report-${selectedAssessmentId.value}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  } catch (error) {
    ElMessage.error("导出报告失败");
  }
};

watch(selectedUserId, async () => {
  await loadHistories();
  await loadTrend();
});

watch(selectedAssessmentId, async () => {
  await loadReport();
});

const handleResize = () => {
  Object.values(charts).forEach((chart) => chart?.resize());
};

onMounted(async () => {
  await loadUsers();
  await loadBenchmark();
  await loadHistories();
  await loadTrend();
  await loadReport();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  Object.values(charts).forEach((chart) => chart?.dispose());
});
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(249, 168, 37, 0.18), transparent 30%),
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.1), transparent 24%),
    linear-gradient(135deg, #fffdf8 0%, #f4f9ff 52%, #eef3f8 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 30px 32px;
  margin-bottom: 18px;
  border-radius: 28px;
  color: #102542;
  background: linear-gradient(135deg, rgba(255, 243, 214, 0.95), rgba(238, 246, 255, 0.94));
  box-shadow: 0 18px 48px rgba(16, 37, 66, 0.08);
}

.hero-copy {
  max-width: 820px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #d97706;
}

.hero h1 {
  margin: 0;
  font-size: 32px;
}

.hero-text {
  margin: 14px 0 0;
  line-height: 1.8;
  color: #607080;
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: flex-start;
}

.panel {
  margin-bottom: 16px;
  border: none;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 14px 36px rgba(16, 37, 66, 0.06);
}

.panel :deep(.el-card__body) {
  padding: 20px;
}

.selector-card {
  margin-bottom: 16px;
}

.selector-label {
  margin-bottom: 8px;
  font-size: 13px;
  color: #607080;
}

.full-width {
  width: 100%;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  margin-bottom: 0;
}

.stat-label {
  font-size: 13px;
  color: #607080;
}

.stat-value {
  margin-top: 12px;
  font-size: 32px;
  font-weight: 700;
  color: #102542;
}

.stat-note {
  margin-top: 10px;
  line-height: 1.6;
  color: #6b7b8e;
}

.card-title {
  margin-bottom: 16px;
  font-size: 18px;
  font-weight: 700;
  color: #102542;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-item {
  padding: 16px;
  border-radius: 16px;
  background: #f8fafc;
}

.profile-item span {
  display: block;
  color: #6b7b8e;
  font-size: 13px;
}

.profile-item strong {
  display: block;
  margin-top: 10px;
  font-size: 18px;
  color: #102542;
}

.conclusion {
  margin-top: 18px;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.model-item {
  padding: 16px;
  border-radius: 16px;
  background: #f8fafc;
}

.model-item strong {
  display: block;
  color: #475569;
}

.model-item p {
  margin: 10px 0 0;
  color: #0f172a;
  line-height: 1.7;
}

.chart {
  height: 340px;
}

.suggestion-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.suggestion-item {
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(16, 185, 129, 0.1);
  color: #0f766e;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .hero,
  .profile-grid,
  .model-grid {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}

@media (max-width: 640px) {
  .page {
    padding: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
