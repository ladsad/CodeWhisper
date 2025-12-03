import os
import argparse
from github import Github
from pathlib import Path

def scrape_repo(token: str, repo_name: str, output_dir: str):
    """
    Scrapes a GitHub repository for .py and .java files.
    """
    print(f"Connecting to GitHub...")
    g = Github(token)
    
    try:
        repo = g.get_repo(repo_name)
        print(f"Accessing repository: {repo.full_name}")
        
        contents = repo.get_contents("")
        
        while contents:
            file_content = contents.pop(0)
            
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
            else:
                save_file = False
                lang = ""
                
                if file_content.path.endswith(".py"):
                    save_file = True
                    lang = "python"
                elif file_content.path.endswith(".java"):
                    save_file = True
                    lang = "java"
                
                if save_file:
                    print(f"Downloading: {file_content.path}")
                    try:
                        # Get raw content
                        raw_content = file_content.decoded_content.decode('utf-8')
                        
                        # Create output path
                        safe_path = file_content.path.replace("/", "_").replace("\\", "_")
                        output_path = Path(output_dir) / f"{repo.name}_{safe_path}.txt"
                        
                        # Add metadata header
                        file_data = f"Repo: {repo.full_name}\nPath: {file_content.path}\nLanguage: {lang}\n\n{raw_content}"
                        
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(file_data)
                            
                    except Exception as e:
                        print(f"Error processing {file_content.path}: {e}")

    except Exception as e:
        print(f"Error accessing repo {repo_name}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Repo Scraper")
    parser.add_argument("--token", type=str, required=True, help="GitHub Personal Access Token")
    parser.add_argument("--repo", type=str, required=True, help="Repository name (e.g., 'owner/repo')")
    parser.add_argument("--output", type=str, default="./scraped_data", help="Output directory")
    
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    
    scrape_repo(args.token, args.repo, args.output)
