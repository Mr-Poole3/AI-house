import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv


def load_env() -> None:
    """
    加载环境变量，初始化项目根目录
    按照项目规范，在文件顶部执行环境初始化
    """
    # 找到项目根目录（包含.env文件的目录）
    current_dir = Path(__file__).parent
    project_root = current_dir.parent  # AI-house目录
    
    # 加载环境变量
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"已加载环境变量: {env_path}")
    else:
        print("警告: 未找到 .env 文件，请创建并配置您的API Key")


def create_doubao_client() -> OpenAI:
    """
    创建豆包（字节跳动方舟）客户端
    
    Returns:
        OpenAI: 配置好的客户端实例
        
    Raises:
        ValueError: 当API key未配置时
    """
    api_key = os.environ.get("ARK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("请在.env文件中设置 ARK_API_KEY")
    
    return OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )


# 环境初始化优先（遵循开发规范）
load_env()

# 初始化客户端
client = create_doubao_client()

def main() -> None:
    """
    主函数：演示豆包文本模型的基本使用
    """

    # Streaming:
    print("----- streaming request -----")
    stream = client.chat.completions.create(
        # 指定您创建的方舟推理接入点 ID，此处已帮您修改为您的推理接入点 ID
        model="doubao-1-5-thinking-pro-250415",
        messages=[
            {"role": "system", "content": "你是人工智能助助手"},
            {"role": "user", "content": "你好"},
        ],
        # 响应内容是否流式返回
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        print(chunk.choices[0].delta.content, end="")
    print()
    
    print("\n测试完成!")


if __name__ == "__main__":
    """
    模块独立运行入口
    可以直接从项目根目录运行: python LLM/doubao-text.py
    """
    main()