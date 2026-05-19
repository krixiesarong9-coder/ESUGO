// Esugo Grocery - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Add to cart animation
    var addToCartButtons = document.querySelectorAll('.btn-success[href*="cart/add"]');
    addToCartButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            this.classList.add('add-to-cart-animation');
            var self = this;
            setTimeout(function() {
                self.classList.remove('add-to-cart-animation');
            }, 300);
        });
    });

    // Quantity input validation
    var quantityInputs = document.querySelectorAll('input[type="number"]');
    quantityInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            var min = parseInt(this.getAttribute('min')) || 1;
            var max = parseInt(this.getAttribute('max')) || 999;
            var value = parseInt(this.value) || min;
            
            if (value < min) {
                this.value = min;
            } else if (value > max) {
                this.value = max;
            }
        });
    });

    // Search form validation
    var searchForm = document.querySelector('form[action*="products"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            var searchInput = this.querySelector('input[name="q"]');
            if (searchInput && searchInput.value.trim() === '') {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }

    // Confirm before removing from cart
    var removeButtons = document.querySelectorAll('form[action*="cart/remove"] button');
    removeButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to remove this item from your cart?')) {
                e.preventDefault();
            }
        });
    });

    // Format currency display
    var priceElements = document.querySelectorAll('.price, .total');
    priceElements.forEach(function(element) {
        var price = parseFloat(element.textContent.replace('$', ''));
        if (!isNaN(price)) {
            element.textContent = '$' + price.toFixed(2);
        }
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            var href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                var target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Lazy loading for images (if not natively supported)
    if ('loading' in HTMLImageElement.prototype) {
        var images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach(function(img) {
            img.src = img.dataset.src;
        });
    } else {
        // Fallback for browsers that don't support lazy loading
        var script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
        document.body.appendChild(script);
    }

    // Cart item count update
    function updateCartCount(count) {
        var cartBadge = document.querySelector('.navbar-nav .badge');
        if (cartBadge) {
            cartBadge.textContent = count;
            if (count === 0) {
                cartBadge.style.display = 'none';
            } else {
                cartBadge.style.display = 'inline';
            }
        }
    }

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Phone number formatting
    var phoneInputs = document.querySelectorAll('input[name="phone"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            var x = e.target.value.replace(/\D/g, '').match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
            e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
        });
    });

    // Postal code formatting
    var postalInputs = document.querySelectorAll('input[name="postal_code"]');
    postalInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
        });
    });

    // Sort dropdown change handler
    var sortSelect = document.querySelector('select[onchange*="location.href"]');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            window.location.href = this.value;
        });
    }

    // Print order functionality
    var printButton = document.querySelector('.btn-print');
    if (printButton) {
        printButton.addEventListener('click', function() {
            window.print();
        });
    }

    // Track page view for analytics (placeholder)
    console.log('Esugo Grocery - Page loaded successfully');
});

// Utility functions
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}

function debounce(func, wait) {
    var timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in other scripts
window.Esugo = {
    formatCurrency: formatCurrency,
    debounce: debounce
};