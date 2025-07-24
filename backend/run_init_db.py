#!/usr/bin/env python3
"""
简单的数据库初始化运行脚本
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 设置环境变量
os.environ.setdefault('PYTHONPATH', project_root)

# 现在可以导入并运行初始化脚本
try:
    from app.db.init_v3_tables import init_v3_database, create_sample_data
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 开始初始化DataBuilder V3数据库...")
    
    success = init_v3_database()
    if success:
        logger.info("✅ DataBuilder V3数据库初始化成功!")
        create_sample_data()
        logger.info("🎉 初始化完成!")
    else:
        logger.error("❌ DataBuilder V3数据库初始化失败")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在backend目录下运行此脚本")
    sys.exit(1)
except Exception as e:
    print(f"❌ 初始化过程出错: {e}")
    sys.exit(1)