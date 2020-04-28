// fetch letter to receive in sigcen by ajax call while scaning the QR code
$(document).ready(function () {
    $('#scan-input').on('change', function () {
        var ts_no = $('#scan-input').val()
        

        url = 'through_pkg';
        // console.log('invoking ajax call');
        var data_dict = { 'ts_no': ts_no, 'csrfmiddlewaretoken': csrf_token };
        $.ajax({
            type: 'POST',
            url: url,
            data: data_dict,
            dataType: 'json',
            success: function (response) {
        
                $('#ts-id').text(response.ts_id)
                $('#ts-from').text(response.ts_from)
                $('#ts-to').text(response.ts_to)                
                $('#ts-date').text(response.ts_date)                
            },
            error: function (jqXHR) {
                alert("Error saving 'through pkg' data." + jqXHR.responseText)
            }
        });
        $(this).val('')

    });

});