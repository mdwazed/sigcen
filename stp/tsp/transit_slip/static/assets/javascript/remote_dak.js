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
$(document).ready(function () {
    // ensure scan-ts input remain invisible on page load
    domains = JSON.parse(domains_str)
    $('#ts-no').hide();
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
        ts_id = $('#ts-no').val()
        from_sta = $('#id-sta').children("option:selected").text();
        let domain = undefined;
        switch (from_sta){
            case 'JSR':
                domain = domains.JSR
                break;
            case 'DHK':
                domain = domains.DHK;
                break;
            default:
                
        } 

        if (typeof domain != 'undefined' && ts_id !=''){
            url = 'http://'+ domain +'/api/ts_detail/' + ts_id;
            $.ajax({
                type: 'GET',
                url: url,
                dataType: 'json',
                crossDomain: true,
                xhrFields: {
                    withCredentials: false,
                },
                success: function (response) {
                    ltr_count = response.ltrs.length;
                    if (ltr_count > 0){
                        $('.ts-ltrs').show();
                        $('#ts-dst').text(response.dst);
                        $('#ts-id').text(response.id);
                        $('#ts-date').text(response.date);
                        $('#ts-ltr-count').text(ltr_count);
                        // console.log(response.ltrs);

                        for (ltr of response.ltrs) {
                            let ltr_elm = ltr.split('__');
                            from_units.push(ltr_elm[0])
                            to_units.push(ltr_elm[1])
                            dates.push(ltr_elm[2])
                            codes.push(ltr_elm[3])
                            ltr_nos.push(ltr_elm[4])
                        };
                        $.when(populate_form_unit_names(), populate_to_unit_names()).then(render_table);
                        $('#ts-info').val(from_sta+"-"+ts_id)
                    }
                },
            });
        }else{
            alert('Error: Not suitable Domain or TS ID!!!');
        };
        
    }); //end of remote ltr fetch



});

function populate_form_unit_names(){
    console.log('populating from unit name');
    const url ='fetch_unit_names/'
    let data_dict = { 'unit_codes': from_units, 'csrfmiddlewaretoken': csrf_token };
    return $.ajax({
        type: 'POST',
        url: url,
        data: data_dict,
        // dataType: 'json',
        success: function (response){
            from_unit_names = response
            // render_dom()
        }
    });
    data_dict = { 'unit_codes': to_units, 'csrfmiddlewaretoken': csrf_token };
    
};

function populate_to_unit_names(){
    console.log('populating to unit name');
    const url = 'fetch_unit_names/';
    let data_dict = { 'unit_codes': to_units, 'csrfmiddlewaretoken': csrf_token };
    return $.ajax({
        type: 'POST',
        url: url,
        data: data_dict,
        // dataType: 'json',
        success: function (response) {
            to_unit_names = response
            // render_dom()
        }
    });
};

function render_table(){
    console.log('rendering dom');
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
}