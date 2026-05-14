from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from bot.models.category import Category


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Category]:
        result = await self.session.execute(
            select(Category).order_by(Category.position, Category.id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, category_id: int) -> Category | None:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, emoji: str = "📦") -> Category:
        category = Category(name=name, emoji=emoji)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def update(self, category_id: int, name: str | None = None, emoji: str | None = None) -> Category | None:
        category = await self.get_by_id(category_id)
        if not category:
            return None
        if name is not None:
            category.name = name
        if emoji is not None:
            category.emoji = emoji
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def delete(self, category_id: int) -> bool:
        category = await self.get_by_id(category_id)
        if not category:
            return False
        await self.session.delete(category)
        await self.session.commit()
        return True

    async def count(self) -> int:
        result = await self.session.execute(select(Category))
        return len(result.scalars().all())
