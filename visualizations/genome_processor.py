from .genome_utils import *

from torchvision import transforms
import json
import matplotlib.pyplot as plt
import numpy as np
from statistics import mean
from tqdm import tqdm


transform = transforms.Compose([transforms.Resize((224, 224)),
                                transforms.ToTensor(),
                                transforms.Normalize((0.485, 0.456, 0.406),(0.229, 0.224, 0.225))])

class GenomeViz():

    def __init__(self, batch_size, model_path, image_data, annotations_data, transform=transform, eval_mode=False, parse_mode="matchmap"):
        """
        If eval_mode is true, compute localization score.
        Otherwise, load models, batch_size data, compute colocalization maps
        """
        self.eval_mode = eval_mode
        self.parse_mode = parse_mode
        self.transform = transform 
        
        self.batch_size = batch_size
        self.model_path = model_path
        self.image_data_file = 'data/visual_genome/coco_image_data.json'
        self.annotations_file = 'data/visual_genome/coco_phrase_data.json'

        self.image_data = image_data
        self.annotations_data = annotations_data

        self.image_model, self.caption_model = get_models_genome(self.model_path)

        self.data_loader, self.image_tensor, self.caption_glove, self.ann_ids = genome_load_data(self.batch_size,
                                                                                                 self.transform)
        if self.eval_mode:
            self.dataset = self.data_loader.dataset

        if self.parse_mode == 'matchmap':
            self.coloc_maps = gen_coloc_maps_matchmap(self.image_model, self.caption_model,
                                             self.image_tensor, self.caption_glove)
        else:
            self.coloc_maps = gen_coloc_maps_phrase(self.image_model, self.caption_model,
                                                    self.image_tensor, self.caption_glove)


    def __getitem__(self, index):
        """
        Fetch an index to create a data element from coloc maps, image and caption data
        :param index: index less than the batch_size of the data pooled
        :return element: data structure containing the image, caption and bounding box information
        used to evaluate and visualize the localization tasks being performed by the system.
        Can only be used when eval_mode is False.
        """
        assert not self.eval_mode, "Evaluation mode has to be False"
        raw_element = fetch_data_genome(index, self.coloc_maps, self.image_tensor, self.ann_ids)
        self.element = genome_element_processor(raw_element, self.image_data, self.annotations_data)
        self.score = hit_score_genome(self.element)

        return {'element': self.element, 'score':self.score}

    def __call__(self, save_flag=False, seg_flag=False, thresh=0.5, name=''):
        element = self.element
        name = element['caption_id']+'.png'
        if seg_flag:
            seg_viz_genome(element, thresh, save_flag, name)
        else:
            mask_viz_genome(element, save_flag, name)
        print("Score: ",self.score)

    def loc_eval(self, last):
        """
        When in eval mode, this will load entire dataset and iteratively find
        localization score for each image first and then average it to find 
        localization score for the entire dataset. Only works when eval_mode is True.
        :param last: number of images to evaluate. For full dataset, use len(data_loader.dataset)
        :return score_list: last - length list of all scores
        :return mean(score_list): mean localization score for dataset. 
        """
        score_list = list()
        for index in tqdm(np.arange(last)):
            image_tensor, caption_glove, cap_id = self.dataset[index]
            image_tensor = image_tensor.unsqueeze(0)
            caption_glove = caption_glove.unsqueeze(0)
            if self.parse_mode == "matchmap":
                coloc_map = gen_coloc_maps_matchmap(self.image_model, self.caption_model,
                                                    image_tensor, caption_glove)
            else:
                coloc_map = gen_coloc_maps_phrase(self.image_model, self.caption_model,
                                                    image_tensor, caption_glove)
            raw_element = fetch_data_genome(0, coloc_map, image_tensor, cap_id)
            element = genome_element_processor(raw_element, self.image_data, self.annotations_data)
            score = int(hit_score_genome(element))
            score_list.append(score)
            if not(index % 100):
                print(index,"--->",score, mean(score_list))

        return score_list, mean(score_list)


