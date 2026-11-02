VALUE = config_value
REASSIGNED = old_value
REASSIGNED = current_value


def supply():
    return supplied_source


class Product:
    @staticmethod
    def run():
        return product_source

    def instance_run(self):
        return instance_source


class DerivedProduct(Product):
    pass


shared = Product()
annotated: Product = unknown_product

updated: Product = unknown_product
updated: DerivedProduct
