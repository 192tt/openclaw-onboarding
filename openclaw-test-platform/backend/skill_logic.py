"""Skill 核心逻辑：对话流程管理 + 卡片生成"""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

# ============ 角色定义 ============

ROLES = {
    "founder": {
        "name": "创业者 / 一人公司",
        "label": "创业者",
        "fields": [
            {"key": "skills", "label": "核心 Skill / 主营业务", "type": "text", "placeholder": "可填 1-3 项"},
            {"key": "stage", "label": "项目阶段", "type": "select", "options": ["想法", "原型", "上线", "盈利", "规模化"]},
            {"key": "funding", "label": "当前融资需求", "type": "text", "placeholder": "无 / 天使轮 / 具体额度"},
            {"key": "needs", "label": "急需资源", "type": "multi_select", "options": ["技术", "资金", "渠道", "供应链", "法务财税", "其他"]},
            {"key": "output", "label": "可对外输出能力", "type": "text", "placeholder": "你能提供什么 Skill"},
            {"key": "highlights", "label": "项目亮点关键词", "type": "text", "placeholder": "3-5 个关键词"},
        ]
    },
    "investor": {
        "name": "投资人 / 天使机构",
        "label": "投资人",
        "fields": [
            {"key": "stage", "label": "投资阶段", "type": "select", "options": ["天使", "早期", "成长期", "全阶段"]},
            {"key": "track", "label": "主攻赛道", "type": "text"},
            {"key": "amount", "label": "单笔可投金额 / 基金规模", "type": "text"},
            {"key": "preference", "label": "偏好项目类型", "type": "multi_select", "options": ["AI", "技术", "消费", "产业", "其他"]},
            {"key": "post_investment", "label": "可提供投后资源", "type": "multi_select", "options": ["导师", "渠道", "政策", "对接", "其他"]},
            {"key": "status", "label": "近期投资状态", "type": "select", "options": ["活跃", "观望"]},
        ]
    },
    "incubator": {
        "name": "孵化器 / 加速器主理人",
        "label": "孵化器",
        "fields": [
            {"key": "type", "label": "空间类型", "type": "select", "options": ["综合孵化器", "垂直赛道孵化器", "产业园区"]},
            {"key": "track", "label": "聚焦赛道", "type": "text"},
            {"key": "policy", "label": "可提供政策", "type": "multi_select", "options": ["免租", "补贴", "投融资对接", "其他"]},
            {"key": "services", "label": "配套服务", "type": "multi_select", "options": ["办公空间", "导师", "法务财税", "其他"]},
            {"key": "location", "label": "所在具体区位", "type": "text"},
            {"key": "requirements", "label": "招募项目要求", "type": "text", "placeholder": "阶段、赛道等"},
        ]
    },
    "enterprise": {
        "name": "企业需求方",
        "label": "企业需求方",
        "fields": [
            {"key": "industry", "label": "企业所属行业 / 主营业务", "type": "text"},
            {"key": "need_type", "label": "核心需求类型", "type": "select", "options": ["技术采购", "服务外包", "项目合作", "产品定制", "生态联动"]},
            {"key": "budget", "label": "需求预算区间", "type": "text"},
            {"key": "scale", "label": "合作规模", "type": "select", "options": ["短期项目", "长期战略合作", "年度采购"]},
            {"key": "scenario", "label": "需求应用场景", "type": "select", "options": ["内部升级", "对外业务", "市场拓展"]},
            {"key": "contact_role", "label": "对接负责人身份", "type": "select", "options": ["企业负责人", "采购总监", "商务合作负责人"]},
        ]
    }
}

# ============ 基础信息字段 ============

BASE_FIELDS = [
    {"key": "nickname", "label": "平台昵称", "type": "text"},
    {"key": "avatar", "label": "头像", "type": "text", "placeholder": "图片URL或描述"},
    {"key": "role", "label": "核心身份", "type": "select", "options": list(ROLES.keys())},
    {"key": "city", "label": "所在城市/区域", "type": "text"},
    {"key": "slogan", "label": "一句话价值介绍", "type": "text", "placeholder": "建议20字内"},
    {"key": "tracks", "label": "关注赛道 / 行业领域", "type": "text", "placeholder": "多选用逗号分隔"},
    {"key": "coop_types", "label": "希望的合作类型", "type": "multi_select", "options": ["资源置换", "投融资", "业务合作", "孵化入驻", "技能对接"]},
]

# ============ 对话流程管理 ============

@dataclass
class SessionState:
    session_id: str
    step: str = "welcome"  # welcome -> base_{i} -> role_{i} -> confirm -> done
    data: Dict[str, Any] = field(default_factory=dict)
    role_data: Dict[str, Any] = field(default_factory=dict)
    base_index: int = 0
    role_index: int = 0
    
    def to_dict(self):
        return asdict(self)

# 内存存储 session（生产环境应使用 Redis）
_sessions: Dict[str, SessionState] = {}

def get_session(sid: str) -> Optional[SessionState]:
    return _sessions.get(sid)

def create_session(sid: str) -> SessionState:
    _sessions[sid] = SessionState(session_id=sid)
    return _sessions[sid]

def save_session(state: SessionState):
    _sessions[state.session_id] = state

# ============ 消息生成 ============

def get_welcome_message() -> Dict:
    return {
        "type": "text",
        "content": "欢迎加入！我是你的数字身份助手 🎴\n\n接下来我会用对话方式帮你创建一张「数字身份卡片」，用于平台内的资源匹配和合作对接。\n\n全程约 3-5 分钟，随时可以暂停。准备好了吗？",
        "options": [{"label": "准备好了，开始", "value": "start"}, {"label": "稍后再说", "value": "pause"}]
    }

def get_base_field_message(field_idx: int) -> Dict:
    field = BASE_FIELDS[field_idx]
    msg = f"【{field['label']}】\n"
    
    if field["key"] == "role":
        msg += "请选择你的核心身份：\n"
        for i, (k, v) in enumerate(ROLES.items(), 1):
            msg += f"{i}. {v['name']}\n"
        msg += "\n请回复数字 1-4"
        return {"type": "text", "content": msg.strip(), "options": [
            {"label": v["name"], "value": k} for k, v in ROLES.items()
        ]}
    
    if field["key"] == "coop_types":
        msg += "可多选，用逗号分隔"
        return {"type": "text", "content": msg.strip(), "options": [
            {"label": o, "value": o} for o in field.get("options", [])
        ]}
    
    if "placeholder" in field:
        msg += f"（{field['placeholder']}）"
    
    return {"type": "text", "content": msg.strip()}

def get_role_field_message(role: str, field_idx: int) -> Dict:
    field = ROLES[role]["fields"][field_idx]
    msg = f"【{field['label']}】"
    
    if field.get("type") == "select":
        msg += "\n请选择："
        for i, opt in enumerate(field["options"], 1):
            msg += f"\n{i}. {opt}"
        return {"type": "text", "content": msg.strip(), "options": [
            {"label": o, "value": o} for o in field["options"]
        ]}
    
    if field.get("type") == "multi_select":
        msg += "\n可多选："
        for opt in field["options"]:
            msg += f"\n· {opt}"
        return {"type": "text", "content": msg.strip(), "options": [
            {"label": o, "value": o} for o in field["options"]
        ]}
    
    if "placeholder" in field:
        msg += f"\n（{field['placeholder']}）"
    
    return {"type": "text", "content": msg.strip()}

def get_summary(state: SessionState) -> str:
    data = state.data
    role = data.get("role", "")
    role_info = ROLES.get(role, {})
    
    lines = ["📋 信息汇总", "请确认是否有误：", ""]
    
    # 基础信息
    for field in BASE_FIELDS:
        val = data.get(field["key"], "未填写")
        if field["key"] == "role":
            val = role_info.get("name", val)
        lines.append(f"· {field['label']}：{val}")
    
    # 角色专属
    if role and state.role_data:
        lines.append("")
        lines.append(f"【{role_info.get('name', '')} 专属信息】")
        for field in role_info.get("fields", []):
            val = state.role_data.get(field["key"], "未填写")
            lines.append(f"· {field['label']}：{val}")
    
    return "\n".join(lines)

def get_confirm_message(state: SessionState) -> Dict:
    return {
        "type": "summary",
        "content": get_summary(state),
        "options": [
            {"label": "✅ 确认无误，生成卡片", "value": "confirm"},
            {"label": "✏️ 修改信息", "value": "edit"}
        ]
    }

# ============ 标签生成 ============

def generate_tags(data: Dict, role_data: Dict, role: str) -> List[Dict]:
    tags = []
    
    # 领域标签：从赛道提取
    tracks = data.get("tracks", "")
    if tracks:
        for t in tracks.replace("，", ",").split(","):
            t = t.strip()
            if t:
                tags.append({"type": "domain", "text": f"#{t}"})
    
    # Skill 标签：从核心能力提取
    skill_sources = []
    if role == "founder":
        skill_sources = [role_data.get("skills", ""), role_data.get("output", "")]
    elif role == "investor":
        skill_sources = [role_data.get("track", ""), data.get("tracks", "")]
    elif role == "incubator":
        skill_sources = [role_data.get("services", "")]
    elif role == "enterprise":
        skill_sources = [role_data.get("industry", "")]
    
    for src in skill_sources:
        for s in str(src).replace("，", ",").split(","):
            s = s.strip()
            if s and len(s) <= 10:
                tags.append({"type": "skill", "text": f"#{s}"})
    
    # 需求标签
    need_sources = []
    if role == "founder":
        need_sources = [role_data.get("needs", ""), role_data.get("funding", "")]
    elif role == "investor":
        need_sources = ["找项目"]
    elif role == "incubator":
        need_sources = ["招募项目"]
    elif role == "enterprise":
        need_sources = [role_data.get("need_type", "")]
    
    for src in need_sources:
        for s in str(src).replace("，", ",").split(","):
            s = s.strip()
            if s and len(s) <= 10:
                tags.append({"type": "need", "text": f"#找{s}" if not s.startswith("找") else f"#{s}"})
    
    # 匹配度标签
    tags.append({"type": "match", "text": "#高匹配"})
    tags.append({"type": "match", "text": "#资源互补"})
    
    # 去重
    seen = set()
    unique_tags = []
    for t in tags:
        key = (t["type"], t["text"])
        if key not in seen:
            seen.add(key)
            unique_tags.append(t)
    
    return unique_tags[:10]  # 最多10个标签

# ============ 卡片生成 ============

def generate_card(state: SessionState) -> Dict:
    data = state.data
    role = data.get("role", "")
    role_info = ROLES.get(role, {})
    role_data = state.role_data
    tags = generate_tags(data, role_data, role)
    
    # 头像（默认 emoji）
    avatar = data.get("avatar", "")
    if not avatar or not avatar.startswith("http"):
        avatar_emoji = {"founder": "🚀", "investor": "💰", "incubator": "🏢", "enterprise": "🏭"}.get(role, "👤")
    else:
        avatar_emoji = avatar
    
    # 第4行：核心 Skill / 能力 / 投资方向
    row4 = ""
    if role == "founder":
        row4 = f"⚡ 核心 Skill：{role_data.get('skills', '')} | 阶段：{role_data.get('stage', '')}"
    elif role == "investor":
        row4 = f"⚡ 投资方向：{role_data.get('track', '')} | 阶段：{role_data.get('stage', '')}"
    elif role == "incubator":
        row4 = f"⚡ 空间：{role_data.get('type', '')} | 聚焦：{role_data.get('track', '')}"
    elif role == "enterprise":
        row4 = f"⚡ 行业：{role_data.get('industry', '')} | 需求：{role_data.get('need_type', '')}"
    
    # 第5行：我需要什么 / 我能提供什么
    row5 = ""
    if role == "founder":
        row5 = f"🔍 急需：{role_data.get('needs', '')} | 💎 可输出：{role_data.get('output', '')}"
    elif role == "investor":
        row5 = f"🔍 寻找：{role_data.get('preference', '')} | 💎 投后：{role_data.get('post_investment', '')}"
    elif role == "incubator":
        row5 = f"🔍 招募：{role_data.get('requirements', '')} | 💎 政策：{role_data.get('policy', '')}"
    elif role == "enterprise":
        row5 = f"🔍 预算：{role_data.get('budget', '')} | 💎 规模：{role_data.get('scale', '')}"
    
    card = {
        "nickname": data.get("nickname", ""),
        "avatar": avatar_emoji,
        "role": role,
        "role_label": role_info.get("label", ""),
        "city": data.get("city", ""),
        "tracks": data.get("tracks", ""),
        "slogan": data.get("slogan", ""),
        "row4": row4,
        "row5": row5,
        "coop_types": data.get("coop_types", ""),
        "tags": tags,
        "role_data": role_data,
    }
    
    return card

# ============ 流程处理 ============

def process_message(session_id: str, user_input: str) -> Dict:
    state = get_session(session_id)
    if not state:
        state = create_session(session_id)
    
    user_input = user_input.strip()
    
    # 欢迎阶段
    if state.step == "welcome":
        if user_input in ["start", "准备好了，开始", "开始", "1", "准备好了"]:
            state.step = "base_0"
            state.base_index = 0
            save_session(state)
            return {"messages": [get_base_field_message(0)], "progress": 5}
        else:
            return {"messages": [{
                "type": "text",
                "content": "好的，随时可以回复「开始」继续注册。"
            }], "progress": 0}
    
    # 基础信息采集阶段
    if state.step.startswith("base_"):
        idx = state.base_index
        field = BASE_FIELDS[idx]
        
        # 处理身份选择
        if field["key"] == "role":
            role_map = {str(i+1): k for i, k in enumerate(ROLES.keys())}
            if user_input in role_map:
                user_input = role_map[user_input]
            if user_input not in ROLES:
                return {"messages": [{"type": "text", "content": "请选择 1-4 对应的身份"}], "progress": int((idx / (len(BASE_FIELDS) + 6)) * 100)}
        
        # 保存数据
        state.data[field["key"]] = user_input
        
        # 进入下一步
        idx += 1
        state.base_index = idx
        
        if idx < len(BASE_FIELDS):
            state.step = f"base_{idx}"
            save_session(state)
            progress = int((idx / (len(BASE_FIELDS) + len(ROLES.get(state.data.get("role", ""), {}).get("fields", [])))) * 100)
            return {"messages": [get_base_field_message(idx)], "progress": progress}
        else:
            # 基础信息完成，进入角色专属
            role = state.data.get("role", "")
            role_fields = ROLES.get(role, {}).get("fields", [])
            if role_fields:
                state.step = "role_0"
                state.role_index = 0
                save_session(state)
                return {"messages": [get_role_field_message(role, 0)], "progress": 50}
            else:
                state.step = "confirm"
                save_session(state)
                return {"messages": [get_confirm_message(state)], "progress": 90}
    
    # 角色专属信息采集阶段
    if state.step.startswith("role_"):
        role = state.data.get("role", "")
        role_fields = ROLES.get(role, {}).get("fields", [])
        idx = state.role_index
        field = role_fields[idx]
        
        # 保存数据
        state.role_data[field["key"]] = user_input
        
        idx += 1
        state.role_index = idx
        
        if idx < len(role_fields):
            state.step = f"role_{idx}"
            save_session(state)
            total_fields = len(BASE_FIELDS) + len(role_fields)
            progress = int(((len(BASE_FIELDS) + idx) / total_fields) * 100)
            return {"messages": [get_role_field_message(role, idx)], "progress": progress}
        else:
            state.step = "confirm"
            save_session(state)
            return {"messages": [get_confirm_message(state)], "progress": 90}
    
    # 确认阶段
    if state.step == "confirm":
        if user_input in ["confirm", "确认", "确认无误，生成卡片", "✅ 确认无误，生成卡片"]:
            card = generate_card(state)
            state.step = "done"
            save_session(state)
            return {
                "messages": [{
                    "type": "text",
                    "content": "✅ 你的数字身份卡片已生成！\n\n卡片信息将同步至平台，其他用户可通过匹配算法发现你。\n\n如需更新卡片信息，随时重新运行本流程即可。"
                }],
                "progress": 100,
                "card": card,
                "done": True
            }
        elif user_input in ["edit", "修改", "修改信息", "✏️ 修改信息"]:
            state.step = "base_0"
            state.base_index = 0
            state.data = {}
            state.role_data = {}
            save_session(state)
            return {
                "messages": [
                    {"type": "text", "content": "好的，我们重新开始采集信息。"},
                    get_base_field_message(0)
                ],
                "progress": 5
            }
        else:
            return {"messages": [get_confirm_message(state)], "progress": 90}
    
    # 已完成
    if state.step == "done":
        return {
            "messages": [{
                "type": "text",
                "content": "你的卡片已生成完毕。回复「重新开始」可以重新注册。"
            }],
            "progress": 100,
            "done": True
        }
    
    return {"messages": [{"type": "text", "content": "抱歉，我不太理解。请按提示操作。"}]}

def restart_session(session_id: str) -> Dict:
    if session_id in _sessions:
        del _sessions[session_id]
    state = create_session(session_id)
    return {
        "messages": [get_welcome_message()],
        "progress": 0,
        "done": False
    }
