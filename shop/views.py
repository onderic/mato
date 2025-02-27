import json
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from shop.forms import ProductForm, ShopRegistrationForm
from shop.models import Category, ContactMessage, Mpesa, Order, Product, Shop
from django.urls import reverse
from django.db.models import Sum,F

from users.models import User
from .daraja import LipaNaMpesa
from django.views.decorators.csrf import csrf_exempt


def home(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'index.html', {'products': products,'categories':categories})


@login_required
def admin_dashboard(request):
    # Fetch the latest 5 orders
    latest_orders = Order.objects.all().order_by('-created_at')[:5]

    total_users = User.objects.count()

    total_orders = Order.objects.count()

    total_sales = Order.objects.annotate(
        total_price=F('product__price') * F('quantity')
    ).aggregate(total_sales=Sum('total_price'))['total_sales'] or 0


    context = {
        'latest_orders': latest_orders,
        'total_users': total_users,
        'total_orders': total_orders,
        'total_sales': total_sales,
    }

    return render(request, 'admin/admin_dashboard.html', context)



@login_required
def shopowner_dashboard(request):
    user = request.user

    try:
        shop = user.shop
    except Shop.DoesNotExist:
        return render(request, 'shopOwner/register_shop.html', {'message': 'Please create your shop to start managing orders and products.'})
    
    orders = Order.objects.filter(product__shop=shop)
    total_sales = sum(order.quantity * order.product.price for order in orders)
    total_orders = orders.count()
    total_products = Product.objects.filter(shop=shop).count()

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_products': total_products,
    }

    return render(request, 'shopOwner/shopowner_dashboard.html', context)



def buyer_dashboard(request):
    return render(request, 'buyer_dashboard.html')



@login_required
def buyer_orders(request):
    
    return render(request, 'buyer/orders.html')

@login_required
def buyer_account_settings(request):
    user = request.user
    context = {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }
    return render(request, 'buyer/account_settings.html', context)



@login_required
def register_shop(request):
    if request.method == 'POST':
        shop_name = request.POST.get('shop_name')
        shop_description = request.POST.get('shop_description')

        existing_shop = Shop.objects.filter(owner=request.user).first()
        if existing_shop:
            messages.error(request, 'You can only own one shop.')
            return redirect('shopowner_register_shop') 

        # Validate the data
        if not shop_name or not shop_description:
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'shop/register_shop.html')

        shop = Shop(
            owner=request.user,
            name=shop_name,
            description=shop_description
        )
        shop.save()

        messages.success(request, 'Shop registered successfully!')
        return redirect('shopowner_register_shop')  

    shops = Shop.objects.filter(owner=request.user)

    return render(request, 'shopOwner/register_shop.html', {'shops': shops})


@login_required
def add_product(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description')
        product_price = request.POST.get('product_price')
        category_id = request.POST.get('category_id')
        product_image = request.FILES.get('product_image')

        if not product_name or not product_description or not product_price or not category_id:
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'shop/add_product.html')

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, 'Selected category does not exist.')
            return render(request, 'shop/add_product.html')

        # Create and save Product instance
        product = Product(
            shop=request.user.shop, 
            name=product_name,
            description=product_description,
            price=product_price,
            category=category,
            image=product_image
        )
        product.save()

        messages.success(request, 'Product added successfully!')
        return redirect('shopowner_add_product') 

    # Handle GET request and fetch products
    products = Product.objects.filter(shop=request.user.shop)
    categories = Category.objects.all()
    form = ProductForm()
    return render(request, 'shopOwner/add_product.html', {'form': form, 'products': products, 'categories': categories})


@login_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.ORDER_STATUS_CHOICES).keys():
            order.status = new_status
            order.save()
        return redirect('shopowner_orders')

    return redirect('shopowner_orders')



def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})

@login_required
def view_orders(request):
    # Get the shop owned by the logged-in user
    try:
        shop = Shop.objects.get(owner=request.user)
    except Shop.DoesNotExist:
        shop = None

    # Fetch orders for the shop
    if shop:
        orders = Order.objects.filter(product__shop=shop).order_by('-created_at')
    else:
        orders = []

    context = {
        'orders': orders,
    }
    return render(request, 'shopOwner/view_orders.html', context)

@login_required
def sales_reports(request):
    reports = request.user.shop.sales_reports.all() 
    return render(request, 'shop/sales_reports.html', {'reports': reports})


def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

@login_required
def checkout(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        location = request.POST.get('location')

        if not (address and phone_number and location ):
            return render(request, 'shop/checkout.html', {
                'product': product,
                'error_message': 'Please fill in all fields.'
            })

        # Create and save the order
        order = Order(
            user=request.user,
            product=product,
            quantity=1, 
            address=address,
            phone_number=phone_number,
            location=location,
        )
        order.save()
        return redirect(reverse('payment_page', args=[order.id]))

    return render(request, 'shop/checkout.html', {'product': product})


@login_required
def payment_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    product = order.product

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')

        if not phone_number:
            return render(request, 'payment.html', {
                'order': order,
                'product': product,
                'error_message': 'Please enter your phone number.'
            })
        
        lipa_na_mpesa = LipaNaMpesa()
        amount = product.price
        payload = {
            'amount': amount,
            'phone_number': phone_number,
            'order': order.id,
        }
        response = lipa_na_mpesa.stk_push(payload)
        
        if response.get('ResponseCode') == '0': 
            checkout_request_id = response.get('CheckoutRequestID')

            Mpesa.objects.create(
                order=order,
                is_processed=False
            )
            
            request.session['order_id'] = order.id
            request.session['checkout_request_id'] = checkout_request_id

            return redirect('payment_waiting_page')
        else:
            return render(request, 'payment.html', {
                'order': order,
                'product': product,
                'error_message': 'Payment initiation failed. Please try again.'
            })

    return render(request, 'payment.html', {'order': order, 'product': product})

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        checkout_request_id = data.get('CheckoutRequestID')
        result_code = data.get('ResultCode')
        result_description = data.get('ResultDesc')

        try:
            transaction = Mpesa.objects.get(checkout_request_id=checkout_request_id)
            transaction.result_code = result_code
            transaction.result_description = result_description
            transaction.is_processed = result_code == 0
            transaction.save()

            if transaction.is_processed:
                order = Order.objects.get(product=transaction.product, user=transaction.user)
                order.status = 'Paid' 
                order.save()

            return JsonResponse({'status': 'success'})
        except Mpesa.DoesNotExist:
            return JsonResponse({'status': 'failed', 'message': 'Transaction not found'})
    
    return JsonResponse({'status': 'failed', 'message': 'Invalid request'})

@login_required
def payment_waiting_page(request):
    order_id = request.session.get('order_id')
    checkout_request_id = request.session.get('checkout_request_id')
    
    if not order_id or not checkout_request_id:
        return redirect('home')

    try:
        transaction = Mpesa.objects.get(checkout_request_id=checkout_request_id)
        
        if transaction.is_processed:
            context = {
                'order': get_object_or_404(Order, id=order_id),
                'transaction': transaction,
                'message': 'Your payment has been processed successfully!'
            }
        else:
            context = {
                'order': get_object_or_404(Order, id=order_id),
                'transaction': transaction,
                'message': 'Your payment is still being processed. Please check back later.'
            }
    except Mpesa.DoesNotExist:
        context = {
            'message': 'Transaction details not found.'
        }
    
    return render(request, 'payment_waiting.html', context)

@login_required
def check_payment_status(request):
    checkout_request_id = request.session.get('checkout_request_id')
    
    if not checkout_request_id:
        return JsonResponse({'error': 'No checkout request ID found'}, status=400)

    try:
        transaction = Mpesa.objects.get(checkout_request_id=checkout_request_id)
        
        if transaction.is_processed:
            return JsonResponse({'is_processed': True})
        else:
            return JsonResponse({'is_processed': False})
    except Mpesa.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, 'shop/order_confirmation.html', {'order': order})


def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Validate form input
        if not all([name, email, subject, message]):
            messages.error(request, "All fields are required.")
            return render(request, 'contact.html')

        contact_message = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        contact_message.save()

        messages.success(request, "Your message has been received successfully!")
        return redirect('contact')

    return render(request, 'contact.html')

@login_required
def contact_message(request):
    contacts = ContactMessage.objects.all()
    return render(request, "admin/messages.html", {"contacts": contacts})


@login_required
def user_dashboard(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')

    orders = orders.select_related('product')

    context = {
        'user': user,
        'orders': orders,
    }
    return render(request, 'user_dashboard.html', context)


@login_required
def manage_users(request):
    if request.method == 'POST':
        if 'edit_user' in request.POST:
            user_id = request.POST.get('user_id')
            username = request.POST.get('username')
            email = request.POST.get('email')
            user = get_object_or_404(User, id=user_id)
            user.username = username
            user.email = email
            user.save()
            messages.success(request, 'User updated successfully.')
        elif 'delete_user' in request.POST:
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            user.delete()
            messages.success(request, 'User deleted successfully.')
        return redirect('manage_users')

    # Fetch all users
    users = User.objects.all()
    return render(request, 'admin/manage_users.html', {'users': users})



@login_required
def manage_products(request):
    if request.method == 'POST':
        if 'delete' in request.POST:
            # Handle deletion
            product_id = request.POST.get('delete')
            product = get_object_or_404(Product, id=product_id)
            product.delete()
            messages.success(request, "Product deleted successfully.")
            return redirect('manage_products')
        
        # Handle form submission for product creation/editing
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product saved successfully.")
            return redirect('manage_products')

    # Fetch all products
    products = Product.objects.all()
    form = ProductForm()
    context = {
        'products': products,
        'form': form
    }
    return render(request, 'admin/manage_products.html', context)

@login_required
def manage_and_add_categories(request):
    if request.method == 'POST':
        category_name = request.POST.get('name')
        if category_name:
            Category.objects.create(name=category_name)
            return redirect('manage_and_add_categories')    
    categories = Category.objects.all()
    return render(request, 'admin/add_category.html', {'categories': categories})