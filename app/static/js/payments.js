// static/js/payments.js
$(document).ready(function() {
    $('[data-bs-toggle="tooltip"]').tooltip();

    document.querySelectorAll('.update-payment').forEach(button => {
        button.addEventListener('click', function () {
            const orderId = this.dataset.orderId;
            const orderTotalPrice = this.dataset.orderTotalPrice;

            document.getElementById('orderId').value = orderId;
            document.getElementById('amount_paid').value = orderTotalPrice;
            fetch(`/payment/get_balance/${orderId}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('balance').innerHTML = `Due Balance: ${data.total_balance}`;
                });

            const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
            modal.show();
        });
    });

    document.getElementById('paymentForm').addEventListener('submit', function (event) {
        event.preventDefault();
        const formData = new FormData(this);

        document.getElementById('loadingSpinner').style.display = 'block';

        fetch(`/payment/update_payment/${document.getElementById('orderId').value}`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('loadingSpinner').style.display = 'none';
            if (data.status === 'success') {
                const successToast = new bootstrap.Toast(document.getElementById('successToast'));
                successToast.show();
                const modal = bootstrap.Modal.getInstance(document.getElementById('paymentModal'));
                modal.hide();
                location.reload();
            } else {
                const errorToast = new bootstrap.Toast(document.getElementById('errorToast'));
                errorToast.show();
            }
        })
        .catch(error => {
            document.getElementById('loadingSpinner').style.display = 'none';
            const errorToast = new bootstrap.Toast(document.getElementById('errorToast'));
            errorToast.show();
            console.error('Error:', error);
        });
    });
});
