import json
import random

def shuffle_jsonl_file(file_path):
    # Read the file content
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Parse JSON objects
    data = [json.loads(line.strip()) for line in lines]

    # Shuffle the data
    random.shuffle(data)

    # Write shuffled data to a new file
    shuffled_file_path = file_path.replace('.jsonl', '_shuffled.jsonl')
    with open(shuffled_file_path, 'w') as shuffled_file:
        for item in data:
            shuffled_file.write(json.dumps(item) + '\n')

    print(f"Shuffled data saved to: {shuffled_file_path}")


# Usage example
file_path = 'valid.jsonl'  # Replace with your file path
shuffle_jsonl_file(file_path)