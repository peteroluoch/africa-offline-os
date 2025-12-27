import re
import os
from pathlib import Path

# Patterns to flag
PATTERNS = {
    "HEX_CODE": r'#([A-Fa-f0-9]{3,6})\b',
    "RGB_RGBA": r'rgba?\([^)]*\)',
    "HARDCODED_PX": r'\b(\d+)px\b',
    # Common Tailwind colors that should be tokenized
    "TAILWIND_COLOR": r'\b(text|bg|border|ring|from|to)-(blue|indigo|slate|gray|green|red|yellow|amber|purple|pink|emerald|cyan)-\d+\b'
}

# Regex to ignore - These attributes often contain numbers or keywords that aren't CSS hardcoding
IGNORE_BLOCKS = [
    r'viewBox="[^"]*"',
    r'stroke-width="[^"]*"',
    r'points="[^"]*"',
    r'd="[^"]*"'
]

EXCEPTIONS = [
    "transparent",
    "currentColor",
    "inherit"
]

TEMPLATES_DIR = Path("aos/api/templates")

def scan_templates():
    print("🔍 Scanning A-OS Templates for Design Compliance violations...\n")
    violations_found = 0
    
    for root, _, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if not file.endswith((".html", ".jinja2")):
                continue
            
            file_path = (Path(root) / file).resolve()
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Strip ignored blocks (SVG paths, etc)
            clean_content = content
            for block_pattern in IGNORE_BLOCKS:
                clean_content = re.sub(block_pattern, "", clean_content)
            
            file_violations = []
            for name, pattern in PATTERNS.items():
                matches = re.finditer(pattern, clean_content)
                for match in matches:
                    # Skip if it looks like a variable or part of a token definition
                    snippet = clean_content[max(0, match.start()-20):min(len(clean_content), match.end()+20)]
                    if "var(--aos-" in snippet or "tokens.json" in str(file_path):
                        continue
                    
                    line_no = clean_content.count('\n', 0, match.start()) + 1
                    file_violations.append((line_no, name, match.group(0)))
            
            if file_violations:
                try:
                    rel_path = file_path.relative_to(Path.cwd().resolve())
                except ValueError:
                    rel_path = file_path
                print(f"📄 {rel_path}")
                for line, v_type, val in file_violations:
                    print(f"  [L{line}] {v_type}: {val}")
                violations_found += len(file_violations)
                print()

    if violations_found:
        print(f"❌ Found {violations_found} design compliance violations!")
        print("MANDATE: Replace all hardcoded values with var(--aos-*) or aos-* utility classes.")
    else:
        print("✅ 100% Design Compliance! No hardcoded values found.")

if __name__ == "__main__":
    scan_templates()
