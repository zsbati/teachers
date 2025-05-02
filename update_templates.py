import os

def update_template(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Add humanize filter if not present
    if '{% load static %}' in content and '{% load humanize %}' not in content:
        content = content.replace('{% load static %}', '{% load static %}\n{% load humanize %}')
    
    # Replace dollar signs with euro signs
    content = content.replace('$', '€')
    
    # Write back the updated content
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def update_all_templates():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, 'templates')
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                print(f'Updating {file_path}')
                update_template(file_path)

if __name__ == '__main__':
    update_all_templates()
