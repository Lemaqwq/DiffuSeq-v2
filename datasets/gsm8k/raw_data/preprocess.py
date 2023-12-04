import json

with open('train.txt', 'r') as file:
    lines = file.readlines()

preprocessed_data = []

line_idx = 0

for line in lines:
    line = line.strip()
    components = line.split('||')
    try:
        src = components[0].strip()
        rationales, trg = components[1].strip().split('####')
    

        preprocessed_line = {
            'src': src,
            'rationales': rationales.strip(),
            'trg': trg.strip()
        }
        preprocessed_data.append(preprocessed_line)

    except Exception:
        print(line_idx)

    finally:
        line_idx+=1

with open('post_process/train.jsonl', 'w') as file:
    for line in preprocessed_data:
        json.dump(line, file)
        file.write('\n')