// used for creating transit slip included in the create_transit_slip.html page
$(document).ready(function () {
    // remove a row/letter from the list on clicking remove btn
    $(".ltr-remove-link").click(function(event){
        event.preventDefault();
        // console.log($(this).parent())
        $(this).closest('tr').remove();
    });
});

