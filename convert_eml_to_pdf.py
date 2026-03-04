import os
import email
from email import policy
import subprocess
import glob
import re

def clean_html_or_text(msg):
    # Prefer HTML
    for part in msg.walk():
        if part.get_content_type() == 'text/html':
            return part.get_payload(decode=True).decode('utf-8', errors='ignore')
            
    # Fallback to plain text
    text = ''
    for part in msg.walk():
        if part.get_content_type() == 'text/plain':
            text += part.get_payload(decode=True).decode('utf-8', errors='ignore') + '\n'
            
    if not text:
        content = msg.get_payload(decode=True)
        if content:
            text = content.decode('utf-8', errors='ignore')
            
    return f"<html><body><pre>{text}</pre></body></html>"

src_dir = os.path.abspath('./WoodWard/2026-03-01-19h10m47s-eml-mail-export')
out_dir = os.path.abspath('./WoodWard/VPS_Investigation_Evidence/07_Right_of_Reply')
os.makedirs(out_dir, exist_ok=True)

# Information to redact (based on instructions)
redact_terms = [
    re.compile(r'\bChris Knight\b', re.IGNORECASE),
    re.compile(r'\bchris\.knight@vansd\.org\b', re.IGNORECASE),
]

eml_files = glob.glob(os.path.join(src_dir, '*.eml'))
for f in eml_files:
    with open(f, 'rb') as f_in:
        msg = email.message_from_binary_file(f_in, policy=policy.default)
        
    subject = str(msg.get('Subject', 'No Subject'))
    sender = str(msg.get('From', ''))
    date = str(msg.get('Date', ''))
    to = str(msg.get('To', ''))
    
    body_html = clean_html_or_text(msg)
    
    # Apply redactions to headers and body
    for pattern in redact_terms:
        subject = pattern.sub('[REDACTED]', subject)
        sender = pattern.sub('[REDACTED]', sender)
        to = pattern.sub('[REDACTED]', to)
        if body_html:
            body_html = pattern.sub('[REDACTED]', body_html)
        
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, sans-serif; margin: 40px; line-height: 1.5; font-size: 14px;}}
            .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }}
            .header div {{ margin-bottom: 5px; }}
            .header strong {{ display: inline-block; width: 80px; color: #555; }}
            pre {{ white-space: pre-wrap; font-family: inherit; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div><strong>From:</strong> {sender}</div>
            <div><strong>To:</strong> {to}</div>
            <div><strong>Date:</strong> {date}</div>
            <div><strong>Subject:</strong> {subject}</div>
        </div>
        <div class="body">
            {body_html}
        </div>
    </body>
    </html>
    """
    
    base_name = os.path.basename(f).replace('.eml', '.pdf')
    pdf_path = os.path.join(out_dir, base_name)
    tmp_html = os.path.join(out_dir, f'tmp_{base_name}.html')
    
    with open(tmp_html, 'w', encoding='utf-8') as tf:
        tf.write(full_html)
        
    # Generate PDF via Chrome Headless
    try:
        subprocess.run([
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '--headless',
            '--disable-gpu',
            '--print-to-pdf=' + pdf_path,
            'file://' + tmp_html
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"Converted: {base_name}")
    except Exception as e:
        print(f"Error converting {base_name}: {e}")
    finally:
        if os.path.exists(tmp_html):
            os.remove(tmp_html)

print("Batch conversion to PDF completed.")
