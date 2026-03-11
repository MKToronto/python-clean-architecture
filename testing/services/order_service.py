import smtplib
from email.mime.text import MIMEText
from db.database import SessionLocal, OrderModel, BookModel


class OrderService:
    """Handles orders, payments, inventory, notifications, discounts, and shipping."""

    def create_order(self, book_id, quantity, customer_email):
        db = SessionLocal()
        book = db.query(BookModel).filter(BookModel.id == book_id).first()
        if not book:
            db.close()
            return None

        total = book.price * quantity

        # Apply discount
        if quantity >= 10:
            discount_type = "bulk"
        elif quantity >= 5:
            discount_type = "medium"
        else:
            discount_type = "none"

        if discount_type == "bulk":
            total = total * 0.8
        elif discount_type == "medium":
            total = total * 0.9
        elif discount_type == "none":
            pass

        order = OrderModel(
            book_id=book_id,
            quantity=quantity,
            customer_email=customer_email,
            total=total,
            status="pending",
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # Send confirmation email
        self._send_email(
            customer_email,
            "Order Confirmation",
            f"Your order #{order.id} for {quantity}x '{book.title}' has been placed. Total: ${total:.2f}",
        )

        # Update inventory
        self._update_inventory(book_id, quantity, db)

        # Log the order
        self._log_order(order.id, customer_email, total)

        db.close()
        return {
            "id": order.id,
            "book_id": book_id,
            "quantity": quantity,
            "total": total,
            "status": "pending",
        }

    def get_order(self, order_id):
        db = SessionLocal()
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        db.close()
        if order:
            return {
                "id": order.id,
                "book_id": order.book_id,
                "quantity": order.quantity,
                "total": order.total,
                "status": order.status,
            }
        return None

    def update_status(self, order_id, new_status):
        db = SessionLocal()
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not order:
            db.close()
            return None
        order.status = new_status
        db.commit()

        if new_status == "shipped":
            self._send_email(
                order.customer_email,
                "Order Shipped",
                f"Your order #{order.id} has been shipped!",
            )
        elif new_status == "delivered":
            self._send_email(
                order.customer_email,
                "Order Delivered",
                f"Your order #{order.id} has been delivered!",
            )

        db.close()
        return {"id": order.id, "status": new_status}

    def cancel_order(self, order_id):
        db = SessionLocal()
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not order:
            db.close()
            return None
        if order.status != "pending":
            db.close()
            return {"error": "Can only cancel pending orders"}
        order.status = "cancelled"
        db.commit()

        # Restore inventory
        self._restore_inventory(order.book_id, order.quantity, db)

        # Send cancellation email
        self._send_email(
            order.customer_email,
            "Order Cancelled",
            f"Your order #{order.id} has been cancelled.",
        )

        # Process refund
        self._process_refund(order.id, order.total)

        db.close()
        return {"id": order.id, "status": "cancelled"}

    def get_order_history(self, customer_email):
        db = SessionLocal()
        orders = db.query(OrderModel).filter(OrderModel.customer_email == customer_email).all()
        db.close()
        return [{"id": o.id, "total": o.total, "status": o.status} for o in orders]

    def calculate_shipping(self, order_id):
        db = SessionLocal()
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not order:
            db.close()
            return None
        if order.total > 50:
            shipping = 0
        elif order.total > 25:
            shipping = 4.99
        else:
            shipping = 9.99
        db.close()
        return {"order_id": order_id, "shipping": shipping}

    def _send_email(self, to, subject, body):
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["To"] = to
            msg["From"] = "noreply@bookstore.com"
            server = smtplib.SMTP("localhost", 587)
            server.send_message(msg)
            server.quit()
        except Exception:
            pass

    def _update_inventory(self, book_id, quantity, db):
        pass

    def _restore_inventory(self, book_id, quantity, db):
        pass

    def _log_order(self, order_id, email, total):
        print(f"Order {order_id} by {email}: ${total}")

    def _process_refund(self, order_id, amount):
        print(f"Refund ${amount} for order {order_id}")
