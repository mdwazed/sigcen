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

//delete a letter by admin
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