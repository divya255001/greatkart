from urllib import request

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from store.models import Product, Variation
from .models import Cart,CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request,product_id):
    current_user= request.user
    product = Product.objects.get(id=product_id) # get the product using the id
    # if user is authenticated
    if current_user.is_authenticated:
        product_variation = []
        if request.method =='POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                # print(f"{key}:{value}")
                try:
                    variation = Variation.objects.get(variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
            
        # color = request.POST.get('color')
        # size = request.POST.get('size')
        # product = Product.objects.get(id=product_id) # get the product using the id
        
        is_cart_item_exists = CartItem.objects.filter(product=product,user = current_user).exists()
        if is_cart_item_exists :
            cart_item = CartItem.objects.filter(product=product, user = current_user) # get the cart item using the product and cart
           
            ex_var_list=[]
            id = []
            for item in cart_item:
                existing_variation = item.variation.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
            # print(ex_var_list)
            if product_variation in ex_var_list:
                # increase cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product =product,id =item_id)
                item.quantity +=1
                item.save()
                
            else:
                item = CartItem.objects.create(product = product, quantity = 1, user =current_user)   
                if len(product_variation) > 0:
                    item.variation.clear()
                    
                    item.variation.add(*product_variation)
            # cart_item.quantity += 1 # increase the quantity of the cart item by 1
                item.save()    
        else :
        
            cart_item = CartItem.objects.create(
                product=product,
                user = current_user,
                quantity=1
                ) # create a new cart item if not exist
            # cart_item.variation.clear()
            if len(product_variation) > 0:
                cart_item.variation.clear()
                cart_item.variation.add(*product_variation)
            cart_item.save()
        
        return redirect('cart')

        
    # if the user is not authenticated 
    else:
        product_variation = []
        if request.method =='POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                # print(f"{key}:{value}")
                try:
                    variation = Variation.objects.get(variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
            
        # color = request.POST.get('color')
        # size = request.POST.get('size')
        product = Product.objects.get(id=product_id) # get the product using the id
        try:
            cart = Cart.objects.get(cart_id = _cart_id(request)) # get the cart using the cart_id present in the session
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id = _cart_id(request)) # create a new cart if not exist
            cart.save()
        is_cart_item_exists = CartItem.objects.filter(product=product,cart=cart).exists()
        if is_cart_item_exists :
            cart_item = CartItem.objects.filter(product=product, cart=cart) # get the cart item using the product and cart
            # existing_variation  =>database
            # current_variation => product_variation
            # item_id =>database
            ex_var_list=[]
            id = []
            for item in cart_item:
                existing_variation = item.variation.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
            print(ex_var_list)
            if product_variation in ex_var_list:
                # increase cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product =product,id =item_id)
                item.quantity +=1
                item.save()
                
            else:
                item = CartItem.objects.create(product = product, quantity = 1, cart = cart)   
                if len(product_variation) > 0:
                    item.variation.clear()
                    
                    item.variation.add(*product_variation)
            # cart_item.quantity += 1 # increase the quantity of the cart item by 1
                item.save()    
        else :
        
            cart_item = CartItem.objects.create(
                product=product,
                cart=cart,
                quantity=1
                ) # create a new cart item if not exist
            # cart_item.variation.clear()
            if len(product_variation) > 0:
                cart_item.variation.clear()
                cart_item.variation.add(*product_variation)
            cart_item.save()
        
        return redirect('cart')
    
    
def remove_cart(request,product_id,cart_item_id):
        
        product = get_object_or_404 (Product,id=product_id) # get the product using the id
        try:
            if request.user.is_authenticated:
                cart_item = CartItem.objects.get(product=product,user=request.user,id = cart_item_id)
            else:
                cart = Cart.objects.get(cart_id = _cart_id(request)) # get the cart using the cart_id present in the session
                cart_item = CartItem.objects.get(product=product,cart=cart,id = cart_item_id) # get the cart item using the product and cart
            if cart_item.quantity > 1:
                cart_item.quantity -= 1 # decrease the quantity of the cart item by 1
                cart_item.save()
            else:
                cart_item.delete() # delete the cart item if quantity is 0
        except:
            pass
        return redirect('cart')

def remove_cart_item(request,product_id,cart_item_id):
    
    product = get_object_or_404 (Product,id=product_id) # get the product using the id
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product,user=request.user,id = cart_item_id) # get the cart item using the product and cart
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request)) # get the cart using the cart_id present in the session
        cart_item = CartItem.objects.get(product=product,cart=cart,id = cart_item_id) # get the cart item using the product and cart
    cart_item.delete() # delete the cart item
    return redirect('cart')

def cart(request,total=0,quantity=0,cart_items=None):
    try:
        tax =0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active=True) 
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))

       # get the cart using the cart_id present in the session
            cart_items = CartItem.objects.filter(cart=cart, is_active=True) # get the cart items using the cart and is_active=True
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity) # calculate the total price of the cart items
            quantity += cart_item.quantity # calculate the total quantity of the cart items
        tax = (2 * total)/100 # calculate the tax of the cart items
        grand_total = total + tax # calculate the total price of the cart items including tax
    except (Cart.DoesNotExist, ObjectDoesNotExist):
        pass # just ignore the exception and continue
    context ={
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request,'store/cart.html',context)


@login_required(login_url='login')
def checkout(request,total=0,quantity=0,cart_items=None):
    try:
        tax =0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user = request.user, is_active=True) 
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))

       # get the cart using the cart_id present in the session
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity) # calculate the total price of the cart items
            quantity += cart_item.quantity # calculate the total quantity of the cart items
        tax = (2 * total)/100 # calculate the tax of the cart items
        grand_total = total + tax # calculate the total price of the cart items including tax
    except (Cart.DoesNotExist, ObjectDoesNotExist):
        pass # just ignore the exception and continue
    context ={
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request,'store/checkout.html',context)




