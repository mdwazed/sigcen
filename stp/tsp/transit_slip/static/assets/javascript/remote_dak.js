// fetch letter to receive in sigcen by ajax call while scaning the QR code
let ts_id = undefined
let from_sta = undefined
let to_units = new Array();
let from_units = new Array();
let to_unit_names = []
let from_unit_names = []
let dates = new Array()
let codes = new Array()
let ltr_nos = new Array()
let ltr_count = 0;
let domain = undefined;
$(document).ready(function () {
    
    // ensure scan-ts input remain invisible on page load
    domains = JSON.parse(domains_str)
    $('#ts-no').hide();
    $('#err-banner').hide();
    $('#ts-no-label').hide();
    $('#fetch-ltr').hide();
    $('.ts-ltrs').hide();
    // show scan-ts input box on selecting sta
    $('#id-sta').change(function () {
        $('#ts-no').show();
        $('#ts-no-label').show();
        $('#fetch-ltr').show();
    });
    
    //fetch ltr on fetch button click
    $('#fetch-ltr').on('click', function () {
        reinit_var();
        ts_id = $('#ts-no').val()
        from_sta = $('#id-sta').children("option:selected").text();
        console.log(local_sta)
        switch (from_sta){
            // case 'JSR':
            //     domain = domains.JSR;
            //     break;
            // case 'DHK':
            //     domain = domains.DHK;
            //     break;
            default:
                domain = domains.DEFAULT;
                
        } 
        // check from_sta and ts_no entered
        if (typeof domain != 'undefined' && ts_id !=''){
            url = '/api/ts_detail/' + ts_id;
            var data_dict = { 'local_sta': local_sta };
            $.ajax({
                type: 'GET',
                url: url,
                data: data_dict,
                dataType: 'json',
                crossDomain: true,
                xhrFields: {
                    withCredentials: false,
                },
                success: function (response, status) {
                    console.log(response.received_on)
                    ltr_count = response.ltrs.length;
                    if (response.received_on){
                        $('#err-banner').show();
                        $('#err-txt').html('This Transit Slip has already been received.'+
                             'Duplicate receive not possible')
                        $('#receive-btn').hide();
                    }else{
                        $('#err-banner').hide();
                        $('#receive-btn').show();

                    }
                    if (ltr_count > 0){
                        $('.ts-ltrs').show();
                        $('#ts-dst').text(response.dst);
                        $('#ts-id').text(response.id);
                        $('#ts-date').text(response.date);
                        $('#ts-ltr-count').text(ltr_count);

                        for (ltr of response.ltrs) {
                            let ltr_elm = ltr.split('__');
                            from_units.push(ltr_elm[0])
                            to_units.push(ltr_elm[1])
                            dates.push(ltr_elm[2])
                            codes.push(ltr_elm[3])
                            ltr_nos.push(ltr_elm[4])
                        };
                        $.when(populate_from_unit_names(), populate_to_unit_names()).then(render_table);
                        $('#ts-info').val(from_sta+"-"+ts_id)
                    }
                },
                error: function(response, status, error){
                    $('#err-txt').html(response.responseText)
                    $('#err-banner').show();
                },
            });
        }else{
            alert('Error: Not suitable Domain or TS ID!!!');
        };
    }); //end of remote ltr fetch

    // received on remote server and save letter in local server
    $('#receive-btn').on('click', function (event) {
        event.preventDefault();
        let x = confirm("Did you received all the DAK? This action will confirm" +
                        " remote sigcen about your reception of all DAK in this TS.");
        if (x == true) {
            url = '/api/ts_detail/' + ts_id;
            var data_dict = { 'local_sta': local_sta, 'ts_id': ts_id, 'csrfmiddlewaretoken': csrf_token  };
            $.ajax({
                type: 'POST',
                url: url,
                data: data_dict,
                dataType: 'json',
                crossDomain: true,
                xhrFields: {
                    withCredentials: false,
                },
                success: function (response, status) {
                    if (status == 'nocontent'){
                        console.log('remote request success')
                        $('#remote-ltrs').submit()
                    }

                },
                error: function (response, status, error) {
                    $('#err-banner').show();
                    $('#err-txt').html('Failed to receive the DAK.' + response.responseText);
                },
                complete: function () {
                    // console.log('completed');
                }
            });


        }
    })
});

function populate_from_unit_names(){
    const url ='fetch_unit_names/'
    let data_dict = { 'unit_codes': from_units, 'csrfmiddlewaretoken': csrf_token };
    return $.ajax({
        type: 'POST',
        url: url,
        data: data_dict,
        // dataType: 'json',
        success: function (response){
            from_unit_names = response.unit_names
            if(response.found_all_unit == false){
                $('#err-banner').show();
                $('#receive-btn').hide();
                $('#err-txt').html(response.err_msg)
            }
        }
    });
};

function populate_to_unit_names(){
    const url = 'fetch_unit_names/';
    let data_dict = { 'unit_codes': to_units, 'csrfmiddlewaretoken': csrf_token };
    return $.ajax({
        type: 'POST',
        url: url,
        data: data_dict,
        // dataType: 'json',
        success: function (response) {
            to_unit_names = response.unit_names
            if (response.found_all_unit == false) {
                $('#err-banner').show();
                $('#receive-btn').hide();
                $('#err-txt').html(response.err_msg)
            }
        }
    });
};

function render_table(){
    console.log('rendering table');
    for (var i = 0; i < ltr_count; i++) {
        let row = "<tr>" +
            "<td>" + from_unit_names[i] + "<input type='hidden' name='from_unit' value="+from_units[i] +"></td>" +
            "<td>" + to_unit_names[i] + "<input type='hidden' name='to_unit' value=" + to_units[i] +"></td>" +
            "<td>" + dates[i] + "<input type='hidden' name='date' value=" + dates[i] +"></td>" +
            "<td>" + codes[i] + "<input type='hidden' name='code' value=" + codes[i] +"></td>" +
            "<td>" + ltr_nos[i] + "<input type='hidden' name='ltr_no' value=" + ltr_nos[i] +"></td>" +
            "</tr>"
        $('tbody').append(row)
    }
};

function reinit_var(){
    $('tbody').html("")
    ts_id = undefined
    from_sta = undefined
    to_units = []
    from_units = []
    to_unit_names = []
    from_unit_names = []
    dates = []
    codes = []
    ltr_nos = []
    ltr_count = 0;
    domain = undefined;
};