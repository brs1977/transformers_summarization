import os

from torch.utils.data import Dataset
import pandas as pd

class SummarizationDataset(Dataset):
    def __init__(self, path="", prefix="train"):
        assert os.path.isdir(path)
        self.prefix = prefix
        csv_file = os.path.join(path,prefix+'.csv')
        self.documents = pd.read_csv(csv_file, encoding="utf-8")

    def __len__(self):
        """ Returns the number of documents. """
        return self.documents.shape[0]

    def __getitem__(self, idx):
        row = self.documents.iloc[idx]
        abstract = row['abstract']
        title = row['title'] if self.prefix=="train" else None
        return str(idx), abstract, title


def fit_to_block_size(sequence, block_size, pad_token_id):
    """ Adapt the source and target sequences' lengths to the block size.
    If the sequence is shorter we append padding token to the right of the sequence.
    """
    if len(sequence) > block_size:
        return sequence[:block_size]
    else:
        sequence.extend([pad_token_id] * (block_size - len(sequence)))
        return sequence


def build_mask(sequence, pad_token_id):
    """ Builds the mask. The attention mechanism will only attend to positions
    with value 1. """
    mask = torch.ones_like(sequence)
    idx_pad_tokens = sequence == pad_token_id
    mask[idx_pad_tokens] = 0
    return mask


def encode_for_summarization(abs_lines, summary_lines, tokenizer):
    """ Encode the story and summary lines, and join them
    as specified in [1] by using `[SEP] [CLS]` tokens to separate
    sentences.
    """
    abs_lines_token_ids = [tokenizer.encode(line) for line in abs_lines]
    abs_token_ids = [token for sentence in abs_lines_token_ids for token in sentence]
    summary_lines_token_ids = [tokenizer.encode(line) for line in summary_lines]
    summary_token_ids = [token for sentence in summary_lines_token_ids for token in sentence]

    return abs_token_ids, summary_token_ids


def compute_token_type_ids(batch, separator_token_id):
    """ Segment embeddings as described in [1]

    The values {0,1} were found in the repository [2].

    Attributes:
        batch: torch.Tensor, size [batch_size, block_size]
            Batch of input.
        separator_token_id: int
            The value of the token that separates the segments.

    [1] Liu, Yang, and Mirella Lapata. "Text summarization with pretrained encoders."
        arXiv preprint arXiv:1908.08345 (2019).
    [2] https://github.com/nlpyang/PreSumm (/src/prepro/data_builder.py, commit fac1217)
    """
    batch_embeddings = []
    for sequence in batch:
        sentence_num = -1
        embeddings = []
        for s in sequence:
            if s == separator_token_id:
                sentence_num += 1
            embeddings.append(sentence_num % 2)
        batch_embeddings.append(embeddings)
    return torch.tensor(batch_embeddings)        