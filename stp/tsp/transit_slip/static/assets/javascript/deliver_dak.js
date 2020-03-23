$(document).ready(function(){
    console.log('delivering dak');
    $('#btn-deliver').on('click', function(event){
        let x = confirm('Did you print and sign the receipt?');
        if(x==false){
            event.preventDefault();
        }

    });
    $('#btn-print').on('click', function (event) {
        event.preventDefault();
        window.print()
    });

})