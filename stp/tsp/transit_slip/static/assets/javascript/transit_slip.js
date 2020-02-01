// used for creating transit slip included in the transit_slip.html page
$(document).ready(function () {
    console.log('transit slip loaded')
    // not sure why i wrote this function. so commented it out.
    // $('#id-sta').on('change', function(){

    //     var choice = $(this).children("option:selected").val();
    //     url = 'transit_slip_ltrs';
    //     // console.log(csrf_token);
    //     var data_dict = { 'sta_id': choice, 'csrfmiddlewaretoken': csrf_token };
    //     $.ajax({
    //         type: 'POST',
    //         url: url,
    //         data: data_dict,
    //         success: function (response) {
    //             console.log(response)
    //         }
    //     });
        
    // });

    // remove a row/letter from the list before creating transit slip
    $(".ltr-remove-link").click(function(event){
        event.preventDefault();
        // console.log($(this).parent())
        $(this).closest('tr').remove();
    });
});

