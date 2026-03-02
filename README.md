# 电商推荐系统（Ecommerce Recommendation）

## 项目简介
本项目是一个基于 Flask + SQLite 的电商/图书推荐系统，包含数据采集、推荐算法、用户行为记录与后台可视化看板。

## 本次更新（2026-02）
已完成以下新增与修复：

1. 首页推荐模块升级
- 首页新增 4 个推荐区块：`热门推荐`、`新品推荐`、`个性化推荐`、`相似推荐`。
- 当新品数据缺失时，自动回退到“最新入库商品”。
- 当个性化或相似推荐缺失时，自动回退到热门推荐，避免空页面。

2. 图书分类修复
- 新增统一分类解析逻辑，支持以下分类字段格式：
  - JSON 数组（如 `[
"玄幻", "武侠"
]`）
  - 普通字符串（如 `玄幻`）
  - 分隔符字符串（如 `玄幻|武侠`、`玄幻/武侠`、`玄幻,武侠`）
- 修复分类筛选与分类展示不一致问题。
- `all_products` 页面新增目录式分类导航（类似标签目录）。

3. 可视化优化
- 重构管理后台看板布局为响应式网格。
- 图表新增空数据占位，避免接口无数据时页面空白。
- 图表支持窗口尺寸变化自动重绘。
- 分类收入统计改为按“拆分后分类”聚合，避免脏分类值污染图表。

4. 稳定性修复
- 重写推荐入口模块，清理不稳定输出，降低首页推荐链路异常风险。

## 主要功能
- 用户注册/登录
- 用户行为记录（浏览、点击、购买等）
- 收藏与评论
- 推荐算法：热门推荐、协同过滤、内容相似推荐
- 后台管理：商品、用户、订单、操作日志
- 数据分析看板：趋势、热销、分类收入、情感统计

## 项目结构
```text
ecommerce_recommendation/
├─ web/                    # Flask Web 层（路由、模板、静态资源）
├─ recommendation/         # 推荐算法与统一推荐入口
├─ database/               # 数据库初始化与 CRUD
├─ analytics/              # 可视化看板数据接口
├─ data_processing/        # 清洗、特征工程、情感处理
├─ crawler/                # 爬虫模块
├─ scripts/                # 辅助脚本
└─ ecommerce.db            # SQLite 数据库
```

## 安装与运行
1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 启动服务
```bash
python -m web.app
```

3. 访问页面
- 前台首页：`http://127.0.0.1:5000/`
- 商品列表：`http://127.0.0.1:5000/all_products`
- 管理后台登录：`http://127.0.0.1:5000/admin/login`
- 管理看板：`http://127.0.0.1:5000/admin/dashboard`

## 关键接口
- `GET /`：首页四类推荐
- `GET /all_products`：全部商品与分类筛选
- `GET /product/<product_id>`：相似商品页
- `GET /api/products`：商品筛选分页 API
- `GET /api/recommend/<user_id>`：用户推荐 API
- `GET /api/analytics/*`：后台可视化数据接口

## 快速验证
```bash
python -m compileall web/app.py recommendation/recommender.py analytics/analytics.py
python scripts/validate_templates.py
```

若以上命令通过，说明核心后端与模板结构可正常解析。
