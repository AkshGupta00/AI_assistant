def count_words_in_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            words = content.split()
            return len(words)
    except FileNotFoundError:
        return "File not found."

# Example usage
file_path = 'output_script.py'  # Replace with your file path
word_count = count_words_in_file(file_path)
print(f"Number of words in the file: {word_count}")
