from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q, Count
from django.utils import timezone
from django.urls import reverse
from .paymongo import create_checkout_session
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Profile, StoreSettings
from .forms import UserProfileForm, CheckoutForm, LoginForm, ProductUploadForm, StoreSettingsForm
from django.core.paginator import Paginator
import django.db.models as models


def is_main_store_owner(user):
    """Return True for the main Esugo store owner account."""
    return (
        user.is_authenticated
        and Profile.objects.filter(user=user, user_type='store_owner').exists()
        and (
            user.username == 'storeowner'
            or StoreSettings.objects.filter(owner=user, store_name__iexact='Esugo Grocery').exists()
        )
    )


def home(request):
    """Home page with featured products and categories"""
    categories = Category.objects.annotate(product_count=Count('products'))[:6]
    featured_products = Product.objects.filter(is_available=True, stock__gt=0).select_related('category', 'owner')[:8]
    fresh_arrivals = Product.objects.filter(is_available=True).select_related('category', 'owner').order_by('-created_at')[:6]

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'fresh_arrivals': fresh_arrivals,
        'register_errors': request.session.pop('register_errors', []),
        'register_data': request.session.pop('register_data', {}),
        'open_auth_modal': request.session.pop('open_auth_modal', ''),
    }
    return render(request, 'myapp/home.html', context)


def login_view(request):
    """Custom login view with role-based redirect"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)

                profile, created = Profile.objects.get_or_create(user=user)
                if created:
                    if user.is_superuser or user.is_staff:
                        profile.user_type = 'admin'
                    elif StoreSettings.objects.filter(owner=user).exists():
                        profile.user_type = 'store_owner'
                    profile.save()

                if profile.user_type == 'rider':
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    return redirect('rider_dashboard')
                elif profile.user_type == 'store_owner':
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    return redirect('store_owner_dashboard')
                elif user.is_staff or profile.user_type == 'admin':
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    return redirect('admin_dashboard')
                else:
                    messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                    return redirect('home')
        else:
            # Form is invalid - add error messages
            for error in form.non_field_errors():
                messages.error(request, error)
            return render(request, 'myapp/login.html', {'form': form})
    else:
        form = LoginForm()
    
    return render(request, 'myapp/login.html', {'form': form})


@login_required
def product_list(request, category_slug=None):
    """Product listing page with category, store filter, and search"""
    category = None
    categories = Category.objects.all()
    selected_store = None
    stores = StoreSettings.objects.select_related('owner').filter(
        owner__profile__user_type='store_owner'
    ).exclude(
        store_name__icontains='Esugo'
    ).order_by('store_name')

    # Filter by customer's preferred store
    store_id = request.GET.get('store') or request.session.get('selected_store_id')
    if store_id and store_id.isdigit():
        selected_store = stores.filter(owner_id=store_id).first()
        if selected_store:
            request.session['selected_store_id'] = str(selected_store.owner_id)
        else:
            request.session.pop('selected_store_id', None)
            store_id = None
    else:
        store_id = None

    if not selected_store:
        messages.info(request, 'Please choose a store before viewing products.')
        return redirect('store_list')

    products = Product.objects.filter(is_available=True, owner=selected_store.owner).select_related('category')

    # Filter by category
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Search functionality
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Sort options
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')

    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': categories,
        'category': category,
        'stores': stores,
        'selected_store': selected_store,
        'store_id': store_id,
        'query': query,
        'sort_by': sort_by,
    }
    return render(request, 'myapp/product_list.html', context)


@login_required
def store_list(request):
    """Let customers choose which store they prefer to shop from."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    if profile.user_type != 'customer':
        messages.error(request, 'Only customers can choose a preferred store.')
        return redirect('home')

    stores = StoreSettings.objects.select_related('owner').filter(
        owner__profile__user_type='store_owner'
    ).exclude(
        store_name__icontains='Esugo'
    ).annotate(
        available_products=Count(
            'owner__store_products',
            filter=Q(owner__store_products__is_available=True, owner__store_products__stock__gt=0)
        )
    ).order_by('store_name')

    context = {
        'stores': stores,
    }
    return render(request, 'myapp/store_list.html', context)


def product_detail(request, category_slug, slug):
    """Product detail page"""
    product = get_object_or_404(Product, slug=slug, is_available=True)
    selected_store_id = request.session.get('selected_store_id')
    if not selected_store_id:
        messages.info(request, 'Please choose a store before viewing products.')
        return redirect('store_list')

    try:
        selected_store_owner_id = int(selected_store_id)
    except (TypeError, ValueError):
        request.session.pop('selected_store_id', None)
        messages.info(request, 'Please choose a store before viewing products.')
        return redirect('store_list')

    if product.owner_id != selected_store_owner_id:
        messages.warning(request, 'Please choose this product from your selected store.')
        return redirect('product_list')

    related_products = Product.objects.filter(
        category=product.category,
        owner=product.owner,
        is_available=True
    ).exclude(slug=slug)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'myapp/product_detail.html', context)


def add_to_cart(request, product_id):
    """Add product to cart"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to add items to your cart.')
        return redirect('login')

    product = get_object_or_404(Product, id=product_id, is_available=True)
    selected_store_id = request.session.get('selected_store_id')
    if not selected_store_id:
        messages.info(request, 'Please choose a store before adding products to your cart.')
        return redirect('store_list')

    try:
        selected_store_owner_id = int(selected_store_id)
    except (TypeError, ValueError):
        request.session.pop('selected_store_id', None)
        messages.info(request, 'Please choose a store before adding products to your cart.')
        return redirect('store_list')

    if product.owner_id != selected_store_owner_id:
        messages.error(request, 'You can only add products from your selected store.')
        return redirect('product_list')

    quantity = 1
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            quantity = 1
    quantity = max(1, min(quantity, product.stock))

    # Get or create cart for user
    cart, created = Cart.objects.get_or_create(user=request.user)

    existing_store_owners = {
        item.product.owner
        for item in cart.items.select_related('product__owner').all()
        if item.product.owner
    }
    if existing_store_owners and product.owner not in existing_store_owners:
        messages.error(request, 'Please checkout or clear items from your current store before adding products from another store.')
        return redirect('product_detail', category_slug=product.category.slug, slug=product.slug)

    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity = min(cart_item.quantity + quantity, product.stock)
    else:
        cart_item.quantity = quantity
    cart_item.save()

    messages.success(request, f'{quantity} {product.name} added to cart!')
    return redirect('cart')


def remove_from_cart(request, product_id):
    """Remove product from cart"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to remove items from your cart.')
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    cart_item.delete()
    messages.success(request, f'{product.name} removed from cart.')
    return redirect('cart')


def update_cart(request, product_id):
    """Update cart item quantity"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to update your cart.')
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, f'{product.name} removed from cart.')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f'Cart updated.')

    return redirect('cart')


def cart_view(request):
    """Shopping cart page"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to view your cart.')
        return redirect('login')

    cart = Cart.objects.filter(user=request.user).prefetch_related(
        'items__product__owner', 'items__product__category'
    ).first()
    cart_items = list(cart.items.all()) if cart else []
    checkout_block_reason = ''
    if cart:
        store_owners = {
            item.product.owner
            for item in cart_items
            if item.product.owner
        }
        if not store_owners and cart.items.exists():
            checkout_block_reason = 'Please choose products from a store before checkout.'
        elif len(store_owners) > 1:
            checkout_block_reason = 'Your cart has products from more than one store. Please remove items until only one store remains.'

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'checkout_block_reason': checkout_block_reason,
    }
    return render(request, 'myapp/cart.html', context)


def checkout(request):
    """Checkout page"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to checkout.')
        return redirect('login')

    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')

    cart_items = cart.items.select_related('product__owner').all()
    store_owners = {item.product.owner for item in cart_items if item.product.owner}
    if not store_owners:
        messages.error(request, 'Please choose products from a store before checkout.')
        return redirect('store_list')
    if len(store_owners) > 1:
        messages.error(request, 'Please checkout items from one store at a time.')
        return redirect('cart')

    store_owner = next(iter(store_owners))

    # Get or create user profile
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            payment_method = request.POST.get('payment_method', 'cod')
            if payment_method not in {'cod', 'paymongo'}:
                payment_method = 'cod'

            delivery_address = f"{form.cleaned_data['address']}, {form.cleaned_data['barangay']}"

            # Create order
            order = Order(
                user=request.user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address=delivery_address,
                city=form.cleaned_data['city'],
                postal_code=form.cleaned_data['postal_code'],
                total_amount=cart.get_total(),
                notes=form.cleaned_data['notes'],
                store_owner=store_owner,
                payment_method=payment_method,
            )
            order.save()

            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    total=cart_item.get_total()
                )

                # Update product stock
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save()

            # Clear cart
            cart.items.all().delete()

            messages.success(request, f'Order placed successfully! Order number: {order.order_number}')
            if payment_method == 'cod':
                return redirect('order_detail', order_number=order.order_number)

            return redirect(f"{reverse('pay_order', args=[order.order_number])}?method=all")
    else:
        form = CheckoutForm(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': profile.phone,
            'address': profile.address,
            'city': profile.city,
            'postal_code': profile.postal_code,
        })

    context = {
        'form': form,
        'cart': cart,
        'cart_items': cart_items,
        'store_owner': store_owner,
        'selected_payment_method': request.POST.get('payment_method', 'cod'),
    }
    return render(request, 'myapp/checkout.html', context)


@login_required
def order_detail(request, order_number):
    """Order detail/success page"""
    order = get_object_or_404(Order, order_number=order_number)
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Check if user has permission to view this order
    main_store_owner = is_main_store_owner(request.user)
    if (
        order.user != request.user
        and order.rider != request.user
        and order.store_owner != request.user
        and not main_store_owner
        and not request.user.is_staff
        and profile.user_type != 'admin'
    ):
        messages.error(request, 'You do not have permission to view this order.')
        return redirect('home')
    
    context = {
        'order': order,
        'can_store_owner_decide': (
            profile.user_type == 'store_owner'
            and order.store_owner == request.user
            and order.status == 'pending'
        ),
        'can_pay_order': (
            order.user == request.user
            and order.payment_method == 'paymongo'
            and order.payment_status != 'paid'
        ),
    }
    return render(request, 'myapp/order_detail.html', context)


@login_required
def order_history(request):
    """User's order history"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    if profile.user_type == 'rider':
        return redirect('rider_dashboard')

    orders = Order.objects.filter(user=request.user).select_related('store_owner').prefetch_related('items__product').order_by('-created_at')

    context = {
        'orders': orders,
    }
    return render(request, 'myapp/order_history.html', context)


def register_view(request):
    """User registration page"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        is_modal_signup = request.POST.get('registration_source') == 'modal'
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        user_type = request.POST.get('user_type', 'customer')
        
        # Validate user_type
        valid_user_types = ['customer', 'admin', 'rider', 'store_owner']
        if user_type not in valid_user_types:
            user_type = 'customer'
        
        # Validation
        errors = []
        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        
        if not email:
            errors.append('Email is required.')
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append('Please enter a valid email address.')
            else:
                email = email.lower()
                if User.objects.filter(email__iexact=email).exists():
                    errors.append('Email already registered.')
        
        if not password1 or len(password1) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        if password1 != password2:
            errors.append('Passwords do not match.')
        
        if not errors:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Set staff status for admin users
            if user_type == 'admin':
                user.is_staff = True
                user.save()
            
            # Create profile with user_type
            Profile.objects.create(user=user, user_type=user_type)
            
            messages.success(request, 'Account created successfully! Please log in to continue.')
            if is_modal_signup:
                request.session['open_auth_modal'] = 'login'
                return redirect('home')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
            register_data = {
                'first_name': first_name,
                'last_name': last_name,
                'username': username,
                'email': email,
                'user_type': user_type,
            }
            if is_modal_signup:
                request.session['register_errors'] = errors
                request.session['register_data'] = register_data
                request.session['open_auth_modal'] = 'signup'
                return redirect('home')
            return render(request, 'myapp/register.html', {
                'register_errors': errors,
                'register_data': register_data,
            })
    
    return render(request, 'myapp/register.html', {
        'register_errors': request.session.pop('register_errors', []),
        'register_data': request.session.pop('register_data', {}),
    })


def manager_dashboard(request):
    """Manager dashboard for store management"""
    # Only allow staff users
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access the manager dashboard.')
        return redirect('home')
    
    # Get dashboard statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    low_stock_products = Product.objects.filter(stock__lt=10, stock__gt=0, is_available=True)
    low_stock_count = low_stock_products.count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(total=models.Sum('total_amount'))['total'] or 0
    
    # Get recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'low_stock_count': low_stock_count,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'myapp/manager_dashboard.html', context)


@login_required
def store_owner_dashboard(request):
    """Dashboard for store owners to manage products and store settings"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    if profile.user_type != 'store_owner':
        messages.error(request, 'You do not have permission to access the store owner dashboard.')
        return redirect('home')

    store_settings, created = StoreSettings.objects.get_or_create(owner=request.user)
    active_tab = request.GET.get('tab', 'home')
    main_store_owner = is_main_store_owner(request.user)
    upload_store_settings = StoreSettings.objects.none()
    if main_store_owner:
        upload_store_settings = StoreSettings.objects.select_related('owner').filter(
            owner__profile__user_type='store_owner'
        ).exclude(
            store_name__icontains='Esugo'
        ).order_by('store_name')

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'product':
            product_form = ProductUploadForm(request.POST, request.FILES)
            settings_form = StoreSettingsForm(instance=store_settings)
            active_tab = 'upload'
            if product_form.is_valid():
                product = product_form.save(commit=False)
                product_owner = request.user
                if main_store_owner:
                    store_owner_id = request.POST.get('product_store_owner')
                    if not store_owner_id or not store_owner_id.isdigit():
                        messages.error(request, 'Please choose which store this product belongs to.')
                        return redirect(f"{reverse('store_owner_dashboard')}?tab=upload")

                    selected_store = upload_store_settings.filter(owner_id=store_owner_id).first()
                    if not selected_store:
                        messages.error(request, 'Please choose which store this product belongs to.')
                        return redirect(f"{reverse('store_owner_dashboard')}?tab=upload")
                    product_owner = selected_store.owner

                product.owner = product_owner
                product.save()
                messages.success(request, 'Product uploaded successfully.')
                return redirect('store_owner_dashboard')
        elif form_type == 'settings':
            product_form = ProductUploadForm()
            settings_form = StoreSettingsForm(request.POST, instance=store_settings)
            active_tab = 'settings'
            if settings_form.is_valid():
                settings_form.save()
                messages.success(request, 'Store settings updated successfully.')
                return redirect('store_owner_dashboard')
        elif form_type == 'branch_settings':
            product_form = ProductUploadForm()
            settings_form = StoreSettingsForm(instance=store_settings)
            active_tab = 'settings'
            if not main_store_owner:
                messages.error(request, 'Only the main store owner can update other store settings.')
                return redirect('store_owner_dashboard')

            branch_settings = get_object_or_404(
                StoreSettings,
                id=request.POST.get('store_settings_id'),
                owner__profile__user_type='store_owner',
            )
            branch_settings.location = request.POST.get('location', '').strip()
            branch_settings.opening_hours = request.POST.get('opening_hours', '').strip()
            branch_settings.save(update_fields=['location', 'opening_hours'])
            messages.success(request, f'{branch_settings.store_name} settings updated successfully.')
            return redirect('store_owner_dashboard')
        else:
            product_form = ProductUploadForm()
            settings_form = StoreSettingsForm(instance=store_settings)
    else:
        product_form = ProductUploadForm()
        settings_form = StoreSettingsForm(instance=store_settings)

    if main_store_owner:
        owner_products = Product.objects.filter(
            owner__store_settings__in=upload_store_settings
        )
    else:
        owner_products = Product.objects.filter(owner=request.user)

    product_filter = request.GET.get('product_filter', 'all')
    if product_filter not in ['all', 'available', 'low_stock', 'out_of_stock']:
        product_filter = 'all'

    filtered_products = owner_products
    product_filter_label = 'Recent Products'
    if product_filter == 'available':
        filtered_products = filtered_products.filter(is_available=True)
        product_filter_label = 'Available Products'
    elif product_filter == 'low_stock':
        filtered_products = filtered_products.filter(stock__lt=10, stock__gt=0, is_available=True)
        product_filter_label = 'Low Stock Products'
    elif product_filter == 'out_of_stock':
        filtered_products = filtered_products.filter(stock=0, is_available=True)
        product_filter_label = 'Out of Stock Products'

    products = filtered_products.select_related('category').order_by('-created_at')

    # All counts in one query
    product_counts = owner_products.aggregate(
        total=Count('id'),
        available=Count('id', filter=Q(is_available=True)),
        low_stock=Count('id', filter=Q(stock__lt=10, stock__gt=0, is_available=True)),
        out_of_stock=Count('id', filter=Q(stock=0, is_available=True)),
    )
    low_stock_count = product_counts['low_stock']
    out_of_stock_count = product_counts['out_of_stock']

    if main_store_owner:
        store_orders = Order.objects.filter(
            store_owner__profile__user_type='store_owner'
        ).exclude(store_owner__store_settings__store_name__icontains='Esugo')
    else:
        store_orders = Order.objects.filter(store_owner=request.user)
    store_orders = store_orders.select_related('user', 'store_owner').prefetch_related('items__product')
    pending_store_orders = store_orders.filter(status='pending').order_by('-created_at')
    recent_store_orders = store_orders.order_by('-created_at')[:8]
    editable_store_settings = StoreSettings.objects.none()
    if main_store_owner:
        editable_store_settings = StoreSettings.objects.select_related('owner').filter(
            owner__profile__user_type='store_owner'
        ).exclude(
            store_name__icontains='Esugo'
        ).order_by('store_name')

    context = {
        'profile': profile,
        'store_settings': store_settings,
        'product_form': product_form,
        'settings_form': settings_form,
        'active_tab': active_tab,
        'product_filter': product_filter,
        'product_filter_label': product_filter_label,
        'total_products': product_counts['total'],
        'available_products': product_counts['available'],
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'recent_products': products,
        'pending_store_orders': pending_store_orders,
        'recent_store_orders': recent_store_orders,
        'pending_store_orders_count': pending_store_orders.count(),
        'is_main_store_owner': main_store_owner,
        'editable_store_settings': editable_store_settings,
        'upload_store_settings': upload_store_settings,
    }
    return render(request, 'myapp/store_owner_dashboard.html', context)


@login_required
def store_owner_update_order(request, order_number):
    """Allow store owners to accept or decline their store orders."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    if profile.user_type != 'store_owner':
        messages.error(request, 'You do not have permission to update store orders.')
        return redirect('home')

    order = get_object_or_404(Order, order_number=order_number)
    main_store_owner = is_main_store_owner(request.user)
    if order.store_owner != request.user and not main_store_owner:
        messages.error(request, 'You can only update orders assigned to your store.')
        return redirect('store_owner_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        if order.status != 'pending':
            messages.warning(request, f'Order {order.order_number} has already been reviewed.')
        elif action == 'accept':
            order.status = 'confirmed'
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Order {order.order_number} accepted.')
        elif action == 'decline':
            order.status = 'cancelled'
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Order {order.order_number} declined.')
        else:
            messages.error(request, 'Invalid order action.')

    next_page = request.POST.get('next')
    if next_page == 'order_detail':
        return redirect('order_detail', order_number=order.order_number)
    return redirect('store_owner_dashboard')


@login_required
def store_owner_delete_product(request, product_id):
    """Delete a product uploaded by the current store owner"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    main_store_owner = is_main_store_owner(request.user)
    if profile.user_type != 'store_owner' and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete products.')
        return redirect('home')

    product = get_object_or_404(Product, id=product_id)
    if product.owner != request.user and not request.user.is_staff and not main_store_owner:
        messages.error(request, 'You can only delete products you uploaded.')
        return redirect('store_owner_dashboard')

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'{product_name} was deleted successfully.')

    return redirect('store_owner_dashboard')


@login_required
def profile_view(request):
    """User profile page"""
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'myapp/profile.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard for administrators"""
    # Only allow admin users (staff or user_type='admin')
    profile, created = Profile.objects.get_or_create(user=request.user)
    if not request.user.is_staff and profile.user_type != 'admin':
        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('home')
    
    # All counts and revenue in two queries
    order_stats = Order.objects.aggregate(
        total_orders=Count('id'),
        pending_orders=Count('id', filter=Q(status='pending')),
        confirmed_orders=Count('id', filter=Q(status='confirmed')),
        preparing_orders=Count('id', filter=Q(status='preparing')),
        out_for_delivery_orders=Count('id', filter=Q(status='out_for_delivery')),
        delivered_orders=Count('id', filter=Q(status='delivered')),
        cancelled_orders=Count('id', filter=Q(status='cancelled')),
        total_revenue=models.Sum('total_amount', filter=Q(payment_status='paid')),
        pending_revenue=models.Sum('total_amount', filter=Q(payment_status='pending')),
    )
    total_orders = order_stats['total_orders']
    pending_orders = order_stats['pending_orders']
    confirmed_orders = order_stats['confirmed_orders']
    preparing_orders = order_stats['preparing_orders']
    out_for_delivery_orders = order_stats['out_for_delivery_orders']
    delivered_orders = order_stats['delivered_orders']
    cancelled_orders = order_stats['cancelled_orders']
    total_revenue = order_stats['total_revenue'] or 0
    pending_revenue = order_stats['pending_revenue'] or 0

    product_stats = Product.objects.filter(is_available=True).aggregate(
        total_products=Count('id'),
        low_stock_products=Count('id', filter=Q(stock__lt=10, stock__gt=0)),
        out_of_stock_products=Count('id', filter=Q(stock=0)),
    )
    total_customers = Profile.objects.filter(user_type='customer', user__is_staff=False).count()
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    top_products = Product.objects.annotate(total_sold=Count('orderitem')).order_by('-total_sold')[:5]

    status_counts = {
        'pending': pending_orders,
        'confirmed': confirmed_orders,
        'preparing': preparing_orders,
        'out_for_delivery': out_for_delivery_orders,
        'delivered': delivered_orders,
        'cancelled': cancelled_orders,
    }

    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'preparing_orders': preparing_orders,
        'out_for_delivery_orders': out_for_delivery_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'total_customers': total_customers,
        'total_products': product_stats['total_products'],
        'low_stock_products': product_stats['low_stock_products'],
        'out_of_stock_products': product_stats['out_of_stock_products'],
        'recent_orders': recent_orders,
        'top_products': top_products,
        'status_counts': status_counts,
        'profile': profile,
    }
    return render(request, 'myapp/admin_dashboard.html', context)


@login_required
def admin_low_stock_products(request):
    """Admin view for low stock products."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    if not request.user.is_staff and profile.user_type != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    low_stock_products = Product.objects.filter(stock__lt=10, stock__gt=0, is_available=True).order_by('stock')
    context = {
        'products': low_stock_products,
        'title': 'Low Stock Products',
        'empty_message': 'No low stock products found.',
        'profile': profile,
    }
    return render(request, 'myapp/admin_stock_alerts.html', context)


@login_required
def admin_out_of_stock_products(request):
    """Admin view for out of stock products."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    if not request.user.is_staff and profile.user_type != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    out_of_stock_products = Product.objects.filter(stock=0, is_available=True).order_by('name')
    context = {
        'products': out_of_stock_products,
        'title': 'Out of Stock Products',
        'empty_message': 'No out of stock products found.',
        'profile': profile,
    }
    return render(request, 'myapp/admin_stock_alerts.html', context)


@login_required
def admin_stock_alerts(request):
    """Admin stock alerts management page."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    if not request.user.is_staff and profile.user_type != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')

    low_stock_products = Product.objects.filter(stock__lt=10, stock__gt=0, is_available=True).order_by('stock')
    out_of_stock_products = Product.objects.filter(stock=0, is_available=True).order_by('name')

    context = {
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'low_stock_count': low_stock_products.count(),
        'out_of_stock_count': out_of_stock_products.count(),
        'profile': profile,
    }
    return render(request, 'myapp/admin_stock_alerts_overview.html', context)


@login_required
def customer_dashboard(request):
    """Customer dashboard for customers"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    customer_orders = Order.objects.filter(user=request.user)

    order_stats = customer_orders.aggregate(
        total_orders=Count('id'),
        pending_orders=Count('id', filter=Q(status__in=['pending', 'confirmed', 'preparing'])),
        completed_orders=Count('id', filter=Q(status='delivered')),
        cancelled_orders=Count('id', filter=Q(status='cancelled')),
        total_spent=models.Sum('total_amount', filter=Q(payment_status='paid')),
    )
    total_orders = order_stats['total_orders']
    pending_orders = order_stats['pending_orders']
    completed_orders = order_stats['completed_orders']
    cancelled_orders = order_stats['cancelled_orders']
    total_spent = order_stats['total_spent'] or 0

    recent_orders = customer_orders.order_by('-created_at')[:5]
    
    # Get cart info
    cart = Cart.objects.filter(user=request.user).first()
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'total_spent': total_spent,
        'recent_orders': recent_orders,
        'cart': cart,
        'profile': profile,
    }
    return render(request, 'myapp/customer_dashboard.html', context)


@login_required
def rider_dashboard(request):
    """Rider dashboard for delivery riders"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Only allow riders
    if profile.user_type != 'rider':
        messages.error(request, 'You do not have permission to access the rider dashboard.')
        return redirect('home')
    
    my_orders = Order.objects.filter(rider=request.user).select_related('user').order_by('-created_at')

    rider_stats = Order.objects.filter(rider=request.user).aggregate(
        total_deliveries=Count('id', filter=Q(status='delivered')),
        pending_deliveries=Count('id', filter=Q(status__in=['pending', 'confirmed', 'preparing', 'out_for_delivery'])),
        completed_today=Count('id', filter=Q(status='delivered', delivered_at__date=timezone.now().date())),
    )
    total_deliveries = rider_stats['total_deliveries']
    pending_deliveries = rider_stats['pending_deliveries']
    completed_today = rider_stats['completed_today']
    total_earnings = total_deliveries * 50
    
    context = {
        'total_deliveries': total_deliveries,
        'pending_deliveries': pending_deliveries,
        'completed_today': completed_today,
        'total_earnings': total_earnings,
        'my_orders': my_orders,
        'profile': profile,
    }
    return render(request, 'myapp/rider_dashboard.html', context)


@login_required
def rider_update_status(request, order_number):
    """Rider updates the status of an assigned order"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Only allow riders
    if profile.user_type != 'rider':
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    order = get_object_or_404(Order, order_number=order_number)
    
    # Check if this rider is assigned to this order
    if order.rider != request.user:
        messages.error(request, 'You are not assigned to this order.')
        return redirect('rider_dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        allowed_transitions = {
            'delivered': ['confirmed', 'preparing', 'out_for_delivery'],
            'cancelled': ['confirmed', 'preparing', 'out_for_delivery'],
        }
        
        if new_status in allowed_transitions and order.status in allowed_transitions[new_status]:
            order.status = new_status
            if new_status == 'delivered':
                order.delivered_at = timezone.now()
                if order.payment_method == 'cod':
                    order.payment_status = 'paid'
            order.save()
            messages.success(request, f'Order {order.order_number} status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status update for this order.')
    
    return redirect('rider_dashboard')


@login_required
def admin_assign_rider(request, order_number):
    """Admin assigns a rider to an order"""
    # Only allow admin users
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('home')
    
    order = get_object_or_404(Order, order_number=order_number)
    if order.status == 'pending':
        messages.error(request, 'The store owner must accept this order before assigning a rider.')
        return redirect('admin_dashboard')

    # Get all riders
    riders = User.objects.filter(profile__user_type='rider')
    
    if request.method == 'POST':
        rider_id = request.POST.get('rider')
        if rider_id:
            rider = get_object_or_404(User, id=rider_id, profile__user_type='rider')
            order.rider = rider
            if order.status in ['confirmed', 'preparing']:
                order.status = 'out_for_delivery'
            order.save()
            messages.success(request, f'Rider {rider.first_name} {rider.last_name} assigned to order {order.order_number}.')
        else:
            messages.error(request, 'Please select a rider.')
        return redirect('admin_dashboard')
    
    context = {
        'order': order,
        'riders': riders,
    }
    return render(request, 'myapp/admin_assign_rider.html', context)



@login_required
def pay_order(request, order_number):
    """Redirect customer to PayMongo checkout page."""
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user
    )

    if order.payment_method == 'cod':
        messages.info(request, 'This order is Cash on Delivery. Please pay when your order arrives.')
        return redirect('order_detail', order_number=order.order_number)

    amount_centavos = int(order.total_amount * 100)
    method = request.GET.get('method', 'all')
    method_map = {
        'gcash': ['gcash'],
        'maya': ['paymaya'],
        'card': ['card'],
        'qrph': ['qrph'],
        'grabpay': ['grab_pay'],
        'all': ['gcash', 'paymaya', 'card', 'qrph', 'grab_pay'],
    }
    payment_method_types = method_map.get(method, method_map['all'])

    redirect_url = request.build_absolute_uri(
        reverse('payment_result', args=[order.order_number])
    )

    try:
        link_data = create_checkout_session(
            amount=amount_centavos,
            description=f"Order {order.order_number}",
            redirect_url=redirect_url,
            payment_method_types=payment_method_types
        )

        order.paymongo_link_id = link_data["checkout_session_id"]
        order.checkout_url = link_data["checkout_url"]
        order.payment_status = 'pending'
        order.save()

        return redirect(link_data["checkout_url"])

    except Exception as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('order_detail', order_number=order.order_number)


@login_required
def payment_result(request, order_number):
    """Display PayMongo payment result and update order payment status."""
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user
    )

    status = request.GET.get("status")

    if status == "success":
        order.payment_status = "paid"
    elif status == "failed":
        order.payment_status = "failed"

    order.save()

    return render(request, 'myapp/payment_result.html', {
        'order': order
    })
