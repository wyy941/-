import { createRouter, createWebHistory } from "vue-router";
import AdminHomeView from "../views/AdminHomeView.vue";
import AssessmentView from "../views/AssessmentView.vue";
import DashboardView from "../views/DashboardView.vue";
import DataCenterView from "../views/DataCenterView.vue";
import IndicatorView from "../views/IndicatorView.vue";
import LoginView from "../views/LoginView.vue";
import ReportView from "../views/ReportView.vue";
import StudentHomeView from "../views/StudentHomeView.vue";
import StudentSelfAssessmentView from "../views/StudentSelfAssessmentView.vue";
import TeacherHomeView from "../views/TeacherHomeView.vue";
import TeacherScopeView from "../views/TeacherScopeView.vue";
import WorkflowCenterView from "../views/WorkflowCenterView.vue";
import {
  getHomeRouteByRole,
  getStoredToken,
  getStoredUser,
  hasRequiredRole
} from "../utils/auth";

const routes = [
  {
    path: "/",
    redirect: () => {
      const user = getStoredUser();
      return user ? getHomeRouteByRole(user.role) : "/login";
    }
  },
  { path: "/login", component: LoginView, meta: { guestOnly: true } },
  {
    path: "/teacher-admin",
    redirect: () => {
      const user = getStoredUser();
      return getHomeRouteByRole(user?.role);
    }
  },
  {
    path: "/teacher-center",
    component: TeacherHomeView,
    meta: { requiresAuth: true, roles: ["teacher"] }
  },
  {
    path: "/admin-center",
    component: AdminHomeView,
    meta: { requiresAuth: true, roles: ["admin"] }
  },
  {
    path: "/student-center",
    component: StudentHomeView,
    meta: { requiresAuth: true, roles: ["student"] }
  },
  {
    path: "/dashboard",
    component: DashboardView,
    meta: { requiresAuth: true, roles: ["teacher", "admin"] }
  },
  {
    path: "/assessment",
    component: AssessmentView,
    meta: { requiresAuth: true, roles: ["teacher", "admin"] }
  },
  {
    path: "/self-assessment",
    component: StudentSelfAssessmentView,
    meta: { requiresAuth: true, roles: ["student"] }
  },
  {
    path: "/indicators",
    component: IndicatorView,
    meta: { requiresAuth: true, roles: ["admin"] }
  },
  {
    path: "/data-center",
    component: DataCenterView,
    meta: { requiresAuth: true, roles: ["admin"] }
  },
  {
    path: "/teacher-scope",
    component: TeacherScopeView,
    meta: { requiresAuth: true, roles: ["admin"] }
  },
  {
    path: "/report",
    component: ReportView,
    meta: { requiresAuth: true, roles: ["teacher", "admin"] }
  },
  {
    path: "/workflow-center",
    component: WorkflowCenterView,
    meta: { requiresAuth: true, roles: ["teacher", "admin"] }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to) => {
  const user = getStoredUser();
  const token = getStoredToken();

  if (to.meta?.guestOnly && user && token) {
    return getHomeRouteByRole(user.role);
  }

  if (to.meta?.requiresAuth && (!user || !token)) {
    return "/login";
  }

  if (to.meta?.roles && !hasRequiredRole(user, to.meta.roles)) {
    return getHomeRouteByRole(user?.role);
  }

  return true;
});

export default router;
