<template>
  <div class="page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Platform Governance</p>
        <h1>{{ PROJECT_NAME }}</h1>
        <p class="hero-text">
          管理员端用于统筹平台运行、样本治理、指标维护和风险闭环管理，适合在课程答辩和项目汇报中展示系统整体价值。
        </p>
      </div>
      <div class="hero-side">
        <div class="hero-badge">管理员工作台</div>
        <div class="hero-meta">
          <span>全局可见</span>
          <strong>{{ currentUser?.username || "--" }}</strong>
        </div>
        <el-button class="hero-button" @click="logout">退出登录</el-button>
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

    <el-row :gutter="16">
      <el-col :xs="24" :xl="15">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">管理重点</div>
              <p>管理员端覆盖全局数据治理、权限控制、指标策略和高风险对象追踪。</p>
            </div>
          </div>

          <div class="permission-list">
            <div class="permission-item">维护评估指标、权重与评分标准，确保模型口径一致。</div>
            <div class="permission-item">管理样本导入、数据库查询、教师任教范围和基础数据配置。</div>
            <div class="permission-item">查看全量群体看板、个人报告与干预中心闭环流程。</div>
            <div class="permission-item highlight">重点关注高风险学生、未闭环工单与阶段性波动趋势。</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="9">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">当前账号</div>
              <p>管理员账号拥有平台级视图和治理权限。</p>
            </div>
          </div>

          <div class="profile-grid">
            <div class="profile-item">
              <span>用户名</span>
              <strong>{{ currentUser?.username || "--" }}</strong>
            </div>
            <div class="profile-item">
              <span>角色</span>
              <strong>管理员端</strong>
            </div>
            <div class="profile-item">
              <span>项目名称</span>
              <strong class="compact">{{ PROJECT_NAME }}</strong>
            </div>
            <div class="profile-item">
              <span>可用模块</span>
              <strong class="compact">看板 / 数据 / 教师权限 / 指标 / 报告 / 干预</strong>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="12">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">重点预警学生</div>
              <p>默认展示近期需要重点关注的学生记录，便于平台级统筹管理。</p>
            </div>
          </div>

          <el-table :data="overview.recent_alerts || []" stripe max-height="360">
            <el-table-column prop="username" label="学生" min-width="120" />
            <el-table-column prop="major" label="专业" min-width="140" />
            <el-table-column prop="risk_level" label="等级" width="100" />
            <el-table-column prop="adjusted_score" label="修正分" width="90" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="12">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">闭环概况</div>
              <p>展示平台层面的评估记录、工单总量与档案覆盖情况。</p>
            </div>
          </div>

          <div class="workflow-grid">
            <div class="workflow-item">
              <span>历史评估记录</span>
              <strong>{{ overview.total_assessments || 0 }}</strong>
            </div>
            <div class="workflow-item">
              <span>工单总量</span>
              <strong>{{ workflowTaskCount }}</strong>
            </div>
            <div class="workflow-item">
              <span>待处理工单</span>
              <strong>{{ workflowSummary.pending_task_count || 0 }}</strong>
            </div>
            <div class="workflow-item">
              <span>纳入档案学生</span>
              <strong>{{ workflowSummary.student_count || 0 }}</strong>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { getOverviewApi, getWorkflowOverviewApi } from "../api/modules";
import { PROJECT_NAME } from "../constants/branding";
import { clearAuth, getStoredUser } from "../utils/auth";

const router = useRouter();
const currentUser = ref(getStoredUser());
const overview = ref({
  total_users: 0,
  total_assessments: 0,
  latest_assessed_user_count: 0,
  average_adjusted_score: 0,
  alert_user_count: 0,
  recent_alerts: []
});
const workflowSummary = ref({
  student_count: 0,
  pending_task_count: 0,
  in_progress_task_count: 0,
  closed_task_count: 0,
  intervention_count: 0
});

const workflowTaskCount = computed(
  () =>
    (workflowSummary.value.pending_task_count || 0) +
    (workflowSummary.value.in_progress_task_count || 0) +
    (workflowSummary.value.closed_task_count || 0)
);

const summaryCards = computed(() => [
  {
    label: "学生总数",
    value: overview.value.total_users || 0,
    note: "系统内已纳入分析与管理的学生规模。"
  },
  {
    label: "历史评估记录",
    value: overview.value.total_assessments || 0,
    note: "平台保存的全部评估历史，支持多次追踪与对比。"
  },
  {
    label: "已评估学生",
    value: overview.value.latest_assessed_user_count || 0,
    note: "当前拥有最新评估结果的学生数量。"
  },
  {
    label: "平均最新修正分",
    value: overview.value.average_adjusted_score || 0,
    note: "按照每位学生最新一次评估结果计算。"
  },
  {
    label: "预警学生数",
    value: overview.value.alert_user_count || 0,
    note: "当前需要重点关注或进入预警队列的学生规模。"
  }
]);

const loadOverview = async () => {
  try {
    const [overviewRes, workflowRes] = await Promise.all([
      getOverviewApi(),
      getWorkflowOverviewApi()
    ]);
    overview.value = overviewRes.data || overview.value;
    workflowSummary.value = workflowRes.data?.summary || workflowSummary.value;
  } catch (error) {
    ElMessage.error("管理员首页数据加载失败");
  }
};

const logout = () => {
  clearAuth();
  router.replace("/login");
};

onMounted(() => {
  loadOverview();
});
</script>

<style scoped>
.page {
  min-height: 100%;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 30px 32px;
  border-radius: 30px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.14), transparent 30%),
    linear-gradient(135deg, #23141d, #5e233a 56%, #8d3353 100%);
  color: #ffffff;
  box-shadow: 0 24px 48px rgba(55, 23, 35, 0.16);
}

.hero-copy {
  max-width: 860px;
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.72);
}

.hero h1 {
  margin: 16px 0 0;
  font-size: 38px;
  line-height: 1.28;
}

.hero-text {
  margin-top: 16px;
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.8;
}

.hero-side {
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: flex-end;
  min-width: 220px;
}

.hero-badge,
.hero-meta {
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(8px);
}

.hero-badge {
  font-size: 13px;
  font-weight: 700;
}

.hero-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 180px;
}

.hero-meta span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.68);
}

.hero-meta strong {
  font-size: 18px;
}

.hero-button {
  width: 100%;
}

.stats-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
}

.panel {
  margin-top: 16px;
  border: none;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14px 36px rgba(16, 37, 66, 0.06);
}

.panel :deep(.el-card__body) {
  padding: 22px;
}

.stat-card {
  margin-top: 0;
  min-height: 158px;
}

.stat-label {
  color: #6b7280;
  font-size: 13px;
}

.stat-value {
  margin-top: 12px;
  font-size: 34px;
  font-weight: 700;
  color: #102542;
}

.stat-note {
  margin-top: 12px;
  color: #6b7280;
  line-height: 1.7;
}

.panel-header.compact {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-title {
  font-size: 18px;
  color: #102542;
  font-weight: 700;
}

.panel-header p {
  margin: 8px 0 0;
  color: #607080;
  line-height: 1.75;
}

.profile-grid,
.workflow-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-item,
.workflow-item {
  padding: 16px 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, #f8fbff, #f3f6fb);
}

.profile-item span,
.workflow-item span {
  display: block;
  color: #6b7280;
  font-size: 13px;
}

.profile-item strong,
.workflow-item strong {
  display: block;
  margin-top: 10px;
  color: #102542;
  font-size: 22px;
}

.profile-item strong.compact {
  font-size: 16px;
  line-height: 1.6;
}

.permission-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.permission-item {
  padding: 15px 16px;
  border-radius: 16px;
  background: #f8fafc;
  color: #4f5f72;
  line-height: 1.75;
}

.permission-item.highlight {
  background: rgba(141, 51, 83, 0.08);
  color: #6f2138;
  font-weight: 600;
}

@media (max-width: 1480px) {
  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1280px) {
  .hero {
    flex-direction: column;
  }

  .hero-side {
    align-items: stretch;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .hero {
    padding: 24px 20px;
  }

  .stats-grid,
  .profile-grid,
  .workflow-grid {
    grid-template-columns: 1fr;
  }
}
</style>
