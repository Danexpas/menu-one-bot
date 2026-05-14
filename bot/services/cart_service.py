from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from bot.models.cart import CartItem


class CartService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_items(self, user_id: int) -> list[CartItem]:
        result = await self.session.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
            .order_by(CartItem.created_at)
        )
        return list(result.scalars().all())

    async def add(self, user_id: int, product_id: int) -> CartItem:
        result = await self.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )
        item = result.scalar_one_or_none()
        if item:
            item.quantity += 1
        else:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
            self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def remove_one(self, user_id: int, product_id: int) -> bool:
        result = await self.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False
        if item.quantity > 1:
            item.quantity -= 1
        else:
            await self.session.delete(item)
        await self.session.commit()
        return True

    async def remove_all(self, user_id: int, product_id: int) -> bool:
        result = await self.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False
        await self.session.delete(item)
        await self.session.commit()
        return True

    async def clear(self, user_id: int) -> int:
        result = await self.session.execute(
            select(CartItem).where(CartItem.user_id == user_id)
        )
        items = result.scalars().all()
        count = len(items)
        for item in items:
            await self.session.delete(item)
        await self.session.commit()
        return count

    async def total(self, user_id: int) -> tuple[int, float]:
        items = await self.get_items(user_id)
        qty = sum(i.quantity for i in items)
        amount = sum(i.quantity * i.product.price for i in items)
        return qty, amount

    async def count(self, user_id: int) -> int:
        items = await self.get_items(user_id)
        return sum(i.quantity for i in items)
