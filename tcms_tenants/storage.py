# Copyright (c) 2019-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import os

from django.conf import settings
from django.utils.functional import cached_property
from django.core.files.storage import FileSystemStorage

from django_tenants import utils


class TenantFileSystemStorage(FileSystemStorage):
    """
    Implementation that extends core Django's FileSystemStorage for multi-tenant setups,
    storing files under induvidual directories. Workaround until
    https://github.com/tomturner/django-tenants/pull/252 gets merged.
    """

    @cached_property
    def relative_media_root(self):  # pylint: disable=no-self-use
        return getattr(settings, "MULTITENANT_RELATIVE_MEDIA_ROOT", "%s")

    @property  # not cached like in parent class
    def base_url(self):  # pylint: disable=invalid-overridden-method
        _url = super().base_url
        _url = os.path.join(
            _url, utils.parse_tenant_config_path(self.relative_media_root)
        )
        if not _url.endswith("/"):
            _url += "/"
        return _url

    @property  # not cached like in parent class
    def location(self):  # pylint: disable=invalid-overridden-method
        _location = os.path.join(
            super().location, utils.parse_tenant_config_path(self.relative_media_root)
        )
        return os.path.abspath(_location)

    def location_for_schema(self, schema_name):
        """
        Returns the storage location for a specific schema name by injecting
        it into relative_media_root.
        """
        relative_root = self.relative_media_root
        try:
            # Insert schema name
            return relative_root % schema_name
        except (TypeError, ValueError):
            # No %s in string; append schema name at the end
            return os.path.join(relative_root, schema_name)

    def delete_for_schema(self, schema_name):
        """
        Deletes the storage directory and all its files for a specific schema name.
        """
        storage_path = self.location_for_schema(schema_name)
        absolute_path = os.path.abspath(os.path.join(super().location, storage_path))
        self.delete(absolute_path)
