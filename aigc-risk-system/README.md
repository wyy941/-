# 大学生 AIGC 技术依赖风险评估系统

本项目依据《大学生AIGC技术依赖风险评估系统设计与实现-开题报告》实现，面向毕业设计演示场景，提供一套从样本数据导入、风险量化评估、协同过滤修正、可视化看板到评估报告生成的完整闭环。

当前版本已升级为更完整的“论文答辩版”：

- 指标体系由基础版 6 项扩展为 10 项
- 评估模型由简单加权求和升级为“专家权重 + 熵权 + 模糊综合评价 + 相似群体修正”
- 前端页面改为动态指标驱动，后续继续扩展指标时无需重写表单

## 1. 技术栈

- 后端：`Flask`、`Flask-RESTful`、`Flask-SQLAlchemy`
- 数据处理：`Pandas`、`NumPy`
- 风险评估：专家权重 + 熵权融合 + 模糊综合评价
- 评估修正：基于余弦相似度的协同过滤
- 缓存：`Redis`（无 Redis 时自动降级）
- 前端：`Vue 3`、`Element Plus`、`ECharts`、`Axios`、`Vite`
- 默认存储：`SQLite`
- 可扩展存储：`MySQL`

## 2. 已实现功能

### 2.1 数据采集与预处理

- 支持读取 `sample_data/aigc_usage_data.csv`
- 支持样本数据预览
- 支持一键导入示例数据
- 导入时自动执行去重、缺失值处理和异常值裁剪

### 2.2 风险评估

- 六项核心指标风险评分
- 十项高级评估指标
- 指标权重可维护
- 生成原始风险得分
- 结合历史相似样本生成修正得分
- 自动划分低风险 / 中风险 / 高风险
- 返回个体改进建议
- 输出模糊隶属度、维度分析和重点风险因子

### 2.3 可视化展示

- 风险总览看板
- 按角色、年级、专业、班级、风险等级筛选
- 风险等级分布图
- 维度均值概览
- 指标平均得分柱状图
- 群体评估趋势图
- 重点风险用户列表
- 个体历史趋势图
- 个体风险雷达图

### 2.4 报告生成

- 支持查看单次评估结构化报告
- 支持报告导出为 JSON
- 报告内容包括：
  - 用户信息
- 原始得分
- 修正得分
- 风险等级
- 模糊隶属度
- 四维度分析
- 指标详情
- 关键风险点
- 改进建议

## 3. 项目结构

```text
aigc-risk-system/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── extensions.py
│   ├── requirements.txt
│   ├── models/
│   ├── resources/
│   ├── services/
│   ├── utils/
│   └── scripts/
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
├── sample_data/
│   └── aigc_usage_data.csv
└── README.md
```

## 4. 后端启动

### 4.1 安装依赖

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4.2 可选环境变量

```bash
set DATABASE_URL=mysql+pymysql://root:123456@127.0.0.1:3306/aigc_risk
set REDIS_URL=redis://127.0.0.1:6379/0
set SECRET_KEY=your-secret-key
```

不配置时默认使用 `SQLite`，可直接演示。

### 4.3 启动服务

```bash
python app.py
```

默认地址：

- 后端首页：`http://127.0.0.1:5000`
- API 根路径：`http://127.0.0.1:5000/api`

### 4.4 初始化演示数据

```bash
python scripts/seed_data.py
```

初始化内容：

- 默认用户：`admin / 123456`
- 默认学生：`student1 / 123456`
- 默认评估指标
- 样本 CSV 导入后的评估记录

## 5. 前端启动

```bash
cd frontend
npm install
npm run dev
```

默认地址：

- 前端页面：`http://127.0.0.1:5173`

## 6. 主要页面

- `/login`：登录页
- `/dashboard`：风险总览看板
- `/assessment`：个体风险评估页
- `/indicators`：指标管理页
- `/data-center`：数据中心
- `/report`：评估报告页

## 7. 核心接口

### 7.1 用户与认证

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users`

### 7.2 指标管理

- `GET /api/indicators`
- `POST /api/indicators`
- `PUT /api/indicators/<id>`
- `DELETE /api/indicators/<id>`

### 7.3 风险评估

- `POST /api/assessments/evaluate`
- `GET /api/assessments/history/<user_id>`

### 7.4 看板分析

- `GET /api/dashboard/overview`
- `GET /api/dashboard/trend/<user_id>`

支持的筛选参数：

- `role`
- `grade`
- `major`
- `class_name`
- `risk_level`

### 7.5 数据中心

- `GET /api/data/sample-preview`
- `POST /api/data/import-sample`

### 7.6 报告中心

- `GET /api/reports/latest/<user_id>`
- `GET /api/reports/assessment/<assessment_id>`
- `GET /api/reports/assessment/<assessment_id>/export`

## 8. 默认评估维度

系统默认使用以下十个评估标准：

1. 使用频率
2. 场景泛化程度
3. 学业替代程度
4. 独立思考弱化
5. 结果核验不足
6. 批判判断弱化
7. 学术诚信风险
8. 隐私与数据安全风险
9. 社交协作替代
10. 情绪依赖程度

分值越高表示风险越高。

## 9. 适合答辩的演示流程

1. 启动后端与前端
2. 进入“数据中心”，导入示例数据
3. 打开“风险总览看板”，演示筛选与群体趋势
4. 进入“个体评估”，选择学生并提交评估
5. 打开“评估报告”，展示关键风险点与改进建议
6. 进入“指标管理”，演示指标可配置能力

## 10. 后续可扩展方向

- 接入真实问卷数据或开源教育数据集
- 导出 PDF / Word 报告
- 增加管理员 / 教师 / 学生多角色权限控制
- 增加日志审计与系统配置页
- 增加定时任务生成日报
- 使用 `MySQL + Redis + Docker + Nginx` 完成部署
