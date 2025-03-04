import send2trash

def delete_file(file_name,filepath):
    file_path_absolute = filepath + "\\" + file_name
    try:
        send2trash.send2trash(file_path_absolute)
        return f"File '{file_name}' moved to trash successfully."
    except FileNotFoundError as e:
        return f"An error occurred: {e}"
    
print(delete_file("text.txt",r"C:\Users\akshg\Downloads"))