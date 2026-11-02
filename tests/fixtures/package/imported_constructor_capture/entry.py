from .worker import Box
from .worker import Box as KeywordBase


def main():
    global Box
    return Box(1), Box(Box := 3)


class KeywordChild(KeywordBase, metaclass=(KeywordBase := type)):
    pass


def inherited_constructor():
    return KeywordChild(1)
