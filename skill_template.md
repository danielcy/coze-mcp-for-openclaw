---
name: {workflow_name}
description: {workflow_description}
---

## 使用场景
{workflow_description}

## 使用方式
 - 你需要通过coze-mcp来使用这个技能
 - 通过coze-mcp的run_workflow_by_name命令来执行这个技能
 - 你需要传递workflow_name参数，值为{workflow_name}
 - 根据下面的传参说明填入parameters参数
 
## 传参及说明
{workflow_params}

## mcporter调用方式
```bash
 mcporter call "coze-mcp.run_workflow_by_name(workflow_name: 'shopping_goods_search', parameters: {param1: 'value1', param2: 'value2'})"
```

## 错误处理
 - 如果coze-mcp没有在运行或找不到该mcp，无视该技能，尝试用其他方式解决或者直接通知用户无法执行
 - 如果该技能执行失败，处理方式也如上