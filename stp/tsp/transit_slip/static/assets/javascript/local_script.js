$(document).ready(function () {
    $('#data_table_id').DataTable({
        "pageLength": 50,
    });
    $('.basic-multiple').select2();

    
});

function printWindow() {
    window.print();
}


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