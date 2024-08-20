document.addEventListener('DOMContentLoaded', function() {
    // Initialize modals using Bootstrap's JavaScript API
    const userAccountsLink = document.getElementById('userAccountsLink');
    const userSelectionModal = new bootstrap.Modal(document.getElementById('userSelectionModal'));
    const userInformationModal = new bootstrap.Modal(document.getElementById('userInformationModal'));
    const orderDetailsModal = new bootstrap.Modal(document.getElementById('orderDetailsModal'));
    const shopForUserModal = new bootstrap.Modal(document.getElementById('shopForUserModal'));

    // Show user selection modal when the button is clicked
    if (userAccountsLink) {
        userAccountsLink.addEventListener('click', function(event) {
            event.preventDefault();
            userSelectionModal.show();
        });
    }

    // Initialize DataTable
    let userTable;
    
    // Load users into the DataTable
    fetch('/admin/get_users')
        .then(response => response.json())
        .then(users => {
            const userTableBody = document.querySelector('#userTable tbody');
            if (userTableBody) {
                userTableBody.innerHTML = '';
                users.forEach(user => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${user.name}</td>
                        <td>${user.email}</td>
                        <td>${user.phone}</td>
                        <td>
                            <button class="btn btn-primary btn-sm" onclick="loadUserInfo(${user.id})">Details</button>
                        </td>
                    `;
                    userTableBody.appendChild(row);
                });

                // Initialize DataTable after populating it
                userTable = $('#userTable').DataTable({
                    "paging": true,
                    "searching": true,
                    "ordering": true
                });
            }
        })
        .catch(error => console.error('Error loading users:', error));

    // Function to load user information
    window.loadUserInfo = function(userId) {
        fetch(`/admin/get_user_info/${userId}`)
            .then(response => response.json())
            .then(userInfo => {
                document.getElementById('userNameInfo').innerText = userInfo.name;
                document.getElementById('userPhoneInfo').innerText = userInfo.phone;
                document.getElementById('userEmailInfo').innerText = userInfo.email;
                document.getElementById('walletBalance').innerText = userInfo.wallet_balance;
                document.getElementById('outstandingBalance').innerText = userInfo.outstanding_balance;
                document.getElementById('purchaseFrequency').innerText = userInfo.purchase_frequency;
                document.getElementById('lastLogin').innerText = userInfo.last_login;
                document.getElementById('mostBoughtItems').innerText = userInfo.most_bought_items;

                const ordersTableBody = document.getElementById('ordersTable').querySelector('tbody');
                if (ordersTableBody) {
                    ordersTableBody.innerHTML = '';
                    userInfo.orders.forEach(order => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${order.order_number}</td>
                            <td>${order.amount}</td>
                            <td>
                                <button class="btn btn-primary" onclick="loadOrderDetails(${order.id})">Details</button>
                                <button class="btn btn-secondary" onclick="shopForUser(${userInfo.id})">Shop for User</button>
                            </td>
                        `;
                        ordersTableBody.appendChild(row);
                    });
                }
                userSelectionModal.hide();
                userInformationModal.show();
            })
            .catch(error => console.error('Error loading user info:', error));
    }

    // Function to load order details
    window.loadOrderDetails = function(orderId) {
        fetch(`/admin/get_order_details/${orderId}`)
            .then(response => response.json())
            .then(orderDetails => {
                const orderDetailsContent = document.getElementById('orderDetailsContent');
                if (orderDetailsContent) {
                    orderDetailsContent.innerHTML = `
                        <p><strong>Order Number:</strong> ${orderDetails.order_number}</p>
                        <p><strong>Amount:</strong> ${orderDetails.amount}</p>
                        <p><strong>Items:</strong> ${orderDetails.items}</p>
                    `;
                    orderDetailsModal.show();
                }
            })
            .catch(error => console.error('Error loading order details:', error));
    }

    // Function to shop for a user
    window.shopForUser = function(userId) {
        fetch('/admin/shop_for_user')
            .then(response => response.json())
            .then(products => {
                const productSelection = document.getElementById('productSelection');
                if (productSelection) {
                    productSelection.innerHTML = '';
                    products.forEach(product => {
                        const productCard = document.createElement('div');
                        productCard.classList.add('card', 'mb-3');
                        productCard.innerHTML = `
                            <div class="card-body">
                                <h5 class="card-title">${product.name}</h5>
                                <p class="card-text">${product.description}</p>
                                <p class="card-text"><strong>Price:</strong> ${product.price}</p>
                                <button class="btn btn-primary" onclick="addToCart(${userId}, ${product.id})">Add to Cart</button>
                            </div>
                        `;
                        productSelection.appendChild(productCard);
                    });
                    shopForUserModal.show();
                }
            })
            .catch(error => console.error('Error loading products:', error));
    }

    // Function to add a product to the cart
    window.addToCart = function(userId, productId) {
        fetch(`/admin/add_to_cart/${userId}/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Product added to cart successfully!');
                shopForUserModal.hide();
            } else {
                alert('Failed to add product to cart.');
            }
        })
        .catch(error => console.error('Error adding product to cart:', error));
    }
});
