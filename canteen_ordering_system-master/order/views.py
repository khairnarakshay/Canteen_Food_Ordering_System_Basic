from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from canteen.models import FoodItem
from .models import Cart, Orders, OrderItems
from .forms import LoginRegisterForm
import random
from django.shortcuts import get_object_or_404, redirect


# Create your views here.
def index(request):
    food = FoodItem.objects.all()
    name_quantity_of_all_food = []
    if request.user.is_authenticated and request.session.get('is_user_logged_in', False):  # Ensure user-side session
        cartitems = Cart.objects.filter(username=request.user)
        for f in food:
            find = False
            name_quantity_combo = []
            for item in cartitems:
                if f.name == item.food.name:
                    name_quantity_combo.append(f.name)
                    name_quantity_combo.append(item.quantity)
                    find = True
                    break
            if not find:
                name_quantity_combo.append(f.name)
                name_quantity_combo.append('0')
            name_quantity_of_all_food.append(name_quantity_combo)
    return render(request, 'order/index.html', {'food': food, 'cartitems': name_quantity_of_all_food})

def register(request):
    if request.method == 'GET':
        form = LoginRegisterForm()
        return render(request, 'order/register.html', {'form': form})
    
    elif request.method == 'POST':
        form = LoginRegisterForm(request.POST)
        if form.is_valid():
            un = form.cleaned_data['username']
            pw = form.cleaned_data['password']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            mobile_no = form.cleaned_data['mobile_no']

            # Check if username already exists
            if User.objects.filter(username=un).exists():
                messages.warning(request, 'User Already Exists, try another unique username')
                return HttpResponseRedirect('/register/')
            
            # Create the user
            new_user = User(username=un, first_name=first_name, last_name=last_name)
            new_user.set_password(pw)
            new_user.save()


            messages.success(request, 'Account Created Successfully, You can Login Now')
            return HttpResponseRedirect('/login/')
        else:
            messages.warning(request, 'There was an error in the form')
            return HttpResponseRedirect('/register/')


def user_login(request):
    if request.method == 'GET':
        form = LoginRegisterForm()
        return render(request, 'order/login.html', {'form': form})
    elif request.method == 'POST':
        form = LoginRegisterForm(request.POST)
        un = request.POST.get('username')
        pw = request.POST.get('password')
        if not User.objects.filter(username=un).exists():
            messages.warning(request, 'User Does Not Exist or Wrong Password, Try Again')
            return HttpResponseRedirect('/login/')
        else:
            auth_user = authenticate(username=un, password=pw)
            if auth_user and not auth_user.is_staff:  # Prevent admin users from logging in as regular users
                login(request, auth_user)
                request.session['is_user_logged_in'] = True  # Custom session key
                return HttpResponseRedirect('/')
            elif auth_user and auth_user.is_staff:
                messages.warning(request, 'Admins cannot log in here.')
                return HttpResponseRedirect('/login/')
            else:
                messages.warning(request, 'User Does Not Exist or Wrong Password, Try Again')
                return HttpResponseRedirect('/login/')

@login_required(login_url='/login/')
def update_cart(request, f_id):
    if not request.session.get('is_user_logged_in', False):  # Ensure user-side session
        return HttpResponseRedirect('/login/')
    food = FoodItem.objects.get(id=f_id)
    if Cart.objects.filter(username=request.user, food=food).exists():
        old_quantity = Cart.objects.values_list('quantity', flat=True).get(username=request.user, food=food)
        if request.GET.get('name') == 'increase_cart':
            updated_quantity = old_quantity + 1
            Cart.objects.filter(username=request.user, food=food).update(quantity=updated_quantity)
        elif request.GET.get('name') == 'decrease_cart':
            updated_quantity = old_quantity - 1
            Cart.objects.filter(username=request.user, food=food).update(quantity=updated_quantity)
        elif request.GET.get('name') == 'delete_cart_item':
            item_to_delete = Cart.objects.get(username=request.user, food=food)
            item_to_delete.delete()
    else:
        cart_item = Cart(username=request.user, food=food)
        cart_item.save()

    if 'cart' in request.META['HTTP_REFERER']:
        return HttpResponseRedirect('/cart/')
    else:
        return HttpResponseRedirect('/')

@login_required(login_url='/login/')
def cart(request):
    if not request.session.get('is_user_logged_in', False):  # Ensure user-side session
        return HttpResponseRedirect('/login/')
    cartitems = Cart.objects.filter(username=request.user)
    total_amount = 0
    if cartitems:
        for item in cartitems:
            sub_total = item.food.price * item.quantity
            total_amount += sub_total
    return render(request, 'order/cart.html', {'cartitems': cartitems, 'total_amount': total_amount})

@login_required(login_url='/login/')
def checkout(request):
    if not request.session.get('is_user_logged_in', False):  # Ensure user-side session
        return HttpResponseRedirect('/login/')
    if request.method == 'POST':
        if request.POST.get('paymode') == 'Cash':
            tn_id = 'CASH' + str(random.randint(111111111111111, 999999999999999))
            payment_mode = "Cash"
            payment_gateway = "Cash"
        elif request.POST.get('paymode') == 'Online' and request.POST.get('paygate') == "Paypal":
            tn_id = request.POST.get('tn_id')
            payment_mode = "Online"
            payment_gateway = "Paypal"
        else:
            return HttpResponse('<H1>Invalid Request</H1>')
        cartitems = Cart.objects.filter(username=request.user)
        total_amount = 0
        new_order = Orders(username=request.user, total_amount=total_amount, payment_mode=payment_mode, transaction_id=tn_id, payment_gateway=payment_gateway)
        new_order.save()
        if cartitems:
            for item in cartitems:
                OrderItems(username=request.user, order=new_order, name=item.food.name, price=item.food.price, quantity=item.quantity, item_total=item.food.price * item.quantity).save()
                sub_total = item.food.price * item.quantity
                total_amount += sub_total
            Orders.objects.filter(id=new_order.id).update(total_amount=total_amount)
        cartitems.delete()
        return HttpResponseRedirect('/myorders/')
    else:
        return HttpResponse('<H1>Invalid Request</H1>')

@login_required(login_url='/login/')
def my_orders(request):
    if not request.session.get('is_user_logged_in', False):  # Ensure user-side session
        return HttpResponseRedirect('/login/')
    orders = Orders.objects.filter(username=request.user).order_by("-order_datetime", "id")
    order_items = OrderItems.objects.filter(username=request.user)
    return render(request, 'order/myorders.html', {'orders': orders, 'order_items': order_items})

@login_required(login_url='/login/')
def cancel_order(request, order_id):
    order = get_object_or_404(Orders, id=order_id, username=request.user, status="Pending")
    order.status = "Cancelled"
    order.cancelled_by = request.user.username  # Record who cancelled the order
    order.save()
    messages.success(request, f"Order #{order_id} has been cancelled successfully.")
    return redirect('/myorders/')


    
def user_logout(request):
    if request.session.get('is_user_logged_in', False):  # Ensure user-side session
        logout(request)
        request.session.flush()  # Clear user-side session
        messages.success(request, 'Logout Successfully')
    return HttpResponseRedirect('/')
