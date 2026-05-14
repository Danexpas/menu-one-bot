from sqlalchemy import Integer, String, Text, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    image_path: Mapped[str] = mapped_column(String(500), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    is_available: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    category: Mapped["Category"] = relationship("Category", back_populates="products")

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name} price={self.price}>"
