import requests
import json
import os
import random
import time
import markdown
from xhtml2pdf import pisa

# Configuration
API_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "gemma-3-4b-it"
OUTPUT_DIR = "generated_cvs"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# CV Styles/Formats
STYLES = [
    "Chronological",
    "Functional",
    "Modern",
    "Creative",
    "Academic",
    "Executive",
    "Entry-Level",
    "Two-Column"
]

# Target Roles for variety
ROLES = [
    "Software Engineer",
    "Data Scientist",
    "Product Manager",
    "Graphic Designer",
    "Marketing Specialist",
    "Sales Representative",
    "Project Manager",
    "DevOps Engineer"
]

# CSS Styles for PDF generation
CSS_STYLES = {
    "Modern": """
        @page { size: A4; margin: 2cm; }
        body { font-family: Helvetica, sans-serif; color: #333; line-height: 1.5; }
        h1 { color: #2c3e50; font-size: 24pt; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
        h2 { color: #2980b9; font-size: 16pt; margin-top: 20px; border-bottom: 1px solid #eee; }
        h3 { color: #7f8c8d; font-size: 12pt; margin-top: 10px; }
        p { font-size: 10pt; margin-bottom: 5px; }
        ul { margin-left: 20px; }
        li { font-size: 10pt; }
        strong { color: #2c3e50; }
    """,
    "Classic": """
        @page { size: A4; margin: 2.5cm; }
        body { font-family: "Times New Roman", serif; color: #000; line-height: 1.4; }
        h1 { font-size: 22pt; text-align: center; text-transform: uppercase; margin-bottom: 20px; }
        h2 { font-size: 14pt; border-bottom: 1px solid #000; text-transform: uppercase; margin-top: 15px; }
        h3 { font-size: 12pt; font-weight: bold; margin-top: 10px; }
        p { font-size: 11pt; text-align: justify; }
        ul { margin-left: 15px; }
        li { font-size: 11pt; }
    """,
    "Creative": """
        @page { size: A4; margin: 1.5cm; }
        body { font-family: Helvetica, sans-serif; color: #444; background-color: #f9f9f9; }
        h1 { color: #e74c3c; font-size: 28pt; font-weight: bold; text-align: left; }
        h2 { color: #fff; background-color: #e74c3c; padding: 5px 10px; font-size: 14pt; margin-top: 20px; border-radius: 5px; }
        h3 { color: #c0392b; font-size: 12pt; margin-top: 10px; }
        p { font-size: 10pt; }
        ul { list-style-type: square; color: #e74c3c; }
        li { color: #444; }
        strong { color: #c0392b; }
    """,
    "Academic": """
        @page { size: A4; margin: 2cm; }
        body { font-family: "Times New Roman", serif; font-size: 10pt; }
        h1 { font-size: 18pt; font-weight: bold; text-align: center; }
        h2 { font-size: 12pt; font-weight: bold; text-transform: uppercase; margin-top: 15px; }
        p { margin-bottom: 2px; }
        ul { margin-top: 2px; }
    """,
    "Sidebar": """
        @page { size: A4; margin: 1cm; }
        body { font-family: Helvetica, sans-serif; color: #333; }
        table { width: 100%; border-collapse: collapse; }
        td { vertical-align: top; padding: 10px; }
        .sidebar { width: 30%; background-color: #f0f0f0; color: #333; }
        .main-content { width: 70%; }
        h1 { font-size: 24pt; color: #2c3e50; margin-bottom: 5px; }
        h2 { font-size: 14pt; color: #2980b9; border-bottom: 1px solid #ccc; margin-top: 15px; margin-bottom: 5px; }
        h3 { font-size: 11pt; font-weight: bold; margin-top: 10px; }
        p { font-size: 10pt; margin-bottom: 5px; }
        ul { margin-left: 15px; padding-left: 0; }
        li { font-size: 9pt; margin-bottom: 2px; }
        .contact-info { font-size: 9pt; margin-bottom: 15px; }
    """,
    "Default": """
        @page { size: A4; margin: 2cm; }
        body { font-family: Helvetica, sans-serif; }
        h1 { font-size: 20pt; border-bottom: 1px solid #ccc; }
        h2 { font-size: 14pt; margin-top: 15px; color: #555; }
    """
}

def get_css(style_name):
    """Returns the CSS string for a given style name."""
    if "Sidebar" in style_name:
        return CSS_STYLES["Sidebar"]
    elif "Modern" in style_name or "Two-Column" in style_name:
        return CSS_STYLES["Modern"]
    elif "Creative" in style_name or "Graphic" in style_name:
        return CSS_STYLES["Creative"]
    elif "Academic" in style_name:
        return CSS_STYLES["Academic"]
    elif "Chronological" in style_name or "Executive" in style_name:
        return CSS_STYLES["Classic"]
    else:
        return CSS_STYLES["Default"]

def generate_cv_content(role, style):
    """Generates CV content in Markdown using the local LLM."""
    
    system_prompt = (
        "You are an expert resume writer. "
        "Generate a realistic, high-quality CV/resume in Markdown format. "
        "Do not include any conversational text, introductions, or explanations. "
        "Start directly with the content or the markdown code block. "
        "Do not use placeholders. Invent realistic details."
    )
    
    user_prompt = (
        f"Generate a {role} resume in '{style}' style. "
        "Output ONLY the markdown content."
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"Generating {style} CV for {role}...")
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        return extract_markdown(content)
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Error parsing response: {e}")
        return None

def generate_cv_json(role):
    """Generates structured CV data in JSON format."""
    system_prompt = (
        "You are an expert resume writer. "
        "Generate a realistic, high-quality CV/resume in JSON format. "
        "The JSON must have the following keys: "
        "'name', 'title', 'contact_info' (list of strings), 'summary', "
        "'education' (list of objects with 'degree', 'school', 'year'), "
        "'skills' (list of strings), 'experience' (list of objects with 'role', 'company', 'duration', 'details' (list of strings)). "
        "Do not use placeholders."
    )
    
    user_prompt = f"Generate a JSON resume for a {role}."

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }
    
    headers = {"Content-Type": "application/json"}

    try:
        print(f"Generating JSON CV for {role}...")
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Clean up potential markdown wrapping around JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1]
            
        return json.loads(content)
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"Error generating JSON: {e}")
        return None

def extract_markdown(text):
    """Extracts content within markdown code blocks if present."""
    if "```markdown" in text:
        parts = text.split("```markdown")
        if len(parts) > 1:
            content = parts[1].split("```")[0]
            return content.strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) > 1:
            content = parts[1]
            return content.strip()
    return text

def create_pdf(markdown_content, output_filename, style):
    """Converts Markdown to PDF with the specified style."""
    html_body = markdown.markdown(markdown_content)
    css = get_css(style)
    full_html = f"<html><head><style>{css}</style></head><body>{html_body}</body></html>"
    generate_pdf_from_html(full_html, output_filename)

def create_sidebar_pdf(json_data, output_filename):
    """Creates a Sidebar style PDF using HTML tables."""
    if not json_data:
        return

    css = get_css("Sidebar")
    
    # Build HTML sections
    contact_html = "<br>".join(json_data.get('contact_info', []))
    
    edu_html = ""
    for edu in json_data.get('education', []):
        edu_html += f"<p><strong>{edu.get('year')}</strong><br>{edu.get('degree')}<br>{edu.get('school')}</p>"
        
    skills_html = "<ul>" + "".join([f"<li>{s}</li>" for s in json_data.get('skills', [])]) + "</ul>"
    
    exp_html = ""
    for job in json_data.get('experience', []):
        details = "<ul>" + "".join([f"<li>{d}</li>" for d in job.get('details', [])]) + "</ul>"
        exp_html += f"<h3>{job.get('role')}</h3><p><strong>{job.get('company')}</strong> | {job.get('duration')}</p>{details}"

    full_html = f"""
    <html>
    <head><style>{css}</style></head>
    <body>
        <table>
            <tr>
                <td class="sidebar">
                    <h2>Contact</h2>
                    <div class="contact-info">{contact_html}</div>
                    <h2>Education</h2>
                    {edu_html}
                    <h2>Skills</h2>
                    {skills_html}
                </td>
                <td class="main-content">
                    <h1>{json_data.get('name')}</h1>
                    <p style="font-size: 12pt; color: #555;">{json_data.get('title')}</p>
                    <hr>
                    <h2>Profile</h2>
                    <p>{json_data.get('summary')}</p>
                    <h2>Experience</h2>
                    {exp_html}
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    generate_pdf_from_html(full_html, output_filename)

def generate_pdf_from_html(html_content, output_filename):
    """Helper to generate PDF from HTML string."""
    try:
        with open(output_filename, "wb") as result_file:
            pisa_status = pisa.CreatePDF(html_content, dest=result_file)
        if pisa_status.err:
            print(f"Error generating PDF: {pisa_status.err}")
        else:
            print(f"Saved PDF to: {output_filename}")
    except Exception as e:
        print(f"Exception during PDF generation: {e}")

import argparse

# ... (existing imports and constants) ...

def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate fake CVs using a local LLM.")
    parser.add_argument("--count", type=int, default=3, help="Number of CVs to generate (default: 3)")
    parser.add_argument("--role", type=str, help="Specific role to generate (e.g., 'Software Engineer')")
    parser.add_argument("--style", type=str, help="Specific style to generate (e.g., 'Modern', 'Classic', 'Sidebar')")
    parser.add_argument("--output", type=str, default="generated_cvs", help="Output directory (default: 'generated_cvs')")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Update Output Directory if needed
    global OUTPUT_DIR
    OUTPUT_DIR = args.output
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Starting Fake CV Generator (PDF Mode)...")
    print(f"Target URL: {API_URL}")
    print(f"Model: {MODEL_NAME}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("-" * 30)

    for i in range(args.count):
        # Determine Role
        if args.role:
            role = args.role
        else:
            role = random.choice(ROLES)
        
        # Determine Style
        if args.style:
            style = args.style
        else:
            # Add Sidebar to random choice
            all_styles = STYLES + ["Sidebar"]
            style = random.choice(all_styles)
        
        # Generate Content based on Style
        if style == "Sidebar":
            json_data = generate_cv_json(role)
            if json_data:
                safe_role = role.lower().replace(" ", "_")
                timestamp = int(time.time())
                filename = f"{safe_role}_sidebar_{timestamp}.pdf"
                filepath = os.path.join(OUTPUT_DIR, filename)
                create_sidebar_pdf(json_data, filepath)
        else:
            md_content = generate_cv_content(role, style)
            if md_content:
                safe_role = role.lower().replace(" ", "_")
                safe_style = style.lower().replace(" ", "_")
                timestamp = int(time.time())
                filename = f"{safe_role}_{safe_style}_{timestamp}.pdf"
                filepath = os.path.join(OUTPUT_DIR, filename)
                create_pdf(md_content, filepath, style)
        
        print("-" * 30)

    print("Generation complete.")

if __name__ == "__main__":
    main()

