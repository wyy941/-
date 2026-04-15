<template>
  <div class="page">
    <div class="header">
      <h2>评估指标管理</h2>
      <div>
        <el-button @click="$router.push('/data-center')">数据中心</el-button>
        <el-button @click="$router.push('/report')">报告中心</el-button>
        <el-button @click="$router.push('/dashboard')">返回看板</el-button>
        <el-button type="primary" @click="openCreate">新增指标</el-button>
      </div>
    </div>

    <el-card>
      <el-table :data="tableData" border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="code" label="指标编码" />
        <el-table-column prop="name" label="指标名称" />
        <el-table-column prop="dimension_name" label="维度" width="120" />
        <el-table-column prop="weight" label="权重" width="100" />
        <el-table-column prop="score_standard" label="评分标准" min-width="220" />
        <el-table-column prop="enabled" label="启用" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.enabled ? 'success' : 'info'">
              {{ scope.row.enabled ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="scope">
            <el-button size="small" @click="openEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="removeRow(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑指标' : '新增指标'">
      <el-form :model="form" label-width="100px">
        <el-form-item label="编码">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="权重">
          <el-input-number v-model="form.weight" :min="0" :max="1" :step="0.01" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="评分标准">
          <el-input v-model="form.score_standard" type="textarea" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  addIndicatorApi,
  deleteIndicatorApi,
  getIndicatorsApi,
  updateIndicatorApi
} from "../api/modules";

const tableData = ref([]);
const dialogVisible = ref(false);
const isEdit = ref(false);

const form = reactive({
  id: null,
  code: "",
  name: "",
  weight: 0.1,
  description: "",
  score_standard: "",
  enabled: true
});

const resetForm = () => {
  form.id = null;
  form.code = "";
  form.name = "";
  form.weight = 0.1;
  form.description = "";
  form.score_standard = "";
  form.enabled = true;
};

const loadData = async () => {
  try {
    const res = await getIndicatorsApi();
    tableData.value = res.data || [];
  } catch (error) {
    ElMessage.error("获取指标失败");
  }
};

const openCreate = () => {
  resetForm();
  isEdit.value = false;
  dialogVisible.value = true;
};

const openEdit = (row) => {
  Object.assign(form, row);
  isEdit.value = true;
  dialogVisible.value = true;
};

const submitForm = async () => {
  try {
    const payload = { ...form };
    if (isEdit.value) {
      await updateIndicatorApi(form.id, payload);
      ElMessage.success("更新成功");
    } else {
      await addIndicatorApi(payload);
      ElMessage.success("新增成功");
    }
    dialogVisible.value = false;
    loadData();
  } catch (error) {
    ElMessage.error("提交失败");
  }
};

const removeRow = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除指标 ${row.name} 吗？`, "提示", {
      type: "warning"
    });
    await deleteIndicatorApi(row.id);
    ElMessage.success("删除成功");
    loadData();
  } catch (error) {
    // 取消时不提示
  }
};

onMounted(loadData);
</script>

<style scoped>
.page {
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
