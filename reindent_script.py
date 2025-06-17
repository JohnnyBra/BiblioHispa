import tokenize
import io

source_path = "classroom_library_app/main.py"  # Specify the target file

try:
    with open(source_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except FileNotFoundError:
    print(f"Error: File {source_path} not found.")
    exit(1)

processed_lines = []
for line_content in lines:
    stripped_line = line_content.lstrip()
    leading_whitespace = line_content[:-len(stripped_line)]

    # Convert tabs to 4 spaces in the leading whitespace
    leading_spaces_only = leading_whitespace.replace('\t', '    ') # Correctly escape tab

    # Reconstruct the line
    processed_lines.append(leading_spaces_only + stripped_line)

try:
    with open(source_path, 'w', encoding='utf-8') as f:
        f.writelines(processed_lines)
    print(f"Successfully converted leading tabs to spaces in {source_path}")
except Exception as e:
    print(f"Error writing changes to {source_path}: {e}")
    exit(1)
