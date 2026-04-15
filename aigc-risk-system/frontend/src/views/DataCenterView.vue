<template>
  <div class="page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Data Center</p>
        <h1>数据库查询与样本数据中心</h1>
        <p class="hero-text">
          本页同时提供数据库查询、样本预览、导入监控和数据画像展示。现在支持按关键词、年级、专业、班级和风险等级查询学生数据，便于课程演示和项目汇报时快速检索。
        </p>
      </div>
      <div class="hero-actions">
        <el-button @click="$router.push('/dashboard')">返回看板</el-button>
        <el-button @click="$router.push('/assessment')">前往评估</el-button>
        <el-button @click="$router.push('/report')">报告中心</el-button>
        <el-button type="primary" :loading="importing" @click="importSample">
          重新导入样本数据
        </el-button>
      </div>
    </section>

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

    <el-card class="panel" shadow="never">
      <div class="panel-header">
        <div>
          <div class="card-title">数据库查询</div>
          <p>按学生画像和最新风险状态检索数据库记录，查询结果支持分页浏览。</p>
        </div>
        <div class="query-actions">
          <el-button @click="resetQuery">重置</el-button>
          <el-button type="primary" @click="loadUserQuery(true)">执行查询</el-button>
        </div>
      </div>

      <el-row :gutter="12">
        <el-col :xs="24" :sm="12" :md="8" :xl="6">
          <el-input
            v-model="queryFilters.keyword"
            clearable
            placeholder="按用户名、年级、专业或班级搜索"
            @keyup.enter="loadUserQuery(true)"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :xl="4">
          <el-select
            v-model="queryFilters.grade"
            clearable
            filterable
            class="full-width"
            placeholder="年级"
            @change="handleCascadeChange('grade')"
          >
            <el-option
              v-for="item in queryFilterOptions.grades"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :xl="5">
          <el-select
            v-model="queryFilters.major"
            clearable
            filterable
            class="full-width"
            placeholder="专业"
            @change="handleCascadeChange('major')"
          >
            <el-option
              v-for="item in queryFilterOptions.majors"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :xl="5">
          <el-select
            v-model="queryFilters.class_name"
            clearable
            filterable
            class="full-width"
            :disabled="!queryFilters.grade || !queryFilters.major"
            :placeholder="queryFilters.grade && queryFilters.major ? '班级' : '请先选择年级和专业'"
            @change="handleCascadeChange('class_name')"
          >
            <el-option
              v-for="item in queryFilterOptions.classes"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8" :xl="4">
          <el-select
            v-model="queryFilters.risk_level"
            clearable
            class="full-width"
            :disabled="!queryFilters.grade || !queryFilters.major || !queryFilters.class_name"
            :placeholder="queryFilters.grade && queryFilters.major && queryFilters.class_name ? '最新风险' : '请先选择班级'"
            @change="handleCascadeChange('risk_level')"
          >
            <el-option
              v-for="item in queryFilterOptions.risk_levels"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-col>
      </el-row>

      <div class="query-tip">
        班级会根据“年级 + 专业”组合联动筛选，只显示该年级该专业对应的班级。
      </div>

      <div class="query-summary">
        <span>命中 {{ queryResult.pagination.total }} 条用户记录</span>
        <span>已评估 {{ queryResult.summary.assessed_users || 0 }} 人</span>
        <span>高风险 {{ queryResult.summary.high_risk_count || 0 }} 人</span>
        <span>平均修正分 {{ queryResult.summary.average_adjusted_score || 0 }}</span>
      </div>
    </el-card>

    <el-card class="panel" shadow="never">
      <div class="panel-header compact">
        <div>
          <div class="card-title">查询结果</div>
          <p>展示数据库中的学生基本信息及最近一次评估情况。</p>
        </div>
      </div>

      <el-table
        :data="queryResult.items"
        stripe
        border
        max-height="540"
        highlight-current-row
        @row-click="loadPersonalByRow"
      >
        <el-table-column prop="username" label="用户名" min-width="130" />
        <el-table-column prop="grade" label="年级" width="90" />
        <el-table-column prop="major" label="专业" min-width="160" />
        <el-table-column prop="class_name" label="班级" min-width="160" />
        <el-table-column label="最新风险" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.latest_assessment" :type="riskTagType(row.latest_assessment.risk_level)">
              {{ row.latest_assessment.risk_level }}
            </el-tag>
            <span v-else>未评估</span>
          </template>
        </el-table-column>
        <el-table-column label="修正分" width="90">
          <template #default="{ row }">
            {{ row.latest_assessment?.adjusted_score ?? "--" }}
          </template>
        </el-table-column>
        <el-table-column label="最近评估时间" min-width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.latest_assessment?.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="个人画像" width="110" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="loadPersonalByRow(row)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="queryFilters.page"
          v-model:page-size="queryFilters.page_size"
          background
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 30, 50]"
          :total="queryResult.pagination.total"
          @current-change="loadUserQuery"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>

    <el-card class="panel" shadow="never">
      <div class="panel-header">
        <div>
          <div class="card-title">个人精准查询</div>
          <p>输入完整用户名，或点击上方查询结果中的任意一行，查看单个学生的风险画像、趋势和关键风险因子。</p>
        </div>
        <div class="query-actions">
          <el-button @click="resetPersonalQuery">清空</el-button>
          <el-button type="primary" :loading="personalLoading" @click="searchPersonalProfile">
            查询个人
          </el-button>
        </div>
      </div>

      <el-row :gutter="12">
        <el-col :xs="24" :lg="12">
          <el-input
            v-model.trim="personalQuery.username"
            clearable
            placeholder="请输入完整用户名，例如 student1"
            @keyup.enter="searchPersonalProfile"
          />
        </el-col>
        <el-col :xs="24" :lg="12">
          <div class="query-summary personal-summary-line">
            <span>支持完整用户名精确查询</span>
            <span>支持点击上方结果表直接加载</span>
            <span v-if="personalProfile?.user">当前对象 {{ personalProfile.user.username }}</span>
          </div>
        </el-col>
      </el-row>

      <template v-if="personalProfile">
        <div class="personal-profile-grid">
          <div class="personal-profile-item">
            <span>用户名</span>
            <strong>{{ personalProfile.user.username }}</strong>
          </div>
          <div class="personal-profile-item">
            <span>年级</span>
            <strong>{{ personalProfile.user.grade || "--" }}</strong>
          </div>
          <div class="personal-profile-item">
            <span>专业</span>
            <strong>{{ personalProfile.user.major || "--" }}</strong>
          </div>
          <div class="personal-profile-item">
            <span>班级</span>
            <strong>{{ personalProfile.user.class_name || "--" }}</strong>
          </div>
          <div class="personal-profile-item">
            <span>评估次数</span>
            <strong>{{ personalProfile.assessment_count || 0 }}</strong>
          </div>
          <div class="personal-profile-item">
            <span>最近风险</span>
            <strong>{{ personalProfile.latest_assessment?.risk_level || "未评估" }}</strong>
          </div>
        </div>

        <div class="query-summary personal-summary-line">
          <span>最近修正分 {{ personalProfile.latest_assessment?.adjusted_score ?? "--" }}</span>
          <span>最近评估 {{ formatDateTime(personalProfile.latest_assessment?.created_at) }}</span>
          <span v-if="personalProfile.latest_assessment?.assessment_id">
            最新评估 ID {{ personalProfile.latest_assessment.assessment_id }}
          </span>
        </div>

        <el-alert
          v-if="!personalProfile.latest_assessment"
          class="personal-empty-alert"
          title="该学生暂无评估记录，暂时无法生成个人风险可视化。"
          type="info"
          :closable="false"
        />

        <template v-else>
          <el-row :gutter="16">
            <el-col :xs="24" :xl="10">
              <el-card class="inner-card" shadow="never">
                <div class="card-title">个人风险隶属度</div>
                <div ref="personalMembershipRef" class="chart"></div>
              </el-card>
            </el-col>
            <el-col :xs="24" :xl="14">
              <el-card class="inner-card" shadow="never">
                <div class="card-title">个人风险趋势</div>
                <div ref="personalTrendRef" class="chart"></div>
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="16">
            <el-col :xs="24" :xl="10">
              <el-card class="inner-card" shadow="never">
                <div class="card-title">风险维度雷达</div>
                <div ref="personalRadarRef" class="chart"></div>
              </el-card>
            </el-col>
            <el-col :xs="24" :xl="14">
              <el-card class="inner-card" shadow="never">
                <div class="card-title">重点风险因子</div>
                <div ref="personalTopRiskRef" class="chart"></div>
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="16">
            <el-col :xs="24" :xl="12">
              <el-card class="inner-card" shadow="never">
                <div class="card-title">最近评估记录</div>
                <el-table :data="personalRecentHistory" stripe max-height="320">
                  <el-table-column prop="created_at" label="评估时间" min-width="150">
                    <template #default="{ row }">
                      {{ formatDateTime(row.created_at) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="risk_level" label="等级" width="90" />
                  <el-table-column prop="adjusted_score" label="修正分" width="90" />
                </el-table>
              </el-card>
            </el-col>
            <el-col :xs="24" :xl="12">
              <el-card class="inner-card" shadow="never">
                <div class="panel-header compact">
                  <div>
                    <div class="card-title">干预建议</div>
                    <p>基于最近一次评估结果输出的个体建议，便于答辩演示个人诊断闭环。</p>
                  </div>
                  <el-button
                    type="primary"
                    link
                    @click="$router.push({ path: '/report', query: { userId: personalProfile.user.id, assessmentId: personalProfile.latest_assessment.assessment_id } })"
                  >
                    查看完整报告
                  </el-button>
                </div>
                <div class="suggestion-list">
                  <div
                    v-for="(item, index) in personalReport?.suggestions || []"
                    :key="index"
                    class="suggestion-item"
                  >
                    {{ item }}
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </template>
      </template>

      <el-empty
        v-else
        description="输入完整用户名或点击上方查询结果表，查看单个学生的个人风险画像"
      />
    </el-card>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <el-card class="panel chart-card" shadow="never">
          <div class="card-title">样本年级分布</div>
          <div ref="gradeRef" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :xl="12">
        <el-card class="panel chart-card" shadow="never">
          <div class="card-title">样本专业分布</div>
          <div ref="majorRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="14">
        <el-card class="panel chart-card" shadow="never">
          <div class="card-title">指标均值概览</div>
          <div ref="indicatorRef" class="chart tall"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :xl="10">
        <el-card class="panel chart-card" shadow="never">
          <div class="card-title">库内风险分布</div>
          <div ref="riskRef" class="chart tall"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="14">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">样本字段结构</div>
              <p>区分样本身份字段与评估指标字段，方便展示数据结构和预处理逻辑。</p>
            </div>
            <el-button @click="loadPreview">刷新样本预览</el-button>
          </div>

          <div class="field-section">
            <div class="field-label">身份与样本字段</div>
            <div class="tag-grid">
              <span
                v-for="item in metaColumns"
                :key="item"
                class="tag tag-meta"
              >
                {{ item }}
              </span>
            </div>
          </div>

          <div class="field-section">
            <div class="field-label">评估指标字段</div>
            <div class="tag-grid">
              <span
                v-for="item in indicatorColumns"
                :key="item"
                class="tag tag-indicator"
              >
                {{ formatColumn(item) }}
              </span>
            </div>
          </div>

          <div class="field-section">
            <div class="field-label">样本文件路径</div>
            <div class="path-box">{{ preview.path || "暂无数据" }}</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="10">
        <el-card class="panel" shadow="never">
          <div class="card-title">导入与治理说明</div>
          <div class="govern-list">
            <div class="govern-card">
              <strong>样本优化</strong>
              <p>样本已扩展为多专业、多年级、多班级和多次评估记录，支持更真实的趋势分析和数据库查询。</p>
            </div>
            <div class="govern-card">
              <strong>查询能力</strong>
              <p>数据库查询现在支持关键词检索、风险筛选和分页浏览，避免用户多时无法快速定位目标记录。</p>
            </div>
            <div class="govern-card">
              <strong>最近导入结果</strong>
              <p v-if="lastImportResult">
                新增 {{ lastImportResult.imported_count }} 条评估记录，跳过 {{ lastImportResult.skipped_count }} 条重复数据，覆盖 {{ lastImportResult.covered_users }} 名学生。
              </p>
              <p v-else>当前展示的是数据库中已有数据，可随时重新导入并刷新查询结果。</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="panel" shadow="never">
      <div class="panel-header compact">
        <div>
          <div class="card-title">样本数据预览</div>
          <p>展示样本文件前 10 条记录，字段会根据当前指标体系自动展开。</p>
        </div>
      </div>

      <el-table :data="preview.rows || []" stripe border max-height="560">
        <el-table-column
          v-for="column in displayColumns"
          :key="column"
          :prop="column"
          :label="formatColumn(column)"
          min-width="120"
        />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  getAssessmentReportApi,
  getHistoryApi,
  getIndicatorsApi,
  getOverviewApi,
  getSamplePreviewApi,
  getTrendApi,
  getUserProfileApi,
  importSampleDataApi,
  queryUsersApi
} from "../api/modules";

const preview = ref({
  path: "",
  total_rows: 0,
  columns: [],
  rows: [],
  indicator_average: {},
  grade_distribution: {},
  major_distribution: {}
});

const liveOverview = ref({
  total_users: 0,
  total_assessments: 0,
  risk_distribution: {},
  filter_options: {
    grades: [],
    majors: [],
    classes: [],
    risk_levels: []
  }
});

const queryResult = ref({
  items: [],
  pagination: {
    page: 1,
    page_size: 10,
    total: 0,
    total_pages: 1
  },
  summary: {
    total_users: 0,
    assessed_users: 0,
    unassessed_users: 0,
    high_risk_count: 0,
    average_adjusted_score: 0,
    latest_assessment_at: null
  },
  filter_options: {
    grades: [],
    majors: [],
    classes: [],
    risk_levels: []
  }
});

const queryFilters = reactive({
  keyword: "",
  role: "student",
  grade: "",
  major: "",
  class_name: "",
  risk_level: "",
  page: 1,
  page_size: 10
});

const indicators = ref([]);
const importing = ref(false);
const lastImportResult = ref(null);
const personalLoading = ref(false);

const personalQuery = reactive({
  username: ""
});

const personalProfile = ref(null);
const personalHistory = ref([]);
const personalTrend = ref([]);
const personalReport = ref(null);

const gradeRef = ref(null);
const majorRef = ref(null);
const indicatorRef = ref(null);
const riskRef = ref(null);
const personalMembershipRef = ref(null);
const personalTrendRef = ref(null);
const personalRadarRef = ref(null);
const personalTopRiskRef = ref(null);
const charts = {};

const indicatorCodes = computed(() => indicators.value.map((item) => item.code));
const indicatorLabelMap = computed(() =>
  Object.fromEntries(indicators.value.map((item) => [item.code, item.name]))
);
const displayColumns = computed(() => preview.value.columns || []);
const metaColumns = computed(() =>
  (preview.value.columns || []).filter((column) => !indicatorCodes.value.includes(column))
);
const indicatorColumns = computed(() =>
  (preview.value.columns || []).filter((column) => indicatorCodes.value.includes(column))
);
const personalRecentHistory = computed(() =>
  [...(personalHistory.value || [])]
    .sort((left, right) => String(right.created_at).localeCompare(String(left.created_at)))
    .slice(0, 6)
);

const queryFilterOptions = computed(() => {
  const fallback = liveOverview.value.filter_options || {};
  const current = queryResult.value.filter_options || {};
  return {
    grades: current.grades || fallback.grades || [],
    majors: current.majors || fallback.majors || [],
    classes:
      queryFilters.grade && queryFilters.major
        ? (current.classes || fallback.classes || [])
        : [],
    risk_levels:
      queryFilters.grade && queryFilters.major && queryFilters.class_name
        ? (current.risk_levels || fallback.risk_levels || [])
        : []
  };
});

const summaryCards = computed(() => [
  {
    label: "样本记录",
    value: preview.value.total_rows || 0,
    note: "当前样本文件中的评估记录总数"
  },
  {
    label: "库内用户",
    value: liveOverview.value.total_users || 0,
    note: "数据库中已纳入分析的用户总量"
  },
  {
    label: "评估记录",
    value: liveOverview.value.total_assessments || 0,
    note: "数据库中已形成的评估结果数量"
  },
  {
    label: "查询命中",
    value: queryResult.value.pagination.total || 0,
    note: "当前筛选条件下命中的用户记录"
  },
  {
    label: "高风险人数",
    value: queryResult.value.summary.high_risk_count || 0,
    note: "基于最近一次评估结果统计"
  },
  {
    label: "平均修正分",
    value: queryResult.value.summary.average_adjusted_score || 0,
    note: queryResult.value.summary.latest_assessment_at
      ? `最近评估：${formatDateTime(queryResult.value.summary.latest_assessment_at)}`
      : "当前筛选结果暂无评估记录",
    compact: true
  }
]);

const formatColumn = (column) => indicatorLabelMap.value[column] || column;

const formatDateTime = (value) => {
  if (!value) {
    return "--";
  }
  return String(value).replace("T", " ").slice(0, 19);
};

const riskTagType = (riskLevel) => {
  if (riskLevel === "高风险") {
    return "danger";
  }
  if (riskLevel === "中风险") {
    return "warning";
  }
  return "success";
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
  await nextTick();

  const gradeDistribution = preview.value.grade_distribution || {};
  const majorDistribution = preview.value.major_distribution || {};
  const indicatorAverage = preview.value.indicator_average || {};
  const riskDistribution = liveOverview.value.risk_distribution || {};

  initChart("grade", gradeRef.value)?.setOption({
    grid: { left: 46, right: 20, top: 24, bottom: 36 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: Object.keys(gradeDistribution)
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
        data: Object.values(gradeDistribution)
      }
    ]
  });

  const majorRows = Object.entries(majorDistribution).slice(0, 8).reverse();
  initChart("major", majorRef.value)?.setOption({
    grid: { left: 130, right: 20, top: 24, bottom: 30 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "value",
      minInterval: 1
    },
    yAxis: {
      type: "category",
      data: majorRows.map(([name]) => name)
    },
    series: [
      {
        type: "bar",
        barWidth: 18,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: "#0f766e" },
            { offset: 1, color: "#5eead4" }
          ]),
          borderRadius: [0, 10, 10, 0]
        },
        data: majorRows.map(([, value]) => value)
      }
    ]
  });

  initChart("indicator", indicatorRef.value)?.setOption({
    grid: { left: 48, right: 20, top: 24, bottom: 80 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: Object.keys(indicatorAverage),
      axisLabel: { rotate: 24, interval: 0 }
    },
    yAxis: {
      type: "value",
      max: 100
    },
    series: [
      {
        type: "bar",
        barWidth: 22,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#f59e0b" },
            { offset: 1, color: "#fb7185" }
          ]),
          borderRadius: [8, 8, 0, 0]
        },
        data: Object.values(indicatorAverage)
      }
    ]
  });

  initChart("risk", riskRef.value)?.setOption({
    color: ["#78c6a3", "#ffb703", "#d8572a"],
    tooltip: { trigger: "item" },
    series: [
      {
        type: "pie",
        radius: ["44%", "74%"],
        center: ["50%", "52%"],
        label: { formatter: "{b}\n{c}" },
        data: [
          { name: "低风险", value: riskDistribution["低风险"] || 0 },
          { name: "中风险", value: riskDistribution["中风险"] || 0 },
          { name: "高风险", value: riskDistribution["高风险"] || 0 }
        ]
      }
    ]
  });
};

const renderPersonalCharts = async () => {
  if (!personalProfile.value?.latest_assessment || !personalReport.value) {
    return;
  }

  await nextTick();

  const memberships = personalReport.value.summary?.fuzzy_memberships || {};
  const dimensionBreakdown = personalReport.value.dimension_breakdown || [];
  const topRisks = personalReport.value.top_risks || [];

  initChart("personalMembership", personalMembershipRef.value)?.setOption({
    grid: { left: 46, right: 20, top: 24, bottom: 30 },
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
        barWidth: 30,
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

  initChart("personalTrend", personalTrendRef.value)?.setOption({
    grid: { left: 48, right: 20, top: 24, bottom: 44 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: personalTrend.value.map((item) => item.date),
      axisLabel: { rotate: 24 }
    },
    yAxis: {
      type: "value",
      max: 100
    },
    series: [
      {
        type: "line",
        smooth: true,
        symbolSize: 8,
        lineStyle: { width: 3, color: "#d97706" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(245, 158, 11, 0.34)" },
            { offset: 1, color: "rgba(245, 158, 11, 0.04)" }
          ])
        },
        data: personalTrend.value.map((item) => item.adjusted_score)
      }
    ]
  });

  initChart("personalRadar", personalRadarRef.value)?.setOption({
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

  initChart("personalTopRisk", personalTopRiskRef.value)?.setOption({
    grid: { left: 126, right: 20, top: 24, bottom: 30 },
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

const loadIndicators = async () => {
  try {
    const res = await getIndicatorsApi();
    indicators.value = res.data || [];
  } catch (error) {
    indicators.value = [];
  }
};

const loadPreview = async () => {
  try {
    const res = await getSamplePreviewApi({ limit: 10 });
    preview.value = res.data || preview.value;
    await renderCharts();
  } catch (error) {
    ElMessage.error("获取样本预览失败，请确认 sample_data 文件存在");
  }
};

const loadOverview = async () => {
  try {
    const res = await getOverviewApi();
    liveOverview.value = res.data || liveOverview.value;
    await renderCharts();
  } catch (error) {
    liveOverview.value = {
      total_users: 0,
      total_assessments: 0,
      risk_distribution: {},
      filter_options: {
        grades: [],
        majors: [],
        classes: [],
        risk_levels: []
      }
    };
  }
};

const clearPersonalProfile = () => {
  personalProfile.value = null;
  personalHistory.value = [];
  personalTrend.value = [];
  personalReport.value = null;
};

const loadPersonalProfile = async (params = {}) => {
  personalLoading.value = true;

  try {
    const profileRes = await getUserProfileApi(params);
    personalProfile.value = profileRes.data || null;
    personalQuery.username = personalProfile.value?.user?.username || personalQuery.username;

    if (!personalProfile.value?.user?.id) {
      clearPersonalProfile();
      return;
    }

    const userId = personalProfile.value.user.id;
    const latestAssessmentId = personalProfile.value.latest_assessment?.assessment_id;

    const [historyRes, trendRes, reportRes] = await Promise.all([
      getHistoryApi(userId),
      getTrendApi(userId),
      latestAssessmentId
        ? getAssessmentReportApi(latestAssessmentId)
        : Promise.resolve({ data: null })
    ]);

    personalHistory.value = historyRes.data || [];
    personalTrend.value = trendRes.data || [];
    personalReport.value = reportRes.data || null;
    await renderPersonalCharts();
  } catch (error) {
    clearPersonalProfile();
    ElMessage.error(error?.response?.data?.message || "未找到对应学生，请输入完整用户名");
  } finally {
    personalLoading.value = false;
  }
};

const buildQueryParams = () => {
  const params = {
    role: queryFilters.role,
    page: queryFilters.page,
    page_size: queryFilters.page_size
  };

  for (const key of ["keyword", "grade", "major", "class_name", "risk_level"]) {
    if (queryFilters[key]) {
      params[key] = queryFilters[key];
    }
  }

  return params;
};

const optionContains = (options, value) => !value || (options || []).includes(value);

const normalizeCascadeSelections = (preferredField = "") => {
  const options = queryFilterOptions.value;
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
    if (optionContains(optionMap[field], queryFilters[field])) {
      continue;
    }

    if (field === preferredField && changed) {
      continue;
    }

    queryFilters[field] = "";
    changed = true;
  }

  return changed;
};

const loadUserQuery = async (resetPage = false, preferredField = "", normalizePass = 0) => {
  if (resetPage === true) {
    queryFilters.page = 1;
  }

  try {
    const res = await queryUsersApi(buildQueryParams());
    queryResult.value = res.data || queryResult.value;
    if (normalizePass < 2 && normalizeCascadeSelections(preferredField)) {
      await loadUserQuery(true, preferredField, normalizePass + 1);
    }
  } catch (error) {
    ElMessage.error("数据库查询失败，请检查后端服务");
  }
};

const handleCascadeChange = async (field) => {
  await loadUserQuery(true, field);
};

const searchPersonalProfile = async () => {
  const username = personalQuery.username.trim();
  if (!username) {
    ElMessage.warning("请输入完整用户名后再查询");
    return;
  }

  await loadPersonalProfile({ username });
};

const loadPersonalByRow = async (row) => {
  if (!row?.id) {
    return;
  }

  personalQuery.username = row.username || "";
  await loadPersonalProfile({ user_id: row.id });
};

const resetPersonalQuery = () => {
  personalQuery.username = "";
  clearPersonalProfile();
};

const resetQuery = async () => {
  queryFilters.keyword = "";
  queryFilters.grade = "";
  queryFilters.major = "";
  queryFilters.class_name = "";
  queryFilters.risk_level = "";
  queryFilters.page = 1;
  queryFilters.page_size = 10;
  await loadUserQuery();
};

const handlePageSizeChange = async (pageSize) => {
  queryFilters.page_size = pageSize;
  queryFilters.page = 1;
  await loadUserQuery();
};

const importSample = async () => {
  importing.value = true;
  try {
    const res = await importSampleDataApi();
    lastImportResult.value = res.data || null;
    ElMessage.success(
      `导入完成：新增 ${res.data.imported_count} 条评估记录，跳过重复 ${res.data.skipped_count} 条`
    );
    await loadPreview();
    await loadOverview();
    await loadUserQuery(true);
    if (personalProfile.value?.user?.id) {
      await loadPersonalProfile({ user_id: personalProfile.value.user.id });
    }
  } catch (error) {
    ElMessage.error("导入失败，请检查后端服务与样本文件");
  } finally {
    importing.value = false;
  }
};

const handleResize = () => {
  Object.values(charts).forEach((chart) => chart?.resize());
};

onMounted(async () => {
  await loadIndicators();
  await loadPreview();
  await loadOverview();
  await loadUserQuery();
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
    radial-gradient(circle at top right, rgba(249, 168, 37, 0.18), transparent 32%),
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.1), transparent 25%),
    linear-gradient(135deg, #fffdf8 0%, #f0f7ff 55%, #edf3f8 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 30px 32px;
  margin-bottom: 18px;
  border-radius: 28px;
  color: #102542;
  background: linear-gradient(135deg, rgba(255, 246, 221, 0.95), rgba(230, 247, 255, 0.94));
  box-shadow: 0 18px 48px rgba(16, 37, 66, 0.08);
}

.hero-copy {
  max-width: 860px;
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
  margin-top: 14px;
  color: #607080;
  line-height: 1.78;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-content: flex-start;
}

.panel {
  margin-bottom: 16px;
  border: none;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 14px 36px rgba(16, 37, 66, 0.06);
}

.panel :deep(.el-card__body) {
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  min-height: 150px;
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
}

.stat-value.compact {
  font-size: 18px;
  line-height: 1.5;
}

.stat-note {
  margin-top: 12px;
  color: #7a8793;
  font-size: 13px;
  line-height: 1.7;
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

.panel-header p {
  margin: 6px 0 0;
  color: #607080;
  line-height: 1.6;
}

.card-title {
  margin: 0;
  font-size: 18px;
  color: #102542;
  font-weight: 700;
}

.query-actions {
  display: flex;
  gap: 10px;
}

.full-width {
  width: 100%;
}

.query-tip {
  margin-top: 14px;
  color: #607080;
  font-size: 13px;
  line-height: 1.7;
}

.query-summary {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.query-summary span {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(16, 37, 66, 0.06);
  color: #415468;
  font-size: 13px;
}

.personal-summary-line {
  margin-top: 0;
  min-height: 40px;
  align-items: center;
}

.personal-profile-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.personal-profile-item {
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff8ee, #eef6ff);
}

.personal-profile-item span {
  display: block;
  color: #607080;
  font-size: 13px;
}

.personal-profile-item strong {
  display: block;
  margin-top: 8px;
  color: #102542;
  font-size: 18px;
}

.personal-empty-alert {
  margin-top: 18px;
}

.inner-card {
  margin-top: 16px;
  border: 1px solid rgba(16, 37, 66, 0.06);
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(244, 249, 255, 0.96));
}

.inner-card :deep(.el-card__body) {
  padding: 18px;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.chart {
  height: 320px;
}

.chart.tall {
  height: 380px;
}

.field-section + .field-section {
  margin-top: 18px;
}

.field-label {
  margin-bottom: 10px;
  color: #415468;
  font-size: 14px;
  font-weight: 700;
}

.tag-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag {
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 13px;
}

.tag-meta {
  background: rgba(37, 99, 235, 0.1);
  color: #1d4ed8;
}

.tag-indicator {
  background: rgba(217, 119, 6, 0.1);
  color: #b45309;
}

.path-box {
  padding: 14px;
  border-radius: 16px;
  background: #f7fafe;
  color: #415468;
  line-height: 1.7;
  word-break: break-all;
}

.govern-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.govern-card {
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff8ee, #f5f9ff);
}

.govern-card strong {
  display: block;
  color: #102542;
}

.govern-card p {
  margin: 8px 0 0;
  color: #607080;
  line-height: 1.72;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggestion-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: #eef6ff;
  color: #24415d;
  line-height: 1.75;
}

@media (max-width: 1500px) {
  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .personal-profile-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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

  .personal-profile-grid {
    grid-template-columns: 1fr;
  }

  .pagination-bar {
    justify-content: flex-start;
    overflow-x: auto;
  }

  .chart,
  .chart.tall {
    height: 300px;
  }
}
</style>
