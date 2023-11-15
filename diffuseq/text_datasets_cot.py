# import blobfile as bf
import numpy as np
from torch.utils.data import DataLoader, Dataset
from torch.utils.data.distributed import DistributedSampler
from itertools import chain
import glob
import torch
import json
import psutil
import datasets
import math
from datasets import Dataset as Dataset2

def load_data_text(
    batch_size, 
    seq_len, 
    deterministic=False, 
    data_args=None, 
    model_emb=None,
    split='train', 
    loaded_vocab=None,
    loop=True,
):
    """
    For a dataset, create a generator over (seqs, kwargs) pairs.

    Each seq is an (bsz, len, h) float tensor, and the kwargs dict contains zero or
    more keys, each of which map to a batched Tensor of their own.
    The kwargs dict can be used for some meta information.

    :param batch_size: the batch size of each returned pair.
    :param seq_len: the max sequence length (one-side).
    :param deterministic: if True, yield results in a deterministic order.
    :param data_args: including dataset directory, num of dataset, basic settings, etc.
    :param model_emb: loaded word embeddings.
    :param loaded_vocab: loaded word vocabs.
    :param loop: loop to get batch data or not.
    """

    print('#'*30, '\nLoading text data...')

    if "pretrain" in data_args.notes:
        print("#### Load Pretrain Data, fold=", data_args.data_split_num)
        training_data = get_corpus_pretrain(data_args, seq_len, split=split, loaded_vocab=loaded_vocab, split_num=data_args.data_split_num)
    else:
        training_data = get_corpus(data_args, seq_len, split=split, loaded_vocab=loaded_vocab)

    dataset = TextDataset(
        training_data,
        data_args,
        model_emb=model_emb
    )

    if split != 'test':
        sampler = DistributedSampler(dataset)
        data_loader = DataLoader(
            dataset,
            batch_size=batch_size,  # 20,
            # drop_last=True,
            sampler=sampler,
            # shuffle=not deterministic,
            num_workers=4,
        )
    else:
        data_loader = DataLoader(
            dataset,
            batch_size=batch_size,  # 20,
            # drop_last=True,
            # sampler=sampler,
            shuffle=not deterministic,
            num_workers=4,
        )

    if loop:
        return infinite_loader(data_loader)
    else:
        # print(data_loader)
        return iter(data_loader)

def infinite_loader(data_loader):
    while True:
        yield from data_loader

def helper_tokenize(sentence_lst, vocab_dict, seq_len):
    # Process.memory_info is expressed in bytes, so convert to megabytes
    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")
    raw_datasets = Dataset2.from_dict(sentence_lst)
    print(raw_datasets)
    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")

    def tokenize_function(examples):
        input_id_x = vocab_dict.encode_token(examples['src'])
        input_id_y = vocab_dict.encode_token(examples['trg'])
        result_dict = {'input_id_x': input_id_x, 'input_id_y': input_id_y}

        return result_dict

    tokenized_datasets = raw_datasets.map(
        tokenize_function,
        batched=True,
        num_proc=4,
        remove_columns=['src', 'trg'],
        load_from_cache_file=True,
        desc="Running tokenizer on dataset",
    )
    print('### tokenized_datasets', tokenized_datasets)
    print('### tokenized_datasets...example', tokenized_datasets['input_id_x'][0])
    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")

    def merge_and_mask(group_lst):
        lst = []
        mask = []
        for i in range(len(group_lst['input_id_x'])):
            end_token = group_lst['input_id_x'][i][-1]
            src = group_lst['input_id_x'][i][:-1]
            trg = group_lst['input_id_y'][i][:-1]
            while len(src) + len(trg) > seq_len - 3:
                if len(src)>len(trg):
                    src.pop()
                elif len(src)<len(trg):
                    trg.pop()
                else:
                    src.pop()
                    trg.pop()
            src.append(end_token)
            trg.append(end_token)

            lst.append(src + [vocab_dict.sep_token_id] + trg)
            mask.append([0]*(len(src)+1))
        group_lst['input_ids'] = lst
        group_lst['input_mask'] = mask
        return group_lst
    
    tokenized_datasets = tokenized_datasets.map(
        merge_and_mask,
        batched=True,
        num_proc=1,
        desc=f"merge and mask",
    )
    
    def pad_function(group_lst):
        max_length = seq_len
        group_lst['input_ids'] = _collate_batch_helper(group_lst['input_ids'], vocab_dict.pad_token_id, max_length)
        group_lst['input_mask'] = _collate_batch_helper(group_lst['input_mask'], 1, max_length)
        return group_lst

    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")

    lm_datasets = tokenized_datasets.map(
        pad_function,
        batched=True,
        num_proc=1,
        desc=f"padding",
    )

    print(lm_datasets, 'padded dataset')
    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")

    raw_datasets = datasets.DatasetDict()
    raw_datasets['train'] = lm_datasets
    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")
    return raw_datasets

def helper_tokenize_pretrain(sentence_lst, vocab_dict, seq_len, mask_ratio=0.5):
    # Process.memory_info is expressed in bytes, so convert to megabytes
    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")
    raw_datasets = Dataset2.from_dict(sentence_lst)
    print(raw_datasets)
    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")

    def tokenize_function(examples):
        input_id = vocab_dict.encode_token(examples['text'])
        result_dict = {'input_ids': input_id}

        return result_dict

    tokenized_datasets = raw_datasets.map(
        tokenize_function,
        batched=True,
        num_proc=4,
        remove_columns=['text'],
        keep_in_memory = True,
        load_from_cache_file=True,
        desc="Running tokenizer on dataset",
    )
    print('### tokenized_datasets', tokenized_datasets)
    print('### tokenized_datasets...example', tokenized_datasets['input_ids'][0])
    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")
    
    block_size = seq_len
    def group_texts(examples):
        concatenated_examples = {k: list(chain(*examples[k])) for k in examples.keys()}
        total_length = len(concatenated_examples[list(examples.keys())[0]])
        if total_length >= block_size:
            total_length = (total_length // block_size) * block_size
        result = {
            k: [t[i: i + block_size] for i in range(0, total_length, block_size)]
            for k, t in concatenated_examples.items()
        }
        random_mask_len = [np.random.randint(mask_ratio*block_size) for _ in range(len(result["input_ids"]))]
        result["input_mask"] = [[0]*l+[1]*(block_size-l) for l in random_mask_len]
        return result

    lm_datasets = tokenized_datasets.map(
        group_texts,
        batched=True,
        num_proc=4,
        keep_in_memory = True,
        load_from_cache_file=True,
        desc=f"Grouping texts in chunks of {block_size}",
    )

    print(lm_datasets, 'padded dataset')
    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")

    raw_datasets = datasets.DatasetDict()
    raw_datasets['train'] = lm_datasets
    print(f"RAM used: {psutil.Process().memory_info().rss / (1024 * 1024):.2f} MB")
    return raw_datasets

def preprocess_AQua(data_line):
    question = json.loads(data_line)['question'].strip()
    options = " ".join(json.loads(data_line)['options'])
    rationales = json.loads(data_line)['rationale'].strip().split("\n")
    correct = json.loads(data_line)['correct'].strip()

    
    cot_sequences = []

    question = question.replace('\n', ' ')

    question = question + " " + options + " "

    if len(rationales) == 4:
        rationales = [" ".join(rationales[0:2]), rationales[2], rationales[3]]

    elif len(rationales) > 4:
        step = math.ceil(len(rationales)/3)
        rationales = [" ".join(rationales[0:step]), " ".join(rationales[step:2*step]), " ".join(rationales[2*step:])]

    rationales = [i.replace('\n', ' ') for i in rationales]
    rationales = [""] + rationales + [" " + correct]

    for i in range(len(rationales)-1):
        cot_sequences.append(tuple([question+" ".join(rationales[0:i+1]), rationales[i+1]]))
    
    return cot_sequences


MAX_DATA_ROW = 200000
def get_corpus(data_args, seq_len, split='train', loaded_vocab=None):

    print('#'*30, '\nLoading dataset {} from {}...'.format(data_args.dataset, data_args.data_dir))

    sentence_lst = {'src':[], 'trg': []}
    
    if split == 'train':
        print('### Loading form the TRAIN set...')
        path = f'{data_args.data_dir}/train.jsonl'
    elif split == 'valid':
        print('### Loading form the VALID set...')
        path = f'{data_args.data_dir}/valid.jsonl'
    elif split == 'test':
        print('### Loading form the TEST set...')
        path = f'{data_args.data_dir}/test.jsonl'
    elif split == 'debug':
        print('### Loading form the DEBUG set...')
        path = f'{data_args.data_dir}/debug.jsonl'
    else:
        assert False, "invalid split for dataset"


    
    with open(path, 'r') as f_reader:
            for row in f_reader:
                cot_sentences = preprocess_AQua(row)
                if len(sentence_lst['src']) < MAX_DATA_ROW:
                    for cot_sentence in cot_sentences:
                        sentence_lst['src'].append(cot_sentence[0])
                        sentence_lst['trg'].append(cot_sentence[1])
                else:
                    break
    
    monitor_path = './proprocess_test_data.jsonl'
    monitor = open(monitor_path, 'a')
    for src, trg in zip(sentence_lst['src'], sentence_lst['trg']):
        print(json.dumps({"source": src, "target": trg}), file=monitor)
    monitor.close()

            # sentence_lst['src'].append(json.loads(row)['src'].strip())
            # sentence_lst['trg'].append(json.loads(row)['trg'].strip())

    print('### Data samples...\n', sentence_lst['src'][:2], sentence_lst['trg'][:2])
        
    # get tokenizer.
    vocab_dict = loaded_vocab

    train_dataset = helper_tokenize(sentence_lst, vocab_dict, seq_len)
    return train_dataset

def get_corpus_pretrain(data_args, seq_len, split='train', loaded_vocab=None, split_num=0):

    print('#'*30, '\nLoading dataset {} from {}...'.format(data_args.dataset, data_args.data_dir))

    sentence_lst = {'text': []}
    path = sorted(glob.glob(f"{data_args.data_dir}/*jsonl"))[split_num]
    with open(path, 'r') as f_reader:
        for row in f_reader:
            sentence_lst['text'].append(json.loads(row)['text'].strip())
    sentence_lst['text'] = sentence_lst['text'][len(sentence_lst['text'])//2:]
    if split == 'train':
        print('### Loading the TRAIN set...')
        sentence_lst['text'] = sentence_lst['text'][:-5000]
    elif split == 'valid':
        print('### Loading the VALID set...')
        sentence_lst['text'] = sentence_lst['text'][-5000:]

    print('### Data samples...\n', sentence_lst['text'][:2])
        
    # get tokenizer.
    vocab_dict = loaded_vocab

    train_dataset = helper_tokenize_pretrain(sentence_lst, vocab_dict, seq_len)
    return train_dataset

class TextDataset(Dataset):
    def __init__(self, text_datasets, data_args, model_emb=None):
        super().__init__()
        self.text_datasets = text_datasets
        self.length = len(self.text_datasets['train'])
        self.data_args = data_args
        self.model_emb = model_emb

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        with torch.no_grad():

            input_ids = self.text_datasets['train'][idx]['input_ids']
            hidden_state = self.model_emb(torch.tensor(input_ids))

            # obtain the input vectors, only used when word embedding is fixed (not trained end-to-end)
            arr = np.array(hidden_state, dtype=np.float32)

            out_kwargs = {}
            out_kwargs['input_ids'] = np.array(self.text_datasets['train'][idx]['input_ids'])
            out_kwargs['input_mask'] = np.array(self.text_datasets['train'][idx]['input_mask'])

            return arr, out_kwargs

def _collate_batch_helper(examples, pad_token_id, max_length, return_mask=False):
    result = torch.full([len(examples), max_length], pad_token_id, dtype=torch.int64).tolist()
    mask_ = torch.full([len(examples), max_length], pad_token_id, dtype=torch.int64).tolist()
    for i, example in enumerate(examples):
        curr_len = min(len(example), max_length)
        result[i][:curr_len] = example[:curr_len]
        mask_[i][:curr_len] = [1] * curr_len
    if return_mask:
        return result, mask_
    return result