from .utils.ocr_utils import PaddleOcrModel
from .utils.recognizer_utils import *
import re
import numpy as np
import pandas as pd

class Boxes:
    img_shape: tuple
    name_box: tuple
    record_box: tuple
    level_box: tuple

class ParadigmRecognizer_SelectingScreen:
    
    def __init__(self, init_img=None, records_file: pd.DataFrame=pd.DataFrame(), use_gpu=False,
                 boxes: Boxes=None):
        self.record_regex = re.compile(r"[0-9]{7}")
        self.level_regex = re.compile(r"[0-9]{1,2}\+?")
        
        self.cn_ocr: PaddleOcrModel = PaddleOcrModel("OCR", context = "gpu" if use_gpu else "cpu")
        
        self.records_file = records_file
        
        if init_img is None:
            if not boxes:
                raise TypeError("init_img or boxes must be given")
            self.img_shape, self.name_box, self.record_box, self.level_box = boxes["img_shape"], boxes["name_box"], boxes["record_box"], boxes["level_box"]
            return
        
        self.img_shape = init_img.shape
        self._init_recognize(init_img)
        # print(f"Initialized {self.img_shape}.")

    def _init_recognize(self, init_img):
        # OCR
        result = self.cn_ocr.recognize(to_black_white(init_img, 220))

        # split
        left_splits = [i["position"][2] for i in result if self.level_regex.fullmatch(i["text"]) and i["position"][0][0] <= init_img.shape[1]*0.6]
        w, b = linear([i[0] for i in left_splits], [i[1] for i in left_splits])

        # recognize boxex
        song_name = []
        song_level = (None, 0) # level, textbox_height
        for ocr_object in result:
            img_height, img_width, _ = init_img.shape
            pos1 = ocr_object["position"][0]
            if pos1[1] < img_height*0.1 or pos1[1] > img_height*0.9 or w*pos1[0] + b > pos1[1]:
                continue
            if pos1[1] < img_height*0.5:
                song_name.append(ocr_object)
            elif self.record_regex.fullmatch(text := ocr_object["text"]):
                song_record = ocr_object
            elif self.level_regex.fullmatch(text):
                if (textbox_height := ocr_object["position"][2][1] - pos1[1]) > song_level[1]:
                    song_level = (ocr_object, textbox_height)
            elif text == "PLAY":
                play_box = ocr_object["position"]

        # name_box
        song_name = [i for i in song_name if i["position"][2][0] > play_box[2][0]]
        if len(song_name) == 4:
            y_start = song_name[0]["position"][2][1]+1
            y_end = song_name[2]["position"][0][1]-1
            x_start = int((y_start-b)//w + 1)
            x_end = (song_name[1]["position"][2][0] + img_width) // 2
            self.name_box = ((x_start, y_start), (x_end, y_end))
        else:
            raise TypeError(f"Cannot recognize song name: {song_name}.")

        # record_box
        xy_start, xy_end = song_record["position"][0], song_record["position"][2]
        x_offset, y_offset = (xy_end[0] - xy_start[0])//8, (xy_end[1] - xy_start[1])//4
        self.record_box = record_box = ((xy_start[0] - x_offset, xy_start[1] - y_offset), (xy_end[0] + x_offset, xy_end[1] + y_offset))

        # level_box
        self.level_box = ((record_box[0][0], song_level[0]["position"][0][1]), (play_box[2][0], song_level[0]["position"][2][1]))
        # print("Boxes completed.")

        self.latest_log = "NAME\tLEVEL\tDIFFICULTY\tRECORD"
        self.latest_update_log = "NAME\tDIFFICULTY(LEVEL)\tRECORD0->RECORD1"
    
    def fast_ocr(self, img, score = False):
        result = self.cn_ocr.fast_recognize(img)
        if not result:
            return
        result = result
        return (result["text"], result["score"]) if score else result["text"]
    
    def recognize_level(self, level_img, score = False):
        result = self.cn_ocr.fast_recognize(to_black_white(level_img))
        if not result:
            return
        if score:
            return result["text"], result["score"]
        return result["text"]

    def recognize_record(self, record_img):
        record = self.cn_ocr.fast_recognize(top_bottom_padding(to_black_white(record_img)))
        if not record:
            return
        else:
            record = record["text"]
        if not self.record_regex.fullmatch(record):
            record2 = self.cn_ocr.fast_recognize(top_bottom_padding(record_img))
            if not record2:
                return record
            record2 = record2["text"]
            if self.record_regex.fullmatch(record2):
                record = record2
        return record
    
    def recognize(self, img, record_log = False, ignore_idx = None):
        if not matchshape(img.shape, self.img_shape):
            raise TypeError("Mismatch image shape.")

        name_img = to_black_white(split_img(img, self.name_box), 245)
        name_result = self.fast_ocr(name_img, True)
        if not name_result:
            return
        name, score = name_result

        level_flag = False
        level_result = self.recognize_level(split_img(img, self.level_box), score = True)
        if level_result is None:
            level = level_score = None
        elif not self.level_regex.fullmatch(level_result[0]):
            level, level_score = level_result
        else:
            level, level_score = level_result
            level_flag = True
            
        record = self.recognize_record(split_img(img, self.record_box))
        if not record:
            return

        if level_flag:
            idx, similarity = self.search(name, level)
        else:
            idx, similarity = self.search(name)

        total_score = score*similarity
        
        if total_score < 0.15 or score is np.nan:
            return
        if record_log and idx != ignore_idx:
            data = self.records_file.loc[idx]
            score_text = "{}%={}%({})*{}%({})".format("%.02f"%(total_score*100), "%.02f"%(score*100), name, "%.02f"%(similarity*100), data['title'])
            if total_score < 0.4:
                score_text = score_text + " ?"
            # level_score_text = "%.02f"%(level_score*100)+"%" if level_score else "?"
            level_score_text = "{}% {}".format("%.02f"%(level_score*100), level) if level else "?% ?"
            if not level_flag:
                level_score_text = level_score_text+" ?"
            difficulty = "?(?)" if level is None else f"{data['difficulty']}({data['level']})"
            record_text = "# {} {}".format(record, '' if self.record_regex.fullmatch(record) else '?')
            self.latest_log = "\t".join([score_text, level_score_text, difficulty, record_text])
        return idx, record
    
    def update_record(self, index, record, record_log = False):
        try:
            record = np.float64(record)
            flag = True
        except:
            flag = False
        if record_log:
            data = self.records_file.iloc[index]
            if flag:
                self.latest_update_log = f"{data['title']}\t{data['difficulty']}(data['level'])\t{data['score']} -> {record}"
            else:
                self.latest_update_log = f"{data['title']}\t{data['difficulty']}(data['level'])\tWrong record: {record} (SKIP)"
        if flag:
            self.records_file.loc[index, "score"] = record
    
    def search(self, name, level = None):
        records_file = self.records_file
        if level:
            level = int(level[:-1]) if level[-1] == "+" else int(level)
            data = records_file[(records_file["level"] >= level) & (records_file["level"] < level+1)]
        else:
            data = records_file
        similarity = [get_string_similarity(i, name) for i in data["title"]]
        return data.index.tolist()[np.argmax(similarity)], max(similarity)
    
    def export(self):
        return {
            "img_shape": self.img_shape,
            "name_box": self.name_box,
            "record_box": self.record_box,
            "level_box": self.level_box
        }

class ParadigmRecognizer_ScoreScreen(ParadigmRecognizer_SelectingScreen):

    def __init__(self, init_img=None, records_file=pd.DataFrame(), use_gpu=True,
                 boxes: Boxes=None):
        super().__init__(init_img, records_file, use_gpu, boxes)

    def _init_recognize(self, init_img):
        height, width, _ = init_img.shape

        # OCR
        result = self.cn_ocr.recognize(init_img)

        # name box
        middle_x = width // 2
        lim_y = height // 3
        middle_boxes = [i for i in result if self._in_middle(middle_x, i["position"]) and i["position"][2][1] < lim_y]
        if not len(middle_boxes) == 3:
            raise TypeError("Cannot recognize name box.")
        if not (difficulty := self._match_difficulty(middle_boxes[2]["text"])):
            raise TypeError("Cannot recognize difficulty box.")
        name_box, level_box = middle_boxes[0]["position"], middle_boxes[2]["position"]
        name_box = ((width//4, name_box[0][1] - (name_box[2][1] - name_box[0][1])//2), (int(width//4*3), middle_boxes[1]["position"][0][1]))
        level_box = ((width//3, level_box[0][1]), (int(width//3*2), level_box[2][1]))

        # record box
        lim_y = height//2
        boxes = [i for i in result if i["position"][2][0] <= middle_x and i["position"][2][1] > lim_y and self.record_regex.fullmatch(i["text"])]
        if len(boxes) > 1:
            idx = np.argmax([i["position"][2][1] - i["position"][0][1] for i in boxes])
            record_box = boxes[idx]["position"]
        elif len(boxes) == 0:
            raise TypeError("Cannot recognize record box.")
        else:
            record_box = boxes[0]["position"]
        record_box_offsetx = (record_box[2][0] - record_box[0][0])//10
        record_box = ((record_box[0][0] - record_box_offsetx, record_box[0][1]), (record_box[2][0] + record_box_offsetx, record_box[2][1]))

        self.name_box, self.level_box, self.record_box = name_box, level_box, record_box

    def _in_middle(self, middle_x, position_box):
        return middle_x > position_box[0][0] and middle_x < position_box[2][0]

    def _match_difficulty(self, text):
        if re.search("massive", text, re.IGNORECASE):
            return "Massive"
        if re.search("invaded", text, re.IGNORECASE):
            return "Invaded"
        if re.search("detected", text, re.IGNORECASE):
            return "Detected"
        text = re.sub(r"[0-9\s]", "", text.lower())
        difficulties = ["massive", "invaded", "detected"]
        matches = [get_string_similarity(i, text) for i in difficulties]
        if max(matches) < 0.7:
            return
        return difficulties[np.argmax(matches)]

    def _match_difficulty_string(self, string: str, difficulty: str):
        string, difficulty = string.upper(), difficulty.upper()
        result = []
        for i in range(len(string)):
            result.append(get_string_similarity(string[:i], difficulty))
        return string[:np.argmax(result)]

    def recognize(self, img, record_log = False, ignore_idx = None):
        if not matchshape(img.shape, self.img_shape):
            raise TypeError("Mismatch image shape.")

        name, score = self.fast_ocr(to_black_white(split_img(img, self.name_box)), True)
        level_text, level_score = self.fast_ocr(top_bottom_padding(split_img(img, self.level_box)), True)
        record = self.recognize_record(split_img(img, self.record_box))
        difficulty = self._match_difficulty(level_text)
        if not difficulty:
            raise TypeError(f"Cannot recognize difficulty: '{level_text}'.")
        level = re.match((difficulty if difficulty in level_text else self._match_difficulty_string(level_text, difficulty))+r"\s*(?P<level>[0-9]{1,2}\+?)", level_text, re.IGNORECASE)
        if not level:
            raise TypeError(f"Cannot recognize level: '{level_text}'.")
        level = level.group("level")
        idx, similarity = self.search(name, level)

        total_score = score * similarity
        if record_log and idx != ignore_idx:
            data = self.records_file.loc[idx]
            score_text = "{}%={}%({})*{}%({})".format("%.02f"%(total_score*100), "%.02f"%(score*100), name, "%.02f"%(similarity*100), data['title'])
            if total_score < 0.4:
                score_text = score_text + " ?"
            level_score_text = "{}% {}".format("%.02f"%(level_score*100), level) if level else "?% ?"
            difficulty = f"{data['difficulty']}({data['level']})"
            record_text = "# {} {}".format(record, '' if self.record_regex.fullmatch(record) else '?')
            self.latest_log = "\t".join([score_text, level_score_text, difficulty, record_text])
        return idx, record