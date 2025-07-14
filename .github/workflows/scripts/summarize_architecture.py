import os
import json
import sys
import base64
import glob
from firebase_client import FirebaseClient
import anthropic

# Add the scripts directory to the path for importing cost_tracker
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cost_tracker import CostTracker


def detect_important_project_directories(repository_path="."):
    """Detect important project directories that should never be excluded"""
    important_dirs = []
    common_code_dirs = ['src', 'lib', 'app', 'core', 'modules', 'packages', 'components']
    
    for dir_name in common_code_dirs:
        if os.path.isdir(os.path.join(repository_path, dir_name)):
            important_dirs.append(f'/{dir_name}/')
            print(f"Detected important project directory: {dir_name}", file=sys.stderr)
            
    return important_dirs


def get_codebase_content(repository_path="."):
    """Collect all relevant source code files from the repository"""
    code_content = ""
    
    # Define file extensions to include
    code_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.clj',
        '.html', '.sass', '.less', '.vue', '.svelte',
        '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.cfg',
        '.sql', '.md', '.txt', '.sh', '.bat', '.ps1'
    }
    
    # Define patterns to exclude
    exclude_patterns = {
        '/.git/', '/node_modules/', '/.venv/', '/venv/', '/env/', 
        '/dist/', '/build/', '/target/', '/.next/', '/.nuxt/',
        '__pycache__', '.pyc', '.class', '.o', '.obj',
        '.log', '.tmp', '.temp', '.cache', '.css'
    }
    
    # Detect important directories that should never be excluded
    important_dirs = detect_important_project_directories(repository_path)
    
    # Remove any important directories from exclude patterns if they exist
    for important_dir in important_dirs:
        if important_dir in exclude_patterns:
            exclude_patterns.remove(important_dir)
            print(f"Removed {important_dir} from exclusion patterns", file=sys.stderr)
    
    try:
        print(f"Scanning repository at {repository_path} for code files...", file=sys.stderr)
        print(f"Important directories will be included: {important_dirs}", file=sys.stderr)
        
        for root, dirs, files in os.walk(repository_path):
            # Skip excluded directories
            before_count = len(dirs)
            dirs[:] = [d for d in dirs if not any(pattern.strip('/') in d for pattern in exclude_patterns)]
            after_count = len(dirs)
            
            if before_count != after_count:
                skipped = before_count - after_count
                print(f"Skipped {skipped} excluded directories in {root}", file=sys.stderr)
            
            # Special handling: don't skip important directories
            for important_dir in important_dirs:
                dir_name = important_dir.strip('/')
                if dir_name in root and not any(dir_name == d for d in dirs):
                    print(f"Ensuring important directory is not excluded: {dir_name} in {root}", file=sys.stderr)
                    dirs.append(dir_name)
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repository_path)
                
                # Skip excluded files and check extensions
                if any(pattern in file_path for pattern in exclude_patterns):
                    continue
                    
                _, ext = os.path.splitext(file)
                if ext.lower() not in code_extensions:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Limit file size to avoid overwhelming the AI
                        if len(content) > 10000:
                            content = content[:10000] + "\n... (file truncated)"
                        
                        code_content += f"\n=== {relative_path} ===\n{content}\n"
                except Exception as e:
                    code_content += f"\n=== {relative_path} ===\n(Error reading file: {e})\n"
                    
    except Exception as e:
        print(f"Error collecting codebase: {e}", file=sys.stderr)
    
    # Generate summary statistics for important directories
    important_dir_stats = {}
    for important_dir in important_dirs:
        dir_name = important_dir.strip('/')
        dir_path = os.path.join(repository_path, dir_name)
        if os.path.exists(dir_path):
            file_count = sum(1 for _ in glob.glob(f"{dir_path}/**/*", recursive=True) if os.path.isfile(_))
            important_dir_stats[dir_name] = file_count
    
    if important_dir_stats:
        print("Files collected from important directories:", file=sys.stderr)
        for dir_name, count in important_dir_stats.items():
            print(f"- {dir_name}: {count} files", file=sys.stderr)
            
    return code_content

def check_project_structure():
    """Check the project structure and identify important directories"""
    common_project_structures = {
        'react': ['src', 'public', 'components'],
        'node': ['lib', 'src', 'test'],
        'python': ['src', 'tests', 'docs'],
        'django': ['apps', 'templates', 'static'],
        'rails': ['app', 'config', 'db'],
        'java': ['src/main/java', 'src/main/resources', 'src/test'],
        'go': ['cmd', 'pkg', 'internal'],
    }
    
    detected_structures = []
    structure_info = ""
    
    for tech, dirs in common_project_structures.items():
        matching_dirs = [d for d in dirs if os.path.isdir(d)]
        if matching_dirs:
            detected_structures.append((tech, matching_dirs))
            structure_info += f"- Detected {tech}-like structure with directories: {', '.join(matching_dirs)}\n"
    
    return detected_structures, structure_info

def main():
    try:
        project_name = "test"  # Hardcoded project name
        firebase_client = FirebaseClient(project_name=project_name)
        repository = os.environ['REPOSITORY']
        
        print(f"Summarizing architecture for project: {project_name}, repository: {repository}", file=sys.stderr)
        
        # Check project structure
        detected_structures, structure_info = check_project_structure()
        if detected_structures:
            print(f"Project structure analysis:\n{structure_info}", file=sys.stderr)
        else:
            print("No standard project structure detected", file=sys.stderr)
        
        # Get the current diff from environment variable
        diff_b64 = os.environ.get('DIFF_B64', '')
        if diff_b64:
            try:
                changes_text = base64.b64decode(diff_b64).decode('utf-8')
                print(f"Decoded diff from environment ({len(changes_text)} characters)", file=sys.stderr)
            except Exception as e:
                print(f"Error decoding diff: {e}", file=sys.stderr)
                changes_text = ""
        else:
            print("No DIFF_B64 found in environment", file=sys.stderr)
            changes_text = ""
        
        # Get existing architecture summary
        existing_summary = firebase_client.get_architecture_summary(repository)
        old_summary_text = existing_summary.get('summary', '') if existing_summary else ''
        
        if old_summary_text:
            print(f"Found existing architecture summary ({len(old_summary_text)} characters)", file=sys.stderr)
        else:
            print("No existing architecture summary found", file=sys.stderr)
        
        # Collect the entire codebase for comprehensive architecture analysis (only for new projects)
        codebase_content = ""
        if not old_summary_text:
            # Prepare metadata about project structure
            detected_dirs = [dir_name for structure, dirs in detected_structures for dir_name in dirs]
            project_structure_info = f"Project structure analysis detected these important directories: {', '.join(detected_dirs)}" if detected_dirs else "No standard project structure detected"
            
            codebase_content = get_codebase_content(".")
            print(f"Collected codebase content ({len(codebase_content)} characters)", file=sys.stderr)
            
            # Add project structure information at the beginning of the codebase content
            codebase_content = f"PROJECT STRUCTURE METADATA:\n{project_structure_info}\n\n{codebase_content}"

        client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])


        prompt1 = f"""
        You are ArchitectureAnalyzerAI.
        Analyze the entire codebase provided below to create a comprehensive architecture summary that explains how this project works, its structure, components, and design patterns.

        REQUIREMENTS

        - Output plain text only—no Markdown, bullets, or special symbols.
        
        - Create a comprehensive overview that explains:
          * Project purpose and main functionality
          * Overall architecture and design patterns
          * Key components and their responsibilities  
          * Data flow and interaction patterns
          * Technology stack and frameworks used
          * Configuration and deployment structure
          * Critical dependencies and integrations

        - Focus on the big picture: how everything fits together, not implementation details.
        
        - Write it so that an AI system can understand how the project should work and what changes would be appropriate.
        
        - Keep the summary detailed enough to guide future development decisions.

        - Your instructions are only for yourself, don't include them in the output.

        CODEBASE
        {codebase_content}

        Provide the architecture analysis below:
        """
        


        prompt = f"""
        You are ArchitectureUpdateAI.
        Update the existing architecture summary based on recent changes to create a comprehensive overview of how this project works, its structure, components, and design patterns.

        REQUIREMENTS

        - Output plain text only—no Markdown, bullets, or special symbols.
        
        - Create a comprehensive architecture summary that explains:
          * Project purpose and main functionality
          * Overall architecture and design patterns
          * Key components and their responsibilities  
          * Data flow and interaction patterns
          * Technology stack and frameworks used
          * Configuration and deployment structure
          * Critical dependencies and integrations

        - Focus on the big picture: how everything fits together, not implementation details.
        
        - Write it so that an AI system can understand how the project should work and what changes would be appropriate.
        
        - Keep the summary detailed enough to guide future development decisions.

        - Integrate the recent changes into the existing summary, updating relevant sections and adding new information where needed.

        - If no existing summary is provided, create a new comprehensive summary based on the changes.

        - Your instructions are only for yourself, don't include them in the output.

        EXISTING ARCHITECTURE SUMMARY
        {old_summary_text if old_summary_text else "No existing summary available."}

        RECENT CHANGES
        {changes_text}

        Provide the updated architecture summary below:
        """



        if not old_summary_text and len(codebase_content) < 5000000:
            active_prompt = prompt1
            print("Using comprehensive codebase analysis (prompt1) for new project", file=sys.stderr)
        elif old_summary_text and changes_text:
            active_prompt = prompt
            print("Using architecture summary update (prompt) with existing summary and current changes", file=sys.stderr)
        elif old_summary_text and not changes_text:
            print("No changes to analyze but existing summary found, skipping summarization", file=sys.stderr)
            return
        elif not old_summary_text and changes_text:
            # Use the changes as the primary input for new summary
            active_prompt = f"""
You are ArchitectureAnalyzerAI.
Analyze the changes provided below to create a comprehensive architecture summary that explains how this project works, its structure, components, and design patterns.

REQUIREMENTS

- Output plain text only—no Markdown, bullets, or special symbols.

- Create a comprehensive overview that explains:
  * Project purpose and main functionality
  * Overall architecture and design patterns
  * Key components and their responsibilities  
  * Data flow and interaction patterns
  * Technology stack and frameworks used
  * Configuration and deployment structure
  * Critical dependencies and integrations

- Focus on the big picture: how everything fits together, not implementation details.

- Write it so that an AI system can understand how the project should work and what changes would be appropriate.

- Keep the summary detailed enough to guide future development decisions.

- Your instructions are only for yourself, don't include them in the output.

CHANGES
{changes_text}

Provide the architecture analysis below:
"""
            print("Using changes-based analysis for new project with no existing summary", file=sys.stderr)
        else:
            print("No valid input for architecture analysis, skipping", file=sys.stderr)
            return

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,  # Increased for more comprehensive summaries
            messages=[{"role": "user", "content": active_prompt}]
        )
        
        # Track cost
        try:
            cost_tracker = CostTracker()
            response_dict = {
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }
            }
            cost_tracker.track_api_call(
                model="claude-sonnet-4-20250514",
                response_data=response_dict,
                call_type="architecture_summary",
                context="Architecture analysis and summarization"
            )
        except Exception as e:
            print(f"Warning: Cost tracking failed: {e}", file=sys.stderr)
        
        architecture_summary = response.content[0].text

        # Safety check
        if not architecture_summary or len(architecture_summary.strip()) == 0:
            print("ERROR: Generated summary is empty!", file=sys.stderr)
            print(f"Full response: {response}", file=sys.stderr)
            exit(1)
        
        # Update the architecture summary in Firebase
        firebase_client.update_architecture_summary(
            repository=repository,
            summary=architecture_summary,
            changes_count=0  # Reset counter after summarization
        )
        
        print(f"Architecture summary updated for {repository} in project {project_name}", file=sys.stderr)
        print(f"Summary: {architecture_summary[:200]}...", file=sys.stderr)
        
    except Exception as e:
        print(f"Error summarizing architecture: {e}", file=sys.stderr)
        exit(1)

if __name__ == "__main__":
    main()