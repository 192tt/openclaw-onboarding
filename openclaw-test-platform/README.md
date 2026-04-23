# OpenClaw 数字身份注册平台

一套完整的对话式注册 + 数字身份卡片生成系统。

包含：
- **Skill 源码**（Kimi Code CLI + OpenClaw 双版本）
- **前后端测试平台**（对话式注册页面 + 卡片展示 + REST API）

---

## 在线演示

**测试平台已部署**：http://124.220.221.242:8000

---

## 目录结构

```
├── openclaw-onboarding/              # Kimi Code CLI 版 Skill
│   ├── SKILL.md
│   └── references/
│       ├── roles.md
│       └── card-template.md
│
├── openclaw-onboarding-openclaw/     # OpenClaw 兼容版 Skill
│   ├── SKILL.md
│   └── references/
│       ├── roles.md
│       └── card-template.md
│
└── openclaw-test-platform/           # 前后端测试平台
    ├── frontend/                     # HTML/CSS/JS 前端
    ├── backend/                      # FastAPI + SQLite 后端
    ├── Dockerfile
    └── docker-compose.yml
```

---

## Skill 使用方式

### 方式一：OpenClaw CLI 安装（推荐）

```bash
# 从 GitHub 安装 OpenClaw 兼容版
openclaw skills install @192tt/openclaw-onboarding

# 或指定子目录安装
openclaw add @192tt/openclaw-onboarding:openclaw-onboarding-openclaw
```

安装完成后，在 OpenClaw 对话中输入以下任意话术即可触发：
- `/openclaw_onboarding`
- `开始注册`
- `填写信息`
- `生成卡片`

### 方式二：手动复制到 Skill 目录

```bash
# 克隆仓库
git clone https://github.com/192tt/openclaw-onboarding.git

# 复制到 OpenClaw skills 目录
cp -r openclaw-onboarding/openclaw-onboarding-openclaw ~/.openclaw/skills/

# 重启 OpenClaw gateway
openclaw gateway restart
```

### 方式三：Kimi Code CLI 使用

```bash
# 下载 .skill 文件后导入 Kimi Code CLI
# 或将 openclaw-onboarding/ 目录放到项目的 .agents/skills/ 下
```

---

## 测试平台部署

### Docker（推荐）

```bash
cd openclaw-test-platform
docker-compose up -d
```

访问 http://localhost:8000

### 本地运行

```bash
cd openclaw-test-platform/backend
pip install -r requirements.txt
python main.py
```

---

## 功能特性

- **对话式信息采集**：7项基础信息 + 6项角色专属信息
- **四种角色**：创业者、投资人、孵化器主理人、企业需求方
- **自动生成智能标签**：领域标签、Skill 标签、需求标签、匹配度标签
- **6行精简数字身份卡片**：头像 + 昵称 + 身份 + 城市 + 赛道 + Slogan + 核心能力 + 需求/供给 + 合作意向
- **数据持久化**：SQLite 数据库
- **REST API**：支持外部系统集成

---

## API 文档

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 发送消息，返回对话状态和卡片 |
| `/api/restart` | POST | 重新开始注册流程 |
| `/api/cards` | GET | 获取所有卡片列表 |
| `/api/cards/{id}` | GET | 获取单张卡片详情 |

---

## 注册流程

```
欢迎语
  → 平台昵称
  → 头像
  → 核心身份（4选1）
  → 所在城市
  → 一句话 Slogan
  → 关注赛道（多选）
  → 合作类型（多选）
  → 角色专属采集（6项）
  → 信息确认
  → 自动生成标签
  → 输出 6行数字身份卡片
```
