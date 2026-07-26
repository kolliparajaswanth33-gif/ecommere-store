from .cart import cart_count


def cart_data(request):
    return {'cart_count': cart_count(request.session)}
