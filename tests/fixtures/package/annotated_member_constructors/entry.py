from .models import Container


def annotated_owner(owner: Container):
    result = owner.Factory()
    return result.run()


def annotated_class(owner: type[Container]):
    result = owner.Factory()
    return result.run()


def constructed_owner():
    owner = Container()
    result = owner.Factory()
    return result.run()
