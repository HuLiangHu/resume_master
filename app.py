from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import requests
import PyPDF2
import docx
from openai import OpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, GOOD_RESUME_RECOMMEND
import json
            
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化 DeepSeek 客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    """检查文件是否是允许的类型"""
    if not filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else None
    return extension in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    """从文件名获取扩展名，如果没有扩展名则返回None"""
    if not filename:
        return None
    if '.' not in filename:
        return None
    ext = filename.rsplit('.', 1)[1].lower()
    return ext if ext in ALLOWED_EXTENSIONS else None

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text

def analyze_resume(resume_text, jd_text):
    print(f"开始分析简历...")
    print(f"简历文本长度: {len(resume_text)}")
    print(f"JD文本长度: {len(jd_text)}")
    
    # 构建提示词
    prompt = f"""作为一个专业的简历分析专家，请对以下简历和职位描述进行分析：

简历内容：
{resume_text}

职位描述：
{jd_text}

请提供以下分析：
1. 简历质量评分（0-10)及评分理由
2. 岗位匹配度评分（0-10）和匹配度分析
3. 简历优化建议以匹配岗位要求（全面详细的改进点）
4. 10个可能的面试问题和相应的分析，包含行为面试（自我介绍等）和技术面试

请以JSON格式返回，包含以下字段：
{{
    "quality_score": "简历质量评分",
    "quality_analysis": {{
        "advantages": ["简历优势1", "简历优势2", ...],
        "disadvantages": ["简历不足1", "简历不足2", ...],
        "suggestions": ["简历建议1", "简历建议2", ...]
    }},
    "match_score": "岗位匹配度评分",
    "job_analysis": {{
        "key_skills": "关键技能要求",
        "experience": "工作经验要求",
        "other_requirements": "其他重要要求"
    }},
    "match_analysis": {{
        "advantages": ["匹配优势1", "匹配优势2", ...],
        "disadvantages": ["不匹配点1", "不匹配点2", ...],
        "suggestions": ["提升建议1", "提升建议2", ...]
    }},
    "suggestions": [
        {{
            "location": "简历中的具体位置",
            "content": "优化建议内容",
            "explanation": "优化说明及示例",
            "additional": "补充建议（可选）"
        }}
    ],
    "mock_interview": [
        {{
            "question": "面试问题",
            "analysis": "回答思路",
            "example": "示例回答，结合岗位要求和简历内容"
        }}
    ]
}}"""

    try:
        print("正在调用 DeepSeek API...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的简历分析专家，擅长评估简历质量和岗位匹配度。请严格按照要求的JSON格式返回分析结果。"},
                {"role": "user", "content": prompt}
            ],
            stream=False,
            temperature=0.7,
            max_tokens=2000
        )
        
        print("API调用成功，正在处理响应...")
        # 解析AI响应
        analysis_text = response.choices[0].message.content
        print(f"API响应内容: {analysis_text}")
        result = json.loads(analysis_text.replace("```json", "").replace("```", ""))
        return result   
    except Exception as e:
        print(f"API调用错误: {str(e)}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # 检查是否有文件
    if 'resume' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
        
    # 检查是否有JD
    if 'jd' not in request.form or not request.form['jd'].strip():
        return jsonify({'error': '请输入职位描述'}), 400
    
    jd = request.form['jd']
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式，请上传 PDF 或 Word 文件'}), 400
    
    try:
        # 确保上传目录存在并有正确的权限
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        os.chmod(upload_dir, 0o755)
        
        # 安全地获取文件扩展名
        extension = file.filename.rsplit('.', 1)[1].lower()
        
        # 生成唯一的文件名
        import uuid
        unique_filename = f"resume_{uuid.uuid4().hex}.{extension}"
        filepath = os.path.join(upload_dir, unique_filename)
        
        # 保存文件
        file.save(filepath)
        print(f"文件已保存到: {filepath}")
        
        try:
            # 提取文本内容
            resume_text = ""
            if extension == 'pdf':
                resume_text = extract_text_from_pdf(filepath)
            elif extension in ['doc', 'docx']:
                resume_text = extract_text_from_docx(filepath)
            
            if not resume_text.strip():
                return jsonify({'error': '无法从文件中提取文本内容'}), 400
            
            # 调用 DeepSeek API 进行分析
            analysis_result = analyze_resume(resume_text, jd)
            
            if analysis_result is None:
                return jsonify({'error': 'AI分析失败，请重试'}), 500
            
            return jsonify(analysis_result)
            
        except Exception as e:
            print(f"处理文件时发生错误: {str(e)}")
            return jsonify({'error': f'处理文件时发生错误: {str(e)}'}), 500
        finally:
            # 删除上传的文件
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"文件已删除: {filepath}")
            except Exception as e:
                print(f"删除文件失败: {str(e)}")
                
    except Exception as e:
        print(f"保存文件时发生错误: {str(e)}")
        return jsonify({'error': f'保存文件时发生错误: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
