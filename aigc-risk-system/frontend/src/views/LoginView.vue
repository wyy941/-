<template>
  <div class="login-page">
    <div class="aurora aurora-left"></div>
    <div class="aurora aurora-right"></div>
    <div class="aurora aurora-center"></div>
    <div class="mesh"></div>

    <section class="login-shell">
      <div class="hero-chip">
        <span>{{ PROJECT_EN_NAME }}</span>
        <span>Glass Edition</span>
      </div>

      <div class="glass-stage">
        <div class="stage-glow"></div>

        <div class="brand-block">
          <div class="brand-mark">
            <span>A</span>
          </div>

          <div class="brand-copy">
            <p class="brand-kicker">{{ PROJECT_EN_NAME }}</p>
            <h1>{{ PROJECT_NAME }}</h1>
            <p class="brand-text">{{ PROJECT_TAGLINE }}</p>
          </div>

          <div class="brand-metrics">
            <div class="metric-card">
              <span>Scene</span>
              <strong>高校项目演示</strong>
            </div>
            <div class="metric-card">
              <span>Mode</span>
              <strong>风险评估与预警</strong>
            </div>
            <div class="metric-card">
              <span>Access</span>
              <strong>Admin / Teacher / Student</strong>
            </div>
          </div>
        </div>

        <main class="login-card">
          <div class="card-highlight"></div>

          <header class="card-header">
            <p class="eyebrow">System Access</p>
            <h2>欢迎进入系统</h2>
            <p class="subtitle">请输入用户名和密码后登录平台。</p>
          </header>

          <div class="access-strip">
            <span>Campus Risk Intelligence</span>
            <span>Visual Decision Platform</span>
          </div>

          <el-form :model="form" class="login-form" @submit.prevent>
            <div class="field">
              <label for="username">用户名</label>
              <el-input
                id="username"
                v-model="form.username"
                size="large"
                placeholder="请输入用户名"
                autocomplete="username"
                @keyup.enter="login"
              />
            </div>

            <div class="field">
              <label for="password">密码</label>
              <el-input
                id="password"
                v-model="form.password"
                size="large"
                type="password"
                placeholder="请输入密码"
                autocomplete="current-password"
                show-password
                @keyup.enter="login"
              />
            </div>

            <el-button
              type="primary"
              size="large"
              class="login-button"
              :loading="loading"
              @click="login"
            >
              登录系统
            </el-button>
          </el-form>

          <footer class="card-footer">
            <span>大学生 AIGC 技术依赖风险评估与预警平台</span>
          </footer>
        </main>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { loginApi } from "../api/modules";
import {
  PROJECT_EN_NAME,
  PROJECT_NAME,
  PROJECT_TAGLINE
} from "../constants/branding";
import { getHomeRouteByRole } from "../utils/auth";

const router = useRouter();
const loading = ref(false);

const form = reactive({
  username: "",
  password: ""
});

const login = async () => {
  if (loading.value) {
    return;
  }

  if (!form.username.trim() || !form.password.trim()) {
    ElMessage.warning("请输入用户名和密码");
    return;
  }

  loading.value = true;

  try {
    const res = await loginApi(form);
    if (res.code === 200) {
      localStorage.setItem("user", JSON.stringify(res.data.user));
      localStorage.setItem("token", res.data.token);
      ElMessage.success("登录成功");
      router.push(res.data.home_route || getHomeRouteByRole(res.data.user?.role));
      return;
    }

    ElMessage.error(res.message || "登录失败");
  } catch (error) {
    ElMessage.error("登录请求失败，请稍后重试");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  overflow: hidden;
  background:
    linear-gradient(145deg, #dbe4ef 0%, #edf3f8 38%, #e7eff7 100%);
}

.aurora,
.mesh {
  position: absolute;
  pointer-events: none;
}

.aurora {
  border-radius: 50%;
  filter: blur(34px);
  opacity: 0.72;
}

.aurora-left {
  top: -120px;
  left: -80px;
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(81, 134, 255, 0.38), transparent 70%);
}

.aurora-right {
  right: -100px;
  bottom: -120px;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(219, 173, 93, 0.32), transparent 70%);
}

.aurora-center {
  top: 18%;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.42), transparent 72%);
}

.mesh {
  inset: 0;
  background-image:
    linear-gradient(rgba(20, 42, 68, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(20, 42, 68, 0.03) 1px, transparent 1px);
  background-size: 28px 28px;
  mask-image: radial-gradient(circle at center, black 32%, transparent 80%);
}

.login-shell {
  position: relative;
  z-index: 1;
  width: min(860px, 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

.hero-chip {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.hero-chip span {
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.55);
  background: rgba(255, 255, 255, 0.32);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.52);
  backdrop-filter: blur(14px);
  color: #49617c;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.glass-stage {
  position: relative;
  width: 100%;
  padding: 22px;
  border-radius: 36px;
  border: 1px solid rgba(255, 255, 255, 0.55);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.16));
  box-shadow:
    0 30px 70px rgba(24, 43, 66, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.58);
  backdrop-filter: blur(22px) saturate(160%);
}

.stage-glow {
  position: absolute;
  inset: 12% 22% auto;
  height: 120px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.42), transparent 68%);
  filter: blur(12px);
  pointer-events: none;
}

.brand-block {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 22px 20px 18px;
  text-align: center;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 86px;
  height: 86px;
  border-radius: 26px;
  border: 1px solid rgba(255, 255, 255, 0.42);
  background:
    linear-gradient(145deg, rgba(17, 37, 63, 0.88), rgba(37, 73, 112, 0.74));
  box-shadow:
    0 20px 34px rgba(16, 37, 66, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.brand-mark span {
  color: #f8fbff;
  font-size: 38px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.brand-copy {
  margin-top: 20px;
  max-width: 620px;
}

.brand-kicker {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #5d728b;
}

.brand-copy h1 {
  margin: 16px 0 0;
  font-size: 42px;
  line-height: 1.28;
  color: #102542;
}

.brand-text {
  margin: 14px auto 0;
  max-width: 560px;
  color: #677b91;
  line-height: 1.85;
  font-size: 15px;
}

.brand-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
  margin-top: 22px;
}

.metric-card {
  padding: 14px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.42);
  background: rgba(255, 255, 255, 0.28);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.54);
  backdrop-filter: blur(16px);
}

.metric-card span {
  display: block;
  color: #7a8da2;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.metric-card strong {
  display: block;
  margin-top: 10px;
  color: #18324d;
  font-size: 16px;
  line-height: 1.6;
}

.login-card {
  position: relative;
  width: min(520px, 100%);
  margin: 6px auto 0;
  padding: 34px 34px 22px;
  border-radius: 32px;
  border: 1px solid rgba(255, 255, 255, 0.62);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.56), rgba(255, 255, 255, 0.3));
  box-shadow:
    0 28px 64px rgba(18, 38, 61, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(24px) saturate(160%);
}

.card-highlight {
  position: absolute;
  inset: 0 0 auto;
  height: 5px;
  border-radius: 32px 32px 0 0;
  background: linear-gradient(90deg, rgba(20, 58, 97, 0.96), rgba(72, 114, 168, 0.92), rgba(212, 161, 77, 0.94));
}

.card-header {
  text-align: center;
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #71859a;
}

.card-header h2 {
  margin: 14px 0 0;
  font-size: 32px;
  color: #102542;
}

.subtitle {
  margin: 10px 0 0;
  color: #607286;
  line-height: 1.8;
}

.access-strip {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  margin: 24px 0 20px;
}

.access-strip span {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.48);
  background: rgba(255, 255, 255, 0.3);
  color: #576c82;
  font-size: 12px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field label {
  font-size: 14px;
  font-weight: 600;
  color: #31455d;
}

.field :deep(.el-input__wrapper) {
  min-height: 50px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.34);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.7),
    0 10px 24px rgba(16, 37, 66, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.42);
  backdrop-filter: blur(14px);
}

.field :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.78),
    0 14px 28px rgba(20, 58, 97, 0.12) !important;
}

.field :deep(.el-input__inner) {
  color: #18324d;
}

.field :deep(.el-input__inner::placeholder) {
  color: #8a9aad;
}

.login-button {
  width: 100%;
  height: 54px;
  margin-top: 10px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(20, 58, 97, 0.96), rgba(49, 98, 149, 0.92));
  box-shadow:
    0 20px 34px rgba(20, 58, 97, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.login-button:hover {
  transform: translateY(-1px);
}

.card-footer {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.42);
  text-align: center;
  color: #7a8c9f;
  font-size: 12px;
  line-height: 1.7;
}

@media (max-width: 900px) {
  .brand-metrics {
    grid-template-columns: 1fr;
  }

  .brand-copy h1 {
    font-size: 32px;
  }
}

@media (max-width: 768px) {
  .login-page {
    padding: 16px;
  }

  .glass-stage {
    padding: 16px;
  }

  .brand-block {
    padding: 16px 8px 10px;
  }

  .login-card {
    padding: 28px 22px 22px;
  }
}
</style>
