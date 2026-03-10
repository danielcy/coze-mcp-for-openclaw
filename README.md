# Coze MCP Server For OpenClaw

这是一个基于MCP（Model Context Protocol）标准的服务器，可以将指定的Coze Workspace中的工作流暴露为MCP工具，主要提供给OpenClaw进行使用，也可以给其他支持MCP协议的AI客户端调用。

本项目旨在通过Coze的工作流提供一种简单、高效的给OpenClaw提供额外技能的方式。相较于直接安装OpenClaw技能，使用Coze工作流进行技能管理主要有以下优势：

1. **无环境依赖**：目前OpenClaw有很多技能涉及到跑Python脚本或其他脚本，如果要使用这些技能，不可避免地会碰到环境依赖问题，而使用Coze来支持技能，仅需要使用http调用即可，无需对环境进行配置
2. **技能测试简单**：对于OpenClaw来说，如果要测试某个技能是否可用，要么是得让OpenClaw直接使用该技能，要么是得阅读并跟着技能的内容一步一步操作来测试，整体较为复杂。而通过Coze工作流，用户仅需在Coze中测试该工作流，即可验证该技能是否可用。

## Coze配置说明
使用本项目前，请先在Coze中创建一个独立的工作空间，并获取其ID，本项目会扫描该空间下所有的已发布的工作流作为OpenClaw的额外技能。

**注意**：请务必为每个工作流，以及它的每个输入输出都配置上描述文本，方便调用方能明确地知道什么时候进行调用以及如何调用


## 功能特性

- 基于MCP标准协议实现，兼容所有支持MCP的AI客户端
- 自动获取指定Workspace中的所有已发布工作流
- 将每个工作流作为一个MCP工具暴露
- 支持工作流列表查询、详情查看和执行
- 提供工作流缓存刷新功能
- 返回调试URL和资源使用情况
- 提供可快速新增/更新/删除技能的脚本，方便OpenClaw用户管理技能

## 快速开始

### 1. 安装uv

如果你还没有安装uv，请先安装：

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 创建虚拟环境并安装依赖

```bash
uv venv
uv sync
```

### 3. 配置环境变量

复制 `.env.example` 文件为 `.env`，并填写以下配置：

```
# Coze API配置
COZE_API_KEY=your_coze_api_key_here
WORKSPACE_ID=your_workspace_id_here
OPENCLAW_SKILLS_DIR=~/.openclaw/skills
```

- `COZE_API_KEY`：你的Coze API密钥（个人访问令牌）
- `WORKSPACE_ID`：你想要加载工作流的Workspace ID
- `OPENCLAW_SKILLS_DIR`：OpenClaw技能目录

### 4. 运行MCP服务器

```bash
uv run coze-mcp
```

或者直接运行Python文件：

```bash
uv run python coze_mcp.py
```

## MCP工具说明

本服务器提供以下MCP工具：

### 1. list_workflows

列出工作空间中所有可用的工作流。

**返回示例:**
```
找到 3 个已发布的工作流：

- **workflow_1** (ID: 73505836754923***)
  描述: 这是一个示例工作流

- **workflow_2** (ID: 73505836754924***)
  描述: 另一个工作流
```

### 2. run_workflow_by_name

根据工作流名称执行工作流。

**参数:**
- `workflow_name` (必需): 工作流名称
- `parameters` (可选): 工作流输入参数，JSON字符串格式

**示例:**
```json
{
  "workflow_name": "my_workflow",
  "parameters": "{\"input\": \"Hello World\"}"
}
```

**返回示例:**
```
工作流执行成功！

**执行结果:**
{
  "output": "处理结果"
}


**资源使用:**
- 输入Token: 50
- 输出Token: 100
- 总Token: 150

**调试链接:** https://www.coze.cn/work_flow?execute_id=xxx
```

### 3. get_workflow_info

获取指定工作流的详细信息。

**参数:**
- `workflow_name` (必需): 工作流名称

**返回示例:**
```
**工作流信息**

- **名称:** my_workflow
- **ID:** 73505836754923***
- **描述:** 这是一个示例工作流
- **图标:** https://example.com/icon.png
- **创建时间:** 1752060786
- **更新时间:** 1752060827
```

### 4. refresh_workflows

刷新工作流列表缓存。

**返回示例:**
```
成功刷新工作流列表，共加载 10 个工作流。
```

## 在AI客户端中配置

### OpenClaw

通过 mcporter 配置 OpenClaw，在配置文件中添加以下内容：

```json
{
  "coze-mcp": {
    "baseUrl": "http://localhost:33123/mcp"
  }
}
```

确保 Coze MCP 服务器正在运行，OpenClaw 将自动连接到该服务。

## 技能生成脚本

本项目提供了一个脚本，用于为所有已发布的工作流生成 OpenClaw 技能文件。

### 环境变量配置

在 `.env` 文件中添加以下配置：

```
OPENCLAW_SKILLS_DIR=C:\Users\你的用户名\.openclaw\skills
```

- `OPENCLAW_SKILLS_DIR`：技能文件存放目录，脚本会在此目录下为每个工作流创建对应的技能文件夹

### 运行脚本

```bash
# 创建新技能（已存在的文件夹会跳过）
uv run python script/make_skills.py

# 更新已存在的技能文件
uv run python script/make_skills.py --update

# 删除指定技能（支持逗号分隔多个）
uv run python script/make_skills.py --remove workflow1,workflow2

# 删除所有技能
uv run python script/make_skills.py --remove all
```

### 脚本功能

1. 从 `.env` 读取 `OPENCLAW_SKILLS_DIR` 环境变量，如未配置则报错退出
2. 调用 Coze API 获取所有已发布的工作流及其参数详情
3. 为每个工作流在技能目录下创建以工作流名称命名的文件夹
4. 使用 `skill_template.md` 模板生成 `SKILL.md` 文件

### 参数说明

| 参数 | 说明 |
|------|------|
| 无参数 | 创建新技能，已存在的文件夹会跳过 |
| `--update` | 更新已存在的技能文件夹内容 |
| `--remove NAMES` | 删除指定的技能文件夹，支持逗号分隔多个名称，或使用 `all` 删除全部（删除前需二次确认） |

## 项目结构

```
coze-mcp/
├── coze_mcp.py          # MCP服务器主文件
├── pyproject.toml       # 项目配置文件
├── .python-version      # Python版本配置
├── .env                 # 环境变量配置
├── .env.example         # 环境变量示例
├── skill_template.md    # 技能文件模板
├── script/
│   └── make_skills.py   # 技能生成脚本
└── README.md            # 项目说明文档
```

## 技术栈

- Python 3.12+
- MCP Python SDK (mcp)
- httpx (异步HTTP客户端)
- python-dotenv (环境变量管理)
- uv (包管理工具)

## API说明

### 获取工作流列表

- **接口**: `GET https://api.coze.cn/v1/workflows`
- **权限**: `listWorkflow`
- **参数**:
  - `workspace_id`: 工作空间ID（必选）
  - `page_num`: 页码（必选，最小值为1）
  - `page_size`: 每页数量（可选，1-30，默认10）
  - `publish_status`: 发布状态（可选，默认`published_online`）

### 执行工作流

- **接口**: `POST https://api.coze.cn/v1/workflow/run`
- **权限**: `run`
- **参数**:
  - `workflow_id`: 工作流ID（必选）
  - `parameters`: 工作流输入参数（可选，JSON对象）
  - `bot_id`: 关联的智能体ID（可选）
  - `is_async`: 是否异步执行（可选，默认false）

## 注意事项

1. 确保你的Coze API密钥具有访问指定Workspace的权限
2. 确保API密钥开通了 `listWorkflow` 和 `run` 权限
3. 服务启动时会自动获取已发布的工作流列表，并存入内存
4. 如果Workspace中的工作流发生变化，可以使用 `refresh_workflows` 工具刷新缓存
5. 只有已发布的工作流才会被加载到服务中
6. 工作流执行超时时间为10分钟，建议执行时间控制在5分钟以内
7. 可以通过返回的 `debug_url` 查看工作流执行的详细过程

## 参考文档

- [MCP官方文档](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [查询工作流列表](https://www.coze.cn/open/docs/developer_guides/get_workflow_list)
- [执行工作流](https://www.coze.cn/open/docs/developer_guides/workflow_run)
