import os
import json
import asyncio
from typing import Any
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP
import httpx

load_dotenv()

COZE_API_KEY = os.getenv("COZE_API_KEY")
WORKSPACE_ID = os.getenv("WORKSPACE_ID")
COZE_API_BASE = "https://api.coze.cn/v1"

mcp = FastMCP("coze-workflows")

workflows_cache: dict[str, dict[str, Any]] = {}

async def get_workflow_list() -> dict[str, dict[str, Any]]:
    """获取工作空间中的所有已发布工作流"""
    global workflows_cache
    
    async with httpx.AsyncClient() as client:
        params = {
            "workspace_id": WORKSPACE_ID,
            "page_num": 1,
            "page_size": 30,
            "publish_status": "published_online"
        }
        
        headers = {
            "Authorization": f"Bearer {COZE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = await client.get(
            f"{COZE_API_BASE}/workflows",
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get workflow list: {response.text}")
        
        result = response.json()
        
        if result.get("code") != 0:
            raise Exception(f"API error: {result.get('msg', 'Unknown error')}")
        
        workflow_dict = {}
        data = result.get("data", {})
        items = data.get("items", [])
        
        for workflow in items:
            workflow_name = workflow.get("workflow_name")
            workflow_id = workflow.get("workflow_id")
            if workflow_name and workflow_id:
                workflow_dict[workflow_name] = {
                    "workflow_id": workflow_id,
                    "workflow_name": workflow_name,
                    "description": workflow.get("description", ""),
                    "icon_url": workflow.get("icon_url", ""),
                    "created_at": workflow.get("created_at", ""),
                    "updated_at": workflow.get("updated_at", "")
                }
        
        workflows_cache = workflow_dict
        return workflow_dict

async def get_workflow_detail(workflow_id: str) -> dict[str, Any]:
    """获取工作流的详细信息，包括输入输出参数"""
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {COZE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = await client.get(
            f"{COZE_API_BASE}/workflows/{workflow_id}",
            headers=headers,
            params={"include_input_output": "true"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get workflow detail: {response.text}")
        
        result = response.json()
        
        if result.get("code") != 0:
            raise Exception(f"API error: {result.get('msg', 'Unknown error')}")
        
        return result.get("data", {})

async def run_workflow(workflow_id: str, parameters: dict[str, Any] = None) -> dict[str, Any]:
    """执行指定的工作流"""
    async with httpx.AsyncClient(timeout=600.0) as client:
        headers = {
            "Authorization": f"Bearer {COZE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "workflow_id": workflow_id,
            "is_async": False
        }

        if type(parameters) == str:
            parameters = json.loads(parameters)
        
        if parameters:
            payload["parameters"] = parameters
        
        response = await client.post(
            f"{COZE_API_BASE}/workflow/run",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to run workflow: {response.text}")
        
        result = response.json()
        
        if result.get("code") != 0:
            raise Exception(f"API error: {result.get('msg', 'Unknown error')}")
        
        return result

def format_parameters(parameters: dict[str, Any]) -> str:
    """格式化参数列表为可读字符串"""
    if not parameters:
        return "无参数"
    
    lines = []
    for param_name, param_info in parameters.items():
        param_type = param_info.get("type", "unknown")
        param_desc = param_info.get("description", "无描述")
        required = param_info.get("required", False)
        
        required_mark = " (必填)" if required else " (可选)"
        lines.append(f"    - `{param_name}` [{param_type}]{required_mark}: {param_desc}")
    
    return "\n".join(lines)

@mcp.tool()
async def list_workflows() -> str:
    """列出工作空间中所有可用的工作流，包括参数列表
    
    Returns:
        工作流列表，包含名称、ID、描述和参数信息
    """
    try:
        workflows = await get_workflow_list()
        
        if not workflows:
            return "当前工作空间中没有已发布的工作流。"
        
        result_lines = [f"找到 {len(workflows)} 个已发布的工作流：\n"]
        
        for name, info in workflows.items():
            desc = info.get("description", "无描述")
            workflow_id = info["workflow_id"]
            
            result_lines.append(f"### {name}")
            result_lines.append(f"- **ID:** {workflow_id}")
            result_lines.append(f"- **描述:** {desc}")
            
            try:
                detail = await get_workflow_detail(workflow_id)
                input_data = detail.get("input", {})
                parameters = input_data.get("parameters", {})
                
                if parameters:
                    result_lines.append(f"- **参数列表:**")
                    result_lines.append(format_parameters(parameters))
                else:
                    result_lines.append(f"- **参数列表:** 无参数")
            except Exception as e:
                result_lines.append(f"- **参数列表:** 获取失败 ({str(e)})")
            
            result_lines.append("")
        
        return "\n".join(result_lines)
    except Exception as e:
        return f"获取工作流列表失败: {str(e)}"

@mcp.tool()
async def refresh_workflows() -> str:
    """刷新工作流列表缓存
    
    Returns:
        刷新结果
    """
    try:
        workflows = await get_workflow_list()
        return f"成功刷新工作流列表，共加载 {len(workflows)} 个工作流。"
    except Exception as e:
        return f"刷新工作流列表失败: {str(e)}"

@mcp.tool()
async def run_workflow_by_name(workflow_name: str, parameters: dict[str, Any] = {}) -> str:
    """根据工作流名称执行工作流
    
    Args:
        workflow_name: 工作流名称
        parameters: 工作流输入参数，JSON字符串格式，例如: {"key": "value"}
    
    Returns:
        工作流执行结果
    """
    try:
        if not workflows_cache:
            await get_workflow_list()
        
        workflow_info = workflows_cache.get(workflow_name)
        if not workflow_info:
            available = ", ".join(workflows_cache.keys()) if workflows_cache else "无"
            return f"未找到名为 '{workflow_name}' 的工作流。\n可用工作流: {available}"
        
        workflow_id = workflow_info["workflow_id"]
        
        try:
            params = parameters
        except json.JSONDecodeError:
            return f"参数格式错误，请提供有效的JSON字符串，例如: {{\"key\": \"value\"}}"

        
        result = await run_workflow(workflow_id, params)
        
        data = result.get("data")
        debug_url = result.get("debug_url", "")
        usage = result.get("usage", {})
        
        output_lines = ["工作流执行成功！\n"]
        
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
                output_lines.append(f"**执行结果:**\n```json\n{json.dumps(parsed_data, ensure_ascii=False, indent=2)}\n```")
            except json.JSONDecodeError:
                output_lines.append(f"**执行结果:**\n{data}")
        else:
            output_lines.append(f"**执行结果:**\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```")
        
        if usage:
            output_lines.append(f"\n**资源使用:**")
            output_lines.append(f"- 输入Token: {usage.get('input_count', 0)}")
            output_lines.append(f"- 输出Token: {usage.get('output_count', 0)}")
            output_lines.append(f"- 总Token: {usage.get('token_count', 0)}")
        
        if debug_url:
            output_lines.append(f"\n**调试链接:** {debug_url}")
        
        return "\n".join(output_lines)
    except Exception as e:
        return f"执行工作流失败: {str(e)}"

@mcp.tool()
async def get_workflow_info(workflow_name: str) -> str:
    """获取指定工作流的详细信息，包括参数列表
    
    Args:
        workflow_name: 工作流名称
    
    Returns:
        工作流的详细信息
    """
    try:
        if not workflows_cache:
            await get_workflow_list()
        
        workflow_info = workflows_cache.get(workflow_name)
        if not workflow_info:
            available = ", ".join(workflows_cache.keys()) if workflows_cache else "无"
            return f"未找到名为 '{workflow_name}' 的工作流。\n可用工作流: {available}"
        
        workflow_id = workflow_info["workflow_id"]
        
        output_lines = [f"**工作流信息**\n"]
        output_lines.append(f"- **名称:** {workflow_info['workflow_name']}")
        output_lines.append(f"- **ID:** {workflow_id}")
        output_lines.append(f"- **描述:** {workflow_info.get('description', '无')}")
        
        if workflow_info.get("icon_url"):
            output_lines.append(f"- **图标:** {workflow_info['icon_url']}")
        
        if workflow_info.get("created_at"):
            output_lines.append(f"- **创建时间:** {workflow_info['created_at']}")
        
        if workflow_info.get("updated_at"):
            output_lines.append(f"- **更新时间:** {workflow_info['updated_at']}")
        
        try:
            detail = await get_workflow_detail(workflow_id)
            input_data = detail.get("input", {})
            parameters = input_data.get("parameters", {})
            
            output_lines.append(f"\n**参数列表:**")
            if parameters:
                output_lines.append(format_parameters(parameters))
            else:
                output_lines.append("无参数")
        except Exception as e:
            output_lines.append(f"\n**参数列表:** 获取失败 ({str(e)})")
        
        return "\n".join(output_lines)
    except Exception as e:
        return f"获取工作流信息失败: {str(e)}"

def main():
    """启动MCP服务器"""
    if not COZE_API_KEY:
        raise ValueError("请在.env文件中设置COZE_API_KEY")
    
    if not WORKSPACE_ID:
        raise ValueError("请在.env文件中设置WORKSPACE_ID")
    
    print(f"启动Coze MCP服务器...")
    print(f"工作空间ID: {WORKSPACE_ID}")
    
    mcp.run(transport="streamable-http", host="0.0.0.0", port=33123, path="/mcp")

if __name__ == "__main__":
    main()
