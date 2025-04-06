import spacy
import os
import re
import glob
import send2trash
import shutil
import difflib
import sqlite3


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
    """Extract possible file path form the user input"""
    file_path = re.findall(r"[A-Za-z]:\\(?:[^<>:\"/\\|?*\n]+\\)*[^<>:\"/\\|?*\n]*",command)
    return file_path

def extract_folder(text):
    """Extract possible folder names from user input."""
    match = re.findall(r'from ([\w\\:/. ]+)', text)
    return match[0] if match else None

def search_file(directory, filename):
    """Search recursively for exact filename (without extension)."""
    search_pattern = os.path.join(directory, '**', f"{filename}.*")
    matching_files = glob.glob(search_pattern, recursive=True)
    return matching_files if matching_files else None

def search_path(folder_name):
    """searches for path from some common locations"""
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
    matches = difflib.get_close_matches(folder_name, common_paths.keys(), n=1, cutoff=0.6)
    if matches:
        return os.path.expandvars(common_paths[matches[0]])
    return None

def intent_detection(command):
    """Extract the intent of the user from the user input"""
    command = command.lower()
    doc = nlp(command)

    intents = {
        "open": ["open", "find and open", "access", "load", "show", "display", "retrieve", "let me see"],
        "search": ["find", "locate", "search"],
        "create": ["create", "make", "new file"],
        "rename": ["rename", "change name"],
        "move": ["move", "transfer"],
        "copy": ["copy", "duplicate"],
        "delete": ["delete", "remove"],
        "compress": ["compress", "zip"],
        "extract": ["extract", "unzip"],
        "storage": ["storage", "disk space", "free space", "disk usage"]
    }

    # Check multi-word phrases
    for intent, phrases in intents.items():
        for phrase in phrases:
            if phrase in command:
                return intent

    # Check individual lemmatized words
    for token in doc:
        for intent, words in intents.items():
            if token.lemma_ in set(words):
                return intent

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
    if "open" == detected_intents and file_name and folder:
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
        return True,"your file has been opened"
    except FileNotFoundError:
        return False,f"Error: File not found at '{filepath}'"
    except Exception as e:
        return False,f"An error occurred: {e}"
    
def file_create(file_name,filepath):
    """creates the file at the given location"""
    file_path_absolute = filepath + "\\" + file_name
    try:
        file = open(file_path_absolute,'x')
        return True,f"file created at {file_path_absolute}"
    except FileExistsError as e:
        return False,f"An error occurred: {e}"
    
def rename_file(old_file_name,new_file_name,file_path):
    """rename the file from old_file_name to new_file_name at the file_path"""
    try:
        old_file_path_absolute = file_path + "\\" + old_file_name
        new_file_path_absolute = file_path + "\\" + new_file_name
        os.rename(old_file_path_absolute, new_file_path_absolute)
        return True,"File renamed successfully."
    except FileNotFoundError:
        return False,"File not found."
    except PermissionError:
        return False,"Permission denied."
    except Exception as e:
        return False,f"An error occurred: {e}"

def move_file(file_name,old_file_path,new_file_path):
    """moves file from old_file_path to new_file_path"""
    try:
        old_file_path_absolute = old_file_path + "\\" + file_name
        new_file_path_absolute = new_file_path + "\\" + file_name
        os.replace(old_file_path_absolute,new_file_path_absolute)
        return True,"File moved succesfully"
    except FileNotFoundError:
        return False,"File not found"
    except PermissionError:
        return False,"Permission denied"
    except Exception as e:
        return False,f"An error occurred: {e}"
        
def copy_file(file_name,old_file_path,new_file_path,new_file_name=None):
    """copies a file from old_file_path to new_file_path and changes the copyed file name to new_file_name if want"""
    try:
        if new_file_name:
            old_file_path_absolute = old_file_path + "\\" + file_name
            new_file_path_absolute = new_file_path + "\\" + new_file_name
        else:
            old_file_path_absolute = old_file_path + "\\" + file_name
            new_file_path_absolute = new_file_path + "\\" + file_name
        cmd = "copy " + old_file_path_absolute + " " + new_file_path_absolute
        os.system(cmd)
        return True,"File copyed succesfully"
    except FileNotFoundError:
        return False,"File not found"
    except PermissionError:
        return False,"Permission denied"
    except Exception as e:
        return False,f"An error occurred: {e}"

def delete_file(file_name,filepath):
    """moves file_name to recycle bin"""
    file_path_absolute = filepath + "\\" + file_name
    try:
        send2trash.send2trash(file_path_absolute)
        return True,f"File '{file_name}' moved to trash successfully."
    except FileNotFoundError as e:
        return False,f"An error occurred: {e}"

def compress_file(folder_path,compressed_file_name):
    """compress folder to compressed_file_name with extention '.zip'"""
    try:
        shutil.make_archive(compressed_file_name, 'zip', folder_path)
        return f"Folder'{folder_path}' compressed successfully"
    except Exception as e:
        return f"An error occurred:'{e}'"

def extract_file(compressed, output_folder):
    """extract '.zip' file to a output folder"""
    try:
        shutil.unpack_archive(compressed, output_folder)
        return True,f"File'{compressed}' extracted successfully"
    except Exception as e:
        return False,f"An error occurred:'{e}'"

def get_storage_usage(path="/"):
    """return storage usage for a particular drive in GB"""
    try:
        total, used, free = shutil.disk_usage(path)
        return {
            "Total Storage": f"{total / (1024**3):.2f} GB",
            "Used Storage": f"{used / (1024**3):.2f} GB",
            "Free Storage": f"{free / (1024**3):.2f} GB"
        }
    except Exception as e:
        return f"An error occurred: {e}"

# handlers return true,massage to print and (1,1,1,1) means file_name, file_ext, file_path or folder or both exist respectively 
def handle_open(result):
    filename = ''
    if len(result["file"]) > 1:
        for i in result["file"]:
            if "." in i:
                filename = i
        if filename == "":
            return False,"which type of file is it?",(1,0,1,1)
    elif len(result["file"]) == 0:
        return False,"what would be the name of the file?",(0,0,1,1)
    else:
        if "." in result["file"][0]:
            filename = result["file"][0]
        else:
            return False,"which type of file is it?",(1,0,1,1)

    if len(result["path"]) == 0:
        if len(result["folder"]) == 0:
            return False,f"where would be the {filename} file be at?",(1,1,0,0)
        else:
            file_path = search_path(result['folder']) + '\\' + filename
    else:
        if filename in result["path"][0]:
            file_path = result["path"][0]
        else:
            file_path = result["path"][0] + '\\' + filename

    flag, message = file_open(file_path)
    if flag:
        return True,message,(1,1,1,1)
    else :
        return False,message,(1,1,1,1)


def handle_create(result):
    filename = ''
    if len(result["file"]) > 1:
        for i in result["file"]:
            if "." in i:
                filename = i
        if filename == "":
            return False,"what type of file do you want to create?",(1,0,1,1)
    elif len(result["file"]) == 0:
        return False,"what should be the file name?",(0,0,1,1)
    else:
        if "." in result["file"][0]:
            filename = result["file"][0]
        else:
            return False,"what type of file do you want to create?",(1,0,1,1)

    if len(result["path"]) == 0:
        if len(result["folder"]) == 0:
            return False,f"where should I create the file '{filename}'?",(1,1,0,0)
        else:
            file_path = search_path(result['folder'])
            if file_path:
                flag, message = file_create(filename, file_path)
                if flag:
                    return True,message,(1,1,1,1)
                else:
                    return False, message, (1, 1, 1, 1)
            else:
                return False,"Could not recognize the folder.",(1,1,0,0)
    else:
        flag, message = file_create(filename, result["path"][0])
        if flag:
            return True,message,(1,1,1,1)
        else:
            return False, message, (1, 1, 1, 1)

def handle_search(result):
    if len(result["file"]) == 0:
        return False, "What is the name of the file you're searching for?", (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0)
    flag, message = search_file(result['path'], result['file'])
    return flag, message, (1, 1 if '.' in result['file'][0] else 0, 1 if result["path"] else 0, 1 if result["folder"] else 0)

def handle_rename(result):
    if len(result["file"]) < 2:
        return False, "Please provide both the current file name and the new name.", (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0)

    old_file_name = result["file"][0]
    new_file_name = result["file"][1]

    if len(result["path"]) == 0:
        if len(result["folder"]) == 0:
            return False, f"Where is the file '{old_file_name}' located?", (1, 1 if "." in old_file_name else 0, 0, 0)
        else:
            file_path = search_path(result["folder"])
            if file_path:
                flag, message = rename_file(old_file_name, new_file_name, file_path)
                return flag, message, (1, 1 if "." in old_file_name else 0, 1, 1)
            else:
                return False, "Could not recognize the folder.", (1, 1 if "." in old_file_name else 0, 0, 0)
    else:
        flag, message = rename_file(old_file_name, new_file_name, result["path"][0])
        return flag, message, (1, 1 if "." in old_file_name else 0, 1, 1 if result["folder"] else 0)

def handle_move(result):
    if len(result["file"]) == 0:
        return False, "What is the name of the file you want to move?", (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0)

    filename = result["file"][0]

    if len(result["path"]) < 2:
        if len(result["folder"]) < 2:
            return False, "Please provide both the source and destination folders.", (1, 1 if "." in filename else 0, 0, 0)
        else:
            source_path = search_path(result["folder"][0])
            destination_path = search_path(result["folder"][1])
            if source_path and destination_path:
                flag, message = move_file(filename, source_path, destination_path)
                return flag, message, (1, 1 if "." in filename else 0, 1, 1)
            else:
                return False, "Could not recognize one or both folders.", (1, 1 if "." in filename else 0, 0, 0)
    else:
        flag, message = move_file(filename, result["path"][0], result["path"][1])
        return flag, message, (1, 1 if "." in filename else 0, 1, 1 if result["folder"] else 0)

def handle_copy(result):
    if len(result["file"]) == 0:
        return False, "What is the name of the file you want to copy?", (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0)

    filename = result["file"][0]

    if len(result["path"]) < 2:
        return False, "Please specify both the source and destination paths.", (1, 1 if "." in filename else 0, 0, 1 if result["folder"] else 0)

    old_path = result["path"][0]
    new_path = result["path"][1]

    new_file_name = result["file"][1] if len(result["file"]) > 1 else None

    flag, message = copy_file(filename, old_path, new_path, new_file_name)
    return flag, message, (1, 1 if "." in filename else 0, 1, 1 if result["folder"] else 0)

def handle_delete(result):
    if len(result["file"]) == 0:
        return False, "What is the name of the file you want to delete?", (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0)

    filename = result["file"][0]

    if len(result["path"]) == 0:
        if len(result["folder"]) == 0:
            return False, f"Where is the file '{filename}' located?", (1, 1 if "." in filename else 0, 0, 0)
        else:
            file_path = search_path(result["folder"])
            if file_path:
                flag, message = delete_file(filename, file_path)
                return flag, message, (1, 1 if "." in filename else 0, 1, 1)
            else:
                return False, "Could not recognize the folder.", (1, 1 if "." in filename else 0, 0, 0)
    else:
        flag, message = delete_file(filename, result["path"][0])
        return flag, message, (1, 1 if "." in filename else 0, 1, 1 if result["folder"] else 0)

def handle_compress(result):
    if len(result["file"]) == 0:
        return False, "What should be the name of the compressed file?", (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0)

    compressed_name = result["file"][0]

    if len(result["path"]) == 0:
        if len(result["folder"]) == 0:
            return False, "Which folder do you want to compress?", (1, 1 if "." in compressed_name else 0, 0, 0)
        else:
            folder_path = search_path(result["folder"])
            if folder_path:
                flag, message = compress_file(folder_path, compressed_name)
                return flag, message, (1, 1 if "." in compressed_name else 0, 1, 1)
            else:
                return False, "Could not recognize the folder to compress.", (1, 1 if "." in compressed_name else 0, 0, 0)
    else:
        flag, message = compress_file(result["path"][0], compressed_name)
        return flag, message, (1, 1 if "." in compressed_name else 0, 1, 1 if result["folder"] else 0)

def handle_extract(result):
    if len(result["file"]) == 0:
        return False, "What is the name of the compressed file you want to extract?", (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0)

    compressed_file = result["file"][0]

    if len(result["path"]) == 0:
        if len(result["folder"]) == 0:
            return False, f"Where should I extract '{compressed_file}'?", (1, 1 if "." in compressed_file else 0, 0, 0)
        else:
            output_folder = search_path(result["folder"])
            if output_folder:
                flag, message = extract_file(compressed_file, output_folder)
                return flag, message, (1, 1 if "." in compressed_file else 0, 1, 1)
            else:
                return False, "Could not recognize the target folder.", (1, 1 if "." in compressed_file else 0, 0, 0)
    else:
        flag, message = extract_file(compressed_file, result["path"][0])
        return flag, message, (1, 1 if "." in compressed_file else 0, 1, 1 if result["folder"] else 0)

def handle_storage(result):
    if len(result["path"]) == 0:
        if len(result["folder"]) == 0:
            usage = get_storage_usage()
            return True, usage, (0, 0, 0, 0)
        else:
            folder_path = search_path(result["folder"])
            if folder_path:
                usage = get_storage_usage(folder_path)
                return True, usage, (0, 0, 1, 1)
            else:
                return False, "Could not recognize the folder.", (0, 0, 0, 0)
    else:
        usage = get_storage_usage(result["path"][0])
        return True, usage, (0, 0, 1, 1 if result["folder"] else 0)

def file_management_cmd_execution(command,cmd_id):
    result = process_command(command)
    intent = result.get("intents")

    if intent == "open":
        return handle_open(result)
    elif intent == "search":
        return handle_search(result)
    elif intent == "create":
        return handle_create(result)
    elif intent == "rename":
        return handle_rename(result)
    elif intent == "move":
        return handle_move(result)
    elif intent == "copy":
        return handle_copy(result)
    elif intent == "delete":
        return handle_delete(result)
    elif intent == "compress":
        return handle_compress(result)
    elif intent == "extract":
        return handle_extract(result)
    elif intent == "storage":
        return handle_storage(result)
    else:
        return False
