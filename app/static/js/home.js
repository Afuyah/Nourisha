// static/js/home.js

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Typed.js for typing effect
    var typed = new Typed('#typed-paragraph', {
        strings: [
            "Discover fresh produce and quality groceries. Shop now and enjoy exclusive discounts up to 90%.",
            "Your satisfaction is our priority."
        ],
        typeSpeed: 50,
        backSpeed: 30,
        backDelay: 2500,
        startDelay: 500,
        loop: true,
        showCursor: true,
        cursorChar: '|'
    });

    // Toggle 'More' / 'Less' services visibility
    const moreButton = document.getElementById('moreButton');
    const moreServices = document.getElementById('moreServices');
    const smallScreenService = document.getElementById('smallScreenService');

    moreButton.addEventListener('click', function () {
        if (moreServices.classList.contains('d-none')) {
            moreServices.classList.remove('d-none');
            moreButton.textContent = 'Less';
        } else {
            moreServices.classList.add('d-none');
            moreButton.textContent = 'More';
        }
    });
});

// Add animation to cards on scroll
$(document).ready(function () {
    $(window).on('scroll', function () {
        $('.card').each(function () {
            if ($(this).offset().top < $(window).scrollTop() + $(window).height() - 100) {
                $(this).addClass('animate__animated animate__fadeInUp');
            }
        });
    });

    // Trigger scroll event on page load
    $(window).trigger('scroll');
});

// Add animation to sections on scroll
$(document).ready(function () {
    $(window).on('scroll', function () {
        $('#about-us').each(function () {
            if ($(this).offset().top < $(window).scrollTop() + $(window).height() - 100) {
                $(this).find('.animate__animated').each(function () {
                    $(this).addClass('animate__fadeInUp');
                });
            }
        });
    });

    // Trigger scroll event on page load
    $(window).trigger('scroll');
});

// Handle navbar transparency on scroll
document.addEventListener('DOMContentLoaded', function () {
    const navbar = document.querySelector('.navbar');
    const toggleButton = document.querySelector('.navbar-toggle');
    const navbarNav = document.querySelector('.navbar-nav');

    // Scroll event to toggle transparent class
    window.addEventListener('scroll', function () {
        if (window.scrollY > 100) {
            navbar.classList.remove('transparent');
        } else {
            navbar.classList.add('transparent');
        }
    });
});

// Carousel for featured categories
$(document).ready(function () {
    $('#featuredCategoriesCarousel').on('slide.bs.carousel', function (e) {
        var $e = $(e.relatedTarget);
        var idx = $e.index();
        var itemsPerSlide = 3;
        var totalItems = $('.carousel-item').length;

        if (idx >= totalItems - (itemsPerSlide - 1)) {
            var it = itemsPerSlide - (totalItems - idx);
            for (var i = 0; i < it; i++) {
                // Append slides to end
                if (e.direction == "left") {
                    $('.carousel-item').eq(i).appendTo('.carousel-inner');
                } else {
                    $('.carousel-item').eq(0).appendTo('.carousel-inner');
                }
            }
        }
    });
});
