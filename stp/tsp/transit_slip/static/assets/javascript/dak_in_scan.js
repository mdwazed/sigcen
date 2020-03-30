// fetch letter to receive in sigcen by ajax call while scaning the QR code
$(document).ready(function () {
    $('#scan-input').on('change', function () {
        var code = $('#scan-input').val()
        var str = code.split("-")
        var date_str = str[0].toString()
        var day = date_str.substr(0,2)
        var mon = date_str.substr(2,2)
        var year = date_str.substr(4,4)
        var date_str = year+'-'+mon+'-'+day
        var u_string = str[1]
        // console.log(date_str)

        url = 'fetch_letter_json';
        // console.log('invoking ajax call');
        var data_dict = { 'date': date_str, 'u_string': u_string, 'csrfmiddlewaretoken': csrf_token };
        $.ajax({
            type: 'POST',
            url: url,
            data: data_dict,
            dataType : 'json',
            success: function (response) {
                console.log(response)
                var ltr = response[0]
                var row = "<tr><td>" + ltr.fields.from_unit + "</td><td>" + ltr.fields.to_unit +
                    "</td><td>" + ltr.fields.ltr_no + "</td><td>" + ltr.fields.date + "</td><td>" +
                    ltr.fields.u_string +
                    "</td><td><input type='checkbox' name='received_ltr' value='" + ltr.pk + "' checked></td>" +
                    "<td><input type='checkbox' name='spl_pkg' value='" + ltr.pk + "' ></td></tr>"

                $('tbody').prepend(row)
            },
            error: function(){
                alert('Can not receive this DAk. May be this DAK has already been received or deleted!!')
            }
        });
        $(this).val('')

    });
    
});