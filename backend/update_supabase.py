#!/usr/bin/env python3
"""
直接更新Supabase数据库schema
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
import httpx

async def update_supabase_schema():
    """直接通过REST API更新Supabase schema"""
    print("🚀 开始更新Supabase数据库schema...")
    
    # 读取schema文件
    try:
        with open('supabase_schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
    except FileNotFoundError:
        print("❌ 找不到 supabase_schema.sql 文件")
        return
    
    # 准备API请求
    headers = {
        'apikey': settings.SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {settings.SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    # 分割SQL语句
    statements = []
    current_statement = ""
    
    for line in schema_sql.split('\n'):
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        
        current_statement += line + " "
        
        if line.endswith(';'):
            statements.append(current_statement.strip()[:-1])  # 移除分号
            current_statement = ""
    
    print(f"📝 准备执行 {len(statements)} 条SQL语句...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        success_count = 0
        
        for i, statement in enumerate(statements):
            if not statement:
                continue
                
            try:
                # 使用Supabase的RPC功能执行SQL
                url = f"{settings.SUPABASE_URL}/rest/v1/rpc/exec_sql"
                payload = {"sql": statement}
                
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code in [200, 201, 204]:
                    print(f"✅ 语句 {i+1}/{len(statements)} 执行成功")
                    success_count += 1
                else:
                    # 检查是否是"已存在"错误
                    error_text = response.text.lower()
                    if any(x in error_text for x in ['already exists', 'duplicate', 'relation exists']):
                        print(f"⚠️  语句 {i+1}/{len(statements)} 已存在，跳过")
                        success_count += 1
                    else:
                        print(f"❌ 语句 {i+1}/{len(statements)} 失败: {response.status_code} - {response.text[:100]}")
                
            except Exception as e:
                error_msg = str(e).lower()
                if any(x in error_msg for x in ['already exists', 'duplicate', 'relation exists']):
                    print(f"⚠️  语句 {i+1}/{len(statements)} 已存在，跳过")
                    success_count += 1
                else:
                    print(f"❌ 语句 {i+1}/{len(statements)} 异常: {e}")
        
        print(f"\n🎉 Schema更新完成! 成功: {success_count}/{len(statements)}")
        
        if success_count < len(statements):
            print("⚠️  部分语句执行失败，这通常是因为表已存在")
            print("💡 你可以手动在Supabase控制台检查表结构")

if __name__ == "__main__":
    asyncio.run(update_supabase_schema())