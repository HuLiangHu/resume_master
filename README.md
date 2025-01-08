# Resume Master - 智能简历分析系统

Resume Master 是一个基于 AI 的智能简历分析系统，能够帮助求职者快速获取简历质量评估和岗位匹配度分析。

## 功能特点

- 📊 简历质量评分：对简历进行全方位评估，给出具体分数
- 🎯 岗位匹配度分析：分析简历与目标职位的匹配程度
- 💡 优化建议：提供详细的简历优化建议
- 🤝 模拟面试：生成可能的面试问题和建议答案

## 技术栈

- 后端：Python + Flask
- 前端：HTML + Bootstrap 5 + JavaScript
- AI：DeepSeek API
- 文件处理：PyPDF2（PDF文件）、python-docx（Word文件）

## 快速开始

1. 克隆项目
```bash
git clone https://github.com/yourusername/resume_master.git
cd resume_master
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
创建 `.env` 文件并添加以下配置：
```
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=your_base_url
```

4. 运行项目
```bash
python app.py
```

访问 http://localhost:5001 即可使用系统。

## 使用说明

1. 上传简历文件（支持 PDF、DOC、DOCX 格式）
2. 输入目标职位的 JD（职位描述）
3. 点击"开始分析"按钮
4. 等待系统分析完成，查看分析报告

## 注意事项

- 确保上传的简历文件小于 16MB
- 建议提供详细的职位描述以获得更准确的匹配度分析
- 系统支持中英文简历分析

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

MIT License
