<template>
  <div class="page">
    <section class="hero">
      <div>
        <p class="eyebrow">Risk Workflow Center</p>
        <h1>风险干预中心</h1>
        <p class="hero-text">
          在这里统一查看学生档案、预警工单和干预记录，完成从预警到闭环的跟进流程。
        </p>
      </div>
      <div class="hero-actions">
        <el-button type="success" :loading="bootstrapping" @click="syncWorkflow">
          同步演示数据
        </el-button>
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

    <el-card class="panel" shadow="never">
      <div class="panel-header">
        <div>
          <div class="card-title">筛选条件</div>
          <p>支持按关键字、年级、专业、预警等级和任务状态查看学生及工单。</p>
        </div>
        <div class="filter-actions">
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="primary" @click="loadAll(true)">查询</el-button>
        </div>
      </div>

      <el-row :gutter="12">
        <el-col :xs="24" :md="8" :xl="6">
          <el-input
            v-model="filters.keyword"
            clearable
            placeholder="输入学生姓名、年级或专业"
            @keyup.enter="loadAll(true)"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="4" :xl="3">
          <el-select
            v-model="filters.grade"
            clearable
            class="full-width"
            placeholder="年级"
            @change="loadAll(true)"
          >
            <el-option
              v-for="item in filterOptions.grades"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6" :xl="5">
          <el-select
            v-model="filters.major"
            clearable
            class="full-width"
            placeholder="专业"
            @change="loadAll(true)"
          >
            <el-option
              v-for="item in filterOptions.majors"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="4" :xl="4">
          <el-select
            v-model="filters.warning_level"
            clearable
            class="full-width"
            placeholder="预警等级"
            @change="loadAll(true)"
          >
            <el-option
              v-for="item in warningOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="4" :xl="4">
          <el-select
            v-model="filters.task_status"
            clearable
            class="full-width"
            placeholder="任务状态"
            @change="loadAll(true)"
          >
            <el-option
              v-for="item in taskStatusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="10">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">学生列表</div>
              <p>点击任意学生可查看档案、工单和干预记录。</p>
            </div>
            <el-button type="primary" :disabled="!selectedStudent" @click="openTaskDialog">
              新建工单
            </el-button>
          </div>

          <el-table
            :data="studentResult.items"
            stripe
            border
            max-height="540"
            highlight-current-row
            @row-click="handleStudentSelect"
          >
            <el-table-column prop="username" label="学生" min-width="110" />
            <el-table-column prop="grade" label="年级" width="84" />
            <el-table-column prop="major" label="专业" min-width="150" />
            <el-table-column label="最新风险" width="100">
              <template #default="{ row }">
                <el-tag
                  v-if="row.latest_assessment"
                  :type="riskTagType(row.latest_assessment.adjusted_score)"
                >
                  {{ riskLabel(row.latest_assessment.adjusted_score) }}
                </el-tag>
                <span v-else>暂无</span>
              </template>
            </el-table-column>
            <el-table-column label="任务状态" width="100">
              <template #default="{ row }">
                <el-tag
                  v-if="row.current_task"
                  :type="taskTagType(row.current_task.task_status)"
                >
                  {{ taskStatusLabel(row.current_task.task_status) }}
                </el-tag>
                <span v-else>暂无</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-bar">
            <el-pagination
              v-model:current-page="filters.page"
              v-model:page-size="filters.page_size"
              background
              layout="total, prev, pager, next"
              :total="studentResult.pagination.total"
              @current-change="loadStudents"
              @size-change="handlePageSizeChange"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="14">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">学生档案</div>
              <p>教师或管理员可以补充联系人、宿舍、支持等级和风险关注点。</p>
            </div>
            <el-button type="primary" :disabled="!selectedStudent" @click="saveArchive">
              保存档案
            </el-button>
          </div>

          <el-empty
            v-if="!selectedStudent"
            description="请选择左侧学生后查看详细档案。"
          />
          <template v-else>
            <div class="profile-grid">
              <div class="profile-card">
                <span>学生</span>
                <strong>{{ selectedStudent.username }}</strong>
              </div>
              <div class="profile-card">
                <span>班级</span>
                <strong>{{ selectedStudent.class_name || "--" }}</strong>
              </div>
              <div class="profile-card">
                <span>最新风险</span>
                <strong>{{ riskLabel(detailBundle.latest_assessment?.adjusted_score) }}</strong>
              </div>
              <div class="profile-card">
                <span>当前工单</span>
                <strong>{{ taskStatusLabel(detailBundle.current_task?.task_status) }}</strong>
              </div>
            </div>

            <el-form label-position="top">
              <el-row :gutter="12">
                <el-col :xs="24" :md="12">
                  <el-form-item label="学号">
                    <el-input v-model="archiveForm.student_no" disabled />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="档案状态">
                    <el-input v-model="archiveForm.archive_status" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="导师">
                    <el-input v-model="archiveForm.advisor_name" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="辅导员">
                    <el-input v-model="archiveForm.counselor_name" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="联系电话">
                    <el-input v-model="archiveForm.contact_phone" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="宿舍">
                    <el-input v-model="archiveForm.dormitory" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="支持等级">
                    <el-select v-model="archiveForm.support_level" class="full-width">
                      <el-option label="基础支持" value="基础支持" />
                      <el-option label="重点关注" value="重点关注" />
                      <el-option label="专项干预" value="专项干预" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :md="12">
                  <el-form-item label="AIGC 使用模式">
                    <el-input v-model="archiveForm.ai_usage_pattern" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24">
                  <el-form-item label="风险关注点">
                    <el-input v-model="archiveForm.risk_focus" type="textarea" :rows="2" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24">
                  <el-form-item label="备注">
                    <el-input v-model="archiveForm.notes" type="textarea" :rows="3" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :xl="13">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">预警工单</div>
              <p>展示当前学生相关的全部工单，可继续跟进或直接闭环。</p>
            </div>
          </div>

          <el-empty
            v-if="!selectedStudent"
            description="请选择学生后查看预警工单。"
          />
          <el-table
            v-else
            :data="tasks"
            stripe
            border
            max-height="420"
            @row-click="handleTaskSelect"
          >
            <el-table-column prop="warning_code" label="工单编号" min-width="120" />
            <el-table-column label="预警等级" width="96">
              <template #default="{ row }">
                {{ warningLevelLabel(row.warning_level) }}
              </template>
            </el-table-column>
            <el-table-column label="任务状态" width="96">
              <template #default="{ row }">
                {{ taskStatusLabel(row.task_status) }}
              </template>
            </el-table-column>
            <el-table-column prop="owner_name" label="负责人" width="96" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click.stop="openInterventionDialog(row)">
                  记录干预
                </el-button>
                <el-button type="success" link @click.stop="closeTask(row)">
                  关闭工单
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="11">
        <el-card class="panel" shadow="never">
          <div class="panel-header compact">
            <div>
              <div class="card-title">干预时间线</div>
              <p>
                {{
                  selectedTask
                    ? `${selectedTask.warning_code} 的干预记录`
                    : "请选择工单后查看对应的干预时间线。"
                }}
              </p>
            </div>
          </div>

          <el-empty
            v-if="!selectedTask"
            description="请选择工单后查看干预记录。"
          />
          <div v-else class="timeline-list">
            <div v-for="item in interventions" :key="item.id" class="timeline-item">
              <div class="timeline-top">
                <strong>{{ item.stage || "干预记录" }}</strong>
                <span>{{ formatDateTime(item.created_at) }}</span>
              </div>
              <div class="timeline-meta">
                <span>{{ item.intervention_method || "--" }}</span>
                <span>{{ item.outcome_level || "--" }}</span>
                <span v-if="item.follow_up_score !== null">
                  跟进分：{{ item.follow_up_score }}
                </span>
              </div>
              <p>{{ item.record_content }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="taskDialog.visible" title="新建预警工单" width="560px">
      <el-form label-position="top">
        <el-form-item label="预警等级">
          <el-select v-model="taskDialog.form.warning_level" class="full-width">
            <el-option
              v-for="item in warningOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="taskDialog.form.owner_name" />
        </el-form-item>
        <el-form-item label="截止时间">
          <el-date-picker
            v-model="taskDialog.form.due_date"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            class="full-width"
          />
        </el-form-item>
        <el-form-item label="工单摘要">
          <el-input v-model="taskDialog.form.summary" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="处理建议">
          <el-input v-model="taskDialog.form.recommendation" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="taskDialog.loading" @click="submitTask">
          提交
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="interventionDialog.visible" title="新增干预记录" width="620px">
      <el-form label-position="top">
        <el-form-item label="阶段">
          <el-input v-model="interventionDialog.form.stage" />
        </el-form-item>
        <el-form-item label="干预方式">
          <el-input v-model="interventionDialog.form.intervention_method" />
        </el-form-item>
        <el-form-item label="记录内容">
          <el-input
            v-model="interventionDialog.form.record_content"
            type="textarea"
            :rows="4"
          />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :xs="24" :md="12">
            <el-form-item label="结果判断">
              <el-select v-model="interventionDialog.form.outcome_level" class="full-width">
                <el-option label="待观察" value="待观察" />
                <el-option label="已改善" value="已改善" />
                <el-option label="需升级" value="需升级" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="工单状态">
              <el-select v-model="interventionDialog.form.task_status" class="full-width">
                <el-option
                  v-for="item in taskStatusOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="跟进分数">
          <el-input-number
            v-model="interventionDialog.form.follow_up_score"
            class="full-width"
            :min="0"
            :max="100"
          />
        </el-form-item>
        <el-form-item label="下一步行动">
          <el-input v-model="interventionDialog.form.next_action" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="interventionDialog.visible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="interventionDialog.loading"
          @click="submitIntervention"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  bootstrapWorkflowApi,
  createInterventionRecordApi,
  createWarningTaskApi,
  getInterventionRecordsApi,
  getStudentArchiveApi,
  getWarningTasksApi,
  getWorkflowOverviewApi,
  getWorkflowStudentsApi,
  updateStudentArchiveApi,
  updateWarningTaskApi
} from "../api/modules";

const overview = ref({
  summary: {
    student_count: 0,
    archive_count: 0,
    pending_task_count: 0,
    in_progress_task_count: 0,
    closed_task_count: 0,
    intervention_count: 0,
    urgent_count: 0
  },
  filter_options: {
    grades: [],
    majors: [],
    warning_levels: [],
    task_statuses: []
  }
});

const studentResult = ref({
  items: [],
  pagination: {
    page: 1,
    page_size: 10,
    total: 0
  }
});

const filters = reactive({
  keyword: "",
  grade: "",
  major: "",
  warning_level: "",
  task_status: "",
  page: 1,
  page_size: 10
});

const selectedStudent = ref(null);
const selectedTask = ref(null);
const tasks = ref([]);
const interventions = ref([]);
const bootstrapping = ref(false);

const detailBundle = ref({
  user: null,
  archive: null,
  latest_assessment: null,
  current_task: null
});

const archiveForm = reactive({
  student_no: "",
  archive_status: "",
  advisor_name: "",
  counselor_name: "",
  contact_phone: "",
  dormitory: "",
  entry_year: "",
  support_level: "",
  ai_usage_pattern: "",
  risk_focus: "",
  notes: ""
});

const taskDialog = reactive({
  visible: false,
  loading: false,
  form: {
    warning_level: "",
    owner_name: "",
    due_date: "",
    summary: "",
    recommendation: ""
  }
});

const interventionDialog = reactive({
  visible: false,
  loading: false,
  taskId: null,
  form: {
    stage: "干预跟进",
    intervention_method: "",
    record_content: "",
    outcome_level: "待观察",
    next_action: "",
    follow_up_score: 60,
    task_status: ""
  }
});

const filterOptions = computed(() => overview.value.filter_options || {
  grades: [],
  majors: [],
  warning_levels: [],
  task_statuses: []
});

const warningOptions = computed(() => {
  const fallback = ["一级预警", "二级预警", "三级关注"];
  const values = filterOptions.value.warning_levels?.length
    ? filterOptions.value.warning_levels
    : fallback;
  return values.map((value, index) => ({
    value,
    label: fallback[index] || value
  }));
});

const taskStatusOptions = computed(() => {
  const fallback = ["待处理", "跟进中", "已闭环"];
  const values = filterOptions.value.task_statuses?.length
    ? filterOptions.value.task_statuses
    : fallback;
  return values.map((value, index) => ({
    value,
    label: fallback[index] || value
  }));
});

const summaryCards = computed(() => {
  const summary = overview.value.summary || {};
  return [
    {
      label: "学生数",
      value: summary.student_count || 0,
      note: "当前筛选范围内纳入工作流的学生人数。"
    },
    {
      label: "学生档案数",
      value: summary.archive_count || 0,
      note: "已建立风险档案的学生数量。"
    },
    {
      label: "待处理工单",
      value: summary.pending_task_count || 0,
      note: "仍未开始跟进的预警任务数量。"
    },
    {
      label: "跟进中工单",
      value: summary.in_progress_task_count || 0,
      note: "已经进入跟进流程但尚未闭环的工单。"
    },
    {
      label: "已闭环工单",
      value: summary.closed_task_count || 0,
      note: "已完成处置并关闭的预警任务数量。"
    },
    {
      label: "干预记录数",
      value: summary.intervention_count || 0,
      note: `其中高优先级预警任务 ${summary.urgent_count || 0} 条。`
    }
  ];
});

const buildQueryParams = () => {
  const params = {
    page: filters.page,
    page_size: filters.page_size
  };
  for (const key of ["keyword", "grade", "major", "warning_level", "task_status"]) {
    if (filters[key]) {
      params[key] = filters[key];
    }
  }
  return params;
};

const warningLevelLabel = (value) =>
  warningOptions.value.find((item) => item.value === value)?.label || value || "--";

const taskStatusLabel = (value) =>
  taskStatusOptions.value.find((item) => item.value === value)?.label || value || "暂无";

const riskLabel = (score) => {
  const numeric = Number(score || 0);
  if (!numeric) {
    return "暂无";
  }
  if (numeric >= 75) {
    return "高风险";
  }
  if (numeric >= 55) {
    return "中风险";
  }
  return "低风险";
};

const formatDateTime = (value) => {
  if (!value) {
    return "--";
  }
  return String(value).replace("T", " ").slice(0, 19);
};

const riskTagType = (score) => {
  const numeric = Number(score || 0);
  if (numeric >= 75) return "danger";
  if (numeric >= 55) return "warning";
  return "success";
};

const taskTagType = (value) => {
  const [pending, inProgress, closed] = taskStatusOptions.value.map((item) => item.value);
  if (value === closed) return "success";
  if (value === inProgress) return "warning";
  if (value === pending) return "danger";
  return "info";
};

const applyArchiveForm = (archive) => {
  archiveForm.student_no = archive?.student_no || "";
  archiveForm.archive_status = archive?.archive_status || "已建档";
  archiveForm.advisor_name = archive?.advisor_name || "";
  archiveForm.counselor_name = archive?.counselor_name || "";
  archiveForm.contact_phone = archive?.contact_phone || "";
  archiveForm.dormitory = archive?.dormitory || "";
  archiveForm.entry_year = archive?.entry_year || "";
  archiveForm.support_level = archive?.support_level || "基础支持";
  archiveForm.ai_usage_pattern = archive?.ai_usage_pattern || "";
  archiveForm.risk_focus = archive?.risk_focus || "";
  archiveForm.notes = archive?.notes || "";
};

const loadOverview = async () => {
  const res = await getWorkflowOverviewApi(buildQueryParams());
  overview.value = res.data || overview.value;
};

const loadInterventions = async () => {
  if (!selectedTask.value?.id) {
    interventions.value = [];
    return;
  }
  const res = await getInterventionRecordsApi({ task_id: selectedTask.value.id });
  interventions.value = res.data || [];
};

const loadSelectedStudentDetails = async () => {
  if (!selectedStudent.value?.id) {
    return;
  }

  const [archiveRes, taskRes] = await Promise.all([
    getStudentArchiveApi(selectedStudent.value.id),
    getWarningTasksApi({ user_id: selectedStudent.value.id })
  ]);

  detailBundle.value = archiveRes.data || detailBundle.value;
  applyArchiveForm(detailBundle.value.archive);
  tasks.value = taskRes.data || [];
  selectedTask.value =
    tasks.value.find((item) => item.id === selectedTask.value?.id) || tasks.value[0] || null;
  await loadInterventions();
};

const loadStudents = async (resetPage = false) => {
  if (resetPage === true) {
    filters.page = 1;
  }
  const res = await getWorkflowStudentsApi(buildQueryParams());
  studentResult.value = res.data || studentResult.value;

  const items = studentResult.value.items || [];
  if (!items.length) {
    selectedStudent.value = null;
    selectedTask.value = null;
    tasks.value = [];
    interventions.value = [];
    applyArchiveForm(null);
    return;
  }

  const matched = items.find((item) => item.id === selectedStudent.value?.id);
  selectedStudent.value = matched || items[0];
  await loadSelectedStudentDetails();
};

const loadAll = async (resetPage = false) => {
  try {
    await Promise.all([loadOverview(), loadStudents(resetPage)]);
  } catch (error) {
    ElMessage.error("干预中心数据加载失败");
  }
};

const handleStudentSelect = async (row) => {
  selectedStudent.value = row;
  selectedTask.value = null;
  await loadSelectedStudentDetails();
};

const handleTaskSelect = async (row) => {
  selectedTask.value = row;
  await loadInterventions();
};

const saveArchive = async () => {
  if (!selectedStudent.value?.id) {
    return;
  }
  try {
    await updateStudentArchiveApi(selectedStudent.value.id, {
      archive_status: archiveForm.archive_status,
      advisor_name: archiveForm.advisor_name,
      counselor_name: archiveForm.counselor_name,
      contact_phone: archiveForm.contact_phone,
      dormitory: archiveForm.dormitory,
      entry_year: archiveForm.entry_year,
      support_level: archiveForm.support_level,
      ai_usage_pattern: archiveForm.ai_usage_pattern,
      risk_focus: archiveForm.risk_focus,
      notes: archiveForm.notes
    });
    ElMessage.success("学生档案已保存");
    await loadAll();
  } catch (error) {
    ElMessage.error("保存学生档案失败");
  }
};

const openTaskDialog = () => {
  if (!selectedStudent.value) {
    return;
  }
  taskDialog.form.warning_level =
    detailBundle.value.current_task?.warning_level ||
    warningOptions.value[1]?.value ||
    warningOptions.value[0]?.value ||
    "";
  taskDialog.form.owner_name = archiveForm.counselor_name || archiveForm.advisor_name;
  taskDialog.form.due_date = "";
  taskDialog.form.summary =
    detailBundle.value.current_task?.summary || "需要针对当前风险情况安排后续跟进。";
  taskDialog.form.recommendation =
    detailBundle.value.current_task?.recommendation || "建议结合评估结果和课程表现开展重点跟进。";
  taskDialog.visible = true;
};

const submitTask = async () => {
  if (!selectedStudent.value?.id) {
    return;
  }
  taskDialog.loading = true;
  try {
    await createWarningTaskApi({
      user_id: selectedStudent.value.id,
      warning_level: taskDialog.form.warning_level,
      owner_name: taskDialog.form.owner_name,
      due_date: taskDialog.form.due_date,
      summary: taskDialog.form.summary,
      recommendation: taskDialog.form.recommendation
    });
    taskDialog.visible = false;
    ElMessage.success("预警工单创建成功");
    await loadAll();
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || "创建预警工单失败");
  } finally {
    taskDialog.loading = false;
  }
};

const openInterventionDialog = (task) => {
  selectedTask.value = task;
  interventionDialog.taskId = task.id;
  interventionDialog.form.stage = "干预跟进";
  interventionDialog.form.intervention_method = "";
  interventionDialog.form.record_content = "";
  interventionDialog.form.outcome_level = "待观察";
  interventionDialog.form.next_action = "";
  interventionDialog.form.follow_up_score = Number(task.trigger_score || 60);
  interventionDialog.form.task_status =
    task.task_status === taskStatusOptions.value[2]?.value
      ? taskStatusOptions.value[1]?.value || task.task_status
      : task.task_status || taskStatusOptions.value[1]?.value || "";
  interventionDialog.visible = true;
};

const submitIntervention = async () => {
  if (!interventionDialog.taskId) {
    return;
  }
  interventionDialog.loading = true;
  try {
    await createInterventionRecordApi({
      task_id: interventionDialog.taskId,
      stage: interventionDialog.form.stage,
      intervention_method: interventionDialog.form.intervention_method,
      record_content: interventionDialog.form.record_content,
      outcome_level: interventionDialog.form.outcome_level,
      next_action: interventionDialog.form.next_action,
      follow_up_score: interventionDialog.form.follow_up_score,
      task_status: interventionDialog.form.task_status
    });
    interventionDialog.visible = false;
    ElMessage.success("干预记录已保存");
    await loadAll();
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || "保存干预记录失败");
  } finally {
    interventionDialog.loading = false;
  }
};

const closeTask = async (task) => {
  try {
    await updateWarningTaskApi(task.id, {
      task_status: taskStatusOptions.value[2]?.value || "已闭环"
    });
    ElMessage.success("工单已关闭");
    await loadAll();
  } catch (error) {
    ElMessage.error("关闭工单失败");
  }
};

const handlePageSizeChange = async (pageSize) => {
  filters.page_size = pageSize;
  filters.page = 1;
  await loadStudents();
};

const resetFilters = async () => {
  filters.keyword = "";
  filters.grade = "";
  filters.major = "";
  filters.warning_level = "";
  filters.task_status = "";
  filters.page = 1;
  filters.page_size = 10;
  await loadAll();
};

const syncWorkflow = async () => {
  bootstrapping.value = true;
  try {
    await bootstrapWorkflowApi();
    ElMessage.success("工作流演示数据已同步");
    await loadAll();
  } catch (error) {
    ElMessage.error("同步演示数据失败");
  } finally {
    bootstrapping.value = false;
  }
};

onMounted(async () => {
  await loadAll(true);
});
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 24px;
  background: linear-gradient(135deg, #fffdf8 0%, #f4f8ff 56%, #eef3f8 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 30px 32px;
  margin-bottom: 18px;
  border-radius: 28px;
  background: linear-gradient(135deg, rgba(255, 244, 221, 0.95), rgba(236, 245, 255, 0.94));
  box-shadow: 0 18px 48px rgba(16, 37, 66, 0.08);
}

.eyebrow {
  margin: 0 0 8px;
  color: #d97706;
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.hero h1 {
  margin: 0;
  color: #102542;
  font-size: 32px;
}

.hero-text {
  margin: 14px 0 0;
  color: #607080;
  line-height: 1.8;
}

.hero-actions,
.filter-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.panel {
  margin-bottom: 16px;
  border: none;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 14px 36px rgba(16, 37, 66, 0.06);
}

.panel :deep(.el-card__body) {
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-header.compact {
  margin-bottom: 16px;
}

.card-title {
  font-size: 18px;
  font-weight: 700;
  color: #102542;
}

.panel-header p {
  margin: 8px 0 0;
  color: #607080;
  line-height: 1.7;
}

.stat-card {
  margin-bottom: 0;
}

.stat-label {
  font-size: 13px;
  color: #607080;
}

.stat-value {
  margin-top: 12px;
  font-size: 32px;
  font-weight: 700;
  color: #102542;
}

.stat-note {
  margin-top: 10px;
  line-height: 1.6;
  color: #6b7b8e;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.profile-card {
  padding: 14px 16px;
  border-radius: 16px;
  background: #f8fafc;
}

.profile-card span {
  display: block;
  color: #6b7b8e;
  font-size: 13px;
}

.profile-card strong {
  display: block;
  margin-top: 8px;
  color: #102542;
  font-size: 18px;
}

.timeline-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.timeline-item {
  padding: 16px;
  border-radius: 16px;
  background: #f8fafc;
}

.timeline-top,
.timeline-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.timeline-top strong {
  color: #0f172a;
}

.timeline-top span,
.timeline-meta span {
  color: #64748b;
  font-size: 13px;
}

.timeline-item p {
  margin: 10px 0 0;
  color: #334155;
  line-height: 1.7;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.full-width {
  width: 100%;
}

@media (max-width: 1440px) {
  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1200px) {
  .profile-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .hero,
  .panel-header {
    flex-direction: column;
  }
}

@media (max-width: 640px) {
  .page {
    padding: 16px;
  }

  .stats-grid,
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
