<template>
  <div v-if="showSideLayout" class="app-shell">
    <aside class="shell-sidebar">
      <div class="sidebar-glow"></div>

      <div class="sidebar-brand">
        <p class="brand-kicker">{{ PROJECT_EN_NAME }}</p>
        <h1>{{ PROJECT_NAME }}</h1>
        <p class="brand-text">{{ PROJECT_TAGLINE }}</p>
        <div class="brand-tags">
          <span>Campus Edition</span>
          <span>{{ roleLabel }}</span>
        </div>
      </div>

      <div class="sidebar-profile">
        <span class="profile-label">当前账号</span>
        <strong>{{ currentUser?.username || "--" }}</strong>
        <small>{{ roleLabel }}</small>
      </div>

      <div
        v-for="section in navigationSections"
        :key="section.title"
        class="sidebar-section"
      >
        <div class="section-title">{{ section.title }}</div>
        <button
          v-for="item in section.items"
          :key="item.path"
          type="button"
          class="nav-item"
          :class="{ active: isActivePath(item.path) }"
          @click="navigate(item.path)"
        >
          <span>{{ item.title }}</span>
          <small>{{ item.description }}</small>
        </button>
      </div>

      <div class="sidebar-footer">
        <el-button class="full-width" @click="navigate(homeRoute)">返回首页</el-button>
        <el-button type="danger" plain class="full-width" @click="logout">退出登录</el-button>
      </div>
    </aside>

    <main class="shell-content">
      <header class="content-header">
        <div class="content-copy">
          <p class="content-kicker">{{ activeItem?.eyebrow || roleLabel }}</p>
          <h2>{{ activeItem?.title || roleLabel }}</h2>
          <p>{{ activeItem?.description || PROJECT_TAGLINE }}</p>
        </div>
        <div class="content-meta">
          <div class="content-pill">Enterprise Workspace</div>
          <div class="content-pill">{{ roleLabel }}</div>
          <div class="content-brand-chip">{{ PROJECT_NAME }}</div>
        </div>
      </header>

      <router-view />
    </main>
  </div>

  <router-view v-else />
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { PROJECT_EN_NAME, PROJECT_NAME, PROJECT_TAGLINE } from "./constants/branding";
import { clearAuth, getHomeRouteByRole, getStoredUser } from "./utils/auth";

const route = useRoute();
const router = useRouter();

const teacherSections = [
  {
    title: "教师工作台",
    items: [
      {
        path: "/teacher-center",
        title: "教师首页",
        eyebrow: "Teacher Console",
        description: "查看任教范围内的总体风险状态、预警学生和待跟进任务。"
      }
    ]
  },
  {
    title: "教学分析",
    items: [
      {
        path: "/dashboard",
        title: "群体风险看板",
        eyebrow: "Risk Dashboard",
        description: "按年级、专业、班级和风险等级查看教师权限范围内的群体态势。"
      },
      {
        path: "/assessment",
        title: "高级评估",
        eyebrow: "Advanced Assessment",
        description: "发起学生风险评估，查看模型输出结果、风险因子与维度诊断。"
      },
      {
        path: "/report",
        title: "报告中心",
        eyebrow: "Report Center",
        description: "查看学生个人报告、历史评估结果与模型分析详情。"
      },
      {
        path: "/workflow-center",
        title: "干预中心",
        eyebrow: "Intervention Center",
        description: "跟进预警任务、记录干预过程，并形成风险闭环。"
      }
    ]
  }
];

const adminSections = [
  {
    title: "管理工作台",
    items: [
      {
        path: "/admin-center",
        title: "管理员首页",
        eyebrow: "Admin Console",
        description: "查看平台总体运行情况、重点风险对象和核心管理指标。"
      }
    ]
  },
  {
    title: "分析业务",
    items: [
      {
        path: "/dashboard",
        title: "群体风险看板",
        eyebrow: "Risk Dashboard",
        description: "从群体态势、阶段趋势和预警名单等角度观察平台风险画像。"
      },
      {
        path: "/assessment",
        title: "高级评估",
        eyebrow: "Advanced Assessment",
        description: "执行学生风险评估，验证模型输出并生成可追踪的诊断结果。"
      },
      {
        path: "/report",
        title: "报告中心",
        eyebrow: "Report Center",
        description: "统一查看学生报告、最新结果与历史诊断记录。"
      }
    ]
  },
  {
    title: "治理配置",
    items: [
      {
        path: "/data-center",
        title: "数据中心",
        eyebrow: "Data Center",
        description: "查询数据库、管理样本数据并查看系统数据结构。"
      },
      {
        path: "/teacher-scope",
        title: "教师任教范围",
        eyebrow: "Teacher Scope",
        description: "维护教师负责的年级、专业和班级权限边界。"
      },
      {
        path: "/indicators",
        title: "指标管理",
        eyebrow: "Indicator Center",
        description: "管理评估指标、权重和评分标准。"
      },
      {
        path: "/workflow-center",
        title: "干预中心",
        eyebrow: "Intervention Center",
        description: "维护预警任务、学生档案和干预闭环流程。"
      }
    ]
  }
];

const currentUser = computed(() => {
  route.fullPath;
  return getStoredUser();
});

const currentRole = computed(() => currentUser.value?.role || "");
const homeRoute = computed(() => getHomeRouteByRole(currentRole.value));

const showSideLayout = computed(
  () => ["teacher", "admin"].includes(currentRole.value) && route.path !== "/login"
);

const navigationSections = computed(() =>
  currentRole.value === "admin" ? adminSections : teacherSections
);

const roleLabel = computed(() =>
  currentRole.value === "admin" ? "管理员端" : "教师端"
);

const activeItem = computed(() =>
  navigationSections.value.flatMap((section) => section.items).find((item) => item.path === route.path)
);

const isActivePath = (path) => route.path === path;

const navigate = (path) => {
  if (!path || route.path === path) {
    return;
  }
  router.push(path);
};

const logout = () => {
  clearAuth();
  router.replace("/login");
};
</script>

<style scoped>
.app-shell {
  display: flex;
  gap: 28px;
  min-height: 100vh;
  padding: 22px;
  background:
    radial-gradient(circle at top left, rgba(53, 97, 166, 0.12), transparent 24%),
    radial-gradient(circle at bottom right, rgba(214, 164, 82, 0.12), transparent 28%),
    linear-gradient(180deg, #edf2f8 0%, #e6ecf4 100%);
}

.shell-sidebar {
  position: relative;
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
  align-self: flex-start;
  padding: 22px 18px 18px;
  border-radius: 28px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(12, 26, 43, 0.96) 0%, rgba(18, 39, 65, 0.98) 100%);
  box-shadow: 0 24px 48px rgba(13, 24, 39, 0.2);
}

.sidebar-glow {
  position: absolute;
  inset: -20% auto auto -10%;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(102, 166, 255, 0.34), transparent 70%);
  pointer-events: none;
}

.sidebar-brand,
.sidebar-profile,
.nav-item,
.sidebar-footer {
  position: relative;
  z-index: 1;
}

.sidebar-brand {
  padding: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.04));
  backdrop-filter: blur(12px);
}

.brand-kicker {
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.62);
}

.sidebar-brand h1 {
  margin: 14px 0 0;
  font-size: 24px;
  line-height: 1.35;
  color: #f8fbff;
}

.brand-text {
  margin: 12px 0 0;
  color: rgba(232, 239, 248, 0.76);
  line-height: 1.75;
  font-size: 13px;
}

.brand-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.brand-tags span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

.sidebar-profile {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.07);
}

.profile-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.58);
}

.sidebar-profile strong {
  color: #ffffff;
  font-size: 19px;
}

.sidebar-profile small {
  color: rgba(255, 255, 255, 0.7);
}

.sidebar-section {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-title {
  padding: 0 6px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.44);
}

.nav-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid transparent;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  color: #eef4fb;
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.nav-item span {
  font-size: 15px;
  font-weight: 700;
}

.nav-item small {
  color: rgba(229, 236, 245, 0.64);
  line-height: 1.65;
}

.nav-item:hover {
  transform: translateX(2px);
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.08);
}

.nav-item.active {
  border-color: rgba(235, 189, 95, 0.5);
  background: linear-gradient(135deg, rgba(215, 171, 84, 0.26), rgba(255, 255, 255, 0.1));
  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.14);
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 6px;
}

.full-width {
  width: 100%;
}

.shell-content {
  flex: 1;
  min-width: 0;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
  padding: 22px 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 16px 34px rgba(22, 36, 53, 0.06);
  backdrop-filter: blur(10px);
}

.content-copy {
  min-width: 0;
}

.content-kicker {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #6d7f92;
}

.content-header h2 {
  margin: 10px 0 0;
  font-size: 28px;
  color: #102542;
}

.content-header p {
  margin: 8px 0 0;
  max-width: 760px;
  color: #607080;
  line-height: 1.75;
}

.content-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  align-items: center;
}

.content-pill {
  padding: 10px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.82), rgba(247, 250, 253, 0.66));
  border: 1px solid rgba(16, 37, 66, 0.06);
  color: #47617d;
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.content-brand-chip {
  flex-shrink: 0;
  padding: 10px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, #f5f8ff, #eef3fb);
  border: 1px solid rgba(16, 37, 66, 0.08);
  color: #28445f;
  font-size: 13px;
  font-weight: 600;
}

@media (max-width: 1280px) {
  .app-shell {
    flex-direction: column;
    padding: 16px;
  }

  .shell-sidebar {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .content-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .content-meta {
    justify-content: flex-start;
  }

  .sidebar-brand h1 {
    font-size: 22px;
  }
}
</style>
