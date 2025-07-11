# Metra平台访问指南

## 🚀 当前运行状态
✅ 后端: http://localhost:8000  
✅ 前端: http://localhost:8086  

## 📋 正确的访问方式

### 1. 访问前端应用
请在浏览器中访问以下任一地址：
- http://localhost:8080
- http://localhost:8081  
- http://localhost:8082
- http://localhost:8083
- http://localhost:8084
- http://localhost:8085
- **http://localhost:8086** (推荐)

### 2. 如果遇到"This file type is not allowed"错误
这通常是因为：
- 访问了错误的URL
- 浏览器缓存问题
- 安全设置阻止了本地文件访问

**解决方案**：
1. 清除浏览器缓存
2. 直接访问: http://localhost:8086
3. 或尝试其他端口: http://localhost:8080

### 3. 测试API
后端API文档: http://localhost:8000/docs

### 4. 登录信息
默认测试账号:
- 邮箱: test@example.com  
- 密码: 123456

或者可以注册新账号。

## 🔧 如果还有问题
请尝试：
1. 重启浏览器
2. 使用无痕模式
3. 检查浏览器控制台的错误信息
4. 确保没有防火墙阻止本地端口访问

## 📱 功能测试顺序
1. 访问首页
2. 注册/登录账号
3. 进入Dashboard
4. 测试Task Definition
5. 测试Model Recommendation
6. 测试Data Builder