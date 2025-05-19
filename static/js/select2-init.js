// Initialize Select2 for teacher and student dropdowns
function initializeSelect2() {
    // Find all select elements with the select2 class
    $('select.select2').each(function() {
        var $select = $(this);
        var id = $select.attr('id');
        
        // Only initialize if this is a student or teacher select
        if (id && (id.includes('student') || id.includes('teacher'))) {
            // Clean up any existing Select2
            $select.select2('destroy');
            
            // Initialize Select2 with AJAX
            $select.select2({
                theme: 'bootstrap-5',
                width: '100%',
                placeholder: 'Search...',
                allowClear: true,
                minimumInputLength: 1,
                dropdownParent: $select.closest('.card-body'),
                ajax: {
                    url: function() {
                        return id.includes('student') ? '/search-students/' : '/search-teachers/';
                    },
                    dataType: 'json',
                    delay: 250,
                    data: function(params) {
                        return {
                            q: params.term,
                            page: params.page
                        };
                    },
                    processResults: function(data, params) {
                        params.page = params.page || 1;
                        return {
                            results: data.results,
                            pagination: {
                                more: (params.page * 20) < data.total_count
                            }
                        };
                    },
                    cache: true
                },
                templateResult: function(data) {
                    if (data.loading) return data.text;
                    return data.full_name || data.username;
                },
                templateSelection: function(data) {
                    return data.full_name || data.username;
                }
            });
            
            // Add custom styling
            $select.next('.select2-container').addClass('form-control');
            
            // Adjust positioning
            $select.closest('.card-body').css('position', 'relative');
        }
    });
}

// Initialize when document is ready
$(document).ready(function() {
    // Initialize Select2 immediately
    initializeSelect2();
    
    // Re-initialize on page load (for redirects)
    window.addEventListener('load', function() {
        initializeSelect2();
    });
    
    // Re-initialize if forms are dynamically loaded
    $(document).ajaxComplete(function() {
        initializeSelect2();
    });
    
    // Also initialize after form submission
    $(document).on('submit', 'form', function() {
        // Wait for the form to be re-rendered
        setTimeout(function() {
            initializeSelect2();
        }, 1000);
    });
});
