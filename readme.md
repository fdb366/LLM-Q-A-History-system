# 中小学历史知识智能问答系统

## 项目简介
基于大模型的RAG智能问答系统，专为中小学历史教育设计。

## 技术栈
- 前端：Vue 3 + Vite + TypeScript + Element Plus
- 后端：Python FastAPI + ChromaDB + MySQL
- AI：百度文心/阿里通义 + RAG架构

## 项目结构
history-qa-system/
├── backend/          # FastAPI后端
├── frontend/         # Vue3前端
├── database/         # 数据库脚本
├── scripts/          # 部署脚本
└── docs/            # 项目文档

## 开发环境
1. Python 3.9+
2. Node.js 16+
3. MySQL 8.0+
4. ChromaDB
## 依赖下载(先进入相应的目录下)
### 后端
cd backend
通过 environment.yml 快速创建相同环境
conda env create -f environment.yml
### 前端
cd frontend
npm i