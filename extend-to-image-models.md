# 扩展Metra支持图像模型

## 1. 修改模型推荐逻辑

在 `backend/app/api/v1/endpoints/recommendations.py` 中：

```python
# 添加图像任务类型映射
TASK_TYPE_MAPPING = {
    # ... 现有的文本任务 ...
    'image-classification': ['image-classification', 'vision'],
    'object-detection': ['object-detection', 'yolo', 'detr'],
    'image-segmentation': ['image-segmentation', 'mask-generation'],
    'image-to-text': ['image-to-text', 'image-captioning'],
}

# 修改排除逻辑，根据任务类型决定
def is_model_relevant(model, task_type: str, language: str, domain: str) -> bool:
    # 如果是图像任务，不排除视觉模型
    if task_type.startswith('image-'):
        # 允许视觉模型
        pass
    else:
        # 原有的排除逻辑
        for excluded in EXCLUDED_MODEL_TYPES:
            if excluded in model_id_lower:
                return False
```

## 2. 更新Data Builder数据类型

在 `metra-ai-factory-main/src/components/DataSynthesizer.tsx` 中：

```typescript
// 添加图像数据源推荐
const getImageDataSources = () => {
  return [
    { name: 'ImageNet', description: '1400万+标注图像', icon: <Image /> },
    { name: 'COCO Dataset', description: '物体检测和分割数据集', icon: <Camera /> },
    { name: 'Unsplash API', description: '高质量免费图片', icon: <Image /> },
    { name: 'Google Images', description: '网络图片搜索', icon: <Globe /> },
    { name: '淘宝商品图', description: '电商产品图片', icon: <ShoppingCart /> }
  ];
};
```

## 3. 支持图像数据预处理

```python
# 在 backend/app/services/data_collection.py 添加
async def process_image_data(images: List[UploadFile]):
    """处理上传的图像文件"""
    processed_images = []
    
    for image in images:
        # 图像预处理
        img_data = {
            'filename': image.filename,
            'size': image.size,
            'format': image.content_type,
            # 生成缩略图
            'thumbnail': generate_thumbnail(image),
            # 提取特征
            'features': extract_image_features(image)
        }
        processed_images.append(img_data)
    
    return processed_images
```

## 4. 推荐的图像模型

### 中文场景
- **CLIP-Chinese**: 支持中文的多模态模型
- **Taiyi-CLIP**: 太乙系列中文CLIP模型
- **WuDao-VL**: 悟道视觉语言模型

### 通用模型
- **CLIP**: OpenAI的图文匹配模型
- **ViT**: Vision Transformer系列
- **ResNet**: 经典CNN架构
- **EfficientNet**: 高效的图像分类模型

## 5. 使用场景示例

### 电商图像分类
```json
{
  "task": "商品图像分类",
  "language": "chinese",
  "task_type": "image-classification",
  "labels": ["服装", "电子产品", "食品", "家居用品"],
  "input_format": {
    "image": "商品图片",
    "size": "224x224"
  },
  "output_format": {
    "category": "商品类别",
    "confidence": "置信度"
  }
}
```

### 医疗影像识别
```json
{
  "task": "X光片异常检测",
  "task_type": "image-classification",
  "labels": ["正常", "肺炎", "骨折", "肿瘤"],
  "domain": "medical"
}
```

## 实现步骤

1. **Phase 1**: 修改模型推荐API支持图像模型
2. **Phase 2**: 更新Data Builder支持图像上传和预览
3. **Phase 3**: 集成图像预处理pipeline
4. **Phase 4**: 支持图像增强和标注工具
5. **Phase 5**: 集成图像模型训练API（如AutoML Vision）

这样Metra就可以支持完整的图像AI工作流了！ 