



    // Function to handle Add to Cart button click
    function addToCartHandler(productId) {
      // Check if the user is authenticated
      if (!isUserAuthenticated()) {
        // If not authenticated, show a message and redirect to the login page
        alert('Please sign in to start shopping with us.');
        window.location.href = '/login';  // Adjust the URL to your login page
        return;
      }

      // If authenticated, open the Add to Cart modal
      openAddToCartModal(productId);
    }

    // Function to check if the user is authenticated
    function isUserAuthenticated() {
      // Adjust this logic based on your authentication implementation
      return {{ current_user.is_authenticated }};
    }

    // Function to open the Add to Cart modal
    function openAddToCartModal(productId) {
      // Use Bootstrap's modal function to open the modal
      $('#addToCartModal' + productId).modal('show');

      // Fetch and update the quantity when the modal is opened
      updateQuantityOnModalOpen(productId);
    }

    // Function to fetch and update the quantity when the modal is opened
    async function updateQuantityOnModalOpen(productId) {
      try {
        const response = await fetch(`/cart/api/get_quantity/${productId}`);
        const data = await response.json();

        if (data.status === 'success') {
          // Update the quantity input in the modal
          const quantityInput = document.getElementById('quantity' + productId);
          quantityInput.value = data.data.quantity;
        } else {
          console.error('Error fetching product quantity:', data.message);
        }
      } catch (error) {
        console.error('Error fetching product quantity:', error);
      }
    }

     // Update cart count using AJAX
 $(document).ready(function () {
  function updateCartCount() {
    console.log('Updating cart count...'); // Debug statement
    $.ajax({
      url: 'cart/get_cart_count',
      method: 'GET',
      success: function (response) {
        console.log('AJAX Response:', response); // Debug statement
        if (response.status === 'success') {
          console.log('Updating cart count:', response.cart_count); // Debug statement
          // Update the badge with the actual cart count
          const cartIcon = $('.floating-cart-icon');
          const currentCount = parseInt(cartIcon.find('.badge').text(), 10);
          const newCount = response.cart_count;

          cartIcon.find('.badge').text(newCount);

          // Toggle visibility of the entire cart icon based on the cart count
          if (newCount > 0) {
            cartIcon.removeClass('inactive');
          } else {
            cartIcon.addClass('inactive');
          }

          // Add shake class to the entire cart icon if the count has increased
          if (newCount > currentCount) {
            cartIcon.addClass('shake');

            // Remove the shake class after a short delay (e.g., 1 second)
            setTimeout(function () {
              cartIcon.removeClass('shake');
            }, 1000);
          }
        } else if (response.status === 'not_logged_in') {
          console.log('User is not logged in, setting cart count to 0'); // Debug statement
          const cartIcon = $('.floating-cart-icon');
          cartIcon.find('.badge').text(0);
          cartIcon.addClass('inactive');
        } else {
          console.error('Error fetching cart count:', response.message);
        }
      },
      error: function (error) {
        console.error('AJAX Error:', error);
      },
    });
  }

  updateCartCount();

  // Set an interval to periodically update the cart count (every 15 seconds as you mentioned)
  setInterval(function () {
    console.log('Periodic cart count update...'); // Debug statement
    updateCartCount();
  }, 15000);
});


  // Trigger the Add to Cart modal when clicking on the floating cart icon
  $('.floating-cart-icon').click(function () {
    // Check if the user is authenticated
    if (!isUserAuthenticated()) {
      // If not authenticated, show a message and redirect to the login page
      alert('Please sign in to start shopping with us.');
      window.location.href = '/login'; // Adjust the URL to your login page
      return;
    }

    // If authenticated, open the Add to Cart modal for the first product
    const firstProductId = $('.product-card:first').data('product-id');
    openAddToCartModal(firstProductId);
  });

  // Function to check if the user is authenticated
  function isUserAuthenticated() {
    // Adjust this logic based on your authentication implementation
    return {{ current_user.is_authenticated }};
  }

  // Function to open the Add to Cart modal
  function openAddToCartModal(productId) {
    // Use Bootstrap's modal function to open the modal
    $('#addToCartModal' + productId).modal('show');

    // Fetch and update the quantity when the modal is opened
    updateQuantityOnModalOpen(productId);
  }

  // Function to fetch and update the quantity when the modal is opened
  async function updateQuantityOnModalOpen(productId) {
    try {
      const response = await fetch(`/cart/api/get_quantity/${productId}`);
      const data = await response.json();

      if (data.status === 'success') {
        // Update the quantity input in the modal
        const quantityInput = document.getElementById('quantity' + productId);
        quantityInput.value = data.data.quantity;
      } else {
        console.error('Error fetching product quantity:', data.message);
      }
    } catch (error) {
      console.error('Error fetching product quantity:', error);
    }
  }

      function searchProducts() {
          var query = document.getElementById("searchInput").value.trim();
          if (query.length === 0) {
              // Clear search results and display all products
              document.getElementById("searchResults").innerHTML = "";
              document.getElementById("productListing").style.display = "block";
              return;
          }
          var xhr = new XMLHttpRequest();
          xhr.open('GET', '/search?query=' + encodeURIComponent(query), true);
          xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
          xhr.onreadystatechange = function() {
              if (xhr.readyState === XMLHttpRequest.DONE) {
                  if (xhr.status === 200) {
                      // Update search results
                      document.getElementById("searchResults").innerHTML = xhr.responseText;
                      // Hide product listing when search results are displayed
                      document.getElementById("productListing").style.display = "none";
                  }
              }
          };
          xhr.send();
      }


    function trackProductEvent(productId, eventType) {
        // Fetch the CSRF token from the meta tag
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

        fetch('/api/track-product-event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken  // Include CSRF token
            },
            body: JSON.stringify({
                productId: productId,
                eventType: eventType,
                timestamp: new Date().toISOString()  // Use current ISO timestamp
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!response.ok) {
                throw new Error(data.error || 'Unknown error');
            }
            console.log('Event tracked:', data);
        })
        .catch(error => {
            console.error('Error tracking event:', error);
        });
    }

    // Example usage for product view event
    document.querySelectorAll('.product-card').forEach(card => {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const productId = entry.target.getAttribute('data-product-id');
                    trackProductEvent(productId, 'view');
                    observer.unobserve(entry.target);  // Stop observing once viewed
                }
            });
        });
        observer.observe(card);
    });


 document.addEventListener("DOMContentLoaded", function () {
    // Initialize event listeners for the existing products
    initializeEventListeners();

    // Load Recommendations for the user
    //loadRecommendations();

    // Add to Cart interaction
    document.querySelectorAll(".add-to-cart-btn").forEach(function (button) {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            const productId = button.getAttribute("data-product-id");
            addToCart(productId);
        });
    });

    // Search Products interaction
    document.getElementById("searchInput").addEventListener("keyup", function() {
        searchProducts();
    });
});

// Function to initialize event listeners for tracking
function initializeEventListeners() {
    // Quick View Button (Track as 'view')
    document.querySelectorAll(".quick-view-btn").forEach(button => {
        button.addEventListener("click", function (event) {
            const productId = event.target.getAttribute("data-product-id");
            trackProductEvent(productId, "view");
        });
    });

    // Product Image and Name (Track as 'click')
    document.querySelectorAll(".product-image, .product-name").forEach(element => {
        element.addEventListener("click", function (event) {
            const productId = event.target.closest(".product-card").getAttribute("data-product-id");
            trackProductEvent(productId, "click");
        });
    });

    // Viewing products using Intersection Observer
    document.querySelectorAll('.product-card').forEach(card => {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const productId = entry.target.getAttribute('data-product-id');
                    trackProductEvent(productId, 'view');
                    observer.unobserve(entry.target);  // Stop observing once viewed
                }
            });
        });
        observer.observe(card);
    });
}

// Function to search products and display results
function searchProducts() {
    var query = document.getElementById("searchInput").value.trim();
    if (query.length === 0) {
        // Clear search results and display all products
        document.getElementById("searchResults").innerHTML = "";
        document.getElementById("searchResults").style.display = "none";
        document.getElementById("productListing").style.display = "block";
        return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/search?query=' + encodeURIComponent(query), true);
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                // Update search results
                document.getElementById("searchResults").innerHTML = xhr.responseText;
                document.getElementById("searchResults").style.display = "block";
                // Hide product listing when search results are displayed
                document.getElementById("productListing").style.display = "none";
                // Initialize event listeners for the search results
                initializeEventListeners();
            }
        }
    };
    xhr.send();
}

function getCSRFToken() {
    // Function to retrieve the CSRF token from the cookie or meta tag
    // Implement this function based on your CSRF token setup
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function trackProductEvent(productId, eventType) {
    const csrfToken = getCSRFToken();

    fetch('/api/track-product-event', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            productId: productId,
            eventType: eventType,
            timestamp: new Date().toISOString()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error || 'Unknown error');
        }
        console.log('Event tracked:', data);
    })
    .catch(error => {
        console.error('Error tracking event:', error);
    });
}

/*
   // Function to load recommendations dynamically
        async function loadRecommendations() {
            try {
                const response = await fetch('/api/recommendations?user_id={{ current_user.id }}&num=5');
                const recommendedProducts = await response.json();

                if (recommendedProducts.length > 0) {
                    const recommendationsSection = document.querySelector(".recommended-products");
                    recommendationsSection.innerHTML = ""; // Clear existing recommendations

                    recommendedProducts.forEach(product => {
                        const productCard = `
                            <div class="col">
                                <div class="card product-card border-0 shadow-sm" data-product-id="${product.id}">
                                    <div class="magnifier position-relative overflow-hidden">
                                        <img src="{{ url_for('static', filename='uploads/') }}${product.image}" class="img-fluid rounded-start" alt="${product.name}">
                                    </div>
                                    <div class="product-overlay d-flex align-items-center justify-content-center">
                                        <div class="card-body text-center">
                                            <h6 class="card-title text-primary mb-2 product-name" data-product-id="${product.id}">${product.brand}</h6>

                                            <button type="button" class="btn btn-light btn-sm quick-view-btn" data-product-id="${product.id}" data-bs-toggle="modal" data-bs-target="#productDetailsModal${product.id}">
                                                Quick View
                                            </button>
                                            <p class="card-text">Price: Ksh ${product.price}</p>
                                            <button type="button" class="btn btn-success btn-sm fs-6" data-bs-toggle="modal" data-bs-target="#addToCartModal${product.id}">
                                                Add To Cart
                                            </button>

                                        </div>
                                    </div>
                                </div>
                            </div>`;

                        recommendationsSection.insertAdjacentHTML('beforeend', productCard);
                    });

                    initializeEventListeners();
                }
            } catch (error) {
                console.error('Error loading recommendations:', error);
            }
        }

        // Call loadRecommendations when the page is loaded
        document.addEventListener('DOMContentLoaded', () => {
            loadRecommendations();
        });

        function initializeEventListeners() {
            // Initialize event listeners for the dynamically created elements
        }

*/
// Function to add product to cart
async function addToCart(productId) {
    try {
        const response = await fetch(`/cart/api/add`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken(),
            },
            body: JSON.stringify({ productId }),
        });

        const data = await response.json();

        if (data.status === "success") {
            toastr.success("Product added to cart");
        } else {
            toastr.error("Failed to add product to cart");
            console.error("Error adding product to cart:", data.message);
        }
    } catch (error) {
        toastr.error("An error occurred");
        console.error("Fetch error:", error);
    }
}

// Function to get CSRF token from meta tag
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.content : "";
}


   document.addEventListener('DOMContentLoaded', () => {
    const lazyImages = document.querySelectorAll('img.lazy');

    if ('IntersectionObserver' in window) {
        const lazyImageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const lazyImage = entry.target;
                    lazyImage.src = lazyImage.dataset.src;
                    lazyImage.classList.add('loaded');
                    lazyImageObserver.unobserve(lazyImage);
                }
            });
        });

        lazyImages.forEach(lazyImage => {
            lazyImageObserver.observe(lazyImage);
        });
    } else {
        // Fallback for older browsers
        const lazyLoad = () => {
            lazyImages.forEach(lazyImage => {
                if (lazyImage.getBoundingClientRect().top < window.innerHeight && lazyImage.getBoundingClientRect().bottom > 0) {
                    lazyImage.src = lazyImage.dataset.src;
                    lazyImage.classList.add('loaded');
                }
            });

            if (lazyImages.length === 0) {
                window.removeEventListener('scroll', lazyLoad);
                window.removeEventListener('resize', lazyLoad);
                window.removeEventListener('orientationchange', lazyLoad);
            }
        };

        window.addEventListener('scroll', lazyLoad);
        window.addEventListener('resize', lazyLoad);
        window.addEventListener('orientationchange', lazyLoad);
        lazyLoad();
    }
});
 
function searchProducts() {
    let query = $('#searchInput').val();
    if (query.length > 0) {
        $.ajax({
            url: '/search', // Adjust this URL based on your route
            method: 'GET',
            data: { q: query },
            success: function(data) {
                $('#product-list').empty();
                data.forEach(function(product) {
                    let productCard = `
                        <div class="col">
                            <div class="card product-card border-0 shadow-sm" data-product-id="${product.id}">
                                <div class="magnifier position-relative overflow-hidden">
                                    ${product.images.length > 0 ? 
                                        `<img data-src="/static/uploads/${product.images[0].cover_image}" class="card-img-top product-image lazy" alt="${product.name}">` : 
                                        `<img data-src="/static/alt_img.png" class="card-img-top product-image lazy" alt="Placeholder Image">`}
                                    <div class="product-overlay d-flex align-items-center justify-content-center">
                                        <button type="button" class="btn btn-light btn-sm quick-view-btn" data-product-id="${product.id}" data-bs-toggle="modal" data-bs-target="#productDetailsModal${product.id}">Quick View</button>
                                    </div>
                                </div>
                                <div class="card-body text-center">
                                    <h6 class="card-title text-primary mb-2 product-name" data-product-id="${product.id}">${product.brand}</h6>
                                    <p class="card-text text-muted fs-6 mb-3">${product.description.substring(0, 80)}...</p>
                                    <p class="card-text fs-6 mb-2"><strong>Ksh ${product.unit_price} / ${product.unit_measurement}</strong></p>
                                    <button type="button" class="btn btn-success btn-sm fs-6" data-bs-toggle="modal" data-bs-target="#addToCartModal${product.id}">
                                        Buy
                                    </button>
                                </div>
                            </div>
                        </div>`;
                    $('#product-list').append(productCard);
                });
            }
        });
    } else {
        // Optionally, you could reload the full product list if the search query is empty
    }
}

// Optional: Use Intersection Observer to lazy load images
$(document).ready(function() {
    let lazyImages = [].slice.call(document.querySelectorAll('img.lazy'));
    let active = false;

    const lazyLoad = function() {
        if (active === false) {
            active = true;

            setTimeout(function() {
                lazyImages.forEach(function(img) {
                    if (img.getBoundingClientRect().top < window.innerHeight && img.getBoundingClientRect().bottom > 0) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        lazyImages = lazyImages.filter(function(img) {
                            return img.classList.contains('lazy');
                        });

                        if (lazyImages.length === 0) {
                            document.removeEventListener('scroll', lazyLoad);
                            window.removeEventListener('resize', lazyLoad);
                            window.removeEventListener('orientationchange', lazyLoad);
                        }
                    }
                });

                active = false;
            }, 200);
        }
    };

    document.addEventListener('scroll', lazyLoad);
    window.addEventListener('resize', lazyLoad);
    window.addEventListener('orientationchange', lazyLoad);

    lazyLoad();
});