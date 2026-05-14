from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.product import Product


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_category(self, category_id: int) -> list[Product]:
        result = await self.session.execute(
            select(Product)
            .where(Product.category_id == category_id, Product.is_available == True)
            .order_by(Product.position, Product.id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self.session.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.category))
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Product]:
        result = await self.session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .order_by(Product.category_id, Product.position, Product.id)
        )
        return list(result.scalars().all())

    async def create(
        self,
        category_id: int,
        name: str,
        description: str | None,
        price: float,
        image_path: str | None = None,
    ) -> Product:
        product = Product(
            category_id=category_id,
            name=name,
            description=description,
            price=price,
            image_path=image_path,
        )
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def update(
        self,
        product_id: int,
        name: str | None = None,
        description: str | None = None,
        price: float | None = None,
        image_path: str | None = None,
        category_id: int | None = None,
        is_available: bool | None = None,
    ) -> Product | None:
        product = await self.get_by_id(product_id)
        if not product:
            return None
        if name is not None:
            product.name = name
        if description is not None:
            product.description = description
        if price is not None:
            product.price = price
        if image_path is not None:
            product.image_path = image_path
        if category_id is not None:
            product.category_id = category_id
        if is_available is not None:
            product.is_available = is_available
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def delete(self, product_id: int) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            return False
        await self.session.delete(product)
        await self.session.commit()
        return True

    async def count_by_category(self, category_id: int) -> int:
        result = await self.session.execute(
            select(Product).where(Product.category_id == category_id)
        )
        return len(result.scalars().all())
