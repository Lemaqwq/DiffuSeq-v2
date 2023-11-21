import json

with open('test_bigbench.txt', 'r') as file:
    lines = file.readlines()

preprocessed_data = []

for line in lines:
    line = line.strip()
    components = line.split('||')
    src = components[0].strip()
    rationales, trg = components[1].strip().split('####')

    preprocessed_line = {
        'src': src,
        'rationales': rationales.strip(),
        'trg': trg.strip()
    }
    preprocessed_data.append(preprocessed_line)

with open('preprocessed/test.jsonl', 'w') as file:
    for line in preprocessed_data:
        json.dump(line, file)
        file.write('\n')