from typing import List, Union, Dict
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np
from pathlib import Path
import logging

class EmbeddingService:
    """文档向量化服务，使用CLIP模型进行文本和图像的向量化处理"""
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """初始化CLIP模型和处理器
        
        Args:
            model_name: CLIP模型名称，默认使用base版本以平衡性能和资源占用
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Using device: {self.device}")
        
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()  # 设置为评估模式
        
        logging.info(f"Loaded CLIP model: {model_name}")
    
    def get_text_embedding(self, texts: Union[str, List[str]]) -> List[float]:
        """获取文本的向量表示
        
        Args:
            texts: 单个文本字符串或文本列表
            
        Returns:
            文本的向量表示（浮点数列表）
        """
        if isinstance(texts, str):
            texts = [texts]
            
        with torch.no_grad():
            inputs = self.processor(
                text=texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77  # CLIP的默认最大文本长度
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            text_features = self.model.get_text_features(**inputs)
            
        # 将numpy数组转换为列表并返回第一个向量
        return text_features.cpu().numpy()[0].tolist()
    
    def get_image_embedding(self, images: Union[str, Path, Image.Image, List[Union[str, Path, Image.Image]]]) -> np.ndarray:
        """获取图像的向量表示
        
        Args:
            images: 图像路径（字符串或Path对象）、PIL图像对象，或它们的列表
            
        Returns:
            图像的向量表示（numpy数组）
        """
        if not isinstance(images, list):
            images = [images]
            
        processed_images = []
        for img in images:
            if isinstance(img, (str, Path)):
                img = Image.open(str(img))
            processed_images.append(img)
            
        with torch.no_grad():
            inputs = self.processor(
                images=processed_images,
                return_tensors="pt",
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            image_features = self.model.get_image_features(**inputs)
            
        return image_features.cpu().numpy()
    
    def compute_similarity(self, text_embedding: np.ndarray, image_embedding: np.ndarray) -> float:
        """计算文本向量和图像向量之间的相似度
        
        Args:
            text_embedding: 文本向量
            image_embedding: 图像向量
            
        Returns:
            相似度分数（0-1之间的浮点数）
        """
        # 确保输入是二维数组
        if len(text_embedding.shape) == 1:
            text_embedding = text_embedding.reshape(1, -1)
        if len(image_embedding.shape) == 1:
            image_embedding = image_embedding.reshape(1, -1)
            
        # 计算余弦相似度
        similarity = np.dot(text_embedding, image_embedding.T)
        text_norm = np.linalg.norm(text_embedding, axis=1)
        image_norm = np.linalg.norm(image_embedding, axis=1)
        similarity = similarity / (text_norm.reshape(-1, 1) @ image_norm.reshape(1, -1))
        
        return similarity[0, 0]  # 返回单个相似度分数 