import os
import torch.utils.data as data

from .coco_loader import COCODataset
from .flickr_loader import FlickrDataset
from .genome_loader import VisualGenome

def get_loader_coco(transform,
                    mode="train",
                    batch_size=1,
                    start_word="<start>",
                    end_word="<end>",
                    unk_word="<unk>",
                    num_workers=4,
                    cocoapi_loc="",
                    vocab_glove_file="data/mscoco/vocab_glove.json",
                    test_size=1000,
                    pad_caption=True):
    """Return the data loader.
    Parameters:
        transform: Image transform.
        mode: One of "train", "val" or "test".
        batch_size: Batch size (if in testing mode, must have batch_size=1).
        vocab_threshold: Minimum word count threshold.
        vocab_file: File containing the vocabulary.
        start_word: Special word denoting sentence start.
        end_word: Special word denoting sentence end.
        unk_word: Special word denoting unknown words.
        vocab_from_file: If False, create vocab from scratch & override any
                         existing vocab_file. If True, load vocab from
                         existing vocab_file, if it exists.
        vocab_glove_file: This JSON file contains the Glove embeddings for each
                    word in the vocabulary.
        num_workers: Number of subprocesses to use for data loading
        cocoapi_loc: The location of the folder containing the COCO API:
                     https://github.com/cocodataset/cocoapi
        fetch_mode: Indicates mode of retrieving data
    """

    assert mode in ["train", "val", "test"], "mode must be one of 'train', 'val' or 'test'."
    # Based on mode (train, val, test), obtain img_folder and annotations_file
    if mode == "train":
        img_folder = os.path.join(cocoapi_loc, "data/mscoco/images/train2014/")
        annotations_file = os.path.join(cocoapi_loc, "data/mscoco/annotations/captions_train2014.json")
    if mode == "val":
        img_folder = os.path.join(cocoapi_loc, "data/mscoco/images/val2014/")
        annotations_file = os.path.join(cocoapi_loc, "data/mscoco/annotations/captions_val2014.json")
    if mode == "test":
        assert batch_size == 1, "Please change batch_size to 1 if testing your model."
        img_folder = os.path.join(cocoapi_loc, "data/mscoco/images/test2014/")
        annotations_file = os.path.join(cocoapi_loc, "data/mscoco/annotations/image_info_test2014.json")

    # COCO caption dataset
    dataset = COCODataset(transform=transform,
                          mode=mode,
                          batch_size=batch_size,
                          annotations_file=annotations_file,
                          vocab_glove_file=vocab_glove_file,
                          img_folder=img_folder,
                          start_word=start_word,
                          end_word=end_word,
                          unk_word=unk_word,
                          pad_caption=True,
                          pad_limit=20)

    if dataset.pad_caption:
        # Randomly sample a caption length, and sample indices with that length.
        indices = dataset.get_indices()
        # Create and assign a batch sampler to retrieve a batch with the sampled indices.
        initial_sampler = data.sampler.SubsetRandomSampler(indices=indices)
        # data loader for COCO dataset.
        data_loader = data.DataLoader(dataset=dataset,
                                      num_workers=num_workers,
                                      batch_sampler=data.sampler.BatchSampler(sampler=initial_sampler,
                                                                              batch_size=dataset.batch_size,
                                                                              drop_last=False))
    else:
        data_loader = data.DataLoader(dataset=dataset,
                                      batch_size=dataset.batch_size,
                                      shuffle=True,
                                      num_workers=num_workers)

    return data_loader


def get_loader_flickr(transform,
                      mode="train",
                      batch_size=1,
                      start_word="<start>",
                      end_word="<end>",
                      unk_word="<unk>",
                      num_workers=1,
                      flickr_loc="",
                      vocab_glove_file="data/flickr_30kentities/vocab_glove_flickr.json",
                      pad_caption=True,
                      pad_limit=20,
                      parse_mode='phrase'):
    image_root = os.path.join(flickr_loc, 'data', 'flickr_30kentities', 'flickr30k-images')
    sentences_root = os.path.join(flickr_loc, 'data', 'flickr_30kentities', 'annotations_flickr', 'Sentences')
    annotations_root = os.path.join(flickr_loc, 'data', 'flickr_30kentities', 'annotations_flickr', 'Annotations')

    assert mode in ["train", "val", "test"], "mode must be one of 'train', 'val' or 'test'."

    # Based on mode (train, val, test), obtain img_folder and annotations_file
    if mode == "train":
        img_folder = os.path.join(flickr_loc, image_root, 'train')
        annotations_folder = os.path.join(flickr_loc, annotations_root, 'train')
        sentences_folder = os.path.join(flickr_loc, sentences_root, 'train')
        sentences_file = os.path.join(sentences_folder, 'data.json')

    if mode == "val":
        img_folder = os.path.join(flickr_loc, image_root, 'val')
        annotations_folder = os.path.join(flickr_loc, annotations_root, 'val')
        sentences_folder = os.path.join(flickr_loc, sentences_root, 'val')
        sentences_file = os.path.join(sentences_folder, 'data.json')

    if mode == "test":
        img_folder = os.path.join(flickr_loc, image_root, 'test')
        annotations_folder = os.path.join(flickr_loc, annotations_root, 'test')
        sentences_folder = os.path.join(flickr_loc, sentences_root, 'test')
        sentences_file = os.path.join(sentences_folder, 'data.json')

    dataset = FlickrDataset(transform=transform,
                            mode=mode,
                            batch_size=batch_size,
                            sentences_file=sentences_file,
                            sentences_root=sentences_folder,
                            annotations_root=annotations_folder,
                            image_root=img_folder,
                            vocab_glove_file=vocab_glove_file,
                            parse_mode=parse_mode,
                            pad_caption=pad_caption,
                            start_word=start_word,
                            end_word=end_word,
                            unk_word=unk_word,
                            pad_limit=pad_limit)

    if dataset.pad_caption:
        # Randomly sample a caption length, and sample indices with that length.
        indices = dataset.get_indices()
        # Create and assign a batch sampler to retrieve a batch with the sampled indices.
        initial_sampler = data.sampler.SubsetRandomSampler(indices=indices)
        # data loader for COCO dataset.
        data_loader = data.DataLoader(dataset=dataset,
                                      num_workers=num_workers,
                                      batch_sampler=data.sampler.BatchSampler(sampler=initial_sampler,
                                                                              batch_size=dataset.batch_size,
                                                                              drop_last=False))

    else:
        data_loader = data.DataLoader(dataset=dataset,
                                      batch_size=dataset.batch_size,
                                      shuffle=True,
                                      num_workers=num_workers)

    return data_loader


def get_loader_genome(transform,
                      mode="train",
                      batch_size=1,
                      start_word="<start>",
                      end_word="<end>",
                      unk_word="<unk>",
                      num_workers=1,
                      genome_loc="",
                      vocab_glove_file="data/visual_genome/vocab_glove.json",
                      pad_caption=True,
                      pad_limit=20):
  
    image_root = os.path.join(genome_loc,'data','visual_genome', 'images')
    annotations_file = os.path.join(genome_loc, 'data','visual_genome', 'coco_phrase_data.json')
    vocab_glove_file = os.path.join(genome_loc, 'data', 'visual_genome', 'vocab_glove.json')

    dataset = VisualGenome(transform=transform, 
                           mode='train', 
                           batch_size=batch_size,
                           annotations_file=annotations_file,
                           img_folder=image_root,
                           vocab_glove_file=vocab_glove_file,
                           start_word=start_word,
                           end_word=end_word,
                           unk_word=unk_word,
                           pad_caption=pad_caption,
                           pad_limit=pad_limit)

    if dataset.pad_caption:
        # Randomly sample a caption length, and sample indices with that length.
        indices = dataset.get_indices()
        # Create and assign a batch sampler to retrieve a batch with the sampled indices.
        initial_sampler = data.sampler.SubsetRandomSampler(indices=indices)
        # data loader for COCO dataset.
        data_loader = data.DataLoader(dataset=dataset,
                                      num_workers=num_workers,
                                      batch_sampler=data.sampler.BatchSampler(sampler=initial_sampler,
                                                                              batch_size=dataset.batch_size,
                                                                              drop_last=False))

    else:
        data_loader = data.DataLoader(dataset=dataset,
                                      batch_size=dataset.batch_size,
                                      shuffle=True,
                                      num_workers = num_workers)

    return data_loader
