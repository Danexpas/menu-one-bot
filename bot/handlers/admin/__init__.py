from aiogram import Router
from .auth import router as auth_router
from .categories import router as categories_router
from .products import router as products_router
from .settings import router as settings_router

admin_router = Router(name="admin")
admin_router.include_router(auth_router)
admin_router.include_router(categories_router)
admin_router.include_router(products_router)
admin_router.include_router(settings_router)

__all__ = ["admin_router"]
