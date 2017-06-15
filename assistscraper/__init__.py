from . import scraper, courses_parser
from .scraper import *
from .courses_parser import *


__all__ = [
    *scraper.__all__,
    *courses_parser.__all__,
]
