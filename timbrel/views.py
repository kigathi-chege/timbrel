from .utils import import_classes, prepare_modules

globals().update(import_classes(prepare_modules("views")))
