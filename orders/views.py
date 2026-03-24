from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
from carts.models import Cart,CartItem
from orders.models import Payment
from .forms import OrderForm
from .models import Order,OrderProduct
import datetime
import json
from django.contrib.auth.decorators import login_required
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def payments(request):
    body =json.loads(request.body)
    order = Order.objects.get(user=request.user,is_ordered =False,order_number=body['orderID'])
    # store transaction details inside Payment model
    payment = Payment(
        user =request.user,
        payment_id =body['transID'],
        payment_method =body['payment_method'],
        amount_paid = order.order_total,
        status =body['status'],


    )
    payment.save()
    order.payment =payment
    order.is_ordered =True
    order.save()
    # Move the cart items to order product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order =order
        orderproduct.payment=payment
        # orderproduct.user_id = request.user.id
        # orderproduct.product_id = item.product_id
        orderproduct.user = request.user
        orderproduct.product = item.product
        orderproduct.quantity=item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered= True
        orderproduct.save()


       
        # ====================================#
    #     ✅ handle variations
        try:
            variations = item.variation.all()
            orderproduct.variation.set(variations)
        except:
            pass
        product = Product.objects.get(id = item.product_id)
        product.stock -= item.quantity
        product.save()
    # # ✅ clear cart
    cart_items.delete()

    # return JsonResponse({
    #     'message': 'Payment successful',
    #     'order_number': order.order_number
    # })

    #Reduce the quantity of the sold products
   
    
    #clear cart

    #send order received email to customer
    mail_subject = 'Thank you for your order! '
    message = render_to_string('orders/order_received_email.html',{
        'user': request.user,
        'order':order,
        
    })
    # to_email = request.user.email
    to_email = order.email
    send_email = EmailMessage(mail_subject,message,to=[to_email])
    send_email.send()
    # Send order number and transaction id back to sendData method via JSONResponse
    data ={
        'order_number':order.order_number,
        'transID':payment.payment_id, #recent change 11.21
    }

    
    return JsonResponse(data)


def place_order(request):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()

    if cart_count <= 0:
        return redirect('store')

    total = 0
    quantity = 0

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method != 'POST':
        return redirect('checkout')

    form = OrderForm(request.POST)

    if form.is_valid():
        data = Order.objects.create(
            user=current_user,
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            phone=form.cleaned_data['phone'],
            email=form.cleaned_data['email'],
            address_line_1=form.cleaned_data['address_line_1'],
            address_line_2=form.cleaned_data['address_line_2'],
            country=form.cleaned_data['country'],
            state=form.cleaned_data['state'],
            city=form.cleaned_data['city'],
            order_note=form.cleaned_data['order_note'],
            order_total=grand_total,
            tax=tax,
            ip=request.META.get('REMOTE_ADDR'),
        )

        # generate order number
        current_date = datetime.date.today().strftime("%Y%m%d")
        data.order_number = current_date + str(data.id)
        data.save()

        context = {
            'order': data,
            'cart_items': cart_items,
            'total': total,
            'tax': tax,
            'grand_total': grand_total,
        }

        return render(request, 'orders/payments.html', context)

    return redirect('checkout')
def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order=Order.objects.get(order_number=order_number,is_ordered =True)
        ordered_products =OrderProduct.objects.filter(order_id =order.id)
        subtotal =0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity
        payment = Payment.objects.get(payment_id=transID)

        context ={
            'order':order,
            'ordered_products':ordered_products,
            'order_number':order.order_number,
            'transID':payment.payment_id,
            'payment':payment,
            'subtotal': subtotal

        }
        return render(request,'orders/order_complete.html',context)
    except(Payment.DoesNotExist,Order.DoesNotExist):
        return redirect('home')
    

    
