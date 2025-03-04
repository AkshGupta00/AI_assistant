import re
import spacy

nlp = spacy.load("en_core_web_sm")
nlp.Defaults.stop_words.remove("move")
nlp.vocab["move"].is_stop = False

commands = [
    "Find and open the project file from Documents",
    "Open budget report from Downloads",
    "Create a new file called notes in Desktop",
    "Rename old_file.txt to new_file.txt",
    "Move report from Downloads to Documents",
    "Copy backup to D:\\Backup",
    "Delete temp file",
    "Compress all files in C:\\Work into archive.zip",
    "Extract backup.zip to C:\\Restored_Files",
    "Show my disk space usage"
]

# Keywords that often precede a filename
keywords = ["open", "rename", "move", "copy", "delete", "compress", "extract", "called","files"]

# Regex patterns to capture filenames with or without extensions
file_pattern = re.compile(r'\b[\w.-]+\.\w+\b')  # Captures filenames with extensions
keyword_pattern = re.compile(r'(?:(?:' + '|'.join(keywords) + r')\s+)([\w.-]+)', re.IGNORECASE)  # Captures words after keywords
file_path_pattern = re.compile(r"[A-Za-z]:\\(?:[^<>:\"/\\|?*\n]+\\)*[^<>:\"/\\|?*\n]*")
extracted_files = {}

for cmd in commands:
    doc = nlp(cmd)
    
    filtered_cmd = " ".join([token.text for token in doc if not token.is_stop]).lower()

    # Find filenames with extensions
    matches = file_pattern.findall(filtered_cmd)
    
    # Find filenames that follow keywords (without extensions)
    keyword_matches = keyword_pattern.findall(filtered_cmd)
    
    # Combine results
    files = list(set(matches + keyword_matches))  # Remove duplicates
    extracted_files[filtered_cmd] = files

# Print results
for cmd, files in extracted_files.items():
    print(f"Command: {cmd}")
    print(f"Extracted File(s): {files}\n")
