// static/script.js

$(document).ready(function() {
    function updateSelectedItemsDisplay() {
        $('#outfitDisplay').empty();
        selectedItems.forEach(function(item) {
            var itemImagePath = item['File path'];
            if (!itemImagePath.startsWith('/')) {
                itemImagePath = '/static/' + itemImagePath;
            }
            var itemImageAlt = item['Style'];
            
            var newItem = $('<img>').attr({
                'src': itemImagePath,
                'alt': itemImageAlt,
                'class': 'selected-item-image'
            });
            
            $('#outfitDisplay').append(newItem);
        });
        
        $('#selectedItems').val(JSON.stringify(selectedItems.map(item => item['Srno'])));
    }

    function updateCheckboxes() {
        $('.check').prop('checked', false);  // Uncheck all checkboxes first
        selectedItems.forEach(function(item) {
            $('#item' + item['Srno']).prop('checked', true);
        });
    }

    updateSelectedItemsDisplay();
    updateCheckboxes();

    $('.check').change(function() {
        var itemId = $(this).val();
        var item = {
            'Srno': itemId,
            'File path': $(this).siblings('label').find('img').attr('src'),
            'Style': $(this).siblings('label').find('img').attr('alt')
        };
        
        if (this.checked) {
            if (!selectedItems.some(i => i['Srno'] === itemId)) {
                selectedItems.push(item);
            }
        } else {
            selectedItems = selectedItems.filter(function(i) { return i['Srno'] !== itemId; });
        }
        
        updateSelectedItemsDisplay();  // Call this function immediately after changing the selection
    });

    $('nav a').click(function(e) {
        e.preventDefault();
        var baseUrl = $(this).attr('href').split('?')[0];
        var url = baseUrl + '?selectedItems=' + encodeURIComponent(JSON.stringify(selectedItems.map(item => item['Srno'])));
        window.location.href = url;
    });

    $('#outfitForm').submit(function(e) {
        e.preventDefault();
        var formData = new FormData(this);
        formData.append('outfitTitle', $('#outfitTitle').val());
        
        $.ajax({
            url: $(this).attr('action'),
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('body').html(response);
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
            }
        });
    });

    // static/script.js

$(document).ready(function() {
    $('.outfit-slider').slick({
        slidesToShow: 3,
        slidesToScroll: 1,
        autoplay: true,
        autoplaySpeed: 3000,
        arrows: true,
        responsive: [
            {
                breakpoint: 1024,
                settings: {
                    slidesToShow: 2
                }
            },
            {
                breakpoint: 600,
                settings: {
                    slidesToShow: 1
                }
            }
        ]
    });

    $('.outfit-horizontal-scroll').slick({
        slidesToShow: 4,
        slidesToScroll: 1,
        autoplay: true,
        autoplaySpeed: 3000,
        arrows: true,
        responsive: [
            {
                breakpoint: 1024,
                settings: {
                    slidesToShow: 3
                }
            },
            {
                breakpoint: 768,
                settings: {
                    slidesToShow: 2
                }
            },
            {
                breakpoint: 480,
                settings: {
                    slidesToShow: 1
                }
            }
        ]
    });
});
});
