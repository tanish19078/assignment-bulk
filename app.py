import json
import re
import io
import time
import os
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)


# ==================== Static Frontend ====================
@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)


# ==================== API: Parse Aims ====================
@app.route('/api/parse', methods=['POST'])
def api_parse():
    try:
        data = request.get_json()
        text = data.get('text', '')
        separator = data.get('separator', '---')

        pattern = r'\n\s*' + re.escape(separator) + r'+\s*\n'
        aim_blocks = re.split(pattern, text)
        aims = [b.strip() for b in aim_blocks if b.strip()]

        return jsonify({'aims': aims})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== API: Generate Content ====================
@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json()
        aim = data.get('aim', '')
        api_key = data.get('api_key', '')
        model = data.get('model', 'llama-3.3-70b-versatile')
        mock = data.get('mock', False)

        if mock or not api_key:
            result = {
                'concept': f'This experiment demonstrates fundamental programming concepts relevant to: {aim[:80]}...',
                'code': f'#include <stdio.h>\n\nint main() {{\n    // Code for: {aim[:40]}\n    printf("Executing experiment...\\n");\n    return 0;\n}}',
                'output': 'Executing experiment...\nOperation Successful.',
                'caption': f'Terminal output for {aim[:25]}'
            }
        else:
            from groq import Groq
            client = Groq(api_key=api_key)

            prompt = f"""You are a professional programming lab assistant. For this experiment aim:

"{aim}"

Identify the most appropriate programming language for this aim (e.g., C, JavaScript, Python, etc.) and provide the following:

Respond EXACTLY in this format (use these exact tags):

[CONCEPT]
Write 3-4 lines explaining the programming concepts used. Academic style.

[CODE]
Write the complete working source code. Plain code only, no markdown fences.

[OUTPUT]
Show the realistic expected terminal or console output when this program runs.

[CAPTION]
Write a very short (3-5 words) descriptive caption for the terminal output screenshot.
"""
            chat_completion = client.chat.completions.create(
                messages=[{'role': 'user', 'content': prompt}],
                model=model,
            )
            text = chat_completion.choices[0].message.content

            # Robust Parsing using Regex
            def extract_section(tag, text):
                pattern = rf"\[{tag}\](.*?)(\[|$)"
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                return match.group(1).strip() if match else None

            concept = extract_section("CONCEPT", text)
            code = extract_section("CODE", text)
            output_part = extract_section("OUTPUT", text)
            caption = extract_section("CAPTION", text)

            # Fallback if tags are missing or malformed
            if not all([concept, code, output_part, caption]):
                # Try to see if we can at least find CODE or CONCEPT
                if not concept: concept = "No concept description provided by API."
                if not code: code = "// No code provided for this experiment."
                if not output_part: output_part = "No output provided."
                if not caption: caption = "Experiment Output"
                
                # If everything is missing, then it's truly malformed
                if "[CONCEPT]" not in text.upper() and "[CODE]" not in text.upper():
                    raise ValueError('Malformed API response — missing expected tags')

            # Clean up markdown fences if present
            code = re.sub(r'```[a-zA-Z]*', '', code).replace('```', '').strip()
            output_part = re.sub(r'```', '', output_part).strip()

            result = {
                'concept': concept,
                'code': code,
                'output': output_part,
                'caption': caption
            }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== API: Download .docx ====================
def set_font(paragraph, font_name='Times New Roman', size=12, bold=False):
    for run in paragraph.runs:
        run.font.name = font_name
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
        run.font.size = Pt(size)
        run.bold = bold


def add_bold_para(doc, text, font_name='Times New Roman', size=12, align=None):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    run = p.add_run(text)
    run.bold = True
    set_font(p, font_name=font_name, size=size, bold=True)
    return p


def add_labeled_para(doc, label, content, font_name='Times New Roman', size=12):
    p = doc.add_paragraph()
    if any(c in content for c in ['*', '•', '·']) or '  ' in content:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run_label = p.add_run(f'{label} ')
    run_label.bold = True
    run_label.font.name = font_name
    run_label.font.size = Pt(size)
    run_content = p.add_run(content)
    run_content.font.name = font_name
    run_content.font.size = Pt(size)
    return p


def add_code_para(doc, code_text, font_name='Times New Roman', size=10):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(code_text)
    run.font.name = font_name
    run.font.size = Pt(size)


def add_caption_para(doc, text, experiment_no, font_name='Times New Roman', size=10):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f'Figure {experiment_no} - {text}')
    run.font.name = font_name
    run.font.size = Pt(size)


def create_terminal_image(output_text, img_width=600):
    font_size = 14
    padding = 20
    try:
        font = ImageFont.truetype('consola.ttf', font_size)
    except IOError:
        try:
            font = ImageFont.truetype('cour.ttf', font_size)
        except IOError:
            font = ImageFont.load_default()

    lines = output_text.split('\n')
    line_height = font_size + 4
    height = (len(lines) * line_height) + (2 * padding)

    img = Image.new('RGB', (img_width, height), color=(30, 30, 30))
    d = ImageDraw.Draw(img)
    y = padding
    for line in lines:
        d.text((padding, y), line, font=font, fill=(200, 200, 200))
        y += line_height

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def add_normal_para(doc, text, font_name='Times New Roman', size=12, align=None):
    if align is None:
        if any(c in text for c in ['*', '•', '·']) or '  ' in text:
            align = WD_ALIGN_PARAGRAPH.LEFT
        else:
            align = WD_ALIGN_PARAGRAPH.JUSTIFY
    p = doc.add_paragraph()
    p.alignment = align
    run = p.add_run(text)
    set_font(p, font_name=font_name, size=size)
    return p


@app.route('/api/download', methods=['POST'])
def api_download():
    try:
        data = request.get_json()
        experiments = data.get('experiments', [])
        settings = data.get('settings', {})

        font_name = settings.get('fontName', 'Times New Roman')
        body_size = int(settings.get('bodySize', 12))
        heading_size = int(settings.get('headingSize', 14))
        code_size = int(settings.get('codeSize', 10))
        caption_size = int(settings.get('captionSize', 10))
        image_width_inches = float(settings.get('imageWidth', 5.0))
        terminal_img_width = int(settings.get('terminalImgWidth', 600))
        output_filename = settings.get('outputFilename', 'Generated_Practical_File.docx')

        doc = Document()

        for i, exp in enumerate(experiments, 1):
            aim = exp.get('aim', '')
            concept = exp.get('concept', '')
            code = exp.get('code', '')
            output = exp.get('output', '')
            caption = exp.get('caption', '')

            # Experiment heading
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(f'Experiment No. {i}')
            run.bold = True
            run.font.name = font_name
            run.font.size = Pt(heading_size)
            doc.add_paragraph('')

            add_labeled_para(doc, 'Aim:', aim, font_name, body_size)
            doc.add_paragraph('')
            add_labeled_para(doc, 'Concept Used:', concept, font_name, body_size)
            doc.add_paragraph('')
            add_bold_para(doc, 'Code:', font_name, body_size)
            add_code_para(doc, code, font_name, code_size)
            doc.add_paragraph('')
            add_bold_para(doc, 'Output:', font_name, body_size)

            try:
                img_buf = create_terminal_image(output, terminal_img_width)
                pic_para = doc.add_paragraph()
                pic_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = pic_para.add_run()
                run.add_picture(img_buf, width=Inches(image_width_inches))
                add_caption_para(doc, caption, i, font_name, caption_size)
            except Exception as e:
                add_normal_para(doc, f'[Error adding image: {e}]', font_name, body_size)
                add_code_para(doc, output, font_name, code_size)

            if i < len(experiments):
                doc.add_page_break()

        file_buf = io.BytesIO()
        doc.save(file_buf)
        file_buf.seek(0)

        return send_file(
            file_buf,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=output_filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print('\n  ⚡ PractiGen running at http://localhost:5000\n')
    app.run(host='0.0.0.0', port=5000, debug=True)
