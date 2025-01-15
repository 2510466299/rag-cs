import torch
from transformers import CLIPProcessor, CLIPModel
import PIL.Image
import requests
from pathlib import Path

def test_clip_installation():
    print("=== CLIP环境检测 ===")
    
    # 1. 检查PyTorch
    print("\n1. PyTorch检测:")
    print(f"PyTorch版本: {torch.__version__}")
    print(f"CUDA是否可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA版本: {torch.version.cuda}")
        print(f"当前设备: {torch.cuda.get_device_name(0)}")
    
    # 2. 检查CLIP模型
    print("\n2. CLIP模型检测:")
    try:
        model_name = "openai/clip-vit-base-patch32"
        print(f"正在加载CLIP模型: {model_name}")
        model = CLIPModel.from_pretrained(model_name)
        processor = CLIPProcessor.from_pretrained(model_name)
        print("✅ CLIP模型加载成功!")
        
        # 3. 测试模型功能
        print("\n3. 模型功能测试:")
        
        def test_image(image_path, texts, description=""):
            print(f"\n测试图片{description}:")
            # 加载图片
            image = PIL.Image.open(image_path)
            
            # 处理输入
            inputs = processor(
                text=texts,
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            # 获取输出
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
            
            print("预测结果:")
            for text, prob in zip(texts, probs[0]):
                print(f"{text}: {prob.item():.2%}")
        
        # 测试本地图片（明月一心界面）
        local_image_path = Path("test_data/yunji_test.jpg")
        if local_image_path.exists():
            # 测试界面类型识别
            test_image(
                local_image_path,
                [
                    "这是一个搜索界面",
                    "这是一个登录界面",
                    "这是一个设置界面",
                    "这是一个聊天界面",
                    "这是一个商品列表界面"
                ],
                "1（界面类型识别）"
            )
            
            # 测试界面功能识别
            test_image(
                local_image_path,
                [
                    "界面包含搜索框",
                    "界面包含导航菜单",
                    "界面包含用户信息",
                    "界面包含热门推荐",
                    "界面包含历史记录"
                ],
                "2（界面功能识别）"
            )
            
            # 测试明月一心特定功能
            test_image(
                local_image_path,
                [
                    "这是明月一心的检索首页",
                    "这是明月一心的知识库页面",
                    "这是明月一心的设置页面",
                    "这是明月一心的统计页面",
                    "这是明月一心的用户页面"
                ],
                "3（明月一心功能识别）"
            )
        else:
            print(f"\n❌ 本地图片不存在: {local_image_path}")
        
        print("\n✅ 功能测试完成!")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == "__main__":
    test_clip_installation() 