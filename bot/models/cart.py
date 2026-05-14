from sqlalchemy import Integer, BigInteger, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped["Product"] = relationship("Product")

    def __repr__(self) -> str:
        return f"<CartItem user={self.user_id} product={self.product_id} qty={self.quantity}>"
