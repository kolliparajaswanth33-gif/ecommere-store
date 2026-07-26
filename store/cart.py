from decimal import Decimal


def get_cart(session):
    return session.get('cart', {})


def cart_count(session):
    return sum(get_cart(session).values())


def cart_total(cart_items):
    return sum((item['subtotal'] for item in cart_items), Decimal('0.00'))
