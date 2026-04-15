import http from "./http";

export const loginApi = (data) => http.post("/auth/login", data);
export const registerApi = (data) => http.post("/auth/register", data);
export const getUsersApi = (params = {}) => http.get("/users", { params });
export const queryUsersApi = (params = {}) => http.get("/users/query", { params });
export const getUserProfileApi = (params = {}) => http.get("/users/profile", { params });
export const getTeachersApi = () => http.get("/teachers");
export const getTeacherAssignmentOptionsApi = (params = {}) =>
  http.get("/teachers/assignment-options", { params });
export const getTeacherAssignmentsApi = (teacherId) =>
  http.get(`/teachers/${teacherId}/assignments`);
export const updateTeacherAssignmentsApi = (teacherId, data) =>
  http.put(`/teachers/${teacherId}/assignments`, data);

export const getIndicatorsApi = () => http.get("/indicators");
export const addIndicatorApi = (data) => http.post("/indicators", data);
export const updateIndicatorApi = (id, data) => http.put(`/indicators/${id}`, data);
export const deleteIndicatorApi = (id) => http.delete(`/indicators/${id}`);

export const evaluateApi = (data) => http.post("/assessments/evaluate", data);
export const getHistoryApi = (userId) => http.get(`/assessments/history/${userId}`);
export const getStudentSelfAssessmentMetaApi = () =>
  http.get("/students/self-assessment/meta");
export const getStudentSelfAssessmentOverviewApi = () =>
  http.get("/students/self-assessment");
export const submitStudentSelfAssessmentApi = (data) =>
  http.post("/students/self-assessment", data);

export const getOverviewApi = (params = {}) => http.get("/dashboard/overview", { params });
export const getTrendApi = (userId) => http.get(`/dashboard/trend/${userId}`);

export const getSamplePreviewApi = (params = {}) =>
  http.get("/data/sample-preview", { params });
export const importSampleDataApi = (data = {}) =>
  http.post("/data/import-sample", data);

export const getLatestReportApi = (userId) => http.get(`/reports/latest/${userId}`);
export const getAssessmentReportApi = (assessmentId) =>
  http.get(`/reports/assessment/${assessmentId}`);
export const exportAssessmentReportApi = (assessmentId) =>
  http.get(`/reports/assessment/${assessmentId}/export`, {
    responseType: "blob"
  });

export const getWorkflowOverviewApi = (params = {}) =>
  http.get("/workflows/overview", { params });
export const getWorkflowStudentsApi = (params = {}) =>
  http.get("/workflows/students", { params });
export const getStudentArchiveApi = (userId) =>
  http.get(`/workflows/archives/${userId}`);
export const updateStudentArchiveApi = (userId, data) =>
  http.put(`/workflows/archives/${userId}`, data);
export const getWarningTasksApi = (params = {}) =>
  http.get("/workflows/tasks", { params });
export const createWarningTaskApi = (data) =>
  http.post("/workflows/tasks", data);
export const updateWarningTaskApi = (taskId, data) =>
  http.put(`/workflows/tasks/${taskId}`, data);
export const getInterventionRecordsApi = (params = {}) =>
  http.get("/workflows/interventions", { params });
export const createInterventionRecordApi = (data) =>
  http.post("/workflows/interventions", data);
export const bootstrapWorkflowApi = () =>
  http.post("/workflows/bootstrap");
