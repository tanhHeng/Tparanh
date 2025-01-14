from typing import Iterable, List
from abc import ABC, abstractmethod
from paddlex import create_pipeline
import numpy as np

class OcrObject:
    text: str
    score: int
    position: Iterable

class AbstractOcrModel(ABC):
    
    @abstractmethod
    def __init__(self, *args, **kwargs):
        self.ocr
    
    @abstractmethod
    def recognize(self, img, *args, **kwargs) -> List[OcrObject]:
        ...


class PaddleOcrModel(AbstractOcrModel):
    
    _singleton = None
    def __new__(cls, *args, **kwargs):
        if not cls._singleton:
            cls._singleton = object.__new__(cls)
        return cls._singleton

    def __init__(self, source = "OCR", context = "gpu", *args, **kwargs):
        if not hasattr(self, "ocr"):
            self.ocr = create_pipeline("OCR", *args, device=context, **kwargs)

    def _transform(self, result: Iterable) -> List[OcrObject]:
        return [{"text": _text, "score": _score1*_score2, "position": _pos} for _pos, _score1, _text, _score2 in zip(*list(next(result).values())[1:])]

    def recognize(self, img: np.ndarray, *args, **kwargs):
        if img.dtype != np.uint8:
            img = np.uint8(img)
        return self._transform(self.ocr.predict(img, *args, **kwargs))

    def fast_recognize(self, img, *args, **kwargs):
        if img.dtype != np.uint8:
            img = np.uint8(img)
        result = next(self.ocr.predict(img, *args, **kwargs))
        text = " ".join(result["rec_text"])
        dt_scores, rec_score = result["dt_scores"], result["rec_score"]
        if not (dt_scores and rec_score and text):
            return
        score = np.mean(dt_scores) * np.mean(rec_score)
        return {"text": text, "score": score}