$(document).ready(function() {
    

    // Show login modal and load form via AJAX
    $('#loginLink').on('click', function(e) {
        e.preventDefault(); // Prevent the default link behavior
        $('#loginModal').modal('show'); // Show the login modal

        $.ajax({
            url: "{{ url_for('auth.login') }}",
            method: 'GET',
            success: function(data) {
                $('#modalBody').html(data); // Load login form into modal body
            },
            error: function(xhr, status, error) {
                console.error('Error loading login form:', error);
                $('#modalBody').html('<p class="text-danger">Error loading form. Please try again later.</p>'); // Display error message
            }
        });
    });

    // Handle form submission
    $(document).on('submit', '#loginForm', function(e) {
        e.preventDefault(); // Prevent the default form submission

        var form = $(this);
        var action = form.attr('action');
        var data = form.serialize();

        $('#loaderModal').modal('show'); // Show loader modal

        $.ajax({
            url: action,
            method: 'POST',
            data: data,
            headers: {
                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content') // Include CSRF token
            },
            success: function(response) {
                $('#loaderModal').modal('hide'); // Hide loader modal

                if (response.success) {
                    $('#resultMessage').html(`
                        <div class="text-success">
                            <i class="bi bi-check-circle fs-1"></i>
                            <p class="mt-3">Login successful! Redirecting...</p>
                        </div>
                    `);
                    $('#resultModal').modal('show');
                    setTimeout(function() {
                        window.location.href = response.redirect; // Redirect after 1.5 seconds
                    }, 1500);
                } else {
                    $('#resultMessage').html(`
                        <div class="text-danger">
                            <i class="bi bi-x-circle fs-1"></i>
                            <p class="mt-3">${response.html}</p>
                        </div>
                    `);
                    $('#resultModal').modal('show');
                }
            },
            error: function(xhr, status, error) {
                $('#loaderModal').modal('hide'); // Hide loader modal
                console.error('Error during login:', error);
                $('#resultMessage').html(`
                    <div class="text-danger">
                        <i class="bi bi-x-circle fs-1"></i>
                        <p class="mt-3">Error during login. Please try again later.</p>
                    </div>
                `);
                $('#resultModal').modal('show');
            }
        });
    });

    // Show the login modal based on URL query parameter
    function getQueryParam(param) {
        var urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }

    if (getQueryParam('show_modal') === 'true') {
        $('#loginModal').modal('show'); // Show the login modal
    }

    // Show the login modal if an AJAX request returns a 401 status
    $(document).ajaxError(function(event, xhr, options, exc) {
        if (xhr.status === 401) {
            $('#loginModal').modal('show'); // Show the login modal
        }
    });
});
