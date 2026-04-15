<template>
  <div class="page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Teacher Workspace</p>
        <h1>{{ PROJECT_NAME }}</h1>
        <p class="hero-text">
          教师端聚焦任教范围内学生的风险监测、评估诊断与干预跟进，方便快速掌握班级态势并完成教学场景下的风险研判。
        </p>
      </div>
      <div class="hero-side">
        <div class="hero-badge">教师工作台</div>
        <div class="hero-meta">
          <span>当前账号</span>
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
              <div class="card-title">教师端使用范围</div>
              <p>教师端围绕班级监测、风险评估、报告查看和预警跟进展开，不展示管理员专属的数据治理模块。</p>
            </div>
          </div>

          <div class="permission-list">
            <div class="permission-item">查看任教范围内的群体风险看板，掌握年级、专业和班级态势。</div>
            <div class="permission-item">发起学生风险评估，查看模型输出、风险因子与历史记录。</div>
            <div class="permission-item">在干预中心跟进预警任务，记录访谈、处理过程和后续行动。</div>
            <div class="permission-item muted">数据中心、指标管理和教师权限维护仅管理员可见。</div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="9">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">当前账号</div>
              <p>当前教师账号仅能访问所分配班级的数据和报告。</p>
            </div>
          </div>

          <div class="profile-grid">
            <div class="profile-item">
              <span>用户名</span>
              <strong>{{ currentUser?.username || "--" }}</strong>
            </div>
            <div class="profile-item">
              <span>角色</span>
              <strong>教师端</strong>
            </div>
            <div class="profile-item">
              <span>项目名称</span>
              <strong class="compact">{{ PROJECT_NAME }}</strong>
            </div>
            <div class="profile-item">
              <span>可用模块</span>
              <strong class="compact">看板 / 评估 / 报告 / 干预</strong>
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
              <p>默认展示当前教师权限范围内优先需要跟进的学生记录。</p>
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
              <div class="card-title">干预任务概况</div>
              <p>帮助教师快速识别仍需跟进的任务状态与干预进度。</p>
            </div>
          </div>

          <div class="workflow-grid">
            <div class="workflow-item">
              <span>待处理工单</span>
              <strong>{{ workflowSummary.pending_task_count || 0 }}</strong>
            </div>
            <div class="workflow-item">
              <span>跟进中工单</span>
              <strong>{{ workflowSummary.in_progress_task_count || 0 }}</strong>
            </div>
            <div class="workflow-item">
              <span>已闭环工单</span>
              <strong>{{ workflowSummary.closed_task_count || 0 }}</strong>
            </div>
            <div class="workflow-item">
              <span>干预记录数</span>
              <strong>{{ workflowSummary.intervention_count || 0 }}</strong>
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
  pending_task_count: 0,
  in_progress_task_count: 0,
  closed_task_count: 0,
  intervention_count: 0
});

const summaryCards = computed(() => [
  {
    label: "可见学生数",
    value: overview.value.total_users || 0,
    note: "当前教师任教范围内可查看的学生总量。"
  },
  {
    label: "历史评估记录",
    value: overview.value.total_assessments || 0,
    note: "系统保留的全部评估历史记录，支持持续追踪。"
  },
  {
    label: "已评估学生",
    value: overview.value.latest_assessed_user_count || 0,
    note: "当前已拥有最新评估结果的学生人数。"
  },
  {
    label: "平均最新修正分",
    value: overview.value.average_adjusted_score || 0,
    note: "按学生最新一次评估结果计算。"
  },
  {
    label: "预警学生数",
    value: overview.value.alert_user_count || 0,
    note: "当前需要重点关注或跟进的学生规模。"
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
    ElMessage.error("教师首页数据加载失败");
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
    linear-gradient(135deg, #153558, #1d4f7d 54%, #2f78ad 100%);
  color: #ffffff;
  box-shadow: 0 24px 48px rgba(21, 53, 88, 0.16);
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
  color: #6b7b8e;
  font-size: 13px;
}

.stat-value {
  margin-top: 12px;
  font-size: 34px;
  font-weight: 700;
  color: #16314d;
}

.stat-note {
  margin-top: 12px;
  color: #6b7b8e;
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
  color: #16314d;
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
  background: linear-gradient(135deg, #f8fbff, #f3f7fc);
}

.profile-item span,
.workflow-item span {
  display: block;
  color: #6b7b8e;
  font-size: 13px;
}

.profile-item strong,
.workflow-item strong {
  display: block;
  margin-top: 10px;
  color: #16314d;
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
  color: #4f6379;
  line-height: 1.75;
}

.permission-item.muted {
  color: #7b8da1;
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
