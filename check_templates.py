"""
Template Syntax Verification Script
Checks all templates for Jinja2 syntax errors without running the server.
"""
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
from pathlib import Path

templates_dir = Path("aos/api/templates")
env = Environment(loader=FileSystemLoader(str(templates_dir)))

templates_to_check = [
    "dashboard.html",
    "agri.html",
    "transport.html",
    "mesh.html",
    "gallery.html",
    "login.html"
]

print("🔍 Checking template syntax...\n")

errors = []
for template_name in templates_to_check:
    try:
        env.get_template(template_name)
        print(f"✅ {template_name}")
    except TemplateSyntaxError as e:
        print(f"❌ {template_name}: {e}")
        errors.append((template_name, str(e)))
    except Exception as e:
        print(f"⚠️  {template_name}: {e}")

if errors:
    print(f"\n❌ Found {len(errors)} template errors")
    for name, error in errors:
        print(f"  - {name}: {error}")
else:
    print("\n✅ All templates are syntactically valid!")
