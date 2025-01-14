import json
import pandas as pd
from .recognizer import Boxes, ParadigmRecognizer_ScoreScreen, ParadigmRecognizer_SelectingScreen
from typing import List
import time
from .utils.recognizer_utils import matchshape, to_better_timer

class Config:
    selecting: List[Boxes]
    score: List[Boxes]

class ParadigmRecognizerAuto:

    def __init__(self, records_file, config: Config={"selecting":[], "score":[]}, use_gpu=True):
        self.config = config
        self.recognizers = {"selecting":{}, "score":{}}
        self.use_gpu = use_gpu
        self.records_file = pd.read_csv(records_file, index_col="song_level_id")
    
    def _recognize(self, img, method, recognizer_class, log):
        t = time.time()
        img_shape = img.shape
        for i in self.config[method]:
            if matchshape(i["img_shape"], img_shape):
                if img_shape in self.recognizers[method].keys():
                    recognizer = self.recognizers[method][img_shape]
                    flag = "[Matched]"
                else:
                    recognizer = recognizer_class(boxes=i, use_gpu=self.use_gpu)
                    self.recognizers[method][img_shape] = recognizer
                    flag = "[Created]"
                break
        else:
            recognizer = recognizer_class(img, use_gpu=self.use_gpu)
            flag = "[New]"
            self.config[method].append(recognizer.export())
            self.recognizers[method][img_shape] = recognizer
        result = recognizer.recognize(img, record_log=log)
        if log:
            print(flag, to_better_timer(time.time()-t), recognizer.latest_log)
        return result
    
    def recognize_selecting(self, img, log=True):
        return self._recognize(img, "selecting", ParadigmRecognizer_SelectingScreen, log)

    def recognize_score(self, img, log=True):
        return self._recognize(img, "score", ParadigmRecognizer_ScoreScreen, log)

    def load(self, filename="config.json"):
        with open(filename, "r") as file:
            self.config = json.loads(file.read())
    
    def save(self, filename="config.json"):
        with open(filename, "w+") as file:
            file.write(json.dumps(self.config, indent="    ", skipkeys=True, default= lambda x: int(x)))
    
    def to_plain_text(self, idx, record):
        data = self.records_file.loc[idx]
        record = int(record)
        return "[{}] {}({}) # {}".format(data["title"], data["difficulty"], data["level"], record)