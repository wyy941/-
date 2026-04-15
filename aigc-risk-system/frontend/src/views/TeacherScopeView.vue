<template>
  <div class="page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Teacher Scope</p>
        <h1>教师任教范围管理</h1>
        <p class="hero-text">
          管理员可以在这里维护教师所负责的年级、专业和班级。教师登录后，只能查看自己任教范围内学生的看板、评估记录、报告和干预任务。
        </p>
      </div>
      <div class="hero-actions">
        <el-button @click="refreshAll">刷新数据</el-button>
        <el-button type="primary" :disabled="!selectedTeacher" :loading="saving" @click="saveAssignments">
          保存任教范围
        </el-button>
      </div>
    </section>

    <section class="stats-grid">
      <el-card v-for="item in summaryCards" :key="item.label" class="panel stat-card" shadow="never">
        <div class="stat-label">{{ item.label }}</div>
        <div class="stat-value">{{ item.value }}</div>
        <div class="stat-note">{{ item.note }}</div>
      </el-card>
    </section>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="9">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">教师账号列表</div>
              <p>点击教师账号后，可在右侧修改其负责的年级、专业和班级。</p>
            </div>
          </div>

          <div class="teacher-list">
            <button
              v-for="teacher in teachers"
              :key="teacher.id"
              type="button"
              class="teacher-card"
              :class="{ active: teacher.id === selectedTeacherId }"
              @click="selectTeacher(teacher)"
            >
              <div class="teacher-top">
                <strong>{{ teacher.username }}</strong>
                <span>{{ teacher.assignment_count || 0 }} 个班级</span>
              </div>
              <div class="teacher-meta">
                {{ summarizeAssignments(teacher.teacher_assignments) }}
              </div>
            </button>
          </div>

          <el-empty v-if="!teachers.length" description="当前没有教师账号" />
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="15">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">任教范围编辑</div>
              <p v-if="selectedTeacher">
                当前编辑教师：{{ selectedTeacher.username }}。每一行对应一个“年级 + 专业 + 班级”的可访问范围。
              </p>
              <p v-else>请选择左侧教师账号开始配置。</p>
            </div>
            <div class="editor-actions">
              <el-button :disabled="!selectedTeacher" @click="resetAssignments">恢复当前配置</el-button>
              <el-button type="primary" :disabled="!selectedTeacher" @click="addAssignmentRow">
                添加班级
              </el-button>
            </div>
          </div>

          <div v-if="selectedTeacher" class="assignment-list">
            <div
              v-for="(item, index) in editableAssignments"
              :key="`${item.grade}-${item.major}-${item.class_name}-${index}`"
              class="assignment-row"
            >
              <el-select
                v-model="item.grade"
                clearable
                filterable
                class="field"
                placeholder="年级"
                @change="handleGradeChange(index)"
              >
                <el-option
                  v-for="option in rootOptions.grades"
                  :key="option"
                  :label="option"
                  :value="option"
                />
              </el-select>

              <el-select
                v-model="item.major"
                clearable
                filterable
                class="field"
                placeholder="专业"
                @change="handleMajorChange(index)"
              >
                <el-option
                  v-for="option in majorOptionsFor(item)"
                  :key="option"
                  :label="option"
                  :value="option"
                />
              </el-select>

              <el-select
                v-model="item.class_name"
                clearable
                filterable
                class="field field-wide"
                :disabled="!item.grade || !item.major"
                :placeholder="item.grade && item.major ? '班级' : '先选择年级和专业'"
              >
                <el-option
                  v-for="option in classOptionsFor(item)"
                  :key="option"
                  :label="option"
                  :value="option"
                />
              </el-select>

              <el-button text type="danger" @click="removeAssignmentRow(index)">删除</el-button>
            </div>

            <div class="tips">
              规则说明：教师保存后，只能查看所配置班级学生的风险看板、评估历史、报告详情和干预任务。
            </div>
          </div>

          <el-empty v-else description="请选择教师账号" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  getTeacherAssignmentOptionsApi,
  getTeachersApi,
  updateTeacherAssignmentsApi
} from "../api/modules";

const teachers = ref([]);
const selectedTeacherId = ref(null);
const editableAssignments = ref([]);
const rootOptions = ref({
  grades: [],
  majors: [],
  classes: []
});
const optionCache = ref({});
const saving = ref(false);

const selectedTeacher = computed(
  () => teachers.value.find((item) => item.id === selectedTeacherId.value) || null
);

const summaryCards = computed(() => [
  {
    label: "教师账号数",
    value: teachers.value.length,
    note: "当前系统内可配置任教范围的教师账号数量"
  },
  {
    label: "已配置班级",
    value: teachers.value.reduce((sum, item) => sum + (item.assignment_count || 0), 0),
    note: "所有教师已录入的年级/专业/班级组合总数"
  },
  {
    label: "当前教师配置",
    value: editableAssignments.value.length,
    note: selectedTeacher.value
      ? `正在编辑 ${selectedTeacher.value.username}`
      : "先从左侧选择教师账号"
  }
]);

const assignmentKey = (grade = "", major = "") => `${grade || ""}|${major || ""}`;

const cloneAssignments = (assignments = []) =>
  assignments.map((item) => ({
    grade: item.grade || "",
    major: item.major || "",
    class_name: item.class_name || ""
  }));

const sanitizeAssignments = () =>
  editableAssignments.value
    .map((item) => ({
      grade: (item.grade || "").trim(),
      major: (item.major || "").trim(),
      class_name: (item.class_name || "").trim()
    }))
    .filter((item) => item.grade || item.major || item.class_name);

const summarizeAssignments = (assignments = []) => {
  if (!assignments.length) {
    return "尚未分配任教班级";
  }
  return assignments
    .slice(0, 3)
    .map((item) => item.class_name || `${item.grade || "--"} ${item.major || "--"}`)
    .join(" / ");
};

const loadOptions = async (grade = "", major = "") => {
  const key = assignmentKey(grade, major);
  if (optionCache.value[key]) {
    return optionCache.value[key];
  }
  const res = await getTeacherAssignmentOptionsApi({
    ...(grade ? { grade } : {}),
    ...(major ? { major } : {})
  });
  optionCache.value[key] = res.data || { grades: [], majors: [], classes: [] };
  return optionCache.value[key];
};

const ensureOptionsFor = async (item) => {
  if (!item.grade) {
    return;
  }
  await loadOptions(item.grade, "");
  if (item.major) {
    await loadOptions(item.grade, item.major);
  }
};

const loadTeachers = async () => {
  const res = await getTeachersApi();
  teachers.value = res.data || [];
  if (!selectedTeacherId.value && teachers.value.length) {
    selectTeacher(teachers.value[0]);
  } else if (selectedTeacherId.value) {
    const current = teachers.value.find((item) => item.id === selectedTeacherId.value);
    if (current) {
      editableAssignments.value = cloneAssignments(current.teacher_assignments);
      await Promise.all(editableAssignments.value.map((item) => ensureOptionsFor(item)));
    }
  }
};

const selectTeacher = async (teacher) => {
  selectedTeacherId.value = teacher.id;
  editableAssignments.value = cloneAssignments(teacher.teacher_assignments);
  if (!editableAssignments.value.length) {
    editableAssignments.value = [{ grade: "", major: "", class_name: "" }];
  }
  await Promise.all(editableAssignments.value.map((item) => ensureOptionsFor(item)));
};

const refreshAll = async () => {
  try {
    rootOptions.value = (await loadOptions("", "")) || rootOptions.value;
    await loadTeachers();
  } catch (error) {
    ElMessage.error("教师任教范围数据加载失败");
  }
};

const resetAssignments = async () => {
  if (!selectedTeacher.value) {
    return;
  }
  await selectTeacher(selectedTeacher.value);
};

const addAssignmentRow = () => {
  editableAssignments.value.push({
    grade: "",
    major: "",
    class_name: ""
  });
};

const removeAssignmentRow = (index) => {
  editableAssignments.value.splice(index, 1);
  if (!editableAssignments.value.length) {
    addAssignmentRow();
  }
};

const majorOptionsFor = (item) => {
  if (!item.grade) {
    return rootOptions.value.majors || [];
  }
  return optionCache.value[assignmentKey(item.grade, "")]?.majors || [];
};

const classOptionsFor = (item) => {
  if (!item.grade || !item.major) {
    return [];
  }
  return optionCache.value[assignmentKey(item.grade, item.major)]?.classes || [];
};

const handleGradeChange = async (index) => {
  const item = editableAssignments.value[index];
  item.major = "";
  item.class_name = "";
  await ensureOptionsFor(item);
};

const handleMajorChange = async (index) => {
  const item = editableAssignments.value[index];
  item.class_name = "";
  await ensureOptionsFor(item);
};

const saveAssignments = async () => {
  if (!selectedTeacher.value) {
    return;
  }

  const invalidRow = sanitizeAssignments().find(
    (item) => !item.grade || !item.major || !item.class_name
  );
  if (invalidRow) {
    ElMessage.warning("每条任教范围都需要完整选择年级、专业和班级");
    return;
  }

  saving.value = true;
  try {
    const res = await updateTeacherAssignmentsApi(selectedTeacher.value.id, {
      assignments: sanitizeAssignments()
    });
    const updated = res.data;
    teachers.value = teachers.value.map((item) =>
      item.id === updated.id ? updated : item
    );
    await selectTeacher(updated);
    ElMessage.success("教师任教范围已更新");
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || "保存失败");
  } finally {
    saving.value = false;
  }
};

onMounted(async () => {
  await refreshAll();
});
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24px;
  background:
    radial-gradient(circle at top right, rgba(29, 78, 216, 0.08), transparent 28%),
    linear-gradient(180deg, #f6f8fc 0%, #eef3f9 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  padding: 28px 32px;
  border-radius: 28px;
  background: linear-gradient(135deg, #f8fbff, #edf4ff 58%, #f6f2ff);
  box-shadow: 0 18px 44px rgba(19, 50, 77, 0.08);
}

.hero-copy {
  max-width: 840px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #3b82f6;
}

.hero h1 {
  margin: 0;
  color: #102542;
  font-size: 32px;
}

.hero-text {
  margin-top: 12px;
  color: #5f6f82;
  line-height: 1.75;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin: 18px 0 16px;
}

.panel {
  border: none;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 14px 36px rgba(16, 37, 66, 0.06);
}

.panel :deep(.el-card__body) {
  padding: 20px;
}

.stat-card {
  min-height: 140px;
}

.stat-label {
  color: #607080;
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
  color: #7a8793;
  line-height: 1.7;
  font-size: 13px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.panel-header.compact {
  margin-bottom: 14px;
}

.panel-header p {
  margin: 6px 0 0;
  color: #607080;
  line-height: 1.7;
}

.card-title {
  margin: 0;
  font-size: 18px;
  color: #102542;
  font-weight: 700;
}

.teacher-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.teacher-card {
  border: 1px solid rgba(16, 37, 66, 0.08);
  border-radius: 18px;
  padding: 16px;
  background: #f8fbff;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.teacher-card:hover,
.teacher-card.active {
  border-color: rgba(59, 130, 246, 0.32);
  background: linear-gradient(135deg, #eff6ff, #f7fbff);
  box-shadow: 0 10px 22px rgba(59, 130, 246, 0.08);
}

.teacher-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #102542;
}

.teacher-meta {
  margin-top: 10px;
  color: #607080;
  font-size: 13px;
  line-height: 1.7;
}

.editor-actions {
  display: flex;
  gap: 10px;
}

.assignment-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.assignment-row {
  display: grid;
  grid-template-columns: 1fr 1.3fr 1.6fr auto;
  gap: 12px;
  align-items: center;
  padding: 14px;
  border-radius: 18px;
  background: linear-gradient(135deg, #f8fbff, #fdfdff);
}

.field {
  width: 100%;
}

.field-wide {
  min-width: 0;
}

.tips {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(59, 130, 246, 0.08);
  color: #35506d;
  line-height: 1.7;
  font-size: 13px;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .assignment-row {
    grid-template-columns: 1fr;
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
}
</style>
