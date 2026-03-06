import json
import time
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

            if mock or not api_key:
                result = {
                    "concept": f"This experiment demonstrates fundamental programming concepts relevant to: {aim[:80]}...",
                    "code": f'#include <stdio.h>\n\nint main() {{\n    // Code for: {aim[:40]}\n    printf("Executing experiment...\\n");\n    return 0;\n}}',
                    "output": "Executing experiment...\nOperation Successful.",
                    "caption": f"Terminal output for {aim[:25]}"
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
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                )
                text = chat_completion.choices[0].message.content

                if "[CONCEPT]" not in text or "[CODE]" not in text or "[OUTPUT]" not in text or "[CAPTION]" not in text:
                    raise ValueError("Malformed API response — missing expected tags")

                concept = text.split("[CONCEPT]")[1].split("[CODE]")[0].strip()
                code = text.split("[CODE]")[1].split("[OUTPUT]")[0].strip()
                output_part = text.split("[OUTPUT]")[1].split("[CAPTION]")[0].strip()
                caption = text.split("[CAPTION]")[1].strip()

                # Clean up markdown fences
                code = code.replace("```c", "").replace("```C", "").replace("```python", "").replace("```javascript", "").replace("```", "").strip()
                output_part = output_part.replace("```", "").strip()

                result = {
                    "concept": concept,
                    "code": code,
                    "output": output_part,
                    "caption": caption
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
