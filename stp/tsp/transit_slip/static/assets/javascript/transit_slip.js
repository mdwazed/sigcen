// used for creating transit slip included in the create_transit_slip.html page
$(document).ready(function () {
    // remove a row/letter from the list on clicking remove btn
    update_count();
    $(".ltr-remove-link").click(function(event){
        event.preventDefault();
        // console.log($(this).parent())
        $(this).closest('tr').remove();
        update_count();
    });
});

function update_count() {
    let ltr_count = $('table tbody tr').length;
    console.log(ltr_count);
    $('#received-count').text(ltr_count);
}; 