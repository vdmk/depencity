class Registry:
    from .one import f

    retained = f()


Exposed = Registry.f


class FactoryRegistry:
    from .one import create

    retained = create()


ExposedFactory = FactoryRegistry.create
