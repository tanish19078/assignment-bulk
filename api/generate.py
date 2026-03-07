import json
import re
import os
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            aim = data.get("aim", "")
            api_key = data.get("api_key", "")
            model = data.get("model", "llama-3.3-70b-versatile")
            mock = data.get("mock", False)

            # Fallback to environment variables if no key provided
            if not api_key:
                if "sarvam" in model.lower():
                    api_key = os.getenv("SARVAM_API_KEY")
                else:
                    api_key = os.getenv("GROQ_API_KEY")

            if mock or not api_key:
                # Mock response
                result = {
                    "concept": f"This experiment demonstrates fundamental programming concepts relevant to: {aim[:80]}...",
                    "code": f'#include <stdio.h>\n\nint main() {{\n    // Code for: {aim[:40]}\n    printf("Executing experiment...\\n");\n    return 0;\n}}',
                    "output": "Executing experiment...\nOperation Successful.",
                    "caption": f"Terminal output for {aim[:25]}"
                }
            else:
                if "sarvam" in model.lower():
                    from sarvamai import SarvamAI
                    client = SarvamAI(api_subscription_key=api_key)
                    # Prompt designed to be identical in structure to Groq's for parsing consistency
                    prompt = f"""You are a professional programming lab assistant with expertise in Indian languages. For this experiment aim:

"{aim}"

Identify the most appropriate programming language for this aim (e.g., C, JavaScript, Python, etc.) and provide the following:

Respond EXACTLY in this format (use these exact tags):

[CONCEPT]
Write 3-4 lines explaining the programming concepts used. Academic style. 
CRITICAL: If the aim is written in an Indian language (like Hindi, Telugu, Tamil, Marathi, etc.), write this CONCEPT section in that same Indian language. Otherwise, use English.

[CODE]
Write the complete working source code. Plain code only, no markdown fences. Code should use standard English keywords (typical for programming).

[OUTPUT]
Show the realistic expected terminal or console output when this program runs.

[CAPTION]
Write a very short (3-5 words) descriptive caption for the terminal output screenshot.
If the aim is in an Indian language, write this caption in that same language.
"""
                    messages = [{"role": "user", "content": prompt}]
                    response = client.chat.completions(messages=messages, model=model)
                    text = response.choices[0].message.content
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
                        messages=[{"role": "user", "content": prompt}],
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
                    if not concept: concept = "No concept description provided by API."
                    if not code: code = "// No code provided for this experiment."
                    if not output_part: output_part = "No output provided."
                    if not caption: caption = "Experiment Output"
                    
                    if "[CONCEPT]" not in text.upper() and "[CODE]" not in text.upper():
                        raise ValueError('Malformed API response — missing expected tags')

                # Clean up markdown fences
                code = re.sub(r'```[a-zA-Z]*', '', code).replace('```', '').strip()
                output_part = re.sub(r'```', '', output_part).strip()

                result = {
                    'concept': concept,
                    'code': code,
                    'output': output_part,
                    'caption': caption
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            error_msg = str(e)
            status_code = 500
            # Detect 401/429 from error message if possible
            if "401" in error_msg or "Invalid API Key" in error_msg:
                status_code = 401
            elif "429" in error_msg or "Rate limit" in error_msg:
                status_code = 429
            
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": error_msg}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
