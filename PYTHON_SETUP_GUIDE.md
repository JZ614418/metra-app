# Metra Python环境设置指南

## 🎯 问题背景

Metra项目在Python 3.13环境下存在AI相关包的兼容性问题，特别是：
- `torch` - PyTorch深度学习框架
- `transformers` - Hugging Face Transformers
- `sentence-transformers` - 句子嵌入模型
- `lxml` - XML/HTML解析器
- `numpy` - 数值计算库

## ✅ 解决方案：使用pyenv管理Python版本

### 步骤1: 安装pyenv

```bash
# 使用Homebrew安装pyenv
brew install pyenv

# 配置shell环境
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# 重新加载shell配置
source ~/.zshrc
```

### 步骤2: 安装Python 3.11

```bash
# 安装Python 3.11.13（最新稳定版）
pyenv install 3.11.13

# 验证安装
pyenv versions
```

### 步骤3: 为Metra项目设置Python环境

```bash
# 进入Metra项目目录
cd /path/to/Metra

# 设置项目使用Python 3.11.13
pyenv local 3.11.13

# 验证Python版本
python --version  # 应该显示 Python 3.11.13
```

### 步骤4: 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 步骤5: 安装完整依赖

```bash
# 安装完整的项目依赖（包括AI包）
pip install -r backend/requirements_full.txt
```

## 📦 已解决的包兼容性

以下AI相关包现在可以正常安装和使用：

- ✅ **PyTorch 2.2.2** - 深度学习框架
- ✅ **Transformers 4.48.3** - Hugging Face模型库
- ✅ **Sentence Transformers 2.7.0** - 句子嵌入
- ✅ **NumPy 1.26.4** - 数值计算
- ✅ **lxml 4.9.3** - XML/HTML解析
- ✅ **Pandas 2.3.1** - 数据处理

## 🧪 验证安装

运行以下命令验证AI功能：

```bash
source venv/bin/activate
python -c "
import torch
import transformers
import sentence_transformers
import pandas as pd
print('✅ All AI packages working!')
print('PyTorch:', torch.__version__)
print('Transformers:', transformers.__version__)
print('MPS available:', torch.backends.mps.is_available())
"
```

## 🚀 启动Metra服务

### 后端服务

```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 前端服务

```bash
cd metra-ai-factory-main
npm install
npm run dev
```

## 📝 关键配置文件

- `.python-version` - pyenv项目Python版本配置
- `backend/requirements_full.txt` - 完整依赖列表（包含AI包）
- `backend/requirements_minimal.txt` - 最小依赖（临时使用）

## 🔧 故障排除

### 如果pyenv没有生效

```bash
# 重新配置shell
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

### 如果虚拟环境Python版本不对

```bash
# 删除重建虚拟环境
rm -rf venv
~/.pyenv/versions/3.11.13/bin/python -m venv venv
```

### 如果AI包安装失败

```bash
# 确保使用Python 3.11
python --version  # 必须是3.11.x

# 升级pip到最新版本
pip install --upgrade pip

# 重新安装依赖
pip install -r backend/requirements_full.txt
```

## 🎉 成功标志

当看到以下输出时，说明环境配置成功：

```
✅ PyTorch: 2.2.2
✅ Transformers: 4.48.3
✅ Sentence Transformers: 2.7.0
✅ MPS available: True
✅ All AI packages working!
```

## 📚 相关文档

- [PyTorch官方文档](https://pytorch.org/docs/stable/index.html)
- [Transformers文档](https://huggingface.co/docs/transformers)
- [pyenv使用指南](https://github.com/pyenv/pyenv#usage)

---

**配置完成后，Metra的所有AI功能将恢复正常，包括数据收集、模型训练和AI增强决策等核心功能。**