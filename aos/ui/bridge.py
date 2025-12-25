import json
import os
from pathlib import Path

class DesignSystemBridge:
    """
    Bridges the JSON Design Tokens to CSS and Template variables.
    Ensures FAANG-grade 'Zero Hardcoded Values' policy.
    """
    
    def __init__(self, tokens_path: str = None):
        if tokens_path is None:
            # Default to relative path from project root
            tokens_path = os.path.join(os.path.dirname(__file__), "tokens.json")
            
        with open(tokens_path, 'r') as f:
            self.tokens = json.load(f)
            
    def generate_css_variables(self) -> str:
        """Generates :root CSS variables from tokens."""
        css = [":root {"]
        
        # Colors - Semantic
        for category, values in self.tokens["colors"]["semantic"].items():
            for key, val in values.items():
                if key in ["base", "hover", "active", "text"]:
                    css.append(f"  --aos-{category}-{key}: {val};")
        
        # Colors - Neutral
        for key, val in self.tokens["colors"]["neutral"].items():
            css.append(f"  --aos-neutral-{key}: {val};")
            
        # Colors - Surface
        for key, val in self.tokens["colors"]["surface"].items():
            css.append(f"  --aos-surface-{key}: {val};")
            
        # Spacing
        for key, val in self.tokens["spacing"].items():
            # Replace . with - for css variable names
            safe_key = str(key).replace(".", "_")
            css.append(f"  --aos-spacing-{safe_key}: {val};")
            
        # Typography - Font Family
        for key, val in self.tokens["typography"]["fontFamily"].items():
            css.append(f"  --aos-font-{key}: {val};")
            
        # Typography - Font Size
        for key, val in self.tokens["typography"]["fontSize"].items():
            css.append(f"  --aos-size-{key}: {val};")
            
        # Border Radius
        for key, val in self.tokens["borderRadius"].items():
            css.append(f"  --aos-radius-{key}: {val};")
            
        # Shadows
        for key, val in self.tokens["shadows"].items():
            css.append(f"  --aos-shadow-{key}: {val};")
            
        css.append("}")
        return "\n".join(css)

    def write_css(self, output_path: str):
        """Writes the generated CSS to a file."""
        css_content = self.generate_css_variables()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(css_content)
        print(f"[DesignSystem] Compiled tokens to {output_path}")

if __name__ == "__main__":
    # Example usage / Manual compile
    bridge = DesignSystemBridge()
    static_css_path = os.path.join(os.path.dirname(__file__), "base.css")
    bridge.write_css(static_css_path)
