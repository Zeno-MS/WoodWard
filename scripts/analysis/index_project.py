import os

def generate_index():
    project_root = "/Users/chrisknight/Projects/WoodWard"
    output_file = os.path.join(project_root, "project_index.txt")
    
    ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
    
    with open(output_file, 'w') as f:
        for root, dirs, files in os.walk(project_root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            # Write current directory
            rel_root = os.path.relpath(root, project_root)
            if rel_root == '.':
                f.write(f"/\n")
            else:
                f.write(f"{rel_root}/\n")
                
            # Write files in current directory
            for file in sorted(files):
                f.write(f"    {file}\n")
                
    print(f"Index successfully generated at {output_file}")

if __name__ == "__main__":
    generate_index()
