<template>
  <div class="page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Student Center</p>
        <h1>{{ PROJECT_NAME }}</h1>
        <p class="hero-text">
          学生端用于完成自我评价，并查看系统基于问卷与权值模型计算出的最终总分变化。
          学生端不展示单项权重和模型细节，只保留总分结果与历史记录。
        </p>
      </div>
      <div class="hero-actions">
        <el-button type="primary" @click="router.push('/self-assessment')">开始自我评价</el-button>
        <el-button @click="logout">退出登录</el-button>
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
        <div class="stat-value">{{ item.value }}</div>
        <div class="stat-note">{{ item.note }}</div>
      </el-card>
    </section>

    <el-row :gutter="18">
      <el-col :xs="24" :xl="8">
        <el-card class="panel" shadow="never">
          <div class="panel-header">
            <div>
              <div class="panel-title">学生信息</div>
              <p>当前登录学生的基础身份信息与班级归属。</p>
            </div>
          </div>

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

          <div class="helper-card">
            自我评价采用 60 道题问卷作答，系统会将问卷结果映射到既有维度与指标后，
            通过权值模型和风险算法计算本次最终总分。
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="16">
        <el-card class="panel" shadow="never">
          <div class="panel-header">
            <div>
              <div class="panel-title">最近一次结果</div>
              <p>
                {{
                  latestAssessment
                    ? `最近一次自我评价时间：${formatDateTime(latestAssessment.created_at)}`
                    : "当前还没有自我评价记录，请先完成一次自我评价。"
                }}
              </p>
            </div>
            <el-button type="primary" @click="router.push('/self-assessment')">
              再次自我评价
            </el-button>
          </div>

          <el-empty
            v-if="!latestAssessment"
            description="提交完成后，这里会显示系统计算出的最新总分。"
          />
          <div v-else class="latest-score-card">
            <span>最终总分</span>
            <strong>{{ latestAssessment.final_score }}</strong>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="18">
      <el-col :xs="24" :xl="14">
        <el-card class="panel" shadow="never">
          <div class="panel-title">总分趋势</div>
          <div ref="trendRef" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :xl="10">
        <el-card class="panel" shadow="never">
          <div class="panel-title">记录摘要</div>
          <div class="score-block">
            <span>当前最终总分</span>
            <strong>{{ latestAssessment?.final_score ?? "--" }}</strong>
          </div>
          <div class="score-block">
            <span>累计评估次数</span>
            <strong>{{ overview.assessment_count || 0 }}</strong>
          </div>
          <div class="score-block">
            <span>最近提交时间</span>
            <strong>{{ formatDateTime(latestAssessment?.created_at) }}</strong>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="18">
      <el-col :xs="24">
        <el-card class="panel" shadow="never">
          <div class="panel-header">
            <div>
              <div class="panel-title">最近评估记录</div>
              <p>学生端仅展示最终总分与提交时间。</p>
            </div>
          </div>

          <el-table :data="overview.recent_records || []" stripe max-height="360">
            <el-table-column prop="created_at" label="提交时间" min-width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="final_score" label="最终总分" width="120" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { getStudentSelfAssessmentOverviewApi } from "../api/modules";
import { PROJECT_NAME } from "../constants/branding";
import { clearAuth, getStoredUser } from "../utils/auth";

const router = useRouter();
const currentUser = ref(getStoredUser());
const overview = ref({
  latest_assessment: null,
  assessment_count: 0,
  recent_records: [],
  trend: []
});
const trendRef = ref(null);
let trendChart;

const latestAssessment = computed(() => overview.value.latest_assessment || null);

const summaryCards = computed(() => [
  {
    label: "当前最终总分",
    value: latestAssessment.value?.final_score ?? "--",
    note: "显示系统基于最近一次自我评价计算出的最终总分。"
  },
  {
    label: "累计评估次数",
    value: overview.value.assessment_count || 0,
    note: "系统已保存的自我评价记录次数。"
  },
  {
    label: "最近提交时间",
    value: formatDateTime(latestAssessment.value?.created_at),
    note: "最近一次总分写入系统的时间。"
  },
  {
    label: "问卷规模",
    value: "60 题",
    note: "学生端以 6 个维度、60 道题的方式完成自我评价。"
  }
]);

const formatDateTime = (value) => {
  if (!value) {
    return "--";
  }
  return String(value).replace("T", " ").slice(0, 16);
};

const renderTrend = async () => {
  await nextTick();
  if (!trendRef.value) {
    return;
  }

  trendChart = trendChart || echarts.init(trendRef.value);
  const trendRows = overview.value.trend || [];

  trendChart.setOption({
    grid: { left: 46, right: 18, top: 26, bottom: 40 },
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
        lineStyle: { width: 3, color: "#1d4ed8" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(29, 78, 216, 0.22)" },
            { offset: 1, color: "rgba(29, 78, 216, 0.04)" }
          ])
        }
      }
    ]
  });
};

const loadStudentData = async () => {
  try {
    const res = await getStudentSelfAssessmentOverviewApi();
    overview.value = res.data || overview.value;
    await renderTrend();
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || "学生端数据加载失败");
  }
};

const handleResize = () => {
  trendChart?.resize();
};

const logout = () => {
  clearAuth();
  router.replace("/login");
};

watch(
  () => overview.value.trend,
  () => {
    renderTrend();
  },
  { deep: true }
);

onMounted(() => {
  loadStudentData();
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
    radial-gradient(circle at top left, rgba(29, 78, 216, 0.08), transparent 24%),
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
  max-width: 840px;
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
  font-size: 38px;
  line-height: 1.28;
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

.stats-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
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

.stat-card {
  margin-top: 0;
}

.stat-label {
  color: #6b7b8e;
  font-size: 13px;
}

.stat-value {
  margin-top: 12px;
  font-size: 34px;
  font-weight: 700;
  color: #102542;
}

.stat-note {
  margin-top: 10px;
  color: #728395;
  line-height: 1.7;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 18px;
  color: #102542;
  font-weight: 700;
}

.panel-header p {
  margin: 8px 0 0;
  color: #6b7b8e;
  line-height: 1.7;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-item {
  padding: 16px;
  border-radius: 18px;
  background: #f6f9fc;
}

.profile-item span,
.score-block span,
.latest-score-card span {
  display: block;
  color: #6e8094;
  font-size: 13px;
}

.profile-item strong {
  display: block;
  margin-top: 10px;
  color: #102542;
  font-size: 20px;
}

.helper-card {
  margin-top: 16px;
  padding: 16px;
  border-radius: 18px;
  background: #f8fafc;
  color: #5e7185;
  line-height: 1.75;
}

.latest-score-card {
  padding: 20px 22px;
  border-radius: 24px;
  background: linear-gradient(135deg, #eff6ff, #f7fbff);
}

.latest-score-card strong {
  display: block;
  margin-top: 10px;
  font-size: 48px;
  font-weight: 700;
  color: #102542;
}

.score-block + .score-block {
  margin-top: 16px;
}

.score-block strong {
  display: block;
  margin-top: 8px;
  color: #102542;
  font-size: 30px;
}

.chart {
  height: 340px;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .hero,
  .panel-header {
    flex-direction: column;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
