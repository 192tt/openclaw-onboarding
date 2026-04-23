# OpenClaw 数字身份注册测试平台

一套完整的对话式注册 + 数字身份卡片生成测试环境。

## 快速启动

### 方式一：Docker（推荐）

```bash
cd openclaw-test-platform
docker-compose up -d
```

访问 http://124.220.221.242:8000

### 方式二：本地运行

```bash
cd openclaw-test-platform/backend
pip install -r requirements.txt
python main.py
```

访问 http://localhost:8000

## 功能

- 对话式信息采集（7项基础 + 6项角色专属）
- 四种角色：创业者、投资人、孵化器、企业需求方
- 自动生成智能标签
- 6行精简数字身份卡片
- 数据持久化（SQLite）
- REST API

## API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 发送消息，返回对话状态和卡片 |
| `/api/restart` | POST | 重新开始注册流程 |
| `/api/cards` | GET | 获取所有卡片列表 |
| `/api/cards/{id}` | GET | 获取单张卡片详情 |

## 部署到服务器

```bash
scp -r openclaw-test-platform root@124.220.221.242:/opt/
ssh root@124.220.221.242
cd /opt/openclaw-test-platform
docker-compose up -d
```
