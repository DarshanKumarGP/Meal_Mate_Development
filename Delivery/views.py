from django.shortcuts import render
from . models import Customer, Item
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from . models import Restaurant
from . models import Cart

import razorpay
from django.conf import settings

# Create your views here.
def index(request):
    return render(request, 'index.html')

def open_signIn(request):
    return render(request, 'SignIn.html')

def open_signUp(request):
    return render(request, 'SignUp.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')


        try:
            Customer.objects.get(username = username)
            return HttpResponse("Duplicates users are not allowed")
        except:
    
        #Creating customer table object
            Customer.objects.create(username = username,
                                password = password,
                                email = email,
                                mobile = mobile,
                                address = address)
        
        return render(request, "signIn.html")
    
    
def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # check if the customer exists
            Customer.objects.get(username=username, password=password)

            # if admin, redirect to admin home
            if username == "admin" and password == "admin":
                return render(request, "admin_home.html")
            else:
                # fetch all restaurants for customer home page
                restaurants = Restaurant.objects.all()
                return render(request, "customer_home.html", {"restaurants": restaurants, "username" : username})

        except Customer.DoesNotExist:
            # invalid login
            return render(request, "fail.html")
    
    # if method is not POST just open sign in page
    return render(request, "SignIn.html")

    
def open_add_restaurant(request):
    return render(request, "add_restaurant.html")


# Adds Restaurant
def add_restaurant(request):
    #return HttpResponse("Working")
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        Restaurant.objects.create(name=name, 
                                  picture=picture, 
                                  cuisine=cuisine,
                                rating=rating)

        restaurants = Restaurant.objects.all()
        return render(request, 'show_restaurant.html', {"restaurants": restaurants})

    return HttpResponse("Invalid request")


def open_update_restaurant(request, restaurant_id):
    #return HttpResponse("Working")
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(request, 'update_restaurant.html', {"restaurant": restaurant})

def open_show_restaurant(request):
    restaurants = Restaurant.objects.all()
    return render(request, 'show_restaurant.html', {"restaurants": restaurants})


def update_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == 'POST':
        restaurant.name = request.POST.get('name')
        restaurant.picture = request.POST.get('picture')
        restaurant.cuisine = request.POST.get('cuisine')
        restaurant.rating = request.POST.get('rating')
        restaurant.save()

        restaurants = Restaurant.objects.all()
        return render(request, 'show_restaurant.html', {"restaurants": restaurants})
    
# Delete Restaurant
def delete_restaurant(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == "POST":
        restaurant.delete()
        return redirect("open_show_restaurant")  # make sure this view exists!
    
    return render(request, "confirm_delete.html", {"restaurant": restaurant})


def open_update_menu(request, restaurant_id):
    restaurant = Restaurant.objects.get( id=restaurant_id)
    # itemList = Item.objects.all()
    itemList = restaurant.items.all()
    return render(request, 'update_menu.html', {"itemList": itemList, "restaurant": restaurant})


def update_menu(request,restaurant_id ):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        is_veg = request.POST.get('is_veg') == 'on'
        picture = request.POST.get('picture')

        
        Item.objects.create(
            restaurant=restaurant,
            name=name,
            description=description,
            price=price,
            is_veg=is_veg,
            picture=picture
        )
        return redirect('open_show_restaurant')
    

def view_menu(request, restaurant_id, username):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.items.all()
    #itemList = Item.objects.all()
    return render(request, 'customer_menu.html'
                  ,{"itemList" : itemList,
                     "restaurant" : restaurant, 
                     "username": username})


def add_to_cart(request, item_id, username):
    item = Item.objects.get(id = item_id)
    customer = Customer.objects.get(username = username)

    cart, created = Cart.objects.get_or_create(customer = customer)

    cart.items.add(item)

    return HttpResponse('added to cart')


def show_cart(request, username):
    customer = Customer.objects.get(username = username)
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    return render(request, 'cart.html',{"itemList" : items, "total_price" : total_price, "username":username})


# Checkout View
def checkout(request, username):
    # Fetch customer and their cart
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    if total_price == 0:
        return render(request, 'checkout.html', {
            'error': 'Your cart is empty!',
        })

    # Initialize Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create Razorpay order
    order_data = {
        'amount': int(total_price * 100),  # Amount in paisa
        'currency': 'INR',
        'payment_capture': '1',  # Automatically capture payment
    }
    order = client.order.create(data=order_data)

    # Pass the order details to the frontend
    return render(request, 'checkout.html', {
        'username': username,
        'cart_items': cart_items,
        'total_price': total_price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],  # Razorpay order ID
        'amount': total_price,
    })

def orders(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()

    # Fetch cart items and total price before clearing the cart
    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    # Clear the cart after fetching its details
    if cart:
        cart.items.clear()

    return render(request, 'orders.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
    })