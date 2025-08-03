import os
import base64
from pathlib import Path
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv


def load_env() -> None:
    """
    加载环境变量，初始化项目根目录
    按照项目规范，在文件顶部执行环境初始化
    """
    # 找到项目根目录（包含.env文件的目录）
    current_dir = Path(__file__).parent
    project_root = current_dir
    while project_root.parent != project_root:
        if (project_root / ".env").exists():
            break
        project_root = project_root.parent
    
    # 加载环境变量
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"已加载环境变量: {env_path}")
    else:
        print("警告: 未找到 .env 文件")


def encode_image_to_base64(image_path: str) -> str:
    """
    将本地图片文件转换为base64编码
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        str: base64编码的图片字符串，包含数据URL前缀
        
    Raises:
        FileNotFoundError: 当图片文件不存在时
        Exception: 当图片读取或编码失败时
    """
    # 转换为绝对路径
    img_path = Path(image_path)
    if not img_path.is_absolute():
        # 相对于项目根目录
        current_dir = Path(__file__).parent
        project_root = current_dir.parent  # AI-house目录
        img_path = project_root / image_path
    
    if not img_path.exists():
        raise FileNotFoundError(f"图片文件不存在: {img_path}")
    
    try:
        with open(img_path, "rb") as image_file:
            # 读取图片并转换为base64
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 获取文件扩展名确定MIME类型
            ext = img_path.suffix.lower()
            mime_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg', 
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }.get(ext, 'image/jpeg')
            
            # 返回完整的data URL格式
            return f"data:{mime_type};base64,{base64_image}"
            
    except Exception as e:
        raise Exception(f"图片编码失败: {e}")


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
        raise ValueError("请在.env文件中设置 ARK_API_KEY 或 OPENAI_API_KEY")
    
    return OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )


# 环境初始化优先（遵循开发规范）
load_env()

# 初始化客户端
client = create_doubao_client()

# 注意：主要逻辑已移至 main() 函数，确保代码结构清晰


def analyze_image(image_path: str, question: str = "这是什么车？") -> None:
    """
    分析本地图片
    
    Args:
        image_path: 图片文件路径
        question: 要问的问题
    """
    try:
        print(f"正在处理图片: {image_path}")
        
        # 将本地图片转换为base64
        base64_image = encode_image_to_base64(image_path)
        print("图片编码完成")
        
        # 调用API分析图片
        response = client.chat.completions.create(
            model="doubao-1.5-vision-pro-250328",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": base64_image
                            },
                        },
                        {"type": "text", "text": question},
                    ],
                }
            ],
        )
        
        print("\n" + "="*50)
        print("豆包分析结果:")
        print("="*50)
        print(response.choices[0].message.content)
        print("\n" + "="*50)
        print("API调用成功!")
        
    except FileNotFoundError as e:
        print(f"文件错误: {e}")
    except Exception as e:
        print(f"调用API时出错: {e}")


def main() -> None:
    """
    主函数：演示豆包视觉模型的使用
    分析图片并返回结果
    """
    # 默认图片路径
    image_path = "image/18AD2E1F-2714-406E-9FEC-BF39D26CA6DB.jpeg"
    question = "这是什么车？"
    
    analyze_image(image_path, question)


if __name__ == "__main__":
    """
    模块独立运行入口
    可以直接从项目根目录运行: python LLM/doubao-version.py
    
    支持命令行参数:
    - 无参数: 使用默认图片和问题
    - python LLM/doubao-version.py [图片路径] [问题]
    """
    import sys
    
    print("启动豆包视觉分析...")
    
    # 支持命令行参数
    if len(sys.argv) >= 2:
        image_path = sys.argv[1]
        question = sys.argv[2] if len(sys.argv) >= 3 else "请描述这张图片"
        print(f"使用自定义参数: 图片={image_path}, 问题={question}")
        analyze_image(image_path, question)
    else:
        print("使用默认参数进行测试...")
        main()
    
    print("\n程序执行完成!")