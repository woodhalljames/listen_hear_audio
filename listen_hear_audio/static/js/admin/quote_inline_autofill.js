(function($) {
    $(document).ready(function() {
        $(document).on('change', 'select[name$="-package"]', function() {
            var $select = $(this);
            var packageId = $select.val();
            if (!packageId) return;

            var prefix = $select.attr('name').replace('-package', '');

            $.getJSON('/admin/quotes/quoterequest/package-info/' + packageId + '/', function(data) {
                var $priceField = $('[name="' + prefix + '-price_snapshot"]');

                if ($priceField.length && !$priceField.val()) {
                    $priceField.val(data.price);
                }
            });
        });
    });
})(django.jQuery);
