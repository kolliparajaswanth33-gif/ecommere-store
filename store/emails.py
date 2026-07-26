from django.conf import settings
from django.core.mail import send_mail


def send_order_receipt(order):
    """Send a simple billing receipt to the email entered at checkout."""
    item_lines = '\n'.join(
        f'- {item.product_name} × {item.quantity}: ₹{item.price * item.quantity}'
        for item in order.items.all()
    )
    message = (
        f'Hello {order.full_name},\n\n'
        f'Thank you for shopping at Kubara Kirana Shop.\n\n'
        f'Order number: #{order.id}\n'
        f'Billing and delivery address:\n{order.address}, {order.city} - {order.postal_code}\n\n'
        f'Items:\n{item_lines}\n\n'
        f'Total amount: ₹{order.total_amount}\n\n'
        'Your order has been received successfully.'
    )
    send_mail(
        subject=f'Kubara Kirana Shop bill - Order #{order.id}',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=False,
    )
