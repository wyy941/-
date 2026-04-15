<template>
  <div class="page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Decision Cockpit</p>
        <h1>大学生 AIGC 技术依赖风险分析驾驶舱</h1>
        <p class="hero-text">
          系统看板按群体态势、阶段趋势、年级对比、指标热区、专业班级画像和预警名单六个层面展示。
        </p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" @click="$router.push('/assessment')">高级评估</el-button>
        <el-button @click="$router.push('/data-center')">数据中心</el-button>
        <el-button @click="$router.push('/indicators')">指标管理</el-button>
        <el-button @click="$router.push('/report')">报告中心</el-button>
      </div>
    </section>

    <el-card class="panel filter-panel" shadow="never">
      <div class="panel-header">
        <div>
          <h3>多维筛选</h3>
          <p>筛选条件会同步影响统计卡片、趋势图、专业排名、班级预警和告警名单。</p>
        </div>
        <div class="filter-actions">
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="primary" @click="loadData">应用筛选</el-button>
        </div>
      </div>

      <el-row :gutter="12">
        <el-col :xs="24" :sm="12" :md="8" :lg="5">
          <el-select
            v-model="filters.grade"
            clearable
            placeholder="年级"
            class="full-width"
            @change="handleFilterChange('grade')"
          >
            <el-option
              v-for="item in filterOptions.grades"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="5">
          <el-select
            v-model="filters.major"
            clearable
            placeholder="专业"
            class="full-width"
            @change="handleFilterChange('major')"
          >
            <el-option
              v-for="item in filterOptions.majors"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="5">
          <el-select
            v-model="filters.class_name"
            clearable
            class="full-width"
            :disabled="!filters.grade || !filters.major"
            :placeholder="filters.grade && filters.major ? '班级' : '请先选择年级和专业'"
            @change="handleFilterChange('class_name')"
          >
            <el-option
              v-for="item in filterOptions.classes"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :lg="4">
          <el-select
            v-model="filters.risk_level"
            clearable
            class="full-width"
            :disabled="!filters.grade || !filters.major || !filters.class_name"
            :placeholder="filters.grade && filters.major && filters.class_name ? '风险等级' : '请先选择班级'"
            @change="handleFilterChange('risk_level')"
          >
            <el-option
              v-for="item in filterOptions.risk_levels"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-col>
      </el-row>

      <div class="filter-tip">
        多维筛选按“年级 + 专业 -> 班级 -> 风险等级”联动，班级只显示该年级该专业对应的班级。
      </div>
    </el-card>

    <section class="stats-grid">
      <el-card
        v-for="item in summaryCards"
        :key="item.label"
        class="panel stat-card"
        shadow="never"
      >
        <div class="stat-label">{{ item.label }}</div>
        <div class="stat-value" :class="{ compact: item.compact }">{{ item.value }}</div>
        <div class="stat-note">{{ item.note }}</div>
      </el-card>
    </section>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="8">
        <el-card class="panel chart-card" shadow="never">
          <div class="card-title">风险等级分布</div>
          <div ref="riskPieRef" class="chart medium"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :xl="16">
        <el-card class="panel chart-card" shadow="never">
          <div class="card-title">月度风险趋势</div>
          <div ref="monthlyTrendRef" class="chart medium"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="14">
        <el-card class="panel chart-card" shadow="never">
          <div class="card-title">年级风险分层</div>
          <div ref="gradeRiskRef" class="chart medium"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :xl="10">
        <el-card class="panel chart-card" shadow="never">
          <div class="card-title">分数段分布</div>
          <div ref="scoreBandRef" class="chart medium"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="14">
        <el-card class="panel chart-card" shadow="never">
          <div class="card-title">风险指标热区排序</div>
          <div ref="indicatorRef" class="chart tall"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :xl="10">
        <el-card class="panel chart-card" shadow="never">
          <div class="card-title">维度雷达画像</div>
          <div ref="dimensionRadarRef" class="chart tall"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="14">
        <el-card class="panel table-card" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">专业风险画像</div>
              <p>按专业统计平均分、高风险占比和样本规模。</p>
            </div>
          </div>
          <el-table :data="overview.major_risk_stats || []" stripe>
            <el-table-column prop="major" label="专业" min-width="160" />
            <el-table-column prop="student_count" label="学生数" width="90" />
            <el-table-column prop="assessment_count" label="评估数" width="90" />
            <el-table-column prop="avg_score" label="均分" width="90" />
            <el-table-column label="高风险占比" min-width="160">
              <template #default="{ row }">
                <div class="progress-cell">
                  <span>{{ row.high_risk_rate }}%</span>
                  <el-progress
                    :percentage="Math.min(Number(row.high_risk_rate) || 0, 100)"
                    :stroke-width="8"
                    :show-text="false"
                    color="#d97706"
                  />
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :xl="10">
        <el-card class="panel table-card" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">班级预警排行</div>
              <p>聚焦平均分更高、告警更密集的班级。</p>
            </div>
          </div>
          <div class="class-list">
            <div
              v-for="item in overview.class_risk_ranking || []"
              :key="item.class_name"
              class="class-card"
            >
              <div class="class-top">
                <strong>{{ item.class_name }}</strong>
                <span>{{ item.avg_score }}</span>
              </div>
              <div class="class-meta">
                学生 {{ item.student_count }} 人 · 评估 {{ item.assessment_count }} 条 · 高风险
                {{ item.high_risk_rate }}%
              </div>
              <el-progress
                :percentage="Math.min(Number(item.avg_score) || 0, 100)"
                :stroke-width="8"
                :show-text="false"
                color="#1d4ed8"
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="14">
        <el-card class="panel table-card" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">重点预警名单</div>
              <p>优先展示高风险或接近高风险阈值的最新样本。</p>
            </div>
          </div>
          <el-table :data="overview.recent_alerts || []" stripe>
            <el-table-column prop="username" label="用户" min-width="120" />
            <el-table-column prop="grade" label="年级" width="90" />
            <el-table-column prop="major" label="专业" min-width="150" />
            <el-table-column prop="top_dimension" label="主要风险维度" min-width="130" />
            <el-table-column prop="adjusted_score" label="修正分" width="90" />
            <el-table-column prop="created_at" label="最近评估" min-width="150" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :xl="10">
        <el-card class="panel model-card" shadow="never">
          <div class="card-title">系统升级亮点</div>
          <div class="model-grid">
            <div class="model-item">
              <strong>多分区驾驶舱</strong>
              <p>从风险分布、年级、专业、班级和告警名单多层联动展示群体状态。</p>
            </div>
            <div class="model-item">
              <strong>动态指标热区</strong>
              <p>指标均值和维度雷达同时输出，能快速识别当前最高风险区域。</p>
            </div>
            <div class="model-item">
              <strong>阶段趋势观察</strong>
              <p>按月度查看低、中、高风险波动，更适合展示阶段性变化。</p>
            </div>
            <div class="model-item">
              <strong>班级级别预警</strong>
              <p>支持把个体结果上卷到班级和专业，展示更强的管理视角。</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { getOverviewApi } from "../api/modules";

const overview = ref({
  total_users: 0,
  total_assessments: 0,
  average_adjusted_score: 0,
  alert_user_count: 0,
  recent_assessment_count: 0,
  risk_distribution: {},
  score_band_distribution: {},
  indicator_average: {},
  indicator_ranking: [],
  dimension_average: {},
  risk_by_grade: [],
  major_risk_stats: [],
  class_risk_ranking: [],
  user_role_distribution: {},
  trend_points: [],
  monthly_risk_trend: [],
  high_risk_users: [],
  recent_alerts: [],
  filter_options: {
    roles: [],
    grades: [],
    majors: [],
    classes: [],
    risk_levels: []
  }
});

const filters = reactive({
  grade: "",
  major: "",
  class_name: "",
  risk_level: ""
});

const riskPieRef = ref(null);
const monthlyTrendRef = ref(null);
const gradeRiskRef = ref(null);
const scoreBandRef = ref(null);
const indicatorRef = ref(null);
const dimensionRadarRef = ref(null);

const charts = {};

const filterOptions = computed(() => {
  const current = overview.value.filter_options || {
    grades: [],
    majors: [],
    classes: [],
    risk_levels: []
  };
  return {
    grades: current.grades || [],
    majors: current.majors || [],
    classes: filters.grade && filters.major ? (current.classes || []) : [],
    risk_levels:
      filters.grade && filters.major && filters.class_name ? (current.risk_levels || []) : []
  };
});

const highRiskRate = computed(() => {
  const total = overview.value.total_assessments || 0;
  if (!total) {
    return "0.0";
  }
  const highRisk = overview.value.risk_distribution?.["高风险"] || 0;
  return ((highRisk / total) * 100).toFixed(1);
});

const dominantDimension = computed(() => {
  const entries = Object.entries(overview.value.dimension_average || {});
  if (!entries.length) {
    return "暂无数据";
  }
  return entries.sort((a, b) => Number(b[1]) - Number(a[1]))[0][0];
});

const activeFilterText = computed(() => {
  const entries = Object.entries(filters).filter(([, value]) => value);
  if (!entries.length) {
    return "全量样本";
  }
  return entries.map(([key, value]) => `${key}:${value}`).join(" / ");
});

const summaryCards = computed(() => [
  {
    label: "覆盖用户",
    value: overview.value.total_users || 0,
    note: "满足当前筛选条件的学生范围"
  },
  {
    label: "评估记录",
    value: overview.value.total_assessments || 0,
    note: "用于模型分析的有效记录量"
  },
  {
    label: "平均修正分",
    value: overview.value.average_adjusted_score || 0,
    note: "当前结果集的整体风险强度"
  },
  {
    label: "高风险占比",
    value: `${highRiskRate.value}%`,
    note: "高风险结果占全部记录比例"
  },
  {
    label: "近 30 天评估",
    value: overview.value.recent_assessment_count || 0,
    note: "用于观察近期系统活跃情况"
  },
  {
    label: "主导风险维度",
    value: dominantDimension.value,
    note: activeFilterText.value,
    compact: true
  }
]);

const buildParams = () =>
  Object.fromEntries(Object.entries(filters).filter(([, value]) => value));

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
  await nextTick();

  const riskDistribution = overview.value.risk_distribution || {};
  const monthlyRiskTrend = overview.value.monthly_risk_trend || [];
  const gradeRisk = overview.value.risk_by_grade || [];
  const scoreBandDistribution = overview.value.score_band_distribution || {};
  const indicatorRanking = overview.value.indicator_ranking || [];
  const dimensionAverage = overview.value.dimension_average || {};

  initChart("riskPie", riskPieRef.value)?.setOption({
    color: ["#78c6a3", "#ffb703", "#d8572a"],
    tooltip: { trigger: "item" },
    series: [
      {
        type: "pie",
        radius: ["42%", "72%"],
        center: ["50%", "54%"],
        label: { formatter: "{b}\n{c}" },
        data: [
          { name: "低风险", value: riskDistribution["低风险"] || 0 },
          { name: "中风险", value: riskDistribution["中风险"] || 0 },
          { name: "高风险", value: riskDistribution["高风险"] || 0 }
        ]
      }
    ]
  });

  initChart("monthlyTrend", monthlyTrendRef.value)?.setOption({
    color: ["#7ccba2", "#f6c85f", "#d95f5f"],
    grid: { left: 48, right: 20, top: 24, bottom: 40 },
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    xAxis: {
      type: "category",
      data: monthlyRiskTrend.map((item) => item.month)
    },
    yAxis: {
      type: "value",
      minInterval: 1
    },
    series: [
      {
        name: "低风险",
        type: "bar",
        stack: "risk",
        data: monthlyRiskTrend.map((item) => item["低风险"])
      },
      {
        name: "中风险",
        type: "bar",
        stack: "risk",
        data: monthlyRiskTrend.map((item) => item["中风险"])
      },
      {
        name: "高风险",
        type: "bar",
        stack: "risk",
        data: monthlyRiskTrend.map((item) => item["高风险"])
      }
    ]
  });

  initChart("gradeRisk", gradeRiskRef.value)?.setOption({
    color: ["#7ccba2", "#f6c85f", "#d95f5f"],
    grid: { left: 56, right: 20, top: 24, bottom: 36 },
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    xAxis: { type: "value", minInterval: 1 },
    yAxis: {
      type: "category",
      data: gradeRisk.map((item) => item.grade)
    },
    series: [
      {
        name: "低风险",
        type: "bar",
        stack: "grade",
        data: gradeRisk.map((item) => item["低风险"])
      },
      {
        name: "中风险",
        type: "bar",
        stack: "grade",
        data: gradeRisk.map((item) => item["中风险"])
      },
      {
        name: "高风险",
        type: "bar",
        stack: "grade",
        data: gradeRisk.map((item) => item["高风险"])
      }
    ]
  });

  initChart("scoreBand", scoreBandRef.value)?.setOption({
    grid: { left: 40, right: 20, top: 24, bottom: 36 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: Object.keys(scoreBandDistribution)
    },
    yAxis: {
      type: "value",
      minInterval: 1
    },
    series: [
      {
        type: "bar",
        barWidth: 34,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#2563eb" },
            { offset: 1, color: "#7dd3fc" }
          ]),
          borderRadius: [10, 10, 0, 0]
        },
        data: Object.values(scoreBandDistribution)
      }
    ]
  });

  const indicatorRows = [...indicatorRanking].slice(0, 8).reverse();
  initChart("indicator", indicatorRef.value)?.setOption({
    grid: { left: 110, right: 24, top: 24, bottom: 30 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "value",
      max: 100
    },
    yAxis: {
      type: "category",
      data: indicatorRows.map((item) => item.name)
    },
    series: [
      {
        type: "bar",
        barWidth: 18,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: "#f59e0b" },
            { offset: 1, color: "#fcd34d" }
          ]),
          borderRadius: [0, 10, 10, 0]
        },
        data: indicatorRows.map((item) => item.average_score)
      }
    ]
  });

  initChart("dimensionRadar", dimensionRadarRef.value)?.setOption({
    color: ["#1d4ed8"],
    tooltip: { trigger: "item" },
    radar: {
      radius: "63%",
      indicator: Object.entries(dimensionAverage).map(([name]) => ({
        name,
        max: 100
      })),
      splitArea: {
        areaStyle: {
          color: ["rgba(255,255,255,0.75)", "rgba(236,244,255,0.95)"]
        }
      }
    },
    series: [
      {
        type: "radar",
        areaStyle: { color: "rgba(37, 99, 235, 0.2)" },
        lineStyle: { width: 2.5 },
        data: [
          {
            value: Object.values(dimensionAverage)
          }
        ]
      }
    ]
  });
};

const optionContains = (options, value) => !value || (options || []).includes(value);

const normalizeFilterSelections = (preferredField = "") => {
  const options = filterOptions.value;
  let changed = false;
  const fields = ["grade", "major", "class_name", "risk_level"];
  const orderedFields = preferredField
    ? fields.filter((field) => field !== preferredField).concat(preferredField)
    : fields;
  const optionMap = {
    grade: options.grades,
    major: options.majors,
    class_name: options.classes,
    risk_level: options.risk_levels
  };

  for (const field of orderedFields) {
    if (optionContains(optionMap[field], filters[field])) {
      continue;
    }

    if (field === preferredField && changed) {
      continue;
    }

    filters[field] = "";
    changed = true;
  }

  return changed;
};

const loadData = async (preferredField = "", normalizePass = 0) => {
  try {
    const res = await getOverviewApi(buildParams());
    overview.value = res.data || overview.value;
    if (normalizePass < 2 && normalizeFilterSelections(preferredField)) {
      await loadData(preferredField, normalizePass + 1);
      return;
    }
    await renderCharts();
  } catch (error) {
    ElMessage.error("获取看板数据失败，请先启动后端并导入样本数据");
  }
};

const handleFilterChange = async (field) => {
  await loadData(field);
};

const resetFilters = async () => {
  filters.grade = "";
  filters.major = "";
  filters.class_name = "";
  filters.risk_level = "";
  await loadData();
};

const handleResize = () => {
  Object.values(charts).forEach((chart) => chart?.resize());
};

onMounted(async () => {
  await loadData();
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
    radial-gradient(circle at top left, rgba(248, 196, 113, 0.22), transparent 32%),
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 26%),
    linear-gradient(135deg, #fffaf2 0%, #f4f8ff 55%, #edf3f8 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 30px 32px;
  margin-bottom: 18px;
  border-radius: 28px;
  color: #102542;
  background:
    linear-gradient(135deg, rgba(255, 246, 221, 0.96), rgba(231, 241, 255, 0.94)),
    #fff;
  box-shadow: 0 20px 50px rgba(17, 37, 66, 0.08);
}

.hero-copy {
  max-width: 860px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #d97706;
}

.hero h1 {
  margin: 0;
  font-size: 32px;
  line-height: 1.24;
}

.hero-text {
  margin: 14px 0 0;
  color: #5b6b7d;
  line-height: 1.78;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  gap: 12px;
}

.panel {
  margin-bottom: 16px;
  border: none;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 14px 36px rgba(20, 33, 61, 0.06);
}

.filter-panel :deep(.el-card__body),
.chart-card :deep(.el-card__body),
.table-card :deep(.el-card__body),
.stat-card :deep(.el-card__body),
.model-card :deep(.el-card__body) {
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.panel-header.compact {
  margin-bottom: 14px;
}

.panel-header h3,
.card-title {
  margin: 0;
  font-size: 18px;
  color: #102542;
  font-weight: 700;
}

.panel-header p {
  margin: 6px 0 0;
  color: #607080;
  line-height: 1.6;
}

.filter-actions {
  display: flex;
  gap: 10px;
}

.filter-tip {
  margin-top: 14px;
  color: #607080;
  font-size: 13px;
  line-height: 1.7;
}

.full-width {
  width: 100%;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  min-height: 154px;
}

.stat-label {
  color: #607080;
  font-size: 14px;
}

.stat-value {
  margin-top: 12px;
  font-size: 34px;
  font-weight: 700;
  color: #102542;
  line-height: 1.15;
}

.stat-value.compact {
  font-size: 20px;
  line-height: 1.5;
}

.stat-note {
  margin-top: 12px;
  color: #7a8793;
  font-size: 13px;
  line-height: 1.7;
}

.chart.medium {
  height: 320px;
}

.chart.tall {
  height: 380px;
}

.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.class-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.class-card {
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff8ef, #f3f8ff);
}

.class-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  color: #102542;
}

.class-meta {
  margin: 8px 0 12px;
  color: #607080;
  font-size: 13px;
  line-height: 1.7;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.model-item {
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff7ec, #f5f9ff);
}

.model-item strong {
  display: block;
  color: #102542;
}

.model-item p {
  margin: 8px 0 0;
  color: #607080;
  line-height: 1.72;
}

@media (max-width: 1500px) {
  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1200px) {
  .model-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page {
    padding: 16px;
  }

  .hero,
  .panel-header {
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .chart.medium,
  .chart.tall {
    height: 300px;
  }
}
</style>
