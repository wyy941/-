<template>
  <div class="page">
    <section class="hero">
      <div>
        <p class="eyebrow">{{ isStudent ? "Self Assessment" : "Advanced Assessment" }}</p>
        <h1>{{ pageTitle }}</h1>
        <p class="hero-text">{{ pageDescription }}</p>
      </div>
      <div v-if="isTeacherSide" class="hero-actions">
        <el-button @click="$router.push('/dashboard')">返回看板</el-button>
        <el-button @click="$router.push('/data-center')">数据中心</el-button>
        <el-button @click="$router.push('/report')">报告中心</el-button>
      </div>
      <div v-else class="hero-actions">
        <el-button type="primary" @click="$router.push('/student-center')">返回学生首页</el-button>
      </div>
    </section>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="11">
        <el-card class="panel" shadow="never">
          <template #header>
            <div class="card-header">
              <div>
                <div class="card-title">{{ isStudent ? "自我评价表单" : "评估表单" }}</div>
                <div class="card-subtitle">
                  {{ isStudent ? "按维度完成自我评价，系统会自动生成风险分析结果" : "动态指标配置，自动跟随后端指标体系" }}
                </div>
              </div>
              <el-tag type="warning">{{ indicators.length }} 项指标</el-tag>
            </div>
          </template>

          <el-form :model="form" label-width="110px">
            <el-form-item :label="isStudent ? '评价对象' : '评估对象'">
              <el-input
                v-if="isStudent"
                :model-value="currentUserLabel"
                class="full-width"
                disabled
              />
              <el-select
                v-else
                v-model="form.user_id"
                class="full-width"
                placeholder="请选择用户"
              >
                <el-option
                  v-for="item in users"
                  :key="item.id"
                  :label="`${item.username} / ${item.major || '未设置专业'} / ${item.class_name || '未设置班级'}`"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-form>

          <div
            v-for="group in groupedIndicators"
            :key="group.dimension"
            class="dimension-section"
          >
            <div class="dimension-header">
              <div>
                <h3>{{ group.dimension_name }}</h3>
                <p>{{ group.summary }}</p>
              </div>
              <el-tag>{{ group.items.length }} 项</el-tag>
            </div>

            <div
              v-for="item in group.items"
              :key="item.code"
              class="indicator-card"
            >
              <div class="indicator-head">
                <div>
                  <div class="indicator-name">{{ item.name }}</div>
                  <div class="indicator-desc">{{ item.description }}</div>
                </div>
                <div class="indicator-side">
                  <span class="indicator-weight">{{ formatWeight(item.weight) }}</span>
                  <span class="indicator-standard">{{ item.score_standard }}</span>
                </div>
              </div>
              <el-slider
                v-model="form.payload[item.code]"
                :min="0"
                :max="100"
                show-input
              />
            </div>
          </div>

          <el-button type="primary" class="full-width submit-btn" @click="submitAssessment">
            {{ isStudent ? "提交自我评价" : "执行高级评估" }}
          </el-button>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="13">
        <el-row :gutter="16">
          <el-col :xs="24">
            <el-card class="panel" shadow="never">
              <div class="result-header">
                <div>
                  <div class="card-title">{{ isStudent ? "自我评价结果" : "评估结果总览" }}</div>
                  <div class="card-subtitle">{{ currentUserLabel }}</div>
                </div>
                <div class="result-actions">
                  <el-button
                    v-if="isTeacherSide && result?.assessment_id"
                    @click="openReport(result.assessment_id)"
                  >
                    查看报告
                  </el-button>
                </div>
              </div>

              <el-empty
                v-if="!result"
                :description="isStudent ? '提交自我评价后显示综合分析结果' : '提交评估后显示综合分析结果'"
              />

              <template v-else>
                <div class="summary-grid">
                  <div class="metric-card">
                    <span>原始得分</span>
                    <strong>{{ result.total_score }}</strong>
                  </div>
                  <div class="metric-card">
                    <span>修正得分</span>
                    <strong>{{ result.adjusted_score }}</strong>
                  </div>
                  <div class="metric-card">
                    <span>风险等级</span>
                    <strong>{{ result.risk_level }}</strong>
                  </div>
                  <div class="metric-card">
                    <span>评估置信度</span>
                    <strong>{{ formatConfidence(result.confidence) }}</strong>
                  </div>
                </div>

                <div class="membership-box">
                  <div class="section-title">模糊隶属度</div>
                  <div class="membership-list">
                    <div
                      v-for="(value, key) in result.memberships || {}"
                      :key="key"
                      class="membership-item"
                    >
                      <span>{{ key }}</span>
                      <strong>{{ formatConfidence(value) }}</strong>
                    </div>
                  </div>
                </div>

                <div class="section-title">重点风险因子</div>
                <div class="risk-list">
                  <div
                    v-for="item in result.top_risks || []"
                    :key="item.code"
                    class="risk-item"
                  >
                    <div>
                      <div class="risk-name">{{ item.name }}</div>
                      <div class="risk-desc">
                        {{ item.dimension_name }} · 权重贡献 {{ item.weighted_contribution }}
                      </div>
                    </div>
                    <div class="risk-score">{{ item.score }}</div>
                  </div>
                </div>

                <div class="section-title">{{ isStudent ? "改进建议" : "干预建议" }}</div>
                <div class="suggestion-list">
                  <span
                    v-for="(item, index) in result.suggestions || []"
                    :key="index"
                    class="suggestion-item"
                  >
                    {{ item }}
                  </span>
                </div>
              </template>
            </el-card>
          </el-col>

          <el-col :xs="24" :lg="12">
            <el-card class="panel" shadow="never">
              <div class="card-title">指标雷达图</div>
              <div ref="radarRef" class="chart"></div>
            </el-card>
          </el-col>

          <el-col :xs="24" :lg="12">
            <el-card class="panel" shadow="never">
              <div class="card-title">历史趋势</div>
              <div ref="trendRef" class="chart"></div>
            </el-card>
          </el-col>

          <el-col :xs="24">
            <el-card class="panel" shadow="never">
              <div class="card-title">维度分析</div>
              <el-table :data="result?.dimension_breakdown || []" stripe>
                <el-table-column prop="dimension_name" label="维度" min-width="140" />
                <el-table-column prop="average_score" label="平均分" width="90" />
                <el-table-column prop="weighted_score" label="加权分" width="90" />
                <el-table-column prop="risk_level" label="等级" width="90" />
                <el-table-column label="涉及指标" min-width="280">
                  <template #default="{ row }">
                    <div class="dimension-tags">
                      <span
                        v-for="item in row.items"
                        :key="item.code"
                        class="dimension-tag"
                      >
                        {{ item.name }} {{ item.score }}
                      </span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch
} from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import {
  evaluateApi,
  getIndicatorsApi,
  getTrendApi,
  getUsersApi
} from "../api/modules";
import { getStoredUser } from "../utils/auth";

const router = useRouter();
const authUser = ref(getStoredUser());

const users = ref([]);
const indicators = ref([]);
const result = ref(null);
const trendData = ref([]);
const radarRef = ref(null);
const trendRef = ref(null);

const form = reactive({
  user_id: null,
  payload: {}
});

let radarChart;
let trendChart;

const isStudent = computed(() => authUser.value?.role === "student");
const isTeacherSide = computed(() => ["teacher", "admin"].includes(authUser.value?.role || ""));

const pageTitle = computed(() =>
  isStudent.value ? "大学生 AIGC 技术依赖自我评价" : "大学生 AIGC 技术依赖高级评估"
);

const pageDescription = computed(() =>
  isStudent.value
    ? "本页面向学生本人开展自我评价，系统会基于当前指标体系自动生成风险等级、关键风险因子与改进建议。"
    : "本页采用“组合权重 + 模糊综合评价 + 相似群体修正”的模型，对行为依赖、认知弱化、伦理安全、社交协作、学习投入和自我调节六个维度进行综合判断。"
);

const dimensionSummaryMap = {
  behavior: "关注 AIGC 是否从辅助工具滑向常态替代。",
  cognition: "关注学生是否把理解、判断和核验过程交给模型。",
  ethics: "关注学术规范、隐私安全与风险边界意识。",
  social: "关注技术使用是否挤压真实协作、沟通与情绪支持渠道。",
  learning: "关注知识内化、任务规划和自主学习闭环是否被模型替代。",
  self_management: "关注时间管理、注意力控制和脱离技术后的自我调节能力。",
  custom: "自定义指标由后台配置动态扩展。"
};
const dimensionOrder = {
  behavior: 1,
  cognition: 2,
  ethics: 3,
  social: 4,
  learning: 5,
  self_management: 6,
  custom: 9
};

const groupedIndicators = computed(() => {
  const groups = new Map();
  for (const item of indicators.value) {
    if (!groups.has(item.dimension)) {
      groups.set(item.dimension, {
        dimension: item.dimension,
        dimension_name: item.dimension_name || "自定义指标",
        summary: dimensionSummaryMap[item.dimension] || dimensionSummaryMap.custom,
        items: []
      });
    }
    groups.get(item.dimension).items.push(item);
  }
  return Array.from(groups.values());
});

const currentUser = computed(
  () =>
    users.value.find((item) => item.id === form.user_id) ||
    (isStudent.value && authUser.value?.id === form.user_id ? authUser.value : null)
);

const currentUserLabel = computed(() => {
  if (!currentUser.value) {
    return isStudent.value ? "当前登录学生" : "请选择用户";
  }
  return `${currentUser.value.username} / ${currentUser.value.major || "未设置专业"} / ${
    currentUser.value.class_name || "未设置班级"
  }`;
});

const formatWeight = (value) => `${Math.round((Number(value) || 0) * 100)}%`;
const formatConfidence = (value) => (Number(value || 0) * 100).toFixed(1) + "%";

const ensurePayloadDefaults = () => {
  for (const item of indicators.value) {
    if (form.payload[item.code] === undefined) {
      form.payload[item.code] = 50;
    }
  }
};

const renderRadar = async () => {
  await nextTick();
  radarChart = radarChart || echarts.init(radarRef.value);

  const detailMap = result.value?.details || form.payload;
  radarChart.setOption({
    radar: {
      radius: "68%",
      splitNumber: 5,
      axisName: { color: "#334e68", fontSize: 12 },
      indicator: indicators.value.map((item) => ({
        name: item.name,
        max: 100
      }))
    },
    series: [
      {
        type: "radar",
        areaStyle: {
          color: "rgba(205, 119, 43, 0.24)"
        },
        lineStyle: {
          width: 3,
          color: "#c96c28"
        },
        itemStyle: {
          color: "#8d5524"
        },
        data: [
          {
            value: indicators.value.map((item) => detailMap[item.code] || 0)
          }
        ]
      }
    ]
  });
};

const renderTrend = async () => {
  await nextTick();
  trendChart = trendChart || echarts.init(trendRef.value);

  trendChart.setOption({
    grid: { left: 48, right: 18, top: 26, bottom: 36 },
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    xAxis: {
      type: "category",
      data: trendData.value.map((item) => item.date),
      axisLabel: { rotate: 20 }
    },
    yAxis: { type: "value", max: 100 },
    series: [
      {
        name: "原始得分",
        type: "line",
        smooth: true,
        data: trendData.value.map((item) => item.total_score),
        lineStyle: { width: 2, color: "#457b9d" }
      },
      {
        name: "修正得分",
        type: "line",
        smooth: true,
        data: trendData.value.map((item) => item.adjusted_score),
        lineStyle: { width: 3, color: "#d62828" }
      }
    ]
  });
};

const loadUsers = async () => {
  if (isStudent.value && authUser.value?.id) {
    users.value = [authUser.value];
    form.user_id = authUser.value.id;
    return;
  }

  try {
    const res = await getUsersApi({ role: "student" });
    users.value = res.data || [];
    if (!form.user_id && users.value.length) {
      const savedUser = JSON.parse(localStorage.getItem("user") || "null");
      form.user_id =
        users.value.find((item) => item.id === savedUser?.id)?.id || users.value[0].id;
    }
  } catch (error) {
    ElMessage.error("获取用户列表失败");
  }
};

const loadIndicators = async () => {
  try {
    const res = await getIndicatorsApi();
    indicators.value = (res.data || [])
      .filter((item) => item.enabled)
      .sort((a, b) => {
        if ((a.dimension || "") === (b.dimension || "")) {
          return (a.id || 0) - (b.id || 0);
        }
        return (dimensionOrder[a.dimension] || 99) - (dimensionOrder[b.dimension] || 99);
      });
    ensurePayloadDefaults();
    renderRadar();
  } catch (error) {
    ElMessage.error("获取指标配置失败");
  }
};

const loadTrend = async () => {
  if (!form.user_id) {
    trendData.value = [];
    renderTrend();
    return;
  }

  try {
    const res = await getTrendApi(form.user_id);
    trendData.value = res.data || [];
    renderTrend();
  } catch (error) {
    ElMessage.error("获取趋势数据失败");
  }
};

const submitAssessment = async () => {
  if (!form.user_id) {
    ElMessage.warning(isStudent.value ? "当前学生信息未加载完成" : "请先选择评估对象");
    return;
  }

  try {
    const res = await evaluateApi(form);
    if (res.code === 201) {
      result.value = res.data;
      ElMessage.success(isStudent.value ? "自我评价已完成" : "高级评估完成");
      await loadTrend();
      renderRadar();
    } else {
      ElMessage.error(res.message || "评估失败");
    }
  } catch (error) {
    ElMessage.error("评估接口调用失败，请检查后端服务");
  }
};

const openReport = (assessmentId) => {
  if (!isTeacherSide.value) {
    return;
  }
  router.push({
    path: "/report",
    query: {
      userId: form.user_id,
      assessmentId
    }
  });
};

const handleResize = () => {
  radarChart?.resize();
  trendChart?.resize();
};

watch(
  () => form.user_id,
  async () => {
    result.value = null;
    await loadTrend();
    renderRadar();
  }
);

watch(
  indicators,
  () => {
    ensurePayloadDefaults();
    renderRadar();
  },
  { deep: true }
);

onMounted(async () => {
  await loadUsers();
  await loadIndicators();
  await loadTrend();
  renderRadar();
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
  radarChart?.dispose();
  trendChart?.dispose();
});
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24px;
  background:
    radial-gradient(circle at right top, rgba(240, 196, 25, 0.2), transparent 30%),
    linear-gradient(135deg, #fffdf8 0%, #eff6ff 55%, #eef2f7 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 30px;
  margin-bottom: 18px;
  border-radius: 24px;
  color: #102542;
  background: linear-gradient(135deg, rgba(255, 242, 214, 0.94), rgba(239, 246, 255, 0.92));
  box-shadow: 0 18px 48px rgba(16, 37, 66, 0.08);
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #c96c28;
}

.hero h1 {
  margin: 0;
  font-size: 30px;
}

.hero-text {
  max-width: 780px;
  margin-top: 12px;
  color: #5c6b7a;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
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

.full-width {
  width: 100%;
}

.card-header,
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.card-title {
  font-size: 18px;
  color: #102542;
  font-weight: 700;
}

.card-subtitle {
  margin-top: 6px;
  color: #607080;
}

.dimension-section + .dimension-section {
  margin-top: 20px;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 12px;
}

.dimension-header h3 {
  margin: 0;
  color: #102542;
}

.dimension-header p {
  margin: 6px 0 0;
  color: #607080;
  line-height: 1.6;
}

.indicator-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff7ec, #f5f9ff);
}

.indicator-card + .indicator-card {
  margin-top: 12px;
}

.indicator-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 10px;
}

.indicator-name {
  font-weight: 700;
  color: #102542;
}

.indicator-desc {
  margin-top: 6px;
  color: #607080;
  line-height: 1.6;
  font-size: 13px;
}

.indicator-side {
  min-width: 170px;
  text-align: right;
}

.indicator-weight {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(201, 108, 40, 0.12);
  color: #8d5524;
  font-weight: 700;
}

.indicator-standard {
  display: block;
  margin-top: 8px;
  color: #7a8793;
  font-size: 12px;
  line-height: 1.5;
}

.submit-btn {
  margin-top: 20px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, #fff4dc, #f4f8ff);
}

.metric-card span {
  display: block;
  color: #607080;
  font-size: 13px;
}

.metric-card strong {
  display: block;
  margin-top: 10px;
  font-size: 28px;
  color: #102542;
}

.section-title {
  margin: 20px 0 12px;
  font-size: 16px;
  font-weight: 700;
  color: #102542;
}

.membership-box {
  margin-top: 18px;
}

.membership-list,
.suggestion-list,
.dimension-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.membership-item,
.suggestion-item,
.dimension-tag {
  padding: 9px 12px;
  border-radius: 999px;
  background: rgba(16, 37, 66, 0.06);
  color: #24415d;
}

.membership-item strong {
  margin-left: 8px;
}

.risk-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.risk-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  background: #fff9ef;
}

.risk-name {
  font-weight: 700;
  color: #102542;
}

.risk-desc {
  margin-top: 6px;
  color: #607080;
  font-size: 13px;
}

.risk-score {
  min-width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #8d5524;
  background: rgba(217, 119, 6, 0.12);
}

.chart {
  height: 340px;
}

@media (max-width: 1200px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .page {
    padding: 16px;
  }

  .hero,
  .card-header,
  .result-header,
  .dimension-header,
  .indicator-head {
    flex-direction: column;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .indicator-side {
    min-width: 0;
    text-align: left;
  }
}
</style>
