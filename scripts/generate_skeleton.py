#!/usr/bin/env python3
"""
LLM Skeleton Generation Module
- Structured prompts with JSON schema constraints
- Failure retry and auto-fix
- Sampling templates (robust/exploratory)
"""
import json
import random
from typing import Optional, Dict, Any, List
from openai import OpenAI

# Default schema for skeleton output
SKELETON_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Unique identifier"},
        "archetype": {"type": "string", "description": "Story archetype (复仇/成长/爱情/悬疑/ etc.)"},
        "title": {"type": "string", "description": "Story title"},
        "logline": {"type": "string", "description": "One-sentence story summary"},
        "style_tags": {"type": "array", "items": {"type": "string"}, "description": "Style tags"},
        "ending": {"type": "string", "enum": ["tragedy", "triumph", "bittersweet", "open", "pyrrhic"]},
        "stakes": {"type": "string", "description": "What's at stake"},
        "actors": {"type": "array", "items": {"type": "string"}, "description": "Characters"},
        "beats": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "desc": {"type": "string"}
                },
                "required": ["id", "name", "desc"]
            },
            "description": "Story beats (6-10 beats)"
        },
        "tension_curve": {"type": "array", "items": {"type": "number"}, "description": "Tension values 0-1"},
        "themes": {"type": "array", "items": {"type": "string"}, "description": "Themes"}
    },
    "required": ["id", "archetype", "title", "logline", "beats", "ending"]
}

# Prompt templates
SYSTEM_PROMPT = """你是一个专业的故事结构生成助手。根据给定的条件，生成符合以下JSON schema的故事骨架。

## 输出 Schema
```json
{schema}
```

## 关键要求
1. beats 数量: 6-10 个，建议 9 个
2. 每个 beat 必须有 name 和 desc，desc 不少于 50 字
3. tension_curve 长度必须与 beats 数量一致
4. ending 必须是: tragedy/triumph/bittersweet/open/pyrrhic 之一
5. 生成的故事必须具有内在逻辑性，beats 之间有因果关联

## beat 命名规范
使用富有意象的名字，如：余烬、暗涌、凝视深渊、镜像的污损、空洞的完成
避免使用：开始、发展、高潮、结局 这种抽象名字
"""

USER_PROMPT_TEMPLATE = """请生成一个故事骨架：

- 原型(archetype): {archetype}
- 结局(ending): {ending}
- 风格标签: {style_tags}
- 核心冲突: {stakes}

请确保：
1. 故事有清晰的张力曲线
2. beats 之间有情感/逻辑递进
3. 标题和 logline 有吸引力
"""

def make_prompt(archetype: str, ending: str, style_tags: List[str], stakes: str) -> tuple:
    """Make structured prompt for generation."""
    system = SYSTEM_PROMPT.format(schema=json.dumps(SKELETON_SCHEMA, ensure_ascii=False))
    user = USER_PROMPT_TEMPLATE.format(
        archetype=archetype,
        ending=ending,
        style_tags=", ".join(style_tags),
        stakes=stakes
    )
    return system, user

def generate_skeleton(
    client: OpenAI,
    archetype: str = "复仇",
    ending: str = "tragedy",
    style_tags: Optional[List[str]] = None,
    stakes: str = "灵魂",
    model: str = "gpt-4o",
    temperature: float = 0.7,
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """Generate skeleton with retry logic."""
    if style_tags is None:
        style_tags = ["悬疑", "现代"]
    
    system, user = make_prompt(archetype, ending, style_tags, stakes)
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
                max_tokens=4000,
            )
            
            content = response.choices[0].message.content
            skeleton = json.loads(content)
            
            # Validate basic structure
            if "beats" in skeleton and len(skeleton["beats"]) >= 6:
                return skeleton
            
        except json.JSONDecodeError as e:
            print(f"[attempt {attempt+1}] JSON parse error: {e}")
        except Exception as e:
            print(f"[attempt {attempt+1}] Error: {e}")
    
    return None

def generate_with_retrieval(
    client: OpenAI,
    query: str,
    retrieval_results: List[Dict],
    model: str = "gpt-4o",
    temperature: float = 0.7,
) -> Optional[Dict[str, Any]]:
    """Generate skeleton using retrieval-augmented context."""
    
    # Build context from retrieved skeletons
    context_parts = ["参考以下相似故事结构：\n"]
    for i, sk in enumerate(retrieval_results[:3]):
        context_parts.append(f"""
--- 参考 {i+1}: {sk.get('title', 'Unknown')}
- 原型: {sk.get('archetype', '')}
- 结局: {sk.get('ending', '')}
- 概要: {sk.get('logline', '')}
- Beats: {len(sk.get('beats', []))} 个
""")
    
    context = "\n".join(context_parts)
    
    system = SYSTEM_PROMPT.format(schema=json.dumps(SKELETON_SCHEMA, ensure_ascii=False))
    user = f"""{context}

请参考上述故事结构，生成一个与以下需求相关的新故事：
{query}

要求：
1. 借鉴参考故事的优点
2. 但要创造不同的情节走向
3. 保持独特的张力曲线
"""
    
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
                max_tokens=4000,
            )
            
            skeleton = json.loads(response.choices[0].message.content)
            if "beats" in skeleton and len(skeleton["beats"]) >= 6:
                return skeleton
                
        except Exception as e:
            print(f"[attempt {attempt+1}] Error: {e}")
    
    return None

# Sampling templates
SAMPLING_TEMPLATES = {
    "robust": {
        "temperature": 0.3,
        "top_p": 0.9,
        "description": "保守生成，输出稳定但可能缺乏创意",
    },
    "balanced": {
        "temperature": 0.7,
        "top_p": 0.95,
        "description": "平衡模式，推荐日常使用",
    },
    "exploratory": {
        "temperature": 1.0,
        "top_p": 0.95,
        "description": "探索模式，可能产生创意结果",
    },
}

if __name__ == "__main__":
    import sys
    # Quick test
    print("LLM Generation Module loaded.")
    print(f"Available sampling templates: {list(SAMPLING_TEMPLATES.keys())}")
    print(f"Schema fields: {list(SKELETON_SCHEMA['properties'].keys())}")
