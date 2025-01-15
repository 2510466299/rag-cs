import pytest
from services.embedding import EmbeddingService
import numpy as np
from PIL import Image
import io
import requests

@pytest.fixture(scope="module")
def embedding_service():
    """创建EmbeddingService实例"""
    return EmbeddingService()

def test_text_embedding(embedding_service):
    """测试文本向量化功能"""
    # 测试单个文本
    text = "这是一个测试文本"
    embedding = embedding_service.get_text_embedding(text)
    assert isinstance(embedding, list)
    assert len(embedding) == 512  # CLIP的文本向量维度
    
    # 测试中文文本
    chinese_text = "测试中文文本的向量化效果"
    chinese_embedding = embedding_service.get_text_embedding(chinese_text)
    assert isinstance(chinese_embedding, list)
    assert len(chinese_embedding) == 512

def test_image_embedding(embedding_service):
    """测试图像向量化功能"""
    # 创建一个测试图像
    img = Image.new('RGB', (224, 224), color='red')
    
    # 获取图像向量
    embedding = embedding_service.get_image_embedding(img)
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape[-1] == 512  # CLIP的图像向量维度

def test_similarity_computation(embedding_service):
    """测试相似度计算功能"""
    # 准备测试数据
    text1 = "一只可爱的猫咪"
    text2 = "一辆红色的汽车"
    
    # 创建测试图像
    cat_img = Image.new('RGB', (224, 224), color='orange')  # 模拟猫咪图片
    car_img = Image.new('RGB', (224, 224), color='red')     # 模拟汽车图片
    
    # 获取向量
    text1_embedding = np.array(embedding_service.get_text_embedding(text1))
    text2_embedding = np.array(embedding_service.get_text_embedding(text2))
    cat_embedding = embedding_service.get_image_embedding(cat_img)
    car_embedding = embedding_service.get_image_embedding(car_img)
    
    # 计算相似度
    similarity1 = embedding_service.compute_similarity(text1_embedding, cat_embedding)
    similarity2 = embedding_service.compute_similarity(text2_embedding, car_embedding)
    
    # 验证相似度是否在合理范围内
    assert -1 <= similarity1 <= 1
    assert -1 <= similarity2 <= 1

def test_cross_modal_retrieval(embedding_service):
    """测试跨模态检索功能"""
    # 准备测试数据
    texts = [
        "一只可爱的猫咪",
        "一辆红色的汽车",
        "一朵美丽的花",
        "一台笔记本电脑"
    ]
    
    # 创建测试图像
    images = [
        Image.new('RGB', (224, 224), color='orange'),  # 猫咪
        Image.new('RGB', (224, 224), color='red'),     # 汽车
        Image.new('RGB', (224, 224), color='pink'),    # 花
        Image.new('RGB', (224, 224), color='gray')     # 电脑
    ]
    
    # 获取所有文本和图像的向量
    text_embeddings = [np.array(embedding_service.get_text_embedding(text)) for text in texts]
    image_embeddings = [embedding_service.get_image_embedding(img) for img in images]
    
    # 计算相似度矩阵
    similarity_matrix = np.zeros((len(texts), len(images)))
    for i, text_emb in enumerate(text_embeddings):
        for j, img_emb in enumerate(image_embeddings):
            similarity_matrix[i][j] = embedding_service.compute_similarity(text_emb, img_emb)
    
    # 验证相似度矩阵的基本属性
    assert similarity_matrix.shape == (len(texts), len(images))
    assert np.all(similarity_matrix >= -1) and np.all(similarity_matrix <= 1) 