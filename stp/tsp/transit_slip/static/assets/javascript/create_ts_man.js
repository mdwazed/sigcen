// fetch letter to receive in sigcen by ajax call while scaning the QR code
$(document).ready(function () {
    // ensure scan-ts input remain invisible on page load
    $('#scan-ts').hide();
    // show scan-ts input box on selecting sta
    $('#id-sta').change(function(){
        $('#scan-ts').show();
        var selected_sta = $(this).children("option:selected").text();
        $('#dst-sta').val(selected_sta);
    });
    //fetch ltr on scan
    $('#scan-ts').on('change', function () {
        // console.log('changed')
        var code = $('#scan-ts').val()
        var str = code.split("-")
        var date_str = str[0].toString()
        var day = date_str.substr(0, 2)
        var mon = date_str.substr(2, 2)
        var year = date_str.substr(4, 4)
        var date_str = year + '-' + mon + '-' + day
        var u_string = str[1]
        // console.log(date_str)
        const rm_lnk_td = '<td><a class="ltr-remove-link" href="#">Remove</a></td></tr>'


        url = 'fetch_letter_json';
        console.log('invoking ajax call');
        var data_dict = { 'date': date_str, 'u_string': u_string, 'csrfmiddlewaretoken': csrf_token, 'ts_making': true };
        $.ajax({
            type: 'POST',
            url: url,
            data: data_dict,
            dataType: 'json',
            success: function (response) {
                console.log(response)
                var ltr = response[0]
                console.log(ltr.pk);
                var ltr_id = '<input type="hidden" name="ltr-ids" value="'+ ltr.pk +'" >';
                var row = "<tr><td>" + ltr.fields.from_unit + "</td><td>" + ltr.fields.to_unit +
                    "</td><td>" + ltr.fields.ltr_no + "</td><td>" + ltr.fields.date + "</td><td>" +
                    ltr.fields.u_string + rm_lnk_td + ltr_id;
                

                $('tbody').prepend($(row).on('click', function(){
                    $(this).remove();
                }));
            },
            error: function(){
                alert('Failed to receive this DAK. details in syslog.')
            }
        });
        $(this).val('')
    });

    
    
});



