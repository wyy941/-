const ADMIN_ROLES = ["admin"];
const TEACHER_ROLES = ["teacher"];
const TEACHER_SIDE_ROLES = [...TEACHER_ROLES, ...ADMIN_ROLES];

export const getStoredUser = () => {
  try {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
};

export const getStoredToken = () => localStorage.getItem("token") || "";

export const clearAuth = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
};

export const isAdminRole = (role) => ADMIN_ROLES.includes(role);

export const isTeacherRole = (role) => TEACHER_ROLES.includes(role);

export const isTeacherSideRole = (role) => TEACHER_SIDE_ROLES.includes(role);

export const getHomeRouteByRole = (role) => {
  if (role === "student") {
    return "/student-center";
  }
  if (role === "teacher") {
    return "/teacher-center";
  }
  return "/admin-center";
};

export const hasRequiredRole = (user, roles = []) => {
  if (!roles.length) {
    return true;
  }
  return roles.includes(user?.role);
};
