<template>
  <div class="page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Teacher / Admin Console</p>
        <h1>教师端 / 管理员端</h1>
        <p class="hero-text">
          面向教师与管理员的统一工作台，用于查看群体风险态势、处理预警任务、管理指标体系，并进入学生风险干预闭环。
        </p>
      </div>
      <div class="hero-actions">
        <el-tag type="success">{{ roleLabel }}</el-tag>
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

    <el-row :gutter="16">
      <el-col :xs="24" :xl="15">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">角色工作区</div>
              <p>统一进入分析、查询、指标配置、报告查看与风险干预等核心模块。</p>
            </div>
          </div>

          <div class="module-grid">
            <button
              v-for="item in moduleCards"
              :key="item.path"
              class="module-card"
              type="button"
              @click="router.push(item.path)"
            >
              <span class="module-kicker">{{ item.kicker }}</span>
              <strong>{{ item.title }}</strong>
              <p>{{ item.description }}</p>
            </button>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="9">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">当前账号</div>
              <p>显示当前登录身份以及该角色的默认工作范围。</p>
            </div>
          </div>

          <div class="profile-grid">
            <div class="profile-item">
              <span>用户名</span>
              <strong>{{ currentUser?.username || "--" }}</strong>
            </div>
            <div class="profile-item">
              <span>角色</span>
              <strong>{{ roleLabel }}</strong>
            </div>
            <div class="profile-item">
              <span>所属专业</span>
              <strong>{{ currentUser?.major || "--" }}</strong>
            </div>
            <div class="profile-item">
              <span>页面权限</span>
              <strong>{{ currentUser?.role === "admin" ? "平台管理权限" : "教学管理权限" }}</strong>
            </div>
          </div>

          <div class="permission-list">
            <div class="permission-item">支持查看风险看板、报告中心与预警任务。</div>
            <div class="permission-item">支持进入工作流中心处理干预记录与闭环跟踪。</div>
            <div class="permission-item">
              {{ currentUser?.role === "admin" ? "管理员可维护指标、数据库和教师任教范围。" : "教师仅查看任教范围内学生数据与报告。" }}
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
              <div class="card-title">最近预警名单</div>
              <p>展示当前范围内需要重点关注的学生风险对象。</p>
            </div>
            <el-button type="primary" link @click="router.push('/dashboard')">进入看板</el-button>
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
              <div class="card-title">工作流进度</div>
              <p>展示当前预警工单与干预记录的处理状态。</p>
            </div>
            <el-button type="primary" link @click="router.push('/workflow-center')">
              进入干预中心
            </el-button>
          </div>

          <div class="workflow-grid">
            <div class="workflow-item">
              <span>待处理任务</span>
              <strong>{{ workflowSummary.pending_task_count || 0 }}</strong>
            </div>
            <div class="workflow-item">
              <span>处理中任务</span>
              <strong>{{ workflowSummary.in_progress_task_count || 0 }}</strong>
            </div>
            <div class="workflow-item">
              <span>已闭环任务</span>
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
import { clearAuth, getStoredUser } from "../utils/auth";

const router = useRouter();
const currentUser = ref(getStoredUser());
const overview = ref({
  total_users: 0,
  total_assessments: 0,
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

const roleLabel = computed(() =>
  currentUser.value?.role === "admin" ? "管理员端" : "教师端"
);

const summaryCards = computed(() => [
  {
    label: "学生规模",
    value: overview.value.total_users || 0,
    note: "当前纳入分析范围的学生总数。"
  },
  {
    label: "评估记录",
    value: overview.value.total_assessments || 0,
    note: "系统已保存的风险评估历史记录。"
  },
  {
    label: "重点预警",
    value: overview.value.alert_user_count || 0,
    note: "当前需要重点关注的高风险学生数量。"
  },
  {
    label: "待处理任务",
    value: workflowSummary.value.pending_task_count || 0,
    note: "尚未完成闭环处理的预警工单数量。"
  }
]);

const moduleCards = computed(() => {
  const commonCards = [
    {
      path: "/dashboard",
      kicker: "Analysis",
      title: "群体风险看板",
      description: "查看群体态势、阶段趋势、年级对比、指标热区和预警名单。"
    },
    {
      path: "/workflow-center",
      kicker: "Intervention",
      title: "风险干预中心",
      description: "维护学生档案、预警工单与干预记录闭环。"
    },
    {
      path: "/report",
      kicker: "Report",
      title: "报告中心",
      description: "查看个体报告、趋势对比和导出结果。"
    },
    {
      path: "/assessment",
      kicker: "Assess",
      title: "高级评估",
      description: "对指定学生发起风险评估并生成诊断结果。"
    }
  ];

  if (currentUser.value?.role === "admin") {
    return [
      ...commonCards,
      {
        path: "/data-center",
        kicker: "Database",
        title: "数据中心",
        description: "执行数据库查询、样本导入和个人精准检索。"
      },
      {
        path: "/indicators",
        kicker: "Config",
        title: "指标管理",
        description: "维护评估指标、权重模型与量化标准。"
      }
    ];
  }

  return commonCards;
});

const loadOverview = async () => {
  try {
    const [overviewRes, workflowRes] = await Promise.all([
      getOverviewApi(),
      getWorkflowOverviewApi()
    ]);
    overview.value = overviewRes.data || overview.value;
    workflowSummary.value = workflowRes.data?.summary || workflowSummary.value;
  } catch (error) {
    ElMessage.error("教师/管理员首页数据加载失败");
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
  min-height: 100vh;
  padding: 24px;
  background: linear-gradient(180deg, #f4f7fb 0%, #eef3f9 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  padding: 28px 32px;
  border-radius: 28px;
  background: linear-gradient(135deg, #102542, #1f3b61 58%, #345f92);
  color: #fff;
  box-shadow: 0 20px 44px rgba(16, 37, 66, 0.16);
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.72);
}

.hero h1 {
  margin: 12px 0 0;
  font-size: 34px;
}

.hero-text {
  max-width: 760px;
  margin-top: 12px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.82);
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.stats-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.panel {
  margin-top: 16px;
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
  line-height: 1.6;
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
  color: #6b7b8e;
  line-height: 1.6;
}

.module-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.module-card {
  padding: 18px;
  border: 1px solid #d9e3ef;
  border-radius: 20px;
  background: linear-gradient(135deg, #ffffff, #f6f9fd);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.module-card:hover {
  transform: translateY(-2px);
  border-color: #9bb4d0;
  box-shadow: 0 12px 28px rgba(52, 95, 146, 0.12);
}

.module-kicker {
  display: block;
  color: #7f93aa;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.module-card strong {
  display: block;
  margin-top: 10px;
  font-size: 18px;
  color: #102542;
}

.module-card p {
  margin: 10px 0 0;
  color: #5d6f83;
  line-height: 1.6;
}

.profile-grid,
.workflow-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-item,
.workflow-item {
  padding: 16px;
  border-radius: 18px;
  background: #f6f9fc;
}

.profile-item span,
.workflow-item span {
  display: block;
  color: #6e8094;
  font-size: 13px;
}

.profile-item strong,
.workflow-item strong {
  display: block;
  margin-top: 10px;
  color: #102542;
  font-size: 20px;
}

.permission-list {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.permission-item {
  padding: 12px 14px;
  border-radius: 16px;
  background: #f8fafc;
  color: #506377;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .hero,
  .panel-header.compact {
    flex-direction: column;
  }

  .module-grid,
  .profile-grid,
  .workflow-grid {
    grid-template-columns: 1fr;
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
