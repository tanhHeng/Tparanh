import json, os
import pandas as pd
from .recognizer import Boxes, ParadigmRecognizer_ScoreScreen, ParadigmRecognizer_SelectingScreen
from typing import List
import time
from .utils.recognizer_utils import matchshape, to_better_timer
import logging

logger = logging.getLogger()

class Config:
    selecting: List[Boxes]
    score: List[Boxes]

class ParadigmRecognizerAuto:

    def __init__(self, records_file, config_file: str = "recognizer.json", use_gpu=True):
        self.config_file = config_file
        self.load()
        self.recognizers = {"selecting":{}, "score":{}}
        self.use_gpu = use_gpu
        self.records_file = pd.read_csv(records_file, index_col="song_level_id", encoding="utf-8")
    
    def _recognize(self, img, method, recognizer_class, log):
        t = time.time()
        img_shape = img.shape
        for i in self.config[method]:
            if matchshape(i["img_shape"], img_shape):
                if img_shape in self.recognizers[method].keys():
                    recognizer = self.recognizers[method][img_shape]
                    flag = "[Matched]"
                else:
                    recognizer = recognizer_class(records_file=self.records_file, boxes=i, use_gpu=self.use_gpu)
                    self.recognizers[method][img_shape] = recognizer
                    flag = "[Created]"
                break
        else:
            recognizer = recognizer_class(img, records_file=self.records_file, use_gpu=self.use_gpu)
            flag = "[New]"
            self.config[method].append(recognizer.export())
            self.recognizers[method][img_shape] = recognizer
        result = recognizer.recognize(img, record_log=log)
        if log:
            logger.info(flag, to_better_timer(time.time()-t), recognizer.latest_log)
        return result
    
    def recognize_selecting(self, img, log=True):
        return self._recognize(img, "selecting", ParadigmRecognizer_SelectingScreen, log)

    def recognize_score(self, img, log=True):
        return self._recognize(img, "score", ParadigmRecognizer_ScoreScreen, log)

    def recognize(self, img, log=True):
        try:
            try:
                return self.recognize_score(img, log)
            except Exception as e:
                return self.recognize_selecting(img, log)
        except Exception as e2:
            raise str(e)+"\n"+str(e2)

    def load(self):
        filename = self.config_file
        if os.path.isfile(filename):
            with open(filename, "r") as file:
                self.config = json.loads(file.read())
        else:
            self.config = {"selecting":[], "score":[]}
            self.save()
    
    def save(self):
        filename = self.config_file
        with open(filename, "w+") as file:
            file.write(json.dumps(self.config, indent="    ", skipkeys=True, default= lambda x: int(x)))
    
    def to_plain_text(self, idx, record):
        data = self.records_file.loc[idx]
        record = int(record)
        return "[{}] {}({}) # {}".format(data["title"], data["difficulty"], data["level"], record)