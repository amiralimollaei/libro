from datetime import datetime
from typing import Callable, Optional

import flet as ft

from ..callbacks import CallbackMixin, CallbackContext
from ..storage.paths import LibroPaths
from ..model.book import BookEntry, Genre


# views shared by most tabs

