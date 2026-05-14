from aiogram import Router
from .start import router as start_router
from .catalog import router as catalog_router
from .cart import router as cart_router
from .about import router as about_router
from .contacts import router as contacts_router
from .admin import admin_router

main_router = Router(name="main")
main_router.include_router(start_router)
main_router.include_router(catalog_router)
main_router.include_router(cart_router)
main_router.include_router(about_router)
main_router.include_router(contacts_router)
main_router.include_router(admin_router)

__all__ = ["main_router"]
