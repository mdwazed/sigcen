// used for creating transit slip included in the transit_slip.html page
$(document).ready(function () {
    $('#id-sta').on('change', function(){

        var choice = $(this).children("option:selected").val();
        url = 'transit_slip_ltrs';
        // console.log(csrf_token);
        var data_dict = { 'sta_id': choice, 'csrfmiddlewaretoken': csrf_token };
        $.ajax({
            type: 'POST',
            url: url,
            data: data_dict,
            success: function (response) {
                console.log(response)
            }
        });
        
    });
});