from fastapi import Depends
from typing import Annotated

from .app import ColocoApp as ColocoAppType, get_current_app

ColocoApp = Annotated[ColocoAppType, Depends(get_current_app)]
