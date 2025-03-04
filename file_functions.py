import spacy
import os
import re
import glob
import send2trash
import shutil


nlp = spacy.load("en_core_web_sm")
nlp.Defaults.stop_words.remove("move")
nlp.vocab["move"].is_stop = False

def extract_file_name(command):
    """Extract possible filenames (without extensions) from user input."""
    doc = nlp(command)

    filtered_cmd = " ".join([token.text for token in doc if not token.is_stop]).lower()
    
    keywords = ["open", "rename", "move", "copy", "delete", "compress", "extract", "called"]

    file_pattern = re.compile(r'\b[\w.-]+\.\w+\b')  # Captures filenames with extensions
    keyword_pattern = re.compile(r'(?:(?:' + '|'.join(keywords) + r')\s+)([\w.-]+)', re.IGNORECASE)  # Captures words after keywords
    # Find filenames with extensions
    matches = file_pattern.findall(filtered_cmd)
    
    # Find filenames that follow keywords (without extensions)
    keyword_matches = keyword_pattern.findall(filtered_cmd)
    files = list(set(matches + keyword_matches))
    return files

def extract_path(command):
    file_path = re.findall(r"[A-Za-z]:\\(?:[^<>:\"/\\|?*\n]+\\)*[^<>:\"/\\|?*\n]*",command)
    return file_path

def extract_folder(text):
    """Extract possible folder names from user input."""
    match = re.findall(r'from ([\w\\:/. ]+)', text)
    return match[0] if match else None

def search_file(directory, filename):
    """Search for a file by name (without extension) in a directory."""
    search_pattern = os.path.join(directory, f"{filename}.*")  # Match any extension
    matching_files = glob.glob(search_pattern)  # Find all matching files
    return matching_files if matching_files else None
def search_path(folder_name):
    common_paths = {
        "Desktop": r"C:\Users\%USERNAME%\Desktop",
        "Documents": r"C:\Users\%USERNAME%\Documents",
        "Downloads": r"C:\Users\%USERNAME%\Downloads",
        "Pictures": r"C:\Users\%USERNAME%\Pictures",
        "Music": r"C:\Users\%USERNAME%\Music",
        "Videos": r"C:\Users\%USERNAME%\Videos",
        "OneDrive": r"C:\Users\%USERNAME%\OneDrive",
        "AppData": r"C:\Users\%USERNAME%\AppData",
        "Local AppData": r"C:\Users\%USERNAME%\AppData\Local",
        "Roaming AppData": r"C:\Users\%USERNAME%\AppData\Roaming",
        "Program Files": r"C:\Program Files",
        "Program Files (x86)": r"C:\Program Files (x86)",
        "Temp": r"C:\Users\%USERNAME%\AppData\Local\Temp",
        "Public Desktop": r"C:\Users\Public\Desktop",
        "Public Documents": r"C:\Users\Public\Documents",
        "Public Downloads": r"C:\Users\Public\Downloads",
    }
    for key,path in common_paths.items():
        if key.lower() == folder_name.lower():
            return path
    return ""

def intent_detection(command):
    doc = nlp(command.lower())
    intents = {
        "open": ["open","Find and open"],
        "search": ["find", "locate", "search"],
        "create": ["create", "make", "new file"],
        "rename": ["rename", "change name"],
        "move": ["move", "transfer"],
        "copy": ["copy", "duplicate"],
        "delete": ["delete", "remove"],
        "compress": ["compress", "zip"],
        "extract": ["extract", "unzip"],
        "storage": ["storage", "disk space", "free space"]
    }
    for i in intents:
        for token in doc:
            if any(token.lemma_ in intents[i] for token in doc):
                return i
    return None        


def process_command(command):
    """Process user input and determine the action to perform."""

    detected_intents = intent_detection(command)
    file_name = extract_file_name(command)
    folder = extract_folder(command)
    path = extract_path(command)
    result = {
        "intents": detected_intents,
        "file": file_name,
        "folder": folder,
        "raw_text": command,
        "path": path
    }

    # If user wants to open a file but didn't specify an extension, search for possible matches
    if "open" in detected_intents and file_name and folder:
        matching_files = search_file(folder, file_name)
        if matching_files:
            result["found_files"] = matching_files
        else:
            result["message"] = f"No files found matching '{file_name}' in '{folder}'"

    return result

def file_open(filepath):
    """Opens the file at the given path using the default application."""
    try:
        os.startfile(filepath)
        return True
    except FileNotFoundError:
        return f"Error: File not found at '{filepath}'"
    except Exception as e:
        return f"An error occurred: {e}"
    
def file_create(file_name,filepath):
    file_path_absolute = filepath + "\\" + file_name
    try:
        file = open(file_path_absolute,'x')
    except FileExistsError as e:
        return f"An error occurred: {e}"
    
def rename_file(old_file_name,new_file_name,file_path):
    try:
        old_file_path_absolute = file_path + "\\" + old_file_name
        new_file_path_absolute = file_path + "\\" + new_file_name
        os.rename(old_file_path_absolute, new_file_path_absolute)
        return "File renamed successfully."
    except FileNotFoundError:
        return "File not found."
    except PermissionError:
        return "Permission denied."
    except Exception as e:
        return f"An error occurred: {e}"

def move_file(file_name,old_file_path,new_file_path):
    try:
        old_file_path_absolute = old_file_path + "\\" + file_name
        new_file_path_absolute = new_file_path + "\\" + file_name
        os.replace(old_file_path_absolute,new_file_path_absolute)
        return "File moved succesfully"
    except FileNotFoundError:
        return "File not found"
    except PermissionError:
        return "Permission denied"
    except Exception as e:
        return f"An error occurred: {e}"
        
def copy_file(file_name,old_file_path,new_file_path,new_file_name=None):
    try:
        if new_file_name:
            old_file_path_absolute = old_file_path + "\\" + file_name
            new_file_path_absolute = new_file_path + "\\" + new_file_name
        else:
            old_file_path_absolute = old_file_path + "\\" + file_name
            new_file_path_absolute = new_file_path + "\\" + file_name
        cmd = "copy " + old_file_path_absolute + " " + new_file_path_absolute
        os.system(cmd)
        return "File copyed succesfully"
    except FileNotFoundError:
        return "File not found"
    except PermissionError:
        return "Permission denied"
    except Exception as e:
        return f"An error occurred: {e}"

def delete_file(file_name,filepath):
    file_path_absolute = filepath + "\\" + file_name
    try:
        send2trash.send2trash(file_path_absolute)
        return f"File '{file_name}' moved to trash successfully."
    except FileNotFoundError as e:
        return f"An error occurred: {e}"

def compress_file(folder_path,compressed_file_name):
    try:
        shutil.make_archive(compressed_file_name, 'zip', folder_path)
        return f"Folder'{folder_path}' compressed successfully"
    except Exception as e:
        return f"An error occurred:'{e}'"

def extract_file(compressed, output_folder):
    try:
        shutil.unpack_archive(compressed, output_folder)
        return f"File'{compressed}' extracted successfully"
    except Exception as e:
        return f"An error occurred:'{e}'"

def get_storage_usage(path="/"):
    try:
        total, used, free = shutil.disk_usage(path)
        return {
            "Total Storage": f"{total / (1024**3):.2f} GB",
            "Used Storage": f"{used / (1024**3):.2f} GB",
            "Free Storage": f"{free / (1024**3):.2f} GB"
        }
    except Exception as e:
        return f"An error occurred: {e}"



# Example usage
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

for cmd in commands:
    print(process_command(cmd))


