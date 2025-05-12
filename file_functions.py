import spacy
import os
import re
import glob
import send2trash
import shutil
import difflib
import sqlite3
import database as db
import extension as ext

nlp = spacy.load("en_core_web_sm")
nlp.Defaults.stop_words.remove("move")
nlp.vocab["move"].is_stop = False


def extract_file_name(command):
    """Extract possible filenames (without extensions) from user input."""
    doc = nlp(command)

    filtered_cmd = " ".join([token.text for token in doc if not token.is_stop]).lower()

    keywords = [
        "open",
        "rename",
        "move",
        "copy",
        "delete",
        "compress",
        "extract",
        "called",
    ]

    file_pattern = re.compile(r"\b[\w.-]+\.\w+\b")  # Captures filenames with extensions
    keyword_pattern = re.compile(
        r"(?:(?:" + "|".join(keywords) + r")\s+)([\w.-]+)", re.IGNORECASE
    )  # Captures words after keywords
    # Find filenames with extensions
    matches = file_pattern.findall(filtered_cmd)

    # Find filenames that follow keywords (without extensions)
    keyword_matches = keyword_pattern.findall(filtered_cmd)
    files = list(set(matches + keyword_matches))
    return files


def extract_path(command):
    """Extract possible file path form the user input"""
    file_path = re.findall(
        r"[A-Za-z]:\\(?:[^<>:\"/\\|?*\n]+\\)*[^<>:\"/\\|?*\n]*", command
    )
    return file_path


def extract_folder(text):
    """Extract possible folder names from user input."""
    match = re.findall(r"from ([\w\\:/. ]+)", text.lower())
    return match[0] if match else None


import os


def extract_file_extension(filename):
    """
    Extracts the file extension from a given filename.

    Parameters:
    - filename (str): The name of the file.

    Returns:
    - str: The file extension, including the dot (e.g., '.txt'). Returns an empty string if no extension is found.
    """
    _, file_extension = os.path.splitext(filename)
    return file_extension


# Example usage:
filename = "example.txt"
extension = extract_file_extension(filename)
print(extension)  # Output: .txt


def search_file(directory, filename):
    """Search recursively for exact filename (without extension)."""
    search_pattern = os.path.join(directory, "**", f"{filename}.*")
    matching_files = glob.glob(search_pattern, recursive=True)
    if matching_files:
        return matching_files
    return []


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
    matches = difflib.get_close_matches(
        folder_name, common_paths.keys(), n=1, cutoff=0.6
    )
    if matches:
        return os.path.expandvars(common_paths[matches[0]])
    return None

def intent_detection(command):
    """Detect file-related intent only if file/folder context is present."""
    command = command.lower()
    doc = nlp(command)

    # Only consider file-related intent if these keywords exist
    file_context_keywords = ["file", "folder", "document", "directory", "txt", "pdf", "doc", "jpg", "mp4"]

    if not any(word in command for word in file_context_keywords):
        return None  # not a file-related command

    intents = {
        "open": [
            "open",
            "find and open",
            "access",
            "load",
            "show",
            "display",
            "retrieve",
            "let me see",
        ],
        "search": ["find", "locate", "search"],
        "create": ["create", "make", "new file"],
        "rename": ["rename", "change name"],
        "move": ["move", "transfer"],
        "copy": ["copy", "duplicate"],
        "delete": ["delete", "remove"],
        "compress": ["compress", "zip"],
        "extract": ["extract", "unzip"],
        "storage": ["storage", "disk space", "free space", "disk usage"],
    }

    for intent, phrases in intents.items():
        for phrase in phrases:
            if phrase in command:
                return intent

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
        "path": path,
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
        return True, "your file has been opened"
    except FileNotFoundError:
        return False, f"Error: File not found at '{filepath}'"
    except Exception as e:
        return False, f"An error occurred: {e}"


def file_create(file_name, filepath):
    """creates the file at the given location"""
    file_path_absolute = filepath + "\\" + file_name
    try:
        file = open(file_path_absolute, "x")
        return True, f"file created at {file_path_absolute}"
    except FileExistsError as e:
        return False, f"An error occurred: {e}"


def rename_file(old_file_name, new_file_name, file_path):
    """rename the file from old_file_name to new_file_name at the file_path"""
    try:
        old_file_path_absolute = file_path + "\\" + old_file_name
        new_file_path_absolute = file_path + "\\" + new_file_name
        os.rename(old_file_path_absolute, new_file_path_absolute)
        return True, "File renamed successfully."
    except FileNotFoundError:
        return False, "File not found."
    except PermissionError:
        return False, "Permission denied."
    except Exception as e:
        return False, f"An error occurred: {e}"


def move_file(file_name, old_file_path, new_file_path):
    """moves file from old_file_path to new_file_path"""
    try:
        old_file_path_absolute = old_file_path + "\\" + file_name
        new_file_path_absolute = new_file_path + "\\" + file_name
        os.replace(old_file_path_absolute, new_file_path_absolute)
        return True, "File moved succesfully"
    except FileNotFoundError:
        return False, "File not found"
    except PermissionError:
        return False, "Permission denied"
    except Exception as e:
        return False, f"An error occurred: {e}"


def copy_file(file_name, old_file_path, new_file_path, new_file_name=None):
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
        return True, "File copyed succesfully"
    except FileNotFoundError:
        return False, "File not found"
    except PermissionError:
        return False, "Permission denied"
    except Exception as e:
        return False, f"An error occurred: {e}"


def delete_file(file_name, filepath):
    """moves file_name to recycle bin"""
    file_path_absolute = filepath + "\\" + file_name
    try:
        send2trash.send2trash(file_path_absolute)
        return True, f"File '{file_name}' moved to trash successfully."
    except FileNotFoundError as e:
        return False, f"An error occurred: {e}"


def compress_file(folder_path, compressed_file_name):
    """Compress folder to compressed_file_name with extension '.zip'"""
    try:
        # Ensure the compressed file name ends with '.zip'
        if not compressed_file_name.lower().endswith(".zip"):
            compressed_file_name += ".zip"

        # Create the zip archive from the folder
        shutil.make_archive(
            compressed_file_name.replace(".zip", ""), "zip", folder_path
        )

        return f"Folder '{folder_path}' compressed successfully to '{compressed_file_name}'"

    except Exception as e:
        return f"An error occurred: {e}"


def detect_file_type(text):
    text = text.lower()
    for file_type, keywords in ext.file_type_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return file_type
    return "text"


def extract_file(compressed, output_folder):
    """extract '.zip' file to a output folder"""
    try:
        shutil.unpack_archive(compressed, output_folder)
        return True, f"File'{compressed}' extracted successfully"
    except Exception as e:
        return False, f"An error occurred:'{e}'"


def get_storage_usage(path="/"):
    """return storage usage for a particular drive in GB"""
    try:
        total, used, free = shutil.disk_usage(path)
        return {
            "Total Storage": f"{total / (1024**3):.2f} GB",
            "Used Storage": f"{used / (1024**3):.2f} GB",
            "Free Storage": f"{free / (1024**3):.2f} GB",
        }
    except Exception as e:
        return f"An error occurred: {e}"


# handlers return true,massage to print and (1,1,1,1) means file_name, file_path or folder or both exist respectively
def handle_open(result):
    if not result["file"]:
        return False, "What would be the name of the file?", (0, 1, 1), None

    if not result["path"] and not result["folder"]:
        return False, "Where would the file be located?", (1, 0, 0), None

    filename = result["file"][0]
    file_ext = extract_file_extension(filename)

    # Use available paths or fallback to folders
    search_locations = []
    search_locations.append(
        result["path"] if result["path"] else search_path(result["folder"])
    )
    matches = []
    for location in search_locations:
        found = search_file(location, os.path.splitext(filename)[0])
        if found:
            matches.extend(found)
    if file_ext and matches:
        flag, message = file_open(search_locations[0] + "\\" + filename)
        return flag, message, (1, 1, 1), None

    if not matches:
        return (
            False,
            f"No file named {filename} found in given path/folder.",
            (1, 1, 1),
            None,
        )

    # Filter exact matches (case-insensitive by name without extension)
    base_name = os.path.splitext(filename)[0].lower()
    exact_matches = [
        m
        for m in matches
        if os.path.splitext(os.path.basename(m))[0].lower() == base_name
    ]

    if len(exact_matches) > 1:
        return (
            True,
            f"Multiple files found: {exact_matches}. Which one do you want?",
            (1, 1, 1),
            exact_matches,
        )
    elif len(exact_matches) == 1:
        flag, message = file_open(exact_matches[0])
        return flag, message, (1, 1, 1), exact_matches
    else:
        return False, f"No exact match found for '{filename}'.", (1, 1, 1), None


def handle_create(result):
    if not result["file"]:
        return False, "What would be the name of the file to create?", (0, 1, 1)

    if not result["path"] and not result["folder"]:
        return False, "Where should the file be created?", (1, 0, 0)

    filename = result["file"][0]
    if "." not in filename:
        ext = ext.extensions.get(detect_file_type(result["raw_text"]).lower(), ".txt")
        filename += ext

    # Use first path or folder
    location = result["path"][0] if result["path"] else search_path(result["folder"][0])
    file_path = os.path.join(location, filename)

    flag, message = file_create(file_path)
    return flag, message, (1, 1, 1)


def handle_search(result):
    if len(result["file"]) == 0:
        return (
            False,
            "What is the name of the file you're searching for?",
            (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0),
            None,
        )
    flag, matched_file, message = search_file(result["path"], result["file"])
    return (
        flag,
        message,
        (
            1,
            1 if "." in result["file"][0] else 0,
            1 if result["path"] else 0,
            1 if result["folder"] else 0,
        ),
        matched_file,
    )


def handle_rename(result):
    if not result["file"]:
        return False, "What file do you want to rename?", (0, 0, 1, 1)

    if len(result["file"]) < 2:
        return False, "What should be the new name?", (1, 0, 1, 1)

    if not result["path"] and not result["folder"]:
        return False, "Where is the file located?", (1, 1, 0, 0)

    old_name = result["file"][0]
    new_name = result["file"][1]
    search_locations = result["path"] if result["path"] else result["folder"]
    matches = []
    for location in search_locations:
        found = search_file(location, os.path.splitext(old_name)[0])
        if found:
            matches.extend(found)

    if not matches:
        return False, f"No file named {old_name} found.", (1, 1, 1, 1)

    base_name = os.path.splitext(old_name)[0].lower()
    exact_matches = [
        m
        for m in matches
        if os.path.splitext(os.path.basename(m))[0].lower() == base_name
    ]

    if len(exact_matches) > 1:
        return (
            True,
            f"Multiple files found: {exact_matches}. Which one do you want to rename?",
            (1, 1, 1, 1),
        )
    elif len(exact_matches) == 1:
        flag, message = rename_file(exact_matches[0], new_name)
        return flag, message, (1, 1, 1, 1)
    else:
        return False, f"No exact match found for '{old_name}'.", (1, 1, 1, 1)


def handle_move(result):
    if len(result["file"]) == 0:
        return (
            False,
            "What is the name of the file you want to move?",
            (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0),
        )

    filename = result["file"][0]

    # If the filename has no extension, try searching it
    if "." not in filename:
        if len(result["path"]) > 0:
            searched_path = []
            for i in result["path"]:
                search = search_file(i, filename)
                searched_path.extend(search if search else [])
            if len(searched_path) > 1:
                return (
                    False,
                    f"Multiple files found: {searched_path}. Which one do you want to move?",
                    (1, 0, 1, 1),
                )
            elif len(searched_path) == 1:
                filename = searched_path[0]
            else:
                return (
                    False,
                    "File not found, please specify a correct filename or path.",
                    (1, 0, 1, 1),
                )
        else:
            return False, "What is the full file name (with extension)?", (1, 0, 1, 1)

    if len(result["path"]) < 2:
        if len(result["folder"]) < 2:
            return (
                False,
                "Please provide both the source and destination folders.",
                (1, 1 if "." in filename else 0, 0, 0),
            )
        else:
            source_path = search_path(result["folder"][0])
            destination_path = search_path(result["folder"][1])
            if source_path and destination_path:
                flag, message = move_file(filename, source_path, destination_path)
                return flag, message, (1, 1 if "." in filename else 0, 1, 1)
            else:
                return (
                    False,
                    "Could not recognize one or both folders.",
                    (1, 1 if "." in filename else 0, 0, 0),
                )
    else:
        flag, message = move_file(filename, result["path"][0], result["path"][1])
        return (
            flag,
            message,
            (1, 1 if "." in filename else 0, 1, 1 if result["folder"] else 0),
        )


def handle_copy(result):
    if len(result["file"]) == 0:
        return (
            False,
            "What is the name of the file you want to copy?",
            (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0),
        )

    filename = result["file"][0]

    # If the filename has no extension, try searching it
    if "." not in filename:
        if len(result["path"]) > 0:
            searched_path = []
            for i in result["path"]:
                search = search_file(i, filename)
                searched_path.extend(search if search else [])
            if len(searched_path) > 1:
                return (
                    False,
                    f"Multiple files found: {searched_path}. Which one do you want to copy?",
                    (1, 0, 1, 1),
                )
            elif len(searched_path) == 1:
                filename = searched_path[0]
            else:
                return (
                    False,
                    "File not found, please specify a correct filename or path.",
                    (1, 0, 1, 1),
                )
        else:
            return False, "What is the full file name (with extension)?", (1, 0, 1, 1)

    # Check if both source and destination paths are provided
    if len(result["path"]) < 2:
        return (
            False,
            "Please specify both the source and destination paths.",
            (1, 1 if "." in filename else 0, 0, 1 if result["folder"] else 0),
        )

    old_path = result["path"][0]
    new_path = result["path"][1]

    new_file_name = result["file"][1] if len(result["file"]) > 1 else None

    flag, message = copy_file(filename, old_path, new_path, new_file_name)
    return (
        flag,
        message,
        (1, 1 if "." in filename else 0, 1, 1 if result["folder"] else 0),
    )


def handle_delete(result):
    if not result["file"]:
        return False, "What would be the name of the file to delete?", (0, 0, 1, 1)

    if not result["path"] and not result["folder"]:
        return False, "Where is the file located?", (1, 1, 0, 0)

    filename = result["file"][0]
    search_locations = result["path"] if result["path"] else result["folder"]
    matches = []
    for location in search_locations:
        found = search_file(location, os.path.splitext(filename)[0])
        if found:
            matches.extend(found)

    if not matches:
        return False, f"No file named {filename} found.", (1, 1, 1, 1)

    base_name = os.path.splitext(filename)[0].lower()
    exact_matches = [
        m
        for m in matches
        if os.path.splitext(os.path.basename(m))[0].lower() == base_name
    ]

    if len(exact_matches) > 1:
        return (
            True,
            f"Multiple files found: {exact_matches}. Which one do you want to delete?",
            (1, 1, 1, 1),
        )
    elif len(exact_matches) == 1:
        flag, message = delete_file(exact_matches[0])
        return flag, message, (1, 1, 1, 1)
    else:
        return False, f"No exact match found for '{filename}'.", (1, 1, 1, 1)


def handle_compress(result):
    if len(result["file"]) == 0:
        return (
            False,
            "What should be the name of the compressed file?",
            (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0),
        )

    compressed_name = result["file"][0]

    # If the compressed name has no extension, try searching it
    if "." not in compressed_name:
        if len(result["path"]) > 0:
            searched_path = []
            for i in result["path"]:
                search = search_file(i, compressed_name)
                searched_path.extend(search if search else [])
            if len(searched_path) > 1:
                return (
                    False,
                    f"Multiple files found: {searched_path}. Which one do you want to compress?",
                    (1, 0, 1, 1),
                )
            elif len(searched_path) == 1:
                compressed_name = searched_path[0]
            else:
                return (
                    False,
                    "File not found, please specify a correct filename or path.",
                    (1, 0, 1, 1),
                )
        else:
            return (
                False,
                "What is the full compressed file name (with extension)?",
                (1, 0, 1, 1),
            )

    # If the user wants to compress a folder (folder compression scenario)
    if len(result["folder"]) > 0:
        folder_path = search_path(result["folder"])
        if folder_path:
            flag, message = compress_file(folder_path, compressed_name)
            return flag, message, (1, 1 if "." in compressed_name else 0, 1, 1)
        else:
            return (
                False,
                "Could not recognize the folder to compress.",
                (1, 1 if "." in compressed_name else 0, 0, 0),
            )

    # Check for folder path or specified path for file compression
    if len(result["path"]) == 0:
        if len(result["folder"]) == 0:
            return (
                False,
                "Which folder do you want to compress?",
                (1, 1 if "." in compressed_name else 0, 0, 0),
            )
        else:
            folder_path = search_path(result["folder"])
            if folder_path:
                flag, message = compress_file(folder_path, compressed_name)
                return flag, message, (1, 1 if "." in compressed_name else 0, 1, 1)
            else:
                return (
                    False,
                    "Could not recognize the folder to compress.",
                    (1, 1 if "." in compressed_name else 0, 0, 0),
                )
    else:
        flag, message = compress_file(result["path"][0], compressed_name)
        return (
            flag,
            message,
            (1, 1 if "." in compressed_name else 0, 1, 1 if result["folder"] else 0),
        )


def handle_extract(result):
    if len(result["file"]) == 0:
        return (
            False,
            "What is the name of the compressed file you want to extract?",
            (0, 0, 1 if result["path"] else 0, 1 if result["folder"] else 0),
        )

    compressed_file = result["file"][0]

    if len(result["path"]) == 0:
        if len(result["folder"]) == 0:
            return (
                False,
                f"Where should I extract '{compressed_file}'?",
                (1, 1 if "." in compressed_file else 0, 0, 0),
            )
        else:
            output_folder = search_path(result["folder"])
            if output_folder:
                flag, message = extract_file(compressed_file, output_folder)
                return flag, message, (1, 1 if "." in compressed_file else 0, 1, 1)
            else:
                return (
                    False,
                    "Could not recognize the target folder.",
                    (1, 1 if "." in compressed_file else 0, 0, 0),
                )
    else:
        flag, message = extract_file(compressed_file, result["path"][0])
        return (
            flag,
            message,
            (1, 1 if "." in compressed_file else 0, 1, 1 if result["folder"] else 0),
        )


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


def file_management_cmd_execution(command, cmd_id):
    result = process_command(command)
    intent = result.get("intents")
    cmd_id = db.get_latest_cmd_id()
    if intent == "open":
        flag, message, db_input, file_found = handle_open(result)
        db.filepush(
            cmd_id,
            1,
            flag,
            result["file"] if db_input[0] == 1 else None,
            file_found,
            result["path"] if db_input[1] == 1 else None,
            result["folder"] if db_input[2] == 1 else None,
            message,
        )
        return message
    elif intent == "search":
        flag, message, db_input, file_found = handle_search(result)
        db.filepush(
            cmd_id,
            2,
            flag,
            result["file"] if db_input[0] == 1 else None,
            file_found,
            result["path"] if db_input[1] == 1 else None,
            result["folder"] if db_input[2] == 1 else None,
            message,
        )
    elif intent == "create":
        flag, message, db_input = handle_create(result)
        db.filepush(
            cmd_id,
            3,
            flag,
            result["file"] if db_input[0] == 1 else None,
            file_ext=ext.extensions.get(
                detect_file_type(result["raw_text"]).lower(), ".txt"
            ),
            file_path=result["path"] if db_input[1] == 1 else None,
            folders=result["folder"] if db_input[2] == 1 else None,
            message=message,
        )
        return message
    elif intent == "rename":
        flag, message, db_input = handle_rename(result)
        db.filepush(
            cmd_id,
            4,
            flag,
            result["file"] if db_input[0] == 1 else None,
            file_ext=(
                ext.extensions.get(detect_file_type(result["raw_text"]).lower(), ".txt")
                if db_input[1] == 1
                else None
            ),
            file_path=result["path"] if db_input[2] == 1 else None,
            folder=result["folder"] if db_input[3] == 1 else None,
            message=message,
        )
        return message
    elif intent == "move":
        flag, message, db_input = handle_move(result)
        db.filepush(
            cmd_id,
            5,
            flag,
            result["file"] if db_input[0] == 1 else None,
            file_ext=(
                ext.extensions.get(detect_file_type(result["raw_text"]).lower(), ".txt")
                if db_input[1] == 1
                else None
            ),
            file_path=result["path"] if db_input[2] == 1 else None,
            folder=result["folder"] if db_input[3] == 1 else None,
            message=message,
        )
        return message
    elif intent == "copy":
        flag, message, db_input = handle_copy(result)
        db.filepush(
            cmd_id,
            6,
            flag,
            result["file"] if db_input[0] == 1 else None,
            file_ext=(
                ext.extensions.get(detect_file_type(result["raw_text"]).lower(), ".txt")
                if db_input[1] == 1
                else None
            ),
            file_path=result["path"] if db_input[2] == 1 else None,
            folder=result["folder"] if db_input[3] == 1 else None,
            message=message,
        )
        return message
    elif intent == "delete":
        flag, message, db_input = handle_delete(result)
        db.filepush(
            cmd_id,
            7,
            flag,
            result["file"] if db_input[0] == 1 else None,
            file_ext=(
                ext.extensions.get(detect_file_type(result["raw_text"]).lower(), ".txt")
                if db_input[1] == 1
                else None
            ),
            file_path=result["path"] if db_input[2] == 1 else None,
            folder=result["folder"] if db_input[3] == 1 else None,
            message=message,
        )
        return message
    elif intent == "compress":
        flag, message, db_input = handle_compress(result)
        db.filepush(
            cmd_id,
            8,
            flag,
            result["file"] if db_input[0] == 1 else None,
            file_ext=(
                ext.extensions.get(detect_file_type(result["raw_text"]).lower(), ".txt")
                if db_input[1] == 1
                else None
            ),
            file_path=result["path"] if db_input[2] == 1 else None,
            folder=result["folder"] if db_input[3] == 1 else None,
            message=message,
        )
        return message
    elif intent == "extract":
        flag, message, db_input = handle_extract(result)
        db.filepush(
            cmd_id,
            9,
            flag,
            result["file"] if db_input[0] == 1 else None,
            file_ext=(
                ext.extensions.get(detect_file_type(result["raw_text"]).lower(), ".txt")
                if db_input[1] == 1
                else None
            ),
            file_path=result["path"] if db_input[2] == 1 else None,
            folder=result["folder"] if db_input[3] == 1 else None,
            message=message,
        )
        return message
    elif intent == "storage":
        flag, message, db_input = handle_storage(result)
        db.filepush(
            cmd_id,
            10,
            flag,
            None,
            None,
            result["path"] if db_input[2] == 1 else None,
            result["folder"] if db_input[3] == 1 else None,
            message=message,
        )
        return message
    else:
        return False


def incomplete_file_cmd_exe(cmd_id, new_command):
    pre_data_list = db.check_pre_file(1)

    pre_data = pre_data_list[0]  # Get the latest record
    if pre_data[8] == 1:
        return file_management_cmd_execution(new_command, cmd_id)

    new_result = process_command(new_command)
    new_intent = new_result["intents"]
    pre_intent = db.get_intent_type(pre_data[2])

    if new_intent != pre_intent:
        return file_management_cmd_execution(new_command, cmd_id)

    same_fields = []
    missing_fields = []
    conflicting_fields = []

    # Compare each field
    fields = {
        "file_name": (pre_data[3], new_result.get("file")),
        "file_found": (pre_data[4], new_result.get("found_files")),
        "file_ext": (pre_data[5], new_result.get("file_ext")),
        "file_path": (pre_data[6], new_result.get("path")),
        "folders": (pre_data[7], new_result.get("folder")),
    }

    for key, (old, new) in fields.items():
        if not old and new:
            missing_fields.append(key)
        elif old and not new:
            continue
        elif old == new:
            same_fields.append(key)
        elif str(old) != str(new):
            conflicting_fields.append(key)

    print("Same:", same_fields)
    print("Newly filled:", missing_fields)
    print("Conflicting:", conflicting_fields)

    if not conflicting_fields:
        new_command = generate_command_from_data(pre_data, new_result)
        return file_management_cmd_execution(new_command, cmd_id)

    return file_management_cmd_execution(new_command, cmd_id)


def generate_command_from_data(pre_data, new_result):
    # Get values from new_result if present, else fallback to pre_data
    file_name = new_result.get("file") or pre_data[3]
    folder = new_result.get("folder") or pre_data[7]
    path = new_result.get("path") or pre_data[6]
    intent = new_result.get("intents") or db.get_intent_type(pre_data[2])

    # Build command sentence based on intent
    sentence = intent

    if intent in ["open", "rename", "delete", "compress", "extract", "copy", "move"]:
        if file_name:
            sentence += f" {file_name}"
        if folder:
            sentence += f" from {folder}"
        if path and folder not in path:
            sentence += f" located at {path}"

    elif intent == "create":
        sentence = f"create a new file"
        if file_name:
            sentence += f" named {file_name}"
        if folder:
            sentence += f" in {folder}"

    elif intent == "search":
        sentence = f"search for {file_name or 'a file'}"
        if folder:
            sentence += f" in {folder}"

    elif intent == "storage":
        sentence = "check storage"

    return sentence

db.cmd_push("open hello.txt from documents", 2)
print(
    file_management_cmd_execution(
        "create  notepad", db.get_latest_cmd_id()
    )
)
