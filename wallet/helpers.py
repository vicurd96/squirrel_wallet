import os
import uuid

from django.utils.deconstruct import deconstructible


@deconstructible
class RandomFileName(object):
    def __init__(self, path):
        self.path = os.path.join(path, "%s")

    def __call__(self, instance, filename):
        # @note It's up to the validators to check if it's the correct file type in name or if one even exist.
        return self.path % (instance.user.id)