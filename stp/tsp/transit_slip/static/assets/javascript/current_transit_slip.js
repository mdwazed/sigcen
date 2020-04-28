$(document).ready(function () {
    console.log("current ts loaded");
    $('.through-despatch').on('click',function(event){
        event.preventDefault()
        ts = $(event.target)
        url = 'through_pkg_despatch'
        data_dict = {'csrfmiddlewaretoken': csrf_token, 'ts_id': event.target.id}
        $.ajax({
            type: 'POST',
            url: url,
            data: data_dict,
            // dataType: 'json',
            success: function (response) {
                    ts.closest('tr').remove();             
                },
            
            error: function (jqXHR, error_type, exception) {
                alert(`${exception}-Failed to retrive this TS.` + jqXHR.responseText)
            }
        });
    });
});