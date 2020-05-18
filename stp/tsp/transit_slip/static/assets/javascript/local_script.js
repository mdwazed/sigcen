$(document).ready(function () {
    // Data table and select2
    $('#data_table_id').DataTable({
        "pageLength": 50,
        "order": [[0, "desc"]]
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

////////////////  delivery setup related function //////////////////

// fetch parent unit of selected child unit for delivery setup
// hide change option during load
$('#change-parent-unit-div').hide()
$('#btn-change-unit').hide()
$('#child-unit').on('change', function(event){
    let child_unit_id = $('#child-unit').val()
    let url = '/get_parent/'
    $.post(url, { 'csrfmiddlewaretoken': csrf_token, 'child_unit_id': child_unit_id},
    function(data, textStatus, jqXHR){
        if (jqXHR.status == 200){
            $('#parent-unit-name').text(data)
            $('#btn-change-unit').show()
        } else {
            alert("failed to retrive unit.")
        }
    });
});

$('#btn-change-unit').on('click', function(event){
    console.log('change btn clicked');
    $('#change-parent-unit-div').show()
});

$('#btn-change-unit-save').on('click', function(event){
    let parent_unit_id  = $('#parent-unit').val();
    let child_unit_id = $('#child-unit').val()
    console.log(parent_unit_id);
    let url = '/change_parent/'
    $.post(url, { 'csrfmiddlewaretoken': csrf_token, 'child_unit_id': child_unit_id,
                'parent_unit_id': parent_unit_id },
        function (data, textStatus, jqXHR) {
            if (jqXHR.status == 204) {
                alert("Delivery option changed Successfully.");
                location.reload();
            }else {
                alert("failed to retrive unit. Try again later.")
            }
        });
});
/////////////////  end delivary setup ///////////////////////

// prevent submission of form if no admin in selected in change-admin-aor
$('#save-admin-aor').on('click', function(event){
    // event.preventDefault()
    admin_user = $('#admin-user').val()
    // alert(admin_user)
    if (!admin_user){
        event.preventDefault()
    }
});
