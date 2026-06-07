from typing import Annotated

from fastapi import Depends

from .app import ColocoApp as ColocoAppType, get_current_app

ColocoApp = Annotated[ColocoAppType, Depends(get_current_app)]
