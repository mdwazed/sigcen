$(document).ready(function () {
    // Data table and select2
    $('#data_table_id').DataTable({
        "pageLength": 50,
    });

    $('.basic-multiple').select2();
});

function printWindow() {
    window.print();
}

// save the date of transit slip received by remote sigcen
$('.received-on-save').click(function(){
    let date = $(this).parent().prev().val();
    let ts_id = $(this).parent().next().val();
    let parent_td = $(this).parent().parent().parent();
    url = 'ts_rcv_update';
    var data_dict = { 'ts_id': ts_id, 'date': date, 'csrfmiddlewaretoken': csrf_token };
    $.ajax({
        type: 'POST',
        url: url,
        data: data_dict,
        // dataType: 'json',
        success: function (response, status) {
            parent_td.text(date);
        },
        error: function(response, status){
            alert(response.responseText);
        }
    });

});

//delete a letter by admin regardless of letter status
$('#ltr-delete-admin').on('click', function(event){
    url = '/letter_delete_admin';
    redirect_url = '/search_ltr';
    let r = window.confirm("Are you sure!! This will DELETE the DAK parmanently and all its history.");
    if(r == true){
        $.post(url, {'csrfmiddlewaretoken': csrf_token, 'ltr_id': ltr_id}, function(data, status){
            if(status == 'success' && data =='true'){
                window.location.replace(redirect_url);
            }else{
                alert('There was some problem deleting DAK. Please try later.')
            }
        });
    }
});
// delete a letter by user only before received by sigcen
$('.ltr-delete').on('click', function (event) {
    ltr_id = $(this).siblings('input').val();
    // console.log($(this).siblings('input').val());
    url = '/letter_delete/';
    redirect_url = '/letter_list/inhouse/';
    let r = window.confirm("Are you sure!! This will DELETE the DAK parmanently. If you already have " +
            "printed the Label sigcen will not be able to receive this DAK anymore.");
    if (r == true) {
        $.post(url, { 'csrfmiddlewaretoken': csrf_token, 'ltr_id': ltr_id },
            function (data, status, jqXHR) {
                if (jqXHR.status == 204) {
                    window.location.replace(redirect_url);
                } else {
                    alert('There was some problem deleting DAK. Please try later.')
                }
        });
    }
});

// deliver local dak by unit DR
$('.ltr-deliver').on('click', function (event) {
    ltr_id = $(this).siblings('input').val();
    url = '/letter_local_deliver/';
    redirect_url = '/letter_list/inhouse/';
    let r = window.confirm("Be sure you have delivered the DAK to unit. Sigcen can not receive" + 
                        "this DAK if you proceed.");
    if (r == true) {
        $.post(url, { 'csrfmiddlewaretoken': csrf_token, 'ltr_id': ltr_id }, 
            function (data, status, jqXHR) {
            if (jqXHR.status == 204) {
                window.location.replace(redirect_url);
            } else {
                alert('There was some problem delivering the local DAK. Please try later.')
            }
        });
    }
});

// warn local admin before deleting a user
$('.user-delete').on('click', function(event){
    user_id = $(this).next().val();
    url = '/delete_user/'
    redirect_url = '/user_list/';
    d = window.confirm("This will delete the user permanently. Are you sure?");
    if (d == true){
        console.log('deleting')
        $.post(url, { 'csrfmiddlewaretoken': csrf_token, 'user_id': user_id }, function (data, status) {
            if (status == 'success') {
                window.location.replace(redirect_url);
            } else {
                alert('There was some problem deleting User. Please try later.')
            }
        });
    }
});

// change mouse on hover above accordion header on home page
$('.accordion-header').on('mouseover', function(){
    $(this).css('cursor', 'pointer')
})

// fetch ltr for rtu
$('#rtu-dak-code').on('change', function (event){
    let date_code = $('#rtu-dak-code').val();
    let url = '/fetch_ltr/';
    $.post(url, { 'csrfmiddlewaretoken': csrf_token, 'date_code': date_code },
        function (data) {
            ltr = data[0];
            console.log(ltr);
            $('#from-unit').text(ltr.fields.from_unit);
            $('#to-unit').text(ltr.fields.to_unit);
            $('#ltr-no').text(ltr.fields.ltr_no);
            $('#ltr-date').text(ltr.fields.date);
            $('#orig-pk').val(ltr.pk);

    }, 'json');
});

// create rtu dak entry
$('#btn-dak-rtu').on('click', function(event){
    let orig_pk = $('#orig-pk').val()
    console.log(orig_pk)
    let url = '/create_rtu_ltr/'
    $.post(url, {'csrfmiddlewaretoken': csrf_token, 'orig_pk': orig_pk},
    function(data, textStatus, jqXHR){
        console.log(data)
        console.log(jqXHR.status)
        if(jqXHR.status == 204) {
            alert("rtu ltr created.")
        }
    });

});

// details btn on rtu page
// $('.btn-rtu-details').on('click', function(){

//     let rtu_pk = $(this).siblings('input').val()
//     let url = '/rtu_ltr_details/'
//     $.post(url, { 'csrfmiddlewaretoken': csrf_token, 'rtu_pk': rtu_pk},
//     function(data, textStatus, jqXHR){
        
//     });
// })
