from fastapi import APIRouter
from db.database import SessionLocal, OrderModel
from models.order import OrderCreate
from services.order_service import OrderService

router = APIRouter()
order_service = OrderService()


@router.post("/")
def create_order(data: OrderCreate):
    result = order_service.create_order(data.book_id, data.quantity, data.customer_email)
    if not result:
        return {"error": "Book not found"}
    return result


@router.get("/{order_id}")
def read_order(order_id: int):
    # Direct DB access instead of going through service
    db = SessionLocal()
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    db.close()
    if not order:
        return {"error": "Order not found"}
    return {
        "id": order.id,
        "book_id": order.book_id,
        "quantity": order.quantity,
        "total": order.total,
        "status": order.status,
    }


@router.put("/{order_id}/status")
def update_status(order_id: int, status: str):
    return order_service.update_status(order_id, status)


@router.delete("/{order_id}")
def cancel(order_id: int):
    return order_service.cancel_order(order_id)


@router.get("/history/{email}")
def order_history(email: str):
    return order_service.get_order_history(email)
