// fetch letter to receive in sigcen by ajax call while scaning the QR code
$(document).ready(function () {
    let selected_sta;
    let codes = [];
    // ensure scan-ts input remain invisible on page load
    $('#scan-ts').hide();
    // show scan-ts input box on selecting sta
    $('#id-sta').change(function(){
        $('#scan-ts').show();
        selected_sta = $(this).children("option:selected").text();
        $('#dst-sta').val(selected_sta);
    });
    //fetch ltr on scan
    $('#scan-ts').on('change', function () {
        var code = $('#scan-ts').val();
        
        var str = code.split("-");
        var date_str = str[0].toString();
        var day = date_str.substr(0, 2);
        var mon = date_str.substr(2, 2);
        var year = date_str.substr(4, 4);
        var date_str = year + '-' + mon + '-' + day;
        var u_string = str[1];
        const rm_lnk_td = '</td><td><a class="ltr-remove-link" href="#">Remove</a></td></tr>'
        url = 'fetch_letter_json';
        // console.log(`invoking ajax call with date ${date_str} u_string ${u_string} dst_data ${selected_sta}`);
        var data_dict = { 'date': date_str, 'u_string': u_string, 'csrfmiddlewaretoken': csrf_token, 
            'ts_making': true, 'dst_sta': selected_sta };
        if(!codes.includes(code)) {
            $.ajax({
                type: 'POST',
                url: url,
                data: data_dict,
                dataType: 'json',
                success: function (response) {
                    var ltr = response[0]
                    var ltr_id = '<input type="hidden" name="ltr-ids" value="' + ltr.pk + '" >';
                    var row = "<tr><td>" + ltr.fields.from_unit + "</td><td>" + ltr.fields.to_unit +
                        "</td><td>" + ltr.fields.ltr_no + "</td><td>" + ltr.fields.date + "</td><td>" +
                        ltr.fields.u_string + rm_lnk_td + ltr_id;
                    $('tbody').prepend($(row).on('click', 'a', function () {
                        $(this).closest('tr').remove();
                        update_count();
                        for(let i = 0; i<codes.length; i++){
                            if (codes[i] == code) {
                                codes.splice(i,1);
                            }
                        }
                    }));
                    codes.push(code);
                },
                error: function (jqXHR, error_type, exception) {
                    alert(`${exception}-Failed to retrive this DAK.` + jqXHR.responseText)
                }
            }).done(function () {
                update_count();
            });
        }else {
            alert('Duplicate DAK scan.');
        }
        
        $(this).val('');
        // update_count();
    });

    $('.table').on('click', function(event) {
        console.log(event.target);
        if (event.target.class == 'ltr-remove-link') {
            // update_count()
        }
    });


});

function update_count() {
    let ltr_count = $('table tbody tr').length;
    console.log(ltr_count);
    $('#received-count').text(ltr_count);
}; 



