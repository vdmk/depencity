from .worker import *


def main():
    return Publisher(), DeletesDecoratorAlias(), DeletesKeywordAlias()


def read_deleted_header_aliases():
    return decorator_alias, keyword_alias
