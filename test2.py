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

def handle_search(result):
    return search_file(result['path'], result['file'])

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
